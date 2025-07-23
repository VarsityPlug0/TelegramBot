import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict, NetworkError, TimedOut
from openai import OpenAI
import logging
import asyncio
from flask import Flask, request, jsonify

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables for tokens
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEBSITE_URL = 'https://safechain-7o0q.onrender.com/'
KNOWLEDGE_FILE = 'knowledge.txt'
SCRAPE_INTERVAL = 6 * 60 * 60  # 6 hours in seconds

# Initialize OpenAI client with new API format
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Flask app for webhook
app = Flask(__name__)

def scrape_website(url):
    """
    Scrape the website and extract only visible, useful text (ignore nav, ads, footers).
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['nav', 'footer', 'header', 'aside', 'script', 'style', '[document]', 'noscript', 'form', 'input', 'button', 'svg']):
            for match in soup.find_all(tag):
                match.decompose()
        
        # Extract visible text more safely
        texts = []
        for text in soup.stripped_strings:
            if text and text.strip():
                # Check if the text's parent element is not in unwanted tags
                try:
                    parent = text.parent
                    if parent and hasattr(parent, 'name') and parent.name not in ['nav', 'footer', 'header', 'aside', 'script', 'style', 'form', 'input', 'button', 'svg']:
                        texts.append(text.strip())
                except AttributeError:
                    # If we can't get parent info, include the text anyway
                    texts.append(text.strip())
        
        visible_text = '\n'.join(texts)
        return visible_text
    except Exception as e:
        logger.error(f"Error scraping website: {e}")
        return "SafeChain AI - AI-powered investment platform. Please visit our website for detailed information."

def update_knowledge():
    """
    Scrape the website and update the knowledge file.
    """
    try:
        logger.info(f"Scraping website: {WEBSITE_URL}")
        content = scrape_website(WEBSITE_URL)
        
        if content and content.strip():
            with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully updated knowledge base with {len(content)} characters")
        else:
            logger.warning("Warning: Scraped content is empty")
            
    except Exception as e:
        logger.error(f"Error updating knowledge: {e}")
        # Create a minimal knowledge file if scraping fails
        try:
            with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
                f.write("SafeChain AI - AI-powered investment platform. Please visit our website for detailed information.")
            logger.info("Created fallback knowledge file")
        except Exception as write_error:
            logger.error(f"Error creating fallback knowledge file: {write_error}")

def schedule_scraping():
    """
    Schedule scraping every 6 hours in a background thread.
    """
    def loop():
        while True:
            update_knowledge()
            time.sleep(SCRAPE_INTERVAL)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

def load_knowledge():
    """
    Load the knowledge base from the file.
    """
    try:
        if not os.path.exists(KNOWLEDGE_FILE):
            logger.info("Knowledge file not found, attempting to scrape website...")
            update_knowledge()
        
        # Check if file was created successfully
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():  # Check if file has content
                    return content
                else:
                    logger.info("Knowledge file is empty, attempting to scrape again...")
                    update_knowledge()
                    if os.path.exists(KNOWLEDGE_FILE):
                        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                            return f.read()
        
        # If we still don't have content, return a default message
        logger.warning("Could not load knowledge base, using default response")
        return "SafeChain AI - AI-powered investment platform. Please visit our website for detailed information."
        
    except Exception as e:
        logger.error(f"Error loading knowledge: {e}")
        return "SafeChain AI - AI-powered investment platform. Please visit our website for detailed information."

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages and reply using OpenAI's ChatCompletion API.
    """
    try:
        user_message = update.message.text
        knowledge = load_knowledge()
        system_prompt = f"""
You are a helpful assistant. Answer the user's question using the knowledge provided below. If the answer is not found in the knowledge, reply: \"I'm not sure about that — please visit our website for more details.\"

--- BEGIN KNOWLEDGE BASE ---\n{knowledge}\n--- END KNOWLEDGE BASE ---
"""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=512,
                temperature=0.2
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            reply = "Sorry, there was an error processing your request."
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error in answer handler: {e}")
        try:
            await update.message.reply_text("Sorry, something went wrong. Please try again later.")
        except:
            pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, Conflict):
        logger.error("Bot conflict detected - another instance may be running")
    elif isinstance(context.error, NetworkError):
        logger.error("Network error occurred")
    elif isinstance(context.error, TimedOut):
        logger.error("Request timed out")
    else:
        logger.error(f"Unexpected error: {context.error}")

async def setup_webhook():
    """
    Set up webhook for the bot.
    """
    try:
        # Get the webhook URL from environment or use a default
        webhook_url = os.getenv('WEBHOOK_URL', 'https://your-app-name.onrender.com/webhook')
        
        # Build the application
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        logger.info("Telegram Application built.")
        # Add handlers
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer))
        logger.info("Message handler added.")
        application.add_error_handler(error_handler)
        logger.info("Error handler added.")
        # Set webhook
        await application.bot.set_webhook(url=f"{webhook_url}")
        logger.info(f"Webhook set to: {webhook_url}")
        
        return application
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return None

# Global variable to store the application
telegram_app = None

@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    logger.info("Received POST /webhook")
    try:
        if telegram_app is None:
            return jsonify({'error': 'Bot not initialized'}), 500
        
        # Process the update
        update = Update.de_json(request.get_json(), telegram_app.bot)
        await telegram_app.process_update(update)
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Render.
    """
    return jsonify({'status': 'healthy', 'bot': 'SafeChain AI Telegram Bot'})

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint.
    """
    return jsonify({
        'message': 'SafeChain AI Telegram Bot',
        'status': 'running',
        'webhook': 'active'
    })

async def initialize_bot():
    """
    Initialize the bot with webhook.
    """
    global telegram_app
    
    logger.info("Initializing SafeChain AI Telegram Bot with webhook...")
    
    # Initialize knowledge base
    logger.info("Initializing knowledge base...")
    load_knowledge()
    
    # Start background scraping
    logger.info("Starting background scraping scheduler...")
    schedule_scraping()
    
    # Set up webhook
    telegram_app = await setup_webhook()
    
    if telegram_app:
        logger.info("Bot initialized successfully with webhook!")
    else:
        logger.error("Failed to initialize bot")

def main():
    """
    Start the Flask app and initialize the bot.
    """
    logger.info("Starting SafeChain AI Telegram Bot (Webhook Mode)...")
    logger.info(f"Website URL: {WEBSITE_URL}")
    logger.info(f"TELEGRAM_TOKEN length: {len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 'NOT SET'}")
    logger.info(f"OPENAI_API_KEY length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 'NOT SET'}")
    logger.info(f"Knowledge file: {KNOWLEDGE_FILE}")
    
    # Start bot initialization in a background thread so Flask starts immediately
    from threading import Thread
    def background_init():
        import asyncio
        asyncio.run(initialize_bot())
    Thread(target=background_init, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main() 
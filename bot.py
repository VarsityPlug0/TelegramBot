import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict, NetworkError, TimedOut
import openai
import logging

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

openai.api_key = OPENAI_API_KEY

def scrape_website(url):
    """
    Scrape the website and extract only visible, useful text (ignore nav, ads, footers).
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Remove unwanted elements
    for tag in soup(['nav', 'footer', 'header', 'aside', 'script', 'style', '[document]', 'noscript', 'form', 'input', 'button', 'svg']):
        for match in soup.find_all(tag):
            match.decompose()
    # Extract visible text
    texts = [t.strip() for t in soup.stripped_strings if t.parent.name not in ['nav', 'footer', 'header', 'aside', 'script', 'style', 'form', 'input', 'button', 'svg']]
    visible_text = '\n'.join(texts)
    return visible_text

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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, Conflict):
        logger.error("Bot conflict detected - another instance may be running")
    elif isinstance(context.error, NetworkError):
        logger.error("Network error occurred")
    elif isinstance(context.error, TimedOut):
        logger.error("Request timed out")

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
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=512,
                temperature=0.2
            )
            reply = response['choices'][0]['message']['content'].strip()
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

def main():
    """
    Start the Telegram bot and schedule scraping.
    """
    logger.info("Starting SafeChain AI Telegram Bot...")
    logger.info(f"Website URL: {WEBSITE_URL}")
    logger.info(f"Knowledge file: {KNOWLEDGE_FILE}")
    
    # Initialize knowledge base
    logger.info("Initializing knowledge base...")
    load_knowledge()
    
    # Start background scraping
    logger.info("Starting background scraping scheduler...")
    schedule_scraping()
    
    # Start the bot
    logger.info("Starting Telegram bot...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer))
    
    logger.info("Bot is ready! Listening for messages...")
    
    try:
        app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main() 
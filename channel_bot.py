import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict, NetworkError, TimedOut, TelegramError
from openai import OpenAI
import logging
import asyncio
from flask import Flask

health_app = Flask(__name__)

@health_app.route("/healthz")
def healthz():
    return "ok", 200

def run_health_server():
    health_app.run(host="0.0.0.0", port=8080)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your channel ID (e.g., '@yourchannel' or '-1001234567890')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')  # Your Telegram user ID
WEBSITE_URL = 'https://safechain-7o0q.onrender.com/'
KNOWLEDGE_FILE = 'knowledge.txt'
SCRAPE_INTERVAL = 6 * 60 * 60  # 6 hours

# Action links and call-to-action messages
ACTION_LINKS = {
    'website': 'https://safechain-7o0q.onrender.com/',
    'get_started': 'https://safechain-7o0q.onrender.com/get-started',
    'learn_more': 'https://safechain-7o0q.onrender.com/about',
    'contact': 'https://safechain-7o0q.onrender.com/contact',
    'demo': 'https://safechain-7o0q.onrender.com/demo'
}

DEFAULT_ACTION_MESSAGE = """
🚀 **Ready to get started?**

🌐 **Visit our website:** {website}
📚 **Learn more:** {learn_more}
📞 **Contact us:** {contact}
🎯 **Try demo:** {demo}

#SafeChainAI #AIInvestment #Innovation
"""

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def scrape_website(url):
    """
    Scrape the website and extract only visible, useful text.
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
                try:
                    parent = text.parent
                    if parent and hasattr(parent, 'name') and parent.name not in ['nav', 'footer', 'header', 'aside', 'script', 'style', 'form', 'input', 'button', 'svg']:
                        texts.append(text.strip())
                except AttributeError:
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
        try:
            with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
                f.write("SafeChain AI - AI-powered investment platform. Please visit our website for more details.")
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
        
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    return content
                else:
                    logger.info("Knowledge file is empty, attempting to scrape again...")
                    update_knowledge()
                    if os.path.exists(KNOWLEDGE_FILE):
                        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                            return f.read()
        
        logger.warning("Could not load knowledge base, using default response")
        return "SafeChain AI - AI-powered investment platform. Please visit our website for detailed information."
        
    except Exception as e:
        logger.error(f"Error loading knowledge: {e}")
        return "SafeChain AI - AI-powered investment platform. Please visit our website for detailed information."

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming photos and post them to the channel with action links.
    """
    try:
        # Check if message is from admin
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_USER_ID:
            await update.message.reply_text("Sorry, only the admin can post images to the channel.")
            return

        # Get the photo
        photo = update.message.photo[-1]  # Get the highest quality photo
        user_caption = update.message.caption or ""
        
        # Create enhanced caption with action links
        if user_caption:
            # If user provided caption, add action links below
            enhanced_caption = f"{user_caption}\n\n{DEFAULT_ACTION_MESSAGE.format(**ACTION_LINKS)}"
        else:
            # If no caption, use default with action links
            enhanced_caption = f"🚀 **SafeChain AI - AI-Powered Investment Platform**\n\n{DEFAULT_ACTION_MESSAGE.format(**ACTION_LINKS)}"
        
        logger.info(f"Received photo from admin, posting to channel {CHANNEL_ID}")
        
        # Post to channel with enhanced caption
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id,
            caption=enhanced_caption,
            parse_mode='Markdown'
        )
        
        # Confirm to admin
        await update.message.reply_text("✅ Photo posted to channel with action links!")
        
    except Exception as e:
        logger.error(f"Error posting photo to channel: {e}")
        await update.message.reply_text("❌ Error posting photo to channel. Please try again.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming documents (like images sent as files) with action links.
    """
    try:
        # Check if message is from admin
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_USER_ID:
            await update.message.reply_text("Sorry, only the admin can post files to the channel.")
            return

        document = update.message.document
        user_caption = update.message.caption or ""
        
        # Create enhanced caption with action links
        if user_caption:
            enhanced_caption = f"{user_caption}\n\n{DEFAULT_ACTION_MESSAGE.format(**ACTION_LINKS)}"
        else:
            enhanced_caption = f"📄 **SafeChain AI Document**\n\n{DEFAULT_ACTION_MESSAGE.format(**ACTION_LINKS)}"
        
        logger.info(f"Received document from admin, posting to channel {CHANNEL_ID}")
        
        # Post to channel with enhanced caption
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=document.file_id,
            caption=enhanced_caption,
            parse_mode='Markdown'
        )
        
        # Confirm to admin
        await update.message.reply_text("✅ Document posted to channel with action links!")
        
    except Exception as e:
        logger.error(f"Error posting document to channel: {e}")
        await update.message.reply_text("❌ Error posting document to channel. Please try again.")

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming text messages and reply using OpenAI's ChatCompletion API with action links.
    """
    try:
        user_message = update.message.text
        knowledge = load_knowledge()
        system_prompt = f"""
You are a helpful assistant for SafeChain AI. Answer the user's question using the knowledge provided below. 
Always end your response with a call-to-action encouraging them to visit the website or take action.
If the answer is not found in the knowledge, reply: "I'm not sure about that — please visit our website for more details."

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
            ai_reply = response.choices[0].message.content.strip()
            
            # Add action links to the response
            action_links = f"\n\n🚀 **Ready to get started?**\n\n🌐 **Visit our website:** {ACTION_LINKS['website']}\n📚 **Learn more:** {ACTION_LINKS['learn_more']}\n📞 **Contact us:** {ACTION_LINKS['contact']}\n🎯 **Try demo:** {ACTION_LINKS['demo']}"
            
            full_reply = ai_reply + action_links
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            full_reply = f"Sorry, there was an error processing your request.\n\n🌐 **Visit our website:** {ACTION_LINKS['website']}"
            
        await update.message.reply_text(full_reply, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in answer handler: {e}")
        try:
            await update.message.reply_text(f"Sorry, something went wrong. Please try again later.\n\n🌐 **Visit our website:** {ACTION_LINKS['website']}", parse_mode='Markdown')
        except:
            pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    """
    user_id = update.effective_user.id
    if str(user_id) == ADMIN_USER_ID:
        await update.message.reply_text(
            "👋 Welcome Admin! I'm your SafeChain AI Bot.\n\n"
            "📸 **To post images to your channel:**\n"
            "• Send me any photo\n"
            "• Add a caption if you want\n"
            "• I'll post it to your channel with action links\n\n"
            "💬 **To ask questions:**\n"
            "• Just type your question\n"
            "• I'll answer using our website knowledge\n"
            "• All responses include action links\n\n"
            "🔗 **Action Links:**\n"
            "• All posts automatically include website links\n"
            "• Use /links to post action links only\n\n"
            "🔄 **Bot Status:** Always Online"
        )
    else:
        await update.message.reply_text(
            "👋 Welcome! I'm the SafeChain AI Bot.\n\n"
            "💬 Ask me any questions about SafeChain AI and I'll help you!\n\n"
            "🔗 All responses include helpful action links to our website."
        )

async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /links command to post action links to channel.
    """
    try:
        # Check if message is from admin
        user_id = update.effective_user.id
        if str(user_id) != ADMIN_USER_ID:
            await update.message.reply_text("Sorry, only the admin can post to the channel.")
            return

        # Create action links message
        action_message = f"🚀 **SafeChain AI - Take Action Today!**\n\n{DEFAULT_ACTION_MESSAGE.format(**ACTION_LINKS)}"
        
        # Post to channel
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=action_message,
            parse_mode='Markdown'
        )
        
        # Confirm to admin
        await update.message.reply_text("✅ Action links posted to channel!")
        
    except Exception as e:
        logger.error(f"Error posting action links to channel: {e}")
        await update.message.reply_text("❌ Error posting action links to channel. Please try again.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command to check bot status.
    """
    user_id = update.effective_user.id
    if str(user_id) == ADMIN_USER_ID:
        await update.message.reply_text(
            "🤖 **Bot Status Report**\n\n"
            "✅ **Status:** Online and Running\n"
            "📡 **Mode:** Polling (Always Active)\n"
            "🔄 **Knowledge Updates:** Every 6 hours\n"
            "📸 **Channel Posting:** Enabled\n"
            "🎯 **Target Channel:** " + (CHANNEL_ID or "Not configured")
        )
    else:
        await update.message.reply_text("✅ Bot is online and ready to help!")

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

async def keep_alive():
    """
    Keep the bot alive by sending periodic status updates.
    """
    while True:
        try:
            logger.info("🔄 Bot heartbeat - Still alive and running")
            await asyncio.sleep(300)  # Log every 5 minutes
        except Exception as e:
            logger.error(f"Error in keep_alive: {e}")

async def run_channel_bot():
    """
    Run the channel bot with enhanced features.
    """
    logger.info("Starting SafeChain AI Channel Bot...")
    
    # Wait 1 minute before starting to avoid conflicts
    logger.info("Waiting 1 minute before starting to avoid conflicts...")
    await asyncio.sleep(60)
    
    # Initialize knowledge base
    logger.info("Initializing knowledge base...")
    load_knowledge()
    
    # Start background scraping
    logger.info("Starting background scraping scheduler...")
    schedule_scraping()
    
    # Build application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    logger.info("Telegram Application built.")
    # Add error handler
    app.add_error_handler(error_handler)
    logger.info("Error handler added.")
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("links", links_command))
    logger.info("Command handlers added.")
    # Add message handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer))
    logger.info("Message handlers added.")
    logger.info("Bot is ready! Starting polling...")
    
    # Start the bot with enhanced polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30,
        bootstrap_retries=5,
        read_timeout_float=30.0
    )
    
    logger.info("Bot started successfully!")
    
    # Start keep-alive task
    asyncio.create_task(keep_alive())
    
    # Keep the bot running
    try:
        await asyncio.Event().wait()  # Wait indefinitely
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await app.stop()
        await app.shutdown()

def main():
    """
    Start the Telegram channel bot.
    """
    logger.info("Starting SafeChain AI Channel Bot...")
    logger.info(f"Website URL: {WEBSITE_URL}")
    logger.info(f"Channel ID: {CHANNEL_ID}")
    logger.info(f"Admin User ID: {ADMIN_USER_ID}")
    logger.info(f"TELEGRAM_TOKEN length: {len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 'NOT SET'}")
    logger.info(f"OPENAI_API_KEY length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 'NOT SET'}")
    
    try:
        asyncio.run(run_channel_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    # Start health check server in background
    threading.Thread(target=run_health_server, daemon=True).start()
    main() 
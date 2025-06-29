# SafeChain AI Telegram Bot - Step by Step Code Guide

## 🎯 What This Bot Does

This bot automatically:
1. **Scrapes** your website every 6 hours
2. **Stores** the content in a file called `knowledge.txt`
3. **Answers** user questions using AI
4. **Runs 24/7** without stopping

---

## 📝 Step-by-Step Code Explanation

### STEP 1: Import Libraries (Lines 1-15)
```python
import os                    # Step 1a: Access environment variables (tokens)
import time                  # Step 1b: Add delays and timing
import threading            # Step 1c: Run tasks in background
import requests             # Step 1d: Download website content
from bs4 import BeautifulSoup  # Step 1e: Parse HTML from website
from telegram import Update  # Step 1f: Telegram bot framework
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict, NetworkError, TimedOut  # Step 1g: Handle errors
from openai import OpenAI   # Step 1h: Connect to AI service
import logging              # Step 1i: Record bot activities
import asyncio              # Step 1j: Handle multiple tasks at once
```

### STEP 2: Set Up Logging (Lines 17-22)
```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
```
**What this does:**
- **Records** when the bot starts, stops, or encounters errors
- **Shows** timestamps for all activities
- **Helps** you debug problems

### STEP 3: Load Configuration (Lines 24-30)
```python
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')      # Your bot's password
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')      # AI service password
WEBSITE_URL = 'https://safechain-7o0q.onrender.com/'  # Website to read
KNOWLEDGE_FILE = 'knowledge.txt'                  # File to save content
SCRAPE_INTERVAL = 6 * 60 * 60                     # Update every 6 hours
```
**What each line does:**
- **Line 24**: Gets your bot's secret token from environment
- **Line 25**: Gets your AI service key from environment
- **Line 26**: Sets which website to scrape
- **Line 27**: Sets filename to save scraped content
- **Line 28**: Sets how often to update (6 hours = 21,600 seconds)

### STEP 4: Create AI Client (Line 32)
```python
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```
**What this does:**
- **Connects** to OpenAI's AI service
- **Prepares** to send questions and get answers

---

## 🔧 Core Functions Explained

### FUNCTION 1: Scrape Website (Lines 34-58)
```python
def scrape_website(url):
    """
    Downloads and cleans website content
    """
```

**Step-by-step what it does:**
1. **Downloads** the webpage using `requests.get(url)`
2. **Parses** the HTML using BeautifulSoup
3. **Removes** unwanted parts (navigation, ads, footers)
4. **Extracts** only the useful text content
5. **Returns** clean, readable text

**Why remove navigation/footers?**
- **Navigation**: Menu items like "Home", "About" - not useful content
- **Footers**: Copyright info, links - not helpful for answering questions
- **Ads**: Advertisement content - not relevant to your business

### FUNCTION 2: Update Knowledge Base (Lines 60-78)
```python
def update_knowledge():
    """
    Saves fresh website content to file
    """
```

**Step-by-step what it does:**
1. **Calls** `scrape_website()` to get fresh content
2. **Checks** if content is not empty
3. **Saves** content to `knowledge.txt` file
4. **Logs** how many characters were saved
5. **Creates** backup content if scraping fails

### FUNCTION 3: Schedule Updates (Lines 80-87)
```python
def schedule_scraping():
    """
    Runs scraping every 6 hours automatically
    """
```

**Step-by-step what it does:**
1. **Creates** a background thread (runs separately from main bot)
2. **Loops** forever: scrape → wait 6 hours → scrape → wait 6 hours
3. **Runs** as daemon (stops when main program stops)
4. **Doesn't interfere** with bot's message handling

### FUNCTION 4: Load Knowledge (Lines 89-115)
```python
def load_knowledge():
    """
    Reads saved content from file
    """
```

**Step-by-step what it does:**
1. **Checks** if `knowledge.txt` file exists
2. **If missing**: Creates it by scraping website
3. **If empty**: Re-scrapes website
4. **Reads** and returns the content
5. **Provides** fallback message if everything fails

---

## 💬 Message Handling Explained

### Main Message Handler (Lines 117-145)
```python
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles when users send messages
    """
```

**Step-by-step what happens when user sends message:**
1. **Gets** the user's message text
2. **Loads** the knowledge base from file
3. **Creates** a prompt for AI with:
   - Instructions on how to answer
   - The knowledge base content
   - The user's question
4. **Sends** to OpenAI API
5. **Gets** AI response back
6. **Sends** response to user in Telegram
7. **Handles** any errors that occur

**Example of what gets sent to AI:**
```
System: You are a helpful assistant. Answer using the knowledge below.
If you don't know: "I'm not sure about that — please visit our website for more details."

--- KNOWLEDGE BASE ---
SafeChain AI is an AI-powered investment platform...
[More website content here]
--- END KNOWLEDGE BASE ---

User: What services do you offer?
```

---

## ⚠️ Error Handling Explained

### Error Handler (Lines 147-159)
```python
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles different types of errors
    """
```

**Types of errors it handles:**
1. **Conflict errors**: When multiple bot instances are running
2. **Network errors**: When internet connection fails
3. **Timeout errors**: When requests take too long
4. **General errors**: Any other unexpected problems

**What it does for each error:**
- **Logs** the error with details
- **Identifies** what type of error it is
- **Continues** running the bot despite errors

---

## 🚀 Bot Startup Process Explained

### Main Startup Function (Lines 161-200)
```python
async def run_bot_simple():
    """
    Starts the bot step by step
    """
```

**Step-by-step startup process:**

#### Step 1: Announce Start
```python
logger.info("Starting SafeChain AI Telegram Bot (Simple Mode)...")
```
**What it does**: Logs that bot is beginning to start

#### Step 2: Wait to Avoid Conflicts
```python
logger.info("Waiting 2 minutes before starting to avoid conflicts...")
await asyncio.sleep(120)  # Wait 2 minutes
```
**Why wait 2 minutes?**
- **Prevents** conflicts with other bot instances
- **Allows** any existing instances to finish
- **Ensures** clean startup

#### Step 3: Load Knowledge Base
```python
logger.info("Initializing knowledge base...")
load_knowledge()
```
**What it does**: Makes sure knowledge base is ready before starting

#### Step 4: Start Background Scraping
```python
logger.info("Starting background scraping scheduler...")
schedule_scraping()
```
**What it does**: Begins the automatic website updates every 6 hours

#### Step 5: Build Bot Application
```python
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_error_handler(error_handler)
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer))
```
**What each line does:**
- **Line 1**: Creates the bot application with your token
- **Line 2**: Adds error handling to the bot
- **Line 3**: Tells bot to call `answer()` function when users send text messages

#### Step 6: Start Listening for Messages
```python
await app.initialize()
await app.start()
await app.updater.start_polling(
    drop_pending_updates=True,    # Ignore old messages
    allowed_updates=Update.ALL_TYPES,  # Handle all message types
    timeout=60,                   # Wait 60 seconds for responses
    read_timeout=60,
    write_timeout=60,
    connect_timeout=60,
    pool_timeout=60
)
```
**What this does:**
- **Initializes** the bot
- **Starts** the bot
- **Begins polling** (checking for new messages every few seconds)
- **Sets timeouts** to prevent hanging

#### Step 7: Keep Bot Running
```python
try:
    await asyncio.Event().wait()  # Run forever
except KeyboardInterrupt:
    logger.info("Bot stopped by user")
finally:
    await app.stop()
    await app.shutdown()
```
**What this does:**
- **Keeps** the bot running indefinitely
- **Handles** when user stops the bot (Ctrl+C)
- **Cleans up** when stopping

---

## 🛠️ Deployment Configuration Explained

### Render Configuration (render.yaml)
```yaml
services:
  - type: worker              # Background worker (not web service)
    name: safechain-telegram-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: TELEGRAM_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
    autoDeploy: true
```

**What each line does:**
- **`type: worker`**: Tells Render this is a background process (not a website)
- **`name`**: Name of your service on Render
- **`env: python`**: Use Python environment
- **`buildCommand`**: Install required packages
- **`startCommand`**: Run the bot
- **`envVars`**: Environment variables (set in Render dashboard)
- **`autoDeploy`**: Automatically update when you push code changes

---

## 📊 How the Bot Works Daily

### Daily Operation Timeline:
```
12:00 AM - Bot starts, waits 2 minutes, loads knowledge
12:02 AM - Bot begins listening for messages
 6:00 AM - Background scraper updates knowledge base
12:00 PM - Background scraper updates knowledge base
 6:00 PM - Background scraper updates knowledge base
12:00 AM - Background scraper updates knowledge base
```

### When User Sends Message:
```
1. User types: "What services do you offer?"
2. Bot loads knowledge.txt file
3. Bot sends to OpenAI: "Answer using this knowledge: [content]"
4. OpenAI responds: "SafeChain AI offers..."
5. Bot sends response to user
6. Total time: ~2-3 seconds
```

---

## 🔍 Monitoring Your Bot

### Good Signs (✅):
- `"Bot started successfully!"` - Bot is running
- `"Successfully updated knowledge base"` - Content updated
- `"HTTP Request: POST"` - API calls working

### Warning Signs (⚠️):
- `"Bot conflict detected"` - Multiple instances running
- `"Error scraping website"` - Website issues

### Problem Signs (❌):
- `"OpenAI API error"` - AI service issues
- `"Network error"` - Connection problems

---

## 🎯 Key Points to Remember

### Code Organization:
- **Each function has one job** - Easy to understand
- **Clear variable names** - Self-explanatory
- **Good error handling** - Bot keeps running even with problems
- **Comprehensive logging** - Easy to track what's happening

### Deployment:
- **Worker service type** - No port binding needed
- **Environment variables** - Secure way to store secrets
- **Auto-deploy** - Updates automatically when you push code

### Maintenance:
- **Check logs regularly** - Monitor bot health
- **Knowledge updates every 6 hours** - Content stays fresh
- **Error monitoring** - Fix issues quickly 
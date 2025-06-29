# SafeChain AI Telegram Bot - Code Structure Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Core Functions](#core-functions)
4. [Message Handling](#message-handling)
5. [Error Handling](#error-handling)
6. [Bot Startup Process](#bot-startup-process)
7. [Deployment Configuration](#deployment-configuration)

---

## 🎯 Overview

This bot is a **Telegram chatbot** that:
- **Scrapes** your website for information
- **Stores** the content in a knowledge base
- **Answers** user questions using OpenAI's GPT
- **Runs continuously** in polling mode

---

## ⚙️ Setup & Configuration

### Step 1: Import Required Libraries
```python
# Line 1-15: Essential imports
import os                    # For environment variables
import time                  # For delays and scheduling
import threading            # For background tasks
import requests             # For web scraping
from bs4 import BeautifulSoup  # For HTML parsing
from telegram import Update  # Telegram bot framework
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict, NetworkError, TimedOut  # Error handling
from openai import OpenAI   # OpenAI API client
import logging              # For logging bot activity
import asyncio              # For async operations
```

### Step 2: Configure Logging
```python
# Line 17-22: Set up logging system
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
```
**Purpose**: Tracks bot activity and helps with debugging

### Step 3: Load Environment Variables
```python
# Line 24-30: Configuration settings
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')      # Your bot's unique token
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')      # OpenAI API access key
WEBSITE_URL = 'https://safechain-7o0q.onrender.com/'  # Website to scrape
KNOWLEDGE_FILE = 'knowledge.txt'                  # File to store scraped content
SCRAPE_INTERVAL = 6 * 60 * 60                     # Update every 6 hours
```

### Step 4: Initialize OpenAI Client
```python
# Line 32: Create OpenAI client for AI responses
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

---

## 🔧 Core Functions

### Function 1: Website Scraping
```python
# Line 34-58: scrape_website(url)
def scrape_website(url):
    """
    Scrapes website and extracts useful text content
    """
```

**Step-by-step process:**
1. **Make HTTP request** to the website
2. **Parse HTML** using BeautifulSoup
3. **Remove unwanted elements** (navigation, footers, ads)
4. **Extract visible text** from remaining elements
5. **Return cleaned content**

**Key features:**
- Filters out navigation, footers, scripts, and ads
- Only keeps meaningful content
- Handles errors gracefully

### Function 2: Knowledge Base Management
```python
# Line 60-78: update_knowledge()
def update_knowledge():
    """
    Updates the knowledge base with fresh website content
    """
```

**Step-by-step process:**
1. **Call scrape_website()** to get fresh content
2. **Check if content is valid** (not empty)
3. **Save to knowledge.txt** file
4. **Log the update** for monitoring
5. **Create fallback content** if scraping fails

### Function 3: Background Scheduling
```python
# Line 80-87: schedule_scraping()
def schedule_scraping():
    """
    Runs scraping every 6 hours in background
    """
```

**Step-by-step process:**
1. **Create background thread** that runs continuously
2. **Call update_knowledge()** every 6 hours
3. **Sleep between updates** to avoid overwhelming the server
4. **Run as daemon thread** (stops when main program stops)

### Function 4: Knowledge Loading
```python
# Line 89-115: load_knowledge()
def load_knowledge():
    """
    Loads knowledge base from file
    """
```

**Step-by-step process:**
1. **Check if knowledge file exists**
2. **If not found**: Create it by scraping website
3. **If file is empty**: Re-scrape website
4. **Read and return content**
5. **Provide fallback message** if all else fails

---

## 💬 Message Handling

### Main Message Handler
```python
# Line 117-145: answer(update, context)
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming user messages
    """
```

**Step-by-step process:**
1. **Extract user message** from Telegram update
2. **Load knowledge base** from file
3. **Create system prompt** with knowledge and instructions
4. **Call OpenAI API** with user's question
5. **Send response** back to user
6. **Handle errors** gracefully

**AI Prompt Structure:**
```
System: You are a helpful assistant. Answer using the knowledge below.
If not found: "I'm not sure about that — please visit our website for more details."

--- KNOWLEDGE BASE ---
[Website content here]
--- END KNOWLEDGE BASE ---

User: [User's question]
```

---

## ⚠️ Error Handling

### Error Handler Function
```python
# Line 147-159: error_handler(update, context)
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles various bot errors
    """
```

**Types of errors handled:**
1. **Conflict errors** - Multiple bot instances running
2. **Network errors** - Connection issues
3. **Timeout errors** - Request timeouts
4. **General errors** - Any other unexpected issues

**Error handling strategy:**
- **Log all errors** for debugging
- **Identify error type** for specific handling
- **Continue bot operation** despite errors

---

## 🚀 Bot Startup Process

### Main Startup Function
```python
# Line 161-200: run_bot_simple()
async def run_bot_simple():
    """
    Main bot startup sequence
    """
```

**Step-by-step startup process:**

#### Step 1: Initial Setup
```python
logger.info("Starting SafeChain AI Telegram Bot (Simple Mode)...")
```

#### Step 2: Conflict Prevention
```python
logger.info("Waiting 2 minutes before starting to avoid conflicts...")
await asyncio.sleep(120)  # Wait 2 minutes
```
**Purpose**: Prevents conflicts with other bot instances

#### Step 3: Initialize Knowledge
```python
logger.info("Initializing knowledge base...")
load_knowledge()
```
**Purpose**: Ensures knowledge base is ready

#### Step 4: Start Background Tasks
```python
logger.info("Starting background scraping scheduler...")
schedule_scraping()
```
**Purpose**: Begins periodic website updates

#### Step 5: Build Bot Application
```python
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_error_handler(error_handler)
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), answer))
```
**Purpose**: Configure bot with handlers

#### Step 6: Start Polling
```python
await app.initialize()
await app.start()
await app.updater.start_polling(
    drop_pending_updates=True,    # Ignore old messages
    allowed_updates=Update.ALL_TYPES,  # Handle all message types
    timeout=60,                   # Various timeout settings
    read_timeout=60,
    write_timeout=60,
    connect_timeout=60,
    pool_timeout=60
)
```
**Purpose**: Begin listening for messages

#### Step 7: Keep Running
```python
try:
    await asyncio.Event().wait()  # Run indefinitely
except KeyboardInterrupt:
    logger.info("Bot stopped by user")
finally:
    await app.stop()
    await app.shutdown()
```
**Purpose**: Keep bot running until stopped

---

## 🛠️ Deployment Configuration

### Render Configuration File
```yaml
# render.yaml
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

**Key Configuration Points:**
1. **Service Type**: `worker` (not `web`) - No port binding needed
2. **Environment**: Python runtime
3. **Build Command**: Install dependencies
4. **Start Command**: Run the bot
5. **Environment Variables**: Set in Render dashboard
6. **Auto Deploy**: Automatic updates on code changes

---

## 📊 Bot Workflow Summary

### Daily Operation Flow:
1. **Bot starts** → Waits 2 minutes → Initializes knowledge
2. **Background scraping** → Updates every 6 hours
3. **Message handling** → Processes user questions
4. **AI responses** → Uses OpenAI + knowledge base
5. **Continuous operation** → Runs 24/7

### Error Recovery:
- **Network issues** → Automatic retry
- **API errors** → Graceful fallback
- **Scraping failures** → Use cached content
- **Bot conflicts** → Wait and retry

---

## 🔍 Monitoring & Logs

### Key Log Messages to Watch:
- ✅ `"Bot started successfully!"` - Bot is running
- ✅ `"Successfully updated knowledge base"` - Content updated
- ✅ `"HTTP Request: POST"` - API calls working
- ⚠️ `"Bot conflict detected"` - Multiple instances
- ❌ `"Error scraping website"` - Scraping issues
- ❌ `"OpenAI API error"` - AI service issues

### Performance Indicators:
- **Message response time** - Should be under 5 seconds
- **Knowledge base size** - Should be 1000+ characters
- **Scraping frequency** - Every 6 hours
- **Error frequency** - Should be minimal

---

## 🎯 Best Practices

### Code Organization:
- **Clear function names** - Easy to understand
- **Comprehensive logging** - Track all activities
- **Error handling** - Graceful failure recovery
- **Modular design** - Separate concerns

### Deployment:
- **Worker service type** - Avoids port binding issues
- **Environment variables** - Secure configuration
- **Auto-deploy** - Easy updates
- **Health monitoring** - Track bot status

### Maintenance:
- **Regular log review** - Monitor performance
- **Knowledge base updates** - Keep content fresh
- **Error monitoring** - Address issues quickly
- **Backup strategy** - Protect bot data 
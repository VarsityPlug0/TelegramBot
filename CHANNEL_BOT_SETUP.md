# SafeChain AI Channel Bot Setup Guide

## 🎯 What This Bot Does

This enhanced bot can:
1. **📸 Post images to your Telegram channel** - Send photos to the bot, they get posted to your channel
2. **💬 Answer questions** - Uses AI to answer questions about SafeChain AI
3. **🔄 Stay always online** - Enhanced polling with keep-alive mechanism
4. **🛡️ Admin-only posting** - Only you can post images to the channel

---

## ⚙️ Setup Instructions

### Step 1: Get Your Telegram User ID

1. **Start a chat** with @userinfobot on Telegram
2. **Send any message** to the bot
3. **Copy your User ID** (it will be a number like `123456789`)

### Step 2: Get Your Channel ID

#### Option A: If your channel is public (has @username)
- Your channel ID is: `@yourchannelname`
- Example: If your channel is @safechain_ai, use `@safechain_ai`

#### Option B: If your channel is private
1. **Add @userinfobot** to your channel
2. **Send any message** in the channel
3. **Copy the Chat ID** (it will be like `-1001234567890`)

### Step 3: Add Bot to Your Channel

1. **Go to your channel** in Telegram
2. **Click on channel name** → **Administrators**
3. **Click "Add Administrator"**
4. **Search for your bot** (using the bot's username)
5. **Add the bot** with these permissions:
   - ✅ **Post Messages**
   - ✅ **Edit Messages**
   - ✅ **Delete Messages** (optional)

### Step 4: Configure Environment Variables

In your **Render Dashboard**:

1. **Go to your service** (safechain-telegram-bot)
2. **Click "Environment"** tab
3. **Add these variables:**

```
TELEGRAM_TOKEN = your_bot_token
OPENAI_API_KEY = your_openai_key
CHANNEL_ID = @yourchannelname (or -1001234567890)
ADMIN_USER_ID = your_telegram_user_id
```

**Example:**
```
TELEGRAM_TOKEN = 8115600534:AAEXbjgs0dq0iV7XeJCMujJ2yYFvVDDAAcA
OPENAI_API_KEY = sk-your-openai-key-here
CHANNEL_ID = @safechain_ai
ADMIN_USER_ID = 123456789
```

---

## 🚀 How to Use the Bot

### For Posting Images:

1. **Send a photo** to your bot
2. **Add a caption** (optional) - this will be the post caption
3. **Bot will post** the image to your channel
4. **You'll get confirmation** message

### For Asking Questions:

1. **Type any question** to the bot
2. **Bot will answer** using SafeChain AI knowledge
3. **Responses are AI-generated** based on your website

### Bot Commands:

- `/start` - Welcome message and instructions
- `/status` - Check bot status (admin only)

---

## 🔧 Features Explained

### Image Posting System:
```python
# When you send a photo to the bot:
1. Bot checks if you're the admin
2. Gets the highest quality version of your photo
3. Posts it to your channel with your caption
4. Sends you a confirmation message
```

### Always Online System:
```python
# Enhanced polling with:
- Faster timeout settings (30 seconds)
- Keep-alive heartbeat every 5 minutes
- Automatic retry on connection issues
- Better error handling
```

### Admin Security:
```python
# Only you can post images:
- Checks your Telegram User ID
- Rejects posts from non-admin users
- Keeps your channel secure
```

---

## 📱 Example Usage

### Posting an Image:
```
You: [Send photo of SafeChain AI logo]
Bot: ✅ Photo posted to channel successfully!
```

### Adding Caption:
```
You: [Send photo] + "Check out our new AI features!"
Bot: ✅ Photo posted to channel successfully!
```

### Asking Questions:
```
You: What services does SafeChain AI offer?
Bot: SafeChain AI offers AI-powered investment solutions...
```

---

## 🔍 Troubleshooting

### Bot Not Posting Images:
- ✅ Check if you're the admin (correct ADMIN_USER_ID)
- ✅ Check if bot has posting permissions in channel
- ✅ Check if CHANNEL_ID is correct

### Bot Going Offline:
- ✅ Check Render logs for errors
- ✅ Verify all environment variables are set
- ✅ Check if bot token is valid

### Permission Errors:
- ✅ Make sure bot is admin in your channel
- ✅ Give bot "Post Messages" permission
- ✅ Check if channel ID format is correct

---

## 🎯 Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Your bot's token | `8115600534:AAEXbjgs0dq0iV7XeJCMujJ2yYFvVDDAAcA` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-your-key-here` |
| `CHANNEL_ID` | Your channel ID | `@safechain_ai` or `-1001234567890` |
| `ADMIN_USER_ID` | Your Telegram user ID | `123456789` |

---

## 🚀 Deployment

1. **Push your code** to GitHub
2. **Render will auto-deploy** the new channel bot
3. **Set environment variables** in Render dashboard
4. **Test the bot** by sending a photo

---

## 📊 Monitoring

### Good Signs:
- ✅ `"Bot started successfully!"`
- ✅ `"Photo posted to channel successfully!"`
- ✅ `"Bot heartbeat - Still alive and running"`

### Warning Signs:
- ⚠️ `"Error posting photo to channel"`
- ⚠️ `"Bot conflict detected"`

### Problem Signs:
- ❌ `"Permission denied"`
- ❌ `"Channel not found"`

---

## 🎉 Success!

Once configured, your bot will:
- **Stay online 24/7**
- **Post your images to the channel**
- **Answer questions about SafeChain AI**
- **Provide admin-only security**

Your channel will have a professional, automated posting system! 🚀 
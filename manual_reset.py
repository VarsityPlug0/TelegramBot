#!/usr/bin/env python3
"""
Manual Bot Reset Script
Run this to force clear all bot conflicts
"""

import requests
import os
import time

def manual_reset():
    """Manually reset the bot state."""
    
    # Get token from environment
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN not found in environment")
        return False
    
    base_url = f"https://api.telegram.org/bot{token}"
    
    print("🔄 Manual Bot Reset")
    print("=" * 40)
    
    try:
        # 1. Verify bot
        print("1. Verifying bot...")
        response = requests.get(f"{base_url}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot: @{bot_info['result']['username']}")
        else:
            print(f"❌ Invalid token: {response.status_code}")
            return False
        
        # 2. Delete webhook multiple times
        print("2. Deleting webhooks...")
        for i in range(5):
            response = requests.get(f"{base_url}/deleteWebhook")
            print(f"   Attempt {i+1}: {response.status_code}")
            time.sleep(1)
        
        # 3. Clear all updates
        print("3. Clearing updates...")
        response = requests.get(f"{base_url}/getUpdates?offset=-1")
        if response.status_code == 200:
            updates = response.json()
            print(f"   Cleared {len(updates['result'])} updates")
        else:
            print(f"   Error: {response.status_code}")
        
        # 4. Test for conflicts
        print("4. Testing for conflicts...")
        for i in range(10):
            response = requests.get(f"{base_url}/getUpdates?limit=1")
            if response.status_code == 200:
                print(f"✅ No conflicts (attempt {i+1})")
                return True
            elif response.status_code == 409:
                print(f"⚠️  Conflict exists (attempt {i+1})")
            else:
                print(f"⚠️  Unexpected: {response.status_code}")
            
            if i < 9:
                time.sleep(3)
        
        print("❌ Conflicts persist after all attempts")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = manual_reset()
    if success:
        print("\n🎉 Reset successful! Bot should start without conflicts.")
    else:
        print("\n❌ Reset failed. Manual intervention may be needed.") 
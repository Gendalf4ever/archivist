#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify bot configuration and database"""

import sys
import traceback
import os

# Установка кодировки для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

print("=" * 50)
print("[BOT] Archivist Bot - Test Script")
print("=" * 50)

# Test 1: Config
print("\n[1/4] Testing config...")
try:
    from config import BOT_TOKEN, BOT_USERNAME, DATABASE_URL
    print(f"OK Config imported")
    print(f"  BOT_TOKEN: {BOT_TOKEN[:20]}...")
    print(f"  BOT_USERNAME: {BOT_USERNAME}")
    print(f"  DATABASE_URL: {DATABASE_URL}")
except Exception as e:
    print(f"ERROR Config: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Database
print("\n[2/4] Testing database...")
try:
    import database as db
    print(f"OK Database module imported")
    
    # Try to query
    links = db.session.query(db.Link).limit(1).all()
    print(f"OK Database query - found {len(links)} links")
    
    presets = db.session.query(db.Preset).limit(1).all()
    print(f"OK Presets query - found {len(presets)} presets")
except Exception as e:
    print(f"ERROR Database: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Bot imports
print("\n[3/4] Testing bot imports...")
try:
    import logging
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    print(f"OK All imports successful")
except Exception as e:
    print(f"ERROR Imports: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Bot functions
print("\n[4/4] Testing bot functions...")
try:
    from bot import extract_links, extract_youtube_title, format_links_response
    
    # Test link extraction
    test_text = "Check this: https://example.com and https://youtube.com/watch?v=abc"
    links = extract_links(test_text)
    print(f"OK extract_links: found {len(links)} links")
    
    # Test youtube title extraction
    test_yt = "Amazing Video\nhttps://youtube.com/watch?v=123"
    title = extract_youtube_title(test_yt)
    print(f"OK extract_youtube_title: {title}")
    
    # Test format
    print(f"OK format_links_response: function available")
    
except Exception as e:
    print(f"ERROR Bot functions: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("SUCCESS: All tests passed! Bot is ready.")
print("=" * 50)
print("\nRun bot with: python bot.py\n")

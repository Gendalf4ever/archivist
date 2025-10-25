#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper to run Archivist Bot
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    
print("\n" + "="*60)
print("[ARCHIVIST BOT] Starting...")
print("="*60 + "\n")

try:
    from bot import main
    main()
except KeyboardInterrupt:
    print("\n\n[BOT] Bot stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERROR] Bot crashed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

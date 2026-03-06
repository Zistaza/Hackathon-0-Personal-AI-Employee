#!/usr/bin/env python3
"""
LinkedIn Authentication Helper
==============================

Interactive script to authenticate with LinkedIn and save session.

Usage:
    python authenticate.py

This will:
1. Open LinkedIn in a browser window
2. Wait for you to log in manually
3. Save your session for automated posting
4. Verify authentication was successful
"""

import sys
import asyncio
import json
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed")
    print("Install with: pip install playwright && playwright install chromium")
    sys.exit(1)


async def authenticate_linkedin():
    """Interactive LinkedIn authentication"""

    # Load config
    config_file = Path(__file__).parent / "config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get LinkedIn config
    linkedin_config = config['platforms']['linkedin']
    browser_config = config['browser']

    # Session directory
    base_dir = Path(__file__).parent.parent.parent
    session_dir = base_dir / "Sessions" / linkedin_config['session_dir']
    session_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("LINKEDIN AUTHENTICATION")
    print("=" * 60)
    print(f"Session directory: {session_dir}")
    print()
    print("Instructions:")
    print("1. A browser window will open")
    print("2. Log in to LinkedIn manually")
    print("3. Once logged in, press ENTER in this terminal")
    print("4. The session will be saved for automated posting")
    print()
    print("=" * 60)
    input("Press ENTER to start...")

    # Start Playwright
    playwright = await async_playwright().start()

    try:
        # Launch persistent context (saves session automatically)
        print("\nOpening browser...")
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport=browser_config.get('viewport', {'width': 1280, 'height': 720}),
            user_agent=browser_config.get('user_agent')
        )

        # Open LinkedIn
        page = context.pages[0] if context.pages else await context.new_page()
        print("Navigating to LinkedIn...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded')

        print("\n" + "=" * 60)
        print("PLEASE LOG IN TO LINKEDIN IN THE BROWSER WINDOW")
        print("=" * 60)
        print("\nOnce you're logged in and can see your feed,")
        print("press ENTER in this terminal to continue...")
        input()

        # Verify authentication
        print("\nVerifying authentication...")
        current_url = page.url

        if 'linkedin.com/feed' in current_url or 'linkedin.com/in/' in current_url:
            print("✅ Authentication successful!")
            print(f"Current URL: {current_url}")

            # Take a screenshot for verification
            screenshot_path = base_dir / "Logs" / "linkedin_auth_success.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved: {screenshot_path}")

            print("\n" + "=" * 60)
            print("SESSION SAVED SUCCESSFULLY")
            print("=" * 60)
            print("\nYour LinkedIn session has been saved.")
            print("You can now use automated posting.")
            print("\nClosing browser in 3 seconds...")
            await asyncio.sleep(3)

        else:
            print("⚠️  Warning: You may not be logged in")
            print(f"Current URL: {current_url}")
            print("\nPlease verify you're logged in to LinkedIn")
            print("Press ENTER to close...")
            input()

        # Close browser
        await context.close()
        await playwright.stop()

        print("\n✅ Done!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        await playwright.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(authenticate_linkedin())

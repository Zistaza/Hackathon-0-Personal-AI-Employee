#!/usr/bin/env python3
"""
Simple LinkedIn Authentication
Just opens LinkedIn and waits for you to confirm you're logged in
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def authenticate_linkedin():
    """Authenticate LinkedIn - simplified version"""
    print("=" * 60)
    print("LinkedIn Authentication (Simplified)")
    print("=" * 60)
    print()

    session_dir = Path(__file__).parent / "linkedin_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print("Opening LinkedIn in browser...")
    print("Please log in if needed and navigate to your feed.")
    print()

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to LinkedIn feed
        print("Navigating to LinkedIn...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)

        print()
        print("Browser is open. Please:")
        print("  1. Log in if prompted")
        print("  2. Wait for your feed to load")
        print("  3. Press ENTER here when you see your feed")
        print()

        # Wait for user confirmation
        input("Press ENTER when you're logged in and see your feed: ")

        print()
        print("Saving session...")
        await asyncio.sleep(2)

        print("✓ LinkedIn authentication complete!")
        print("✓ Session saved to:", session_dir)
        print()

        await context.close()

    finally:
        await playwright.stop()

    return True


async def authenticate_whatsapp():
    """Authenticate WhatsApp - simplified version"""
    print("=" * 60)
    print("WhatsApp Authentication (Simplified)")
    print("=" * 60)
    print()

    session_dir = Path(__file__).parent / "whatsapp_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print("Opening WhatsApp Web in browser...")
    print("Please scan the QR code if shown.")
    print()

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to WhatsApp
        print("Navigating to WhatsApp Web...")
        await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)

        print()
        print("Browser is open. Please:")
        print("  1. Scan the QR code if shown")
        print("  2. Wait for your chats to load")
        print("  3. Press ENTER here when you see your chats")
        print()

        # Wait for user confirmation
        input("Press ENTER when you're logged in and see your chats: ")

        print()
        print("Saving session...")
        await asyncio.sleep(2)

        print("✓ WhatsApp authentication complete!")
        print("✓ Session saved to:", session_dir)
        print()

        await context.close()

    finally:
        await playwright.stop()

    return True


async def main():
    """Main menu"""
    while True:
        print()
        print("=" * 60)
        print("Simple Browser Authentication")
        print("=" * 60)
        print()
        print("1) Authenticate WhatsApp")
        print("2) Authenticate LinkedIn")
        print("3) Authenticate Both")
        print("4) Exit")
        print()

        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            try:
                await authenticate_whatsapp()
            except Exception as e:
                print(f"\n✗ Error: {e}\n")

        elif choice == "2":
            try:
                await authenticate_linkedin()
            except Exception as e:
                print(f"\n✗ Error: {e}\n")

        elif choice == "3":
            try:
                await authenticate_whatsapp()
                await authenticate_linkedin()
            except Exception as e:
                print(f"\n✗ Error: {e}\n")

        elif choice == "4":
            print()
            print("Done! Restart the watchers with: pm2 restart ai-watchers")
            print()
            break

        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    asyncio.run(main())

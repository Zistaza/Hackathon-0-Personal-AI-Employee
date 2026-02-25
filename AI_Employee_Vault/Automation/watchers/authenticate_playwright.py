#!/usr/bin/env python3
"""
Playwright Authentication Helper
Authenticates WhatsApp and LinkedIn using Playwright's browser
This ensures session compatibility with the watchers
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def authenticate_whatsapp():
    """Authenticate WhatsApp using Playwright"""
    print("=" * 60)
    print("WhatsApp Authentication (Playwright)")
    print("=" * 60)
    print()
    print("A browser window will open with WhatsApp Web.")
    print("Scan the QR code with your phone and wait for chats to load.")
    print()
    input("Press ENTER to start...")

    session_dir = Path(__file__).parent / "whatsapp_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("Opening WhatsApp Web...")
    print()

    playwright = await async_playwright().start()

    try:
        # Launch browser in non-headless mode
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to WhatsApp
        await page.goto('https://web.whatsapp.com', wait_until='networkidle')

        print("Waiting for WhatsApp to load...")
        print("Please scan the QR code if shown.")
        print()

        # Wait for either QR code or chat list
        await page.wait_for_selector(
            'canvas[aria-label="Scan me!"], [data-testid="chat-list"]',
            timeout=60000
        )

        # Check if QR code is present
        qr_code = await page.query_selector('canvas[aria-label="Scan me!"]')

        if qr_code:
            print("QR code detected - please scan with your phone")
            print("Waiting for login (up to 3 minutes)...")
            await page.wait_for_selector('[data-testid="chat-list"]', timeout=180000)
            print()
            print("✓ Login successful!")
        else:
            print("✓ Already logged in!")

        # Wait a bit for session to save
        await asyncio.sleep(3)

        print()
        print("✓ WhatsApp authentication complete!")
        print("✓ Session saved to:", session_dir)
        print()

        await context.close()

    finally:
        await playwright.stop()

    return True


async def authenticate_linkedin():
    """Authenticate LinkedIn using Playwright"""
    print("=" * 60)
    print("LinkedIn Authentication (Playwright)")
    print("=" * 60)
    print()
    print("A browser window will open with LinkedIn.")
    print("Log in with your credentials and wait for your feed to load.")
    print()
    input("Press ENTER to start...")

    session_dir = Path(__file__).parent / "linkedin_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("Opening LinkedIn...")
    print()

    playwright = await async_playwright().start()

    try:
        # Launch browser in non-headless mode
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to LinkedIn
        await page.goto('https://www.linkedin.com', wait_until='networkidle')

        print("Waiting for LinkedIn to load...")
        print("Please log in if prompted.")
        print()

        # Wait for either login form or feed
        await page.wait_for_selector(
            'input[name="session_key"], [data-test-id="feed-container"]',
            timeout=60000
        )

        # Check if login is required
        login_form = await page.query_selector('input[name="session_key"]')

        if login_form:
            print("Login form detected - please enter your credentials")
            print("Waiting for login (up to 5 minutes)...")
            await page.wait_for_selector('[data-test-id="feed-container"]', timeout=300000)
            print()
            print("✓ Login successful!")
        else:
            print("✓ Already logged in!")

        # Wait a bit for session to save
        await asyncio.sleep(3)

        print()
        print("✓ LinkedIn authentication complete!")
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
        print("Playwright Authentication Helper")
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

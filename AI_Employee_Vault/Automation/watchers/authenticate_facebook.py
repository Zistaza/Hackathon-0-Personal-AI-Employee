#!/usr/bin/env python3
"""
Facebook Authentication Script
Run this once to authenticate and save your Facebook session
"""

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: Playwright not installed")
    print("Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


async def authenticate_facebook():
    """Authenticate with Facebook and save session"""

    user_data_dir = Path(__file__).parent / "facebook_session"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Facebook Authentication")
    print("=" * 80)
    print()
    print("This script will open Facebook in a browser window.")
    print("Please log in with your Facebook account.")
    print("Your session will be saved for future use.")
    print()
    print("Press Enter to continue...")
    input()

    playwright = await async_playwright().start()

    try:
        # Launch browser with persistent context
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

        # Get or create page
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()

        # Hide automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("Opening Facebook...")
        await page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
        await asyncio.sleep(3)

        # Check if already logged in
        logged_in_selectors = [
            'div[role="navigation"]',
            'a[href*="/notifications"]',
            'a[aria-label*="Profile"]',
        ]

        logged_in = False
        for selector in logged_in_selectors:
            element = await page.query_selector(selector)
            if element:
                logged_in = True
                break

        if logged_in:
            print()
            print("✓ Already logged in!")
            print("✓ Session saved successfully")
            print()
        else:
            print()
            print("=" * 80)
            print("PLEASE LOG IN TO FACEBOOK")
            print("=" * 80)
            print()
            print("1. Enter your email/phone and password")
            print("2. Complete any security checks (2FA, etc.)")
            print("3. Wait for the home page to load")
            print()
            print("The script will automatically detect when you're logged in...")
            print()

            # Wait for login
            for i in range(180):  # Wait up to 15 minutes
                await asyncio.sleep(5)

                # Check if logged in
                for selector in logged_in_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        print()
                        print("✓ Login successful!")
                        print("✓ Session saved successfully")
                        print()
                        logged_in = True
                        break

                if logged_in:
                    break

                if i % 6 == 0 and i > 0:  # Log every 30 seconds
                    print(f"Still waiting for login... ({(i+1)*5} seconds elapsed)")

            if not logged_in:
                print()
                print("✗ Login timeout")
                print("Please try running the script again")
                print()

        if logged_in:
            print("Session details:")
            print(f"  Session directory: {user_data_dir}")
            print()
            print("You can now run the Facebook watcher in headless mode!")
            print()
            print("To test the watcher:")
            print("  python facebook_watcher.py")
            print()
            print("To run all watchers:")
            print("  python run_all_watchers.py")
            print()

        print("Press Enter to close the browser...")
        input()

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"Error: {e}")
        await playwright.stop()


def main():
    """Main entry point"""
    asyncio.run(authenticate_facebook())


if __name__ == "__main__":
    main()

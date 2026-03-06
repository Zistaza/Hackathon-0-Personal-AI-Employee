#!/usr/bin/env python3
"""
Quick authentication test for LinkedIn
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def test_linkedin_auth():
    """Test if LinkedIn session is valid"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("Testing LinkedIn authentication...")
    print(f"Session directory: {session_dir}")

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("\nNavigating to LinkedIn...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)

        await page.wait_for_timeout(3000)

        current_url = page.url
        print(f"Current URL: {current_url}")

        if '/login' in current_url or '/uas/login' in current_url:
            print("\n❌ NOT LOGGED IN - Session expired")
            print("\nPlease run: python3 Skills/social_media_executor/authenticate.py")
        else:
            print("\n✅ LOGGED IN - Session is valid!")

            # Try to find the start post button
            try:
                await page.wait_for_selector("[aria-label*='Start a post']", timeout=5000)
                print("✅ Found 'Start a post' button - Ready to post!")
            except:
                print("⚠️  Could not find 'Start a post' button")

        print("\nClosing in 5 seconds...")
        await asyncio.sleep(5)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        await playwright.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_linkedin_auth())

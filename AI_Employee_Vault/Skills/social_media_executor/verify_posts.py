#!/usr/bin/env python3
"""
Verify LinkedIn post by checking profile
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def verify_posts():
    """Check if posts actually appear on LinkedIn profile"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"
    logs_dir = Path(__file__).parent.parent.parent / "Logs"

    print("=" * 60)
    print("LINKEDIN POST VERIFICATION")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Go to feed
        print("\nNavigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        # Check current user
        print("\nChecking logged in user...")
        try:
            # Try to find the "Me" button or profile link
            me_button = await page.query_selector('button:has-text("Me"), a:has-text("Me")')
            if me_button:
                await me_button.click()
                await page.wait_for_timeout(2000)

                # Get profile link
                profile_link = await page.query_selector('a[href*="/in/"]')
                if profile_link:
                    href = await profile_link.get_attribute('href')
                    print(f"✅ Logged in as: {href}")

                    # Navigate to profile
                    print("\nNavigating to your profile...")
                    await page.goto(f"https://www.linkedin.com{href}", wait_until='domcontentloaded')
                    await page.wait_for_timeout(5000)

                    # Check for recent posts
                    print("\nChecking for recent posts...")
                    content = await page.content()

                    if "TESTING AUTO POST AI" in content:
                        print("✅ FOUND: 'TESTING AUTO POST AI' post")
                    else:
                        print("❌ NOT FOUND: 'TESTING AUTO POST AI' post")

                    if "LinkedIn automation is working" in content:
                        print("✅ FOUND: 'LinkedIn automation is working' post")
                    else:
                        print("❌ NOT FOUND: 'LinkedIn automation is working' post")

                    # Take screenshot
                    screenshot_path = logs_dir / "profile_verification.png"
                    print(f"\nTaking screenshot: {screenshot_path}")
                    await page.screenshot(path=str(screenshot_path))

        except Exception as e:
            print(f"Error checking profile: {e}")

        print("\nClosing in 10 seconds...")
        await asyncio.sleep(10)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(verify_posts())

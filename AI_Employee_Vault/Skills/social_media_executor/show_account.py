#!/usr/bin/env python3
"""
Show which account is logged in and where to find posts
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def show_account_info():
    """Display which account is logged in"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("LINKEDIN ACCOUNT VERIFICATION")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("\n[1] Navigating to LinkedIn...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        print("\n[2] Identifying logged-in account...")

        # Try to get profile name and URL
        try:
            # Look for the "Me" button or profile link
            me_button = await page.query_selector('button:has-text("Me")')
            if me_button:
                await me_button.click()
                await page.wait_for_timeout(2000)

                # Get profile link
                profile_links = await page.query_selector_all('a[href*="/in/"]')
                if profile_links:
                    for link in profile_links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        if '/in/' in href and text.strip():
                            print(f"\n✅ LOGGED IN AS:")
                            print(f"   Name: {text.strip()}")
                            print(f"   Profile: https://www.linkedin.com{href}")

                            profile_url = f"https://www.linkedin.com{href}"

                            # Navigate to profile
                            print(f"\n[3] Navigating to your profile...")
                            await page.goto(profile_url, wait_until='domcontentloaded')
                            await page.wait_for_timeout(5000)

                            print(f"\n[4] Checking for recent posts on profile...")

                            # Look for activity section
                            content = await page.content()

                            # Search for our test post IDs
                            test_ids = [
                                "1772755193",  # VERIFICATION TEST
                                "1772757846",  # VERIFY Real post test
                                "1772758235",  # PUBLIC TEST
                                "TESTING AUTO POST AI",
                                "LinkedIn automation is working"
                            ]

                            found_posts = []
                            for test_id in test_ids:
                                if test_id in content:
                                    found_posts.append(test_id)

                            if found_posts:
                                print(f"\n✅✅✅ POSTS FOUND ON PROFILE!")
                                print(f"   Found {len(found_posts)} test post(s):")
                                for post in found_posts:
                                    print(f"   - {post}")
                                print(f"\n   The automation IS working!")
                                print(f"   Posts are on your profile at: {profile_url}")
                            else:
                                print(f"\n❌ No test posts found on profile")
                                print(f"   This could mean:")
                                print(f"   1. Posts are being saved as drafts")
                                print(f"   2. Posts are restricted/hidden")
                                print(f"   3. LinkedIn is blocking automated posts")

                            break

                # Close the menu
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(1000)

        except Exception as e:
            print(f"   Error getting account info: {e}")

        print("\n" + "=" * 60)
        print("MANUAL VERIFICATION REQUIRED")
        print("=" * 60)
        print("\nPlease do the following:")
        print("1. In the browser window, click on 'Me' in the top right")
        print("2. Click 'View Profile'")
        print("3. Scroll down to your 'Activity' section")
        print("4. Look for posts with these texts:")
        print("   - 'TESTING AUTO POST AI'")
        print("   - 'VERIFICATION TEST'")
        print("   - 'PUBLIC TEST'")
        print("\n5. If you see them: ✅ Automation is working!")
        print("6. If you don't see them: ❌ Posts aren't being published")
        print("\nBrowser will stay open for 60 seconds...")
        print("=" * 60)

        await asyncio.sleep(60)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(show_account_info())

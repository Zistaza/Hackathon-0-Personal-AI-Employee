#!/usr/bin/env python3
"""
Check audience settings and post publicly
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def check_audience_and_post():
    """Check audience settings before posting"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("AUDIENCE SETTINGS CHECK")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("\n[1] Navigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        print("\n[2] Clicking 'Start a post'...")
        await page.click("button:has-text('Start a post')")
        await page.wait_for_timeout(2000)

        print("\n[3] Checking current audience setting...")
        # Look for the audience button
        audience_button = await page.query_selector('[role="dialog"] button.share-unified-settings-entry-button')

        if audience_button:
            audience_text = await audience_button.inner_text()
            print(f"   Current audience: {audience_text.strip()}")

            if "Anyone" not in audience_text:
                print("   ⚠️  Audience is NOT set to 'Anyone' - this is why posts aren't visible!")
                print("\n[4] Clicking audience button to change it...")
                await audience_button.click()
                await page.wait_for_timeout(2000)

                # Look for "Anyone" option
                print("   Looking for 'Anyone' option...")
                anyone_options = await page.query_selector_all("text='Anyone'")

                if anyone_options:
                    print(f"   Found {len(anyone_options)} 'Anyone' options")
                    # Click the first one
                    await anyone_options[0].click()
                    await page.wait_for_timeout(1000)
                    print("   ✅ Set audience to 'Anyone'")
                else:
                    print("   ❌ Could not find 'Anyone' option")
            else:
                print("   ✅ Audience already set to 'Anyone'")
        else:
            print("   ❌ Could not find audience button")

        print("\n[5] Typing test content...")
        import time
        unique_id = int(time.time())
        test_content = f"PUBLIC TEST {unique_id} - This should be visible to everyone!"

        editor = '.ql-editor[contenteditable="true"]'
        await page.click(editor)
        await page.keyboard.type(test_content, delay=50)
        await page.wait_for_timeout(1000)

        print("\n[6] Clicking Post button...")
        post_button = '[role="dialog"] button.share-actions__primary-action'
        await page.click(post_button)
        print("   ✅ Clicked")

        print("\n[7] Waiting for confirmation...")
        await page.wait_for_timeout(5000)

        # Check for success message
        try:
            success_toast = await page.query_selector("text='Post successful'")
            if success_toast:
                print("   ✅ LinkedIn confirmed: 'Post successful'")
        except:
            pass

        print("\n[8] Refreshing and checking feed...")
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        content = await page.content()
        if str(unique_id) in content:
            print(f"   ✅✅✅ SUCCESS! Post {unique_id} found in feed!")
        else:
            print(f"   ❌ Post {unique_id} not found in feed")

        print("\n" + "=" * 60)
        print("Please manually check your LinkedIn profile")
        print(f"Look for post with ID: {unique_id}")
        print("=" * 60)
        print("\nBrowser staying open for 30 seconds...")
        await asyncio.sleep(30)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(check_audience_and_post())

#!/usr/bin/env python3
"""
Manual verification - post and wait for user to check
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def manual_verification():
    """Post with manual verification"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("MANUAL VERIFICATION TEST")
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

        import time
        unique_id = int(time.time())
        test_content = f"🔍 MANUAL VERIFICATION {unique_id}"

        print(f"\n[3] Typing: {test_content}")
        editor = '.ql-editor[contenteditable="true"]'
        await page.click(editor)
        await page.keyboard.type(test_content, delay=50)
        await page.wait_for_timeout(1000)

        print("\n[4] Looking for the PRIMARY ACTION Post button...")
        post_button_selector = '[role="dialog"] button.share-actions__primary-action'

        try:
            await page.wait_for_selector(post_button_selector, timeout=5000, state='visible')
            print(f"✅ Found button: {post_button_selector}")

            # Get button text to confirm
            button_text = await page.text_content(post_button_selector)
            print(f"   Button text: '{button_text}'")

            is_disabled = await page.is_disabled(post_button_selector)
            print(f"   Disabled: {is_disabled}")

        except Exception as e:
            print(f"❌ Could not find button: {e}")

        print("\n" + "=" * 60)
        print("PAUSING FOR MANUAL VERIFICATION")
        print("=" * 60)
        print("\nPlease check the browser window:")
        print("1. Is the post modal open?")
        print("2. Is the content typed correctly?")
        print("3. Can you see the 'Post' button?")
        print("4. What does the button say?")
        print("\nPress ENTER when ready to click the Post button...")
        input()

        print("\n[5] Clicking Post button...")
        await page.click(post_button_selector)
        print("✅ Clicked")

        print("\n[6] Waiting 5 seconds...")
        await page.wait_for_timeout(5000)

        print("\n[7] Checking if modal closed...")
        try:
            modal_visible = await page.is_visible(editor)
            if modal_visible:
                print("⚠️  Modal still visible")
            else:
                print("✅ Modal closed")
        except:
            print("✅ Modal closed")

        print("\n" + "=" * 60)
        print("NOW CHECK YOUR LINKEDIN FEED")
        print("=" * 60)
        print(f"\nLook for post with ID: {unique_id}")
        print("Do you see it in your feed?")
        print("\nBrowser will stay open for 60 seconds...")
        await asyncio.sleep(60)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(manual_verification())

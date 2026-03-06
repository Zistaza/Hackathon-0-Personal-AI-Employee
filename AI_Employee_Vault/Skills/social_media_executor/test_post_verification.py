#!/usr/bin/env python3
"""
Detailed LinkedIn posting test with verification
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def test_post_with_verification():
    """Post to LinkedIn and immediately verify it appears"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"
    logs_dir = Path(__file__).parent.parent.parent / "Logs"
    logs_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("LINKEDIN POST TEST WITH VERIFICATION")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to feed
        print("\n[1] Navigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)
        print(f"✅ Current URL: {page.url}")

        # Check which account is logged in
        print("\n[2] Checking logged in account...")
        try:
            # Look for profile image or name
            profile_elements = await page.query_selector_all('img[alt*="Photo"], img[alt*="photo"]')
            if profile_elements:
                print(f"✅ Found {len(profile_elements)} profile images")
        except:
            pass

        # Click Start a post
        print("\n[3] Clicking 'Start a post'...")
        await page.click("button:has-text('Start a post')")
        await page.wait_for_timeout(2000)
        print("✅ Clicked")

        # Type content with unique identifier
        import time
        unique_id = int(time.time())
        test_content = f"🔍 VERIFICATION TEST {unique_id} - If you see this, automation works!"

        print(f"\n[4] Typing content: {test_content}")
        editor = '.ql-editor[contenteditable="true"]'
        await page.wait_for_selector(editor, timeout=10000, state='visible')
        await page.click(editor)
        await page.wait_for_timeout(500)
        await page.keyboard.type(test_content, delay=50)
        await page.wait_for_timeout(1000)
        print("✅ Content typed")

        # Check if Post button is enabled
        print("\n[5] Checking Post button status...")
        post_buttons = await page.query_selector_all("button:has-text('Post')")
        print(f"Found {len(post_buttons)} buttons with 'Post' text")

        for i, btn in enumerate(post_buttons):
            is_visible = await btn.is_visible()
            is_disabled = await btn.is_disabled()
            print(f"   Button {i+1}: visible={is_visible}, disabled={is_disabled}")

        # Click Post button
        print("\n[6] Clicking Post button...")
        enabled_button = None
        for btn in post_buttons:
            if await btn.is_visible() and not await btn.is_disabled():
                enabled_button = btn
                break

        if not enabled_button:
            print("❌ No enabled Post button found!")
            await context.close()
            await playwright.stop()
            return

        await enabled_button.click()
        print("✅ Clicked Post button")

        # Wait for modal to close
        print("\n[7] Waiting for post to complete...")
        await page.wait_for_timeout(5000)

        # Check if modal closed
        try:
            modal_visible = await page.is_visible(editor)
            if modal_visible:
                print("⚠️  Modal still visible - post may not have completed")
            else:
                print("✅ Modal closed")
        except:
            print("✅ Modal closed")

        # Refresh feed and look for the post
        print("\n[8] Refreshing feed to check for post...")
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        # Search for our unique content
        print(f"\n[9] Looking for post with ID: {unique_id}")
        page_content = await page.content()

        if str(unique_id) in page_content:
            print(f"✅ SUCCESS! Post found in feed with ID {unique_id}")
            print("   The post was actually published!")
        else:
            print(f"❌ FAILED! Post with ID {unique_id} NOT found in feed")
            print("   The post did NOT actually publish!")

        # Also check for the text
        if "VERIFICATION TEST" in page_content:
            print("✅ Found 'VERIFICATION TEST' text in feed")
        else:
            print("❌ 'VERIFICATION TEST' text NOT in feed")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print("\nBrowser will stay open for 30 seconds so you can verify manually...")
        await asyncio.sleep(30)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_post_with_verification())

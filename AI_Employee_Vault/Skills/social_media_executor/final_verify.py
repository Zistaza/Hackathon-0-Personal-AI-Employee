#!/usr/bin/env python3
"""
Complete post and verify in feed - no user input needed
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def post_and_verify():
    """Post and immediately check feed"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("POST AND VERIFY TEST")
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
        test_content = f"VERIFY {unique_id} - Real post test"

        print(f"\n[3] Typing: {test_content}")
        editor = '.ql-editor[contenteditable="true"]'
        await page.click(editor)
        await page.keyboard.type(test_content, delay=50)
        await page.wait_for_timeout(1000)

        print("\n[4] Clicking PRIMARY ACTION Post button...")
        post_button = '[role="dialog"] button.share-actions__primary-action'
        await page.click(post_button)
        print("✅ Clicked")

        print("\n[5] Waiting 10 seconds for post to process...")
        await page.wait_for_timeout(10000)

        print("\n[6] Refreshing feed...")
        await page.reload(wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        print(f"\n[7] Searching for post with ID: {unique_id}")
        content = await page.content()

        if str(unique_id) in content:
            print(f"✅✅✅ SUCCESS! Post {unique_id} FOUND in feed!")
            print("    The post was ACTUALLY published to LinkedIn!")
        else:
            print(f"❌❌❌ FAILED! Post {unique_id} NOT in feed")
            print("    The post did NOT actually publish")

        if "VERIFY" in content and str(unique_id) in content:
            print("✅ Full text match confirmed")

        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)

        if str(unique_id) in content:
            print("✅ POST IS LIVE ON LINKEDIN")
        else:
            print("❌ POST DID NOT PUBLISH")
            print("\nPossible reasons:")
            print("1. Wrong button clicked")
            print("2. Privacy settings blocking")
            print("3. LinkedIn requires additional confirmation")
            print("4. Rate limiting")

        print("\nBrowser staying open for 30 seconds for manual check...")
        await asyncio.sleep(30)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(post_and_verify())

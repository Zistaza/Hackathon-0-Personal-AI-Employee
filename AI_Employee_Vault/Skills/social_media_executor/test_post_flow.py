#!/usr/bin/env python3
"""
Test LinkedIn posting flow to identify correct selectors
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def test_post_flow():
    """Test LinkedIn posting flow step by step"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"
    logs_dir = Path(__file__).parent.parent.parent / "Logs"
    logs_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("LINKEDIN POST FLOW TEST")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Step 1: Navigate
        print("\n[1/5] Navigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)
        print(f"✅ Current URL: {page.url}")

        # Take screenshot
        screenshot_path = logs_dir / "test_step1_feed.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")

        # Step 2: Find "Start a post" button
        print("\n[2/5] Looking for 'Start a post' button...")

        selectors_to_try = [
            "[aria-label*='Start a post']",
            "button:has-text('Start a post')",
            ".share-box-feed-entry__trigger",
            "[data-control-name='share_box_trigger']",
            ".artdeco-button--secondary:has-text('Start')",
            "button.share-box-feed-entry__trigger",
            ".share-creation-state__text",
            "[data-test-share-box-trigger]"
        ]

        found_selector = None
        for selector in selectors_to_try:
            try:
                print(f"   Trying: {selector}")
                element = await page.wait_for_selector(selector, timeout=2000, state='visible')
                if element:
                    found_selector = selector
                    print(f"   ✅ FOUND: {selector}")
                    break
            except:
                print(f"   ❌ Not found")

        if not found_selector:
            print("\n❌ Could not find 'Start a post' button with any selector")
            print("\nLet me check what's on the page...")

            # Get page content
            content = await page.content()
            if 'Start a post' in content:
                print("✅ 'Start a post' text exists in page HTML")
            else:
                print("❌ 'Start a post' text NOT found in page HTML")

            screenshot_path = logs_dir / "test_step2_no_button.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot: {screenshot_path}")

            print("\nClosing in 10 seconds...")
            await asyncio.sleep(10)
            await context.close()
            await playwright.stop()
            return

        # Step 3: Click the button
        print(f"\n[3/5] Clicking 'Start a post' button...")
        await page.click(found_selector)
        await page.wait_for_timeout(2000)
        print("✅ Clicked")

        screenshot_path = logs_dir / "test_step3_clicked.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")

        # Step 4: Find editor
        print("\n[4/5] Looking for post editor...")

        editor_selectors = [
            '.ql-editor[contenteditable="true"]',
            '[role="textbox"][contenteditable="true"]',
            '.ql-editor',
            'div[data-placeholder*="share"]',
            '[data-test-ql-editor-contenteditable]'
        ]

        found_editor = None
        for selector in editor_selectors:
            try:
                print(f"   Trying: {selector}")
                element = await page.wait_for_selector(selector, timeout=2000, state='visible')
                if element:
                    found_editor = selector
                    print(f"   ✅ FOUND: {selector}")
                    break
            except:
                print(f"   ❌ Not found")

        if not found_editor:
            print("\n❌ Could not find editor")
            screenshot_path = logs_dir / "test_step4_no_editor.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot: {screenshot_path}")
            print("\nClosing in 10 seconds...")
            await asyncio.sleep(10)
            await context.close()
            await playwright.stop()
            return

        # Step 5: Type test content
        print(f"\n[5/5] Typing test content...")
        await page.click(found_editor)
        await page.wait_for_timeout(500)
        await page.keyboard.type("TEST - This is an automated test post", delay=50)
        await page.wait_for_timeout(1000)
        print("✅ Content typed")

        screenshot_path = logs_dir / "test_step5_content.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")

        # Find Post button
        print("\n[BONUS] Looking for Post button...")

        post_button_selectors = [
            "button[type='submit']:has-text('Post')",
            "button.share-actions__primary-action:has-text('Post')",
            "button:has-text('Post'):not(:disabled)",
            "[aria-label*='Post']",
            ".share-actions__primary-action"
        ]

        found_post_button = None
        for selector in post_button_selectors:
            try:
                print(f"   Trying: {selector}")
                element = await page.wait_for_selector(selector, timeout=2000, state='visible')
                if element:
                    is_disabled = await page.is_disabled(selector)
                    if not is_disabled:
                        found_post_button = selector
                        print(f"   ✅ FOUND (enabled): {selector}")
                        break
                    else:
                        print(f"   ⚠️  Found but disabled: {selector}")
            except:
                print(f"   ❌ Not found")

        if found_post_button:
            print(f"\n✅ Post button found: {found_post_button}")
            print("\n⚠️  NOT clicking - this is just a test!")
        else:
            print("\n❌ Could not find enabled Post button")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print("\nClosing in 10 seconds...")
        await asyncio.sleep(10)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_post_flow())

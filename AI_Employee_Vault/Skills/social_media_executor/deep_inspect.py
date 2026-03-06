#!/usr/bin/env python3
"""
Deep inspection - what happens after clicking Post?
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def deep_inspection():
    """Inspect what happens after clicking Post"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("DEEP INSPECTION - POST BUTTON BEHAVIOR")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))

        print("\n[1] Navigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        print("\n[2] Clicking 'Start a post'...")
        await page.click("button:has-text('Start a post')")
        await page.wait_for_timeout(2000)

        print("\n[3] Typing test content...")
        editor = '.ql-editor[contenteditable="true"]'
        await page.click(editor)
        await page.keyboard.type("INSPECTION TEST - checking what happens", delay=50)
        await page.wait_for_timeout(1000)

        print("\n[4] Analyzing all buttons in the modal...")
        modal = await page.query_selector('[role="dialog"]')
        if modal:
            all_buttons = await modal.query_selector_all('button')
            print(f"   Found {len(all_buttons)} buttons in modal\n")

            for i, btn in enumerate(all_buttons):
                text = await btn.inner_text()
                text = text.strip().replace('\n', ' ')
                if text:
                    class_name = await btn.get_attribute('class') or ''
                    is_disabled = await btn.is_disabled()
                    is_visible = await btn.is_visible()

                    if 'primary' in class_name.lower() or 'post' in text.lower():
                        print(f"   Button {i+1}: '{text[:50]}'")
                        print(f"      Class: {class_name[:80]}")
                        print(f"      Disabled: {is_disabled}, Visible: {is_visible}")
                        print()

        print("\n[5] Looking for the share-actions__primary-action button...")
        primary_button = await page.query_selector('[role="dialog"] button.share-actions__primary-action')

        if primary_button:
            btn_text = await primary_button.inner_text()
            print(f"   Found button with text: '{btn_text.strip()}'")

            # Check if it's actually the Post button
            if 'Post' in btn_text and 'Anyone' not in btn_text:
                print("   ✅ This appears to be the correct Post button")
            else:
                print(f"   ⚠️  This might be the wrong button: '{btn_text}'")

        print("\n[6] Clicking the button and watching for changes...")

        # Set up listeners for network requests
        requests_made = []
        page.on("request", lambda req: requests_made.append(f"{req.method} {req.url}"))

        await page.click('[role="dialog"] button.share-actions__primary-action')
        print("   ✅ Clicked")

        print("\n[7] Waiting 5 seconds and monitoring...")
        await page.wait_for_timeout(5000)

        print(f"\n[8] Network requests made (last 10):")
        for req in requests_made[-10:]:
            if 'voyager' in req or 'share' in req or 'post' in req.lower():
                print(f"   {req}")

        print("\n[9] Checking for error messages...")
        # Look for common error selectors
        error_selectors = [
            '.artdeco-inline-feedback--error',
            '[role="alert"]',
            '.error-message',
            '.artdeco-toast-item'
        ]

        for selector in error_selectors:
            try:
                error_elem = await page.query_selector(selector)
                if error_elem:
                    error_text = await error_elem.inner_text()
                    print(f"   ⚠️  Error found: {error_text}")
            except:
                pass

        print("\n[10] Checking if modal is still open...")
        try:
            modal_still_visible = await page.is_visible('[role="dialog"]')
            if modal_still_visible:
                print("   ⚠️  Modal is STILL OPEN - post may not have submitted")
            else:
                print("   ✅ Modal closed - post may have submitted")
        except:
            print("   ✅ Modal closed")

        print("\n" + "=" * 60)
        print("Browser will stay open for 60 seconds")
        print("Please manually check:")
        print("1. Did the post appear in your feed?")
        print("2. Are there any error messages?")
        print("3. Check your profile - is the post there?")
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
    asyncio.run(deep_inspection())

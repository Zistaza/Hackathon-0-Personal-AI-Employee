#!/usr/bin/env python3
"""
Debug: Identify the correct Post button
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def debug_post_button():
    """Find the correct Post button to click"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("DEBUG: FINDING CORRECT POST BUTTON")
    print("=" * 60)

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("\nNavigating to LinkedIn feed...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)

        print("\nClicking 'Start a post'...")
        await page.click("button:has-text('Start a post')")
        await page.wait_for_timeout(2000)

        print("\nTyping test content...")
        editor = '.ql-editor[contenteditable="true"]'
        await page.click(editor)
        await page.keyboard.type("TEST - Finding correct button", delay=50)
        await page.wait_for_timeout(1000)

        print("\n" + "=" * 60)
        print("ANALYZING ALL 'POST' BUTTONS")
        print("=" * 60)

        # Get all buttons
        all_buttons = await page.query_selector_all("button")
        print(f"\nTotal buttons on page: {len(all_buttons)}")

        post_buttons = []
        for i, btn in enumerate(all_buttons):
            try:
                text = await btn.inner_text()
                if 'Post' in text or 'post' in text:
                    is_visible = await btn.is_visible()
                    is_disabled = await btn.is_disabled()

                    # Get attributes
                    class_name = await btn.get_attribute('class') or ''
                    aria_label = await btn.get_attribute('aria-label') or ''
                    data_control = await btn.get_attribute('data-control-name') or ''

                    if is_visible:
                        post_buttons.append({
                            'index': i,
                            'text': text.strip(),
                            'visible': is_visible,
                            'disabled': is_disabled,
                            'class': class_name,
                            'aria_label': aria_label,
                            'data_control': data_control
                        })
            except:
                pass

        print(f"\nFound {len(post_buttons)} visible buttons with 'Post' text:\n")

        for i, btn_info in enumerate(post_buttons):
            print(f"Button {i+1}:")
            print(f"  Text: '{btn_info['text']}'")
            print(f"  Disabled: {btn_info['disabled']}")
            print(f"  Class: {btn_info['class'][:100]}...")
            print(f"  Aria-label: {btn_info['aria_label']}")
            print(f"  Data-control: {btn_info['data_control']}")
            print()

        # Look for the modal specifically
        print("=" * 60)
        print("LOOKING FOR POST MODAL")
        print("=" * 60)

        # Try to find the modal container
        modal_selectors = [
            '[role="dialog"]',
            '.share-creation-state',
            '.artdeco-modal',
            '[data-test-modal]'
        ]

        for selector in modal_selectors:
            try:
                modal = await page.query_selector(selector)
                if modal:
                    print(f"\n✅ Found modal with selector: {selector}")

                    # Find Post button within this modal
                    modal_buttons = await modal.query_selector_all('button')
                    print(f"   Modal has {len(modal_buttons)} buttons")

                    for btn in modal_buttons:
                        text = await btn.inner_text()
                        if 'Post' in text:
                            is_disabled = await btn.is_disabled()
                            class_name = await btn.get_attribute('class') or ''
                            print(f"\n   POST BUTTON IN MODAL:")
                            print(f"     Text: '{text.strip()}'")
                            print(f"     Disabled: {is_disabled}")
                            print(f"     Class: {class_name}")
                    break
            except:
                pass

        print("\n\nBrowser will stay open for 30 seconds...")
        print("Please manually check which button should be clicked!")
        await asyncio.sleep(30)

        await context.close()
        await playwright.stop()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_post_button())

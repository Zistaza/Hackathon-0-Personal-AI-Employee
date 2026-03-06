#!/usr/bin/env python3
"""
Simple selector test for LinkedIn - no screenshots
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright

async def test_selectors():
    """Test LinkedIn selectors"""
    session_dir = Path(__file__).parent.parent.parent / "Sessions" / "linkedin"

    print("=" * 60)
    print("LINKEDIN SELECTOR TEST")
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
        await page.wait_for_timeout(5000)  # Give extra time for dynamic content
        print(f"✅ Loaded: {page.url}")

        # Check if logged in
        if '/login' in page.url:
            print("❌ Not logged in!")
            await context.close()
            await playwright.stop()
            return

        print("\n" + "=" * 60)
        print("SEARCHING FOR 'START A POST' BUTTON")
        print("=" * 60)

        selectors_to_try = [
            ("Aria label", "[aria-label*='Start a post' i]"),
            ("Button text", "button:has-text('Start a post')"),
            ("Share box class", ".share-box-feed-entry__trigger"),
            ("Data control", "[data-control-name='share_box_trigger']"),
            ("Artdeco button", ".artdeco-button--secondary:has-text('Start')"),
            ("Share box button", "button.share-box-feed-entry__trigger"),
            ("Share creation", ".share-creation-state__text"),
            ("Test attribute", "[data-test-share-box-trigger]"),
            ("Any button with Start", "button:has-text('Start')"),
            ("Share link", "a:has-text('Start a post')"),
            ("Div with Start", "div:has-text('Start a post')"),
        ]

        found_selector = None
        for name, selector in selectors_to_try:
            try:
                print(f"\n[{name}] {selector}")
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"   ✅ FOUND {len(elements)} element(s)")
                    # Check if visible
                    for i, elem in enumerate(elements):
                        is_visible = await elem.is_visible()
                        print(f"      Element {i+1}: visible={is_visible}")
                        if is_visible and not found_selector:
                            found_selector = selector
                            print(f"      ⭐ This one is visible and clickable!")
                else:
                    print(f"   ❌ Not found")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        if found_selector:
            print("\n" + "=" * 60)
            print(f"✅ SUCCESS! Working selector: {found_selector}")
            print("=" * 60)

            # Try clicking it
            print("\nAttempting to click...")
            try:
                await page.click(found_selector)
                await page.wait_for_timeout(3000)
                print("✅ Clicked successfully!")

                # Now look for editor
                print("\n" + "=" * 60)
                print("SEARCHING FOR POST EDITOR")
                print("=" * 60)

                editor_selectors = [
                    ("QL Editor", '.ql-editor[contenteditable="true"]'),
                    ("Textbox role", '[role="textbox"][contenteditable="true"]'),
                    ("QL Editor any", '.ql-editor'),
                    ("Data placeholder", 'div[data-placeholder*="share" i]'),
                    ("Contenteditable div", 'div[contenteditable="true"]'),
                ]

                found_editor = None
                for name, selector in editor_selectors:
                    try:
                        print(f"\n[{name}] {selector}")
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"   ✅ FOUND {len(elements)} element(s)")
                            for i, elem in enumerate(elements):
                                is_visible = await elem.is_visible()
                                print(f"      Element {i+1}: visible={is_visible}")
                                if is_visible and not found_editor:
                                    found_editor = selector
                                    print(f"      ⭐ This one is visible!")
                        else:
                            print(f"   ❌ Not found")
                    except Exception as e:
                        print(f"   ❌ Error: {e}")

                if found_editor:
                    print("\n" + "=" * 60)
                    print(f"✅ Editor found: {found_editor}")
                    print("=" * 60)
                else:
                    print("\n❌ No editor found")

            except Exception as e:
                print(f"❌ Click failed: {e}")
        else:
            print("\n" + "=" * 60)
            print("❌ NO WORKING SELECTOR FOUND")
            print("=" * 60)
            print("\nLet me check the page HTML...")
            content = await page.content()
            if 'Start a post' in content:
                print("✅ 'Start a post' text EXISTS in HTML")
                # Find the context
                import re
                matches = re.findall(r'.{0,100}Start a post.{0,100}', content, re.IGNORECASE)
                if matches:
                    print("\nContext snippets:")
                    for match in matches[:3]:
                        print(f"   ...{match}...")
            else:
                print("❌ 'Start a post' text NOT in HTML")

        print("\n\nClosing in 10 seconds...")
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
    asyncio.run(test_selectors())

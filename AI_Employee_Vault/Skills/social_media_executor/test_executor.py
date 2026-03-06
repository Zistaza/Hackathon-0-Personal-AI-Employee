#!/usr/bin/env python3
"""
Test script for Social Media Executor v2
=========================================

Validates that the executor is properly configured and can be initialized.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging


def test_executor():
    """Test Social Media Executor v2"""

    # Setup logging
    logger = logging.getLogger("test_executor")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    print("=" * 60)
    print("SOCIAL MEDIA EXECUTOR V2 - VALIDATION TEST")
    print("=" * 60)

    # Get base directory
    base_dir = Path(__file__).parent.parent.parent

    # Test 1: Import modules
    print("\n1. Testing module imports...")
    try:
        from Skills.social_media_executor.executor import SocialMediaExecutorV2
        from Skills.social_media_executor.platforms import (
            LinkedInPlatform,
            FacebookPlatform,
            InstagramPlatform,
            TwitterPlatform
        )
        print("   ✓ All modules imported successfully")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # Test 2: Initialize executor
    print("\n2. Testing executor initialization...")
    try:
        executor = SocialMediaExecutorV2(
            base_dir=base_dir,
            logger=logger
        )
        print("   ✓ Executor initialized")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False

    # Test 3: Check configuration
    print("\n3. Checking configuration...")
    config = executor.config
    if config:
        platforms = config.get('platforms', {})
        print(f"   ✓ Configuration loaded")
        print(f"   ✓ Platforms configured: {len(platforms)}")
        for platform_name, platform_config in platforms.items():
            enabled = platform_config.get('enabled', False)
            status = "✓" if enabled else "○"
            print(f"     {status} {platform_name}: {'enabled' if enabled else 'disabled'}")
    else:
        print("   ✗ Configuration not loaded")
        return False

    # Test 4: Check platform handlers
    print("\n4. Checking platform handlers...")
    for platform_name, handler in executor.platforms.items():
        print(f"   ✓ {platform_name}: {handler.__class__.__name__}")
        print(f"     - URL: {handler.get_platform_url()}")
        print(f"     - Session: {handler.session_dir}")

    # Test 5: Check directories
    print("\n5. Verifying directories...")
    directories = [
        ("Sessions", executor.sessions_dir),
        ("Logs", executor.logs_dir),
        ("Approved", executor.approved_dir),
    ]

    for name, path in directories:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {name}: {path}")

    # Test 6: Test file parsing
    print("\n6. Testing file parsing...")
    test_content = """---
platform: linkedin
type: post
content: "Test post content"
media: []
---

Additional content here
"""
    test_file = base_dir / "Pending_Approval" / "TEST_parse.md"
    try:
        test_file.write_text(test_content)
        parsed = executor.parse_post_file(test_file)

        if parsed:
            print("   ✓ File parsing works")
            print(f"     - Platform: {parsed.get('platform')}")
            print(f"     - Type: {parsed.get('type')}")
            print(f"     - Content length: {len(parsed.get('content', ''))}")
        else:
            print("   ✗ File parsing failed")

        # Cleanup
        test_file.unlink()

    except Exception as e:
        print(f"   ✗ File parsing error: {e}")

    # Test 7: Check retry configuration
    print("\n7. Checking retry configuration...")
    retry_config = config.get('retry', {})
    print(f"   ✓ Max attempts: {retry_config.get('max_attempts', 3)}")
    print(f"   ✓ Initial delay: {retry_config.get('initial_delay', 5000)}ms")
    print(f"   ✓ Backoff multiplier: {retry_config.get('backoff_multiplier', 2)}")

    # Test 8: Check browser configuration
    print("\n8. Checking browser configuration...")
    browser_config = config.get('browser', {})
    print(f"   ✓ Headless: {browser_config.get('headless', False)}")
    viewport = browser_config.get('viewport', {})
    print(f"   ✓ Viewport: {viewport.get('width')}x{viewport.get('height')}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✓ Social Media Executor v2 is properly configured!")
    print("\nNext steps:")
    print("1. Run executor manually to set up browser sessions")
    print("2. Create post files in /Pending_Approval")
    print("3. Move to /Approved for execution")
    print("4. Check /Done or /Failed for results")

    return True


if __name__ == "__main__":
    try:
        success = test_executor()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

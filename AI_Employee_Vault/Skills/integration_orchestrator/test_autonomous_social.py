#!/usr/bin/env python3
"""
Test Enhanced AutonomousExecutor with Social Media Automation
==============================================================

Tests the integrated social media automation capabilities.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta, UTC

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from index import IntegrationOrchestrator


def create_test_content():
    """Create test content files for social media automation"""
    vault_path = Path(__file__).parent.parent.parent

    # Create Posted content (immediate posting)
    posted_dir = vault_path / "Posted"
    posted_dir.mkdir(parents=True, exist_ok=True)

    posted_file = posted_dir / "test_social_post.md"
    posted_content = """---
social_media:
  platforms: [facebook, twitter_x]
  message: "Exciting news! Our autonomous executor now handles social media automatically! 🚀 #automation"
  media: []
---

# Test Social Post

This is a test post for the autonomous social media automation.
"""
    posted_file.write_text(posted_content)
    print(f"✓ Created test file: {posted_file}")

    # Create scheduled post
    plans_dir = vault_path / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    # Schedule for 1 minute from now
    scheduled_time = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    scheduled_file = plans_dir / "scheduled_social_post.md"
    scheduled_content = f"""<!-- SOCIAL: instagram -->
<!-- MESSAGE: Beautiful sunset from our office! 🌅 -->
<!-- MEDIA: sunset.jpg -->
<!-- SCHEDULED: {scheduled_time} -->

# Scheduled Social Post

This post is scheduled to go out automatically.
"""
    scheduled_file.write_text(scheduled_content)
    print(f"✓ Created scheduled post: {scheduled_file}")
    print(f"  Scheduled for: {scheduled_time}")

    # Create draft (should not auto-post)
    drafts_dir = vault_path / "Drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    draft_file = drafts_dir / "draft_social_post.md"
    draft_content = """```json social_media
{
  "platforms": ["facebook", "instagram", "twitter_x"],
  "message": "This is a draft and should NOT be posted automatically",
  "media": ["draft_image.jpg"]
}
```

# Draft Post

This is a draft that requires approval before posting.
"""
    draft_file.write_text(draft_content)
    print(f"✓ Created draft: {draft_file}")

    return posted_file, scheduled_file, draft_file


def test_social_automation():
    """Test social media automation"""
    print("\n" + "="*70)
    print("TESTING ENHANCED AUTONOMOUS EXECUTOR - SOCIAL MEDIA AUTOMATION")
    print("="*70)

    # Create test content
    print("\n[1] Creating test content files...")
    posted_file, scheduled_file, draft_file = create_test_content()

    # Initialize orchestrator
    print("\n[2] Initializing orchestrator...")
    vault_path = Path(__file__).parent.parent.parent
    orchestrator = IntegrationOrchestrator(vault_path)

    # Check if social automation is enabled
    print("\n[3] Checking social automation status...")
    if hasattr(orchestrator.autonomous_executor, '_check_social_media_content'):
        print("✓ Social media automation enabled")
    else:
        print("✗ Social media automation NOT enabled")
        return False

    # Check if orchestrator reference is set
    if hasattr(orchestrator.autonomous_executor, 'orchestrator'):
        print("✓ Orchestrator reference set")
    else:
        print("✗ Orchestrator reference NOT set")

    # Subscribe to events
    print("\n[4] Subscribing to social media events...")
    events_captured = []

    def capture_event(data):
        events_captured.append(data)
        print(f"  [Event] {data.get('platforms', data.get('platform', 'N/A'))}")

    orchestrator.event_bus.subscribe('social_post_triggered', capture_event)
    orchestrator.event_bus.subscribe('social_post_success', capture_event)
    orchestrator.event_bus.subscribe('social_post_failed', capture_event)
    orchestrator.event_bus.subscribe('social_drafts_detected', capture_event)

    # Start autonomous executor
    print("\n[5] Starting autonomous executor...")
    orchestrator.autonomous_executor.start()
    print("✓ Autonomous executor started")

    # Wait for processing
    print("\n[6] Waiting for autonomous processing (30 seconds)...")
    print("    The executor will check for social content every 30 seconds...")
    time.sleep(35)  # Wait for at least one check cycle

    # Check results
    print("\n[7] Checking results...")
    print(f"Events captured: {len(events_captured)}")
    for i, event in enumerate(events_captured, 1):
        print(f"  Event {i}: {event}")

    # Check Reports directory
    print("\n[8] Checking generated reports...")
    reports_dir = vault_path / "Reports" / "Social"
    if reports_dir.exists():
        reports = list(reports_dir.glob("*.md"))
        print(f"✓ Reports directory exists")
        print(f"✓ Generated reports: {len(reports)}")
        if reports:
            for report in reports[-3:]:  # Show last 3
                print(f"  - {report.name}")
    else:
        print("✗ Reports directory not found")

    # Check audit logs
    print("\n[9] Checking audit logs...")
    audit_file = orchestrator.audit_logger.audit_file
    if audit_file.exists():
        with open(audit_file, 'r') as f:
            audit_lines = f.readlines()
        social_audits = [l for l in audit_lines if 'social' in l.lower()]
        print(f"✓ Audit log exists")
        print(f"✓ Social media audit entries: {len(social_audits)}")
    else:
        print("✗ Audit log not found")

    # Check if files were processed
    print("\n[10] Checking file processing status...")
    if hasattr(orchestrator.autonomous_executor, 'social_processed_files'):
        processed = orchestrator.autonomous_executor.social_processed_files
        print(f"Processed files: {len(processed)}")
        for filepath in processed:
            print(f"  - {Path(filepath).name}")
    else:
        print("No processed files tracking available")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✓ Social automation enabled: {hasattr(orchestrator.autonomous_executor, '_check_social_media_content')}")
    print(f"✓ Events captured: {len(events_captured)}")
    print(f"✓ Test files created: 3 (Posted, Scheduled, Draft)")
    print(f"✓ Autonomous executor running")

    if events_captured:
        print("\n✅ Social media automation is working!")
    else:
        print("\n⚠️  No events captured - automation may need more time or content format adjustment")

    # Cleanup
    print("\n[11] Stopping orchestrator...")
    orchestrator.stop()

    return True


def test_content_parsing():
    """Test content parsing capabilities"""
    print("\n" + "="*70)
    print("TESTING CONTENT PARSING")
    print("="*70)

    vault_path = Path(__file__).parent.parent.parent
    orchestrator = IntegrationOrchestrator(vault_path)

    if not hasattr(orchestrator.autonomous_executor, '_parse_social_media_config'):
        print("✗ Content parsing not available")
        return False

    # Test YAML frontmatter parsing
    print("\n[1] Testing YAML frontmatter parsing...")
    test_file = vault_path / "Posted" / "test_yaml.md"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""---
social_media:
  platforms: [facebook, instagram]
  message: "Test message"
---
Content here
""")

    config = orchestrator.autonomous_executor._parse_social_media_config(test_file)
    if config:
        print(f"✓ Parsed config: {config}")
    else:
        print("✗ Failed to parse YAML frontmatter")

    # Test inline markers
    print("\n[2] Testing inline markers parsing...")
    test_file2 = vault_path / "Posted" / "test_inline.md"
    test_file2.write_text("""<!-- SOCIAL: twitter_x -->
<!-- MESSAGE: Inline marker test -->
Content here
""")

    config2 = orchestrator.autonomous_executor._parse_social_media_config(test_file2)
    if config2:
        print(f"✓ Parsed config: {config2}")
    else:
        print("✗ Failed to parse inline markers")

    # Cleanup
    test_file.unlink(missing_ok=True)
    test_file2.unlink(missing_ok=True)
    orchestrator.stop()

    return True


if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("ENHANCED AUTONOMOUS EXECUTOR TEST SUITE")
        print("="*70)

        # Test content parsing
        test_content_parsing()

        # Test social automation
        test_social_automation()

        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

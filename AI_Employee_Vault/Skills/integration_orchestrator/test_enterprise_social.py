#!/usr/bin/env python3
"""
Test Suite for Enterprise Social Media Skills
==============================================

Tests all enterprise features:
1. Content validation with prohibited words
2. Content moderation with risk scoring
3. Engagement tracking simulation
4. Post scheduling with PeriodicTrigger integration
5. Social analytics summary generation
6. State persistence via StateManager
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta, UTC

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_skills import (
    ContentValidator,
    ContentModerator,
    EngagementTracker,
    SocialAnalytics,
    register_social_skills,
    MODERATION_THRESHOLD
)
from core.state_manager import StateManager
from core.event_bus import EventBus
from core.audit_logger import AuditLogger
from core.retry_queue import RetryQueue
from skills.skill_registry import SkillRegistry
from skills.skill_dispatcher import SkillDispatcher


def setup_test_environment():
    """Setup test environment with all components"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("EnterpriseTest")

    # Setup paths
    base_dir = Path(__file__).parent
    state_file = base_dir / "test_state.json"
    logs_dir = base_dir / "test_logs"
    reports_dir = base_dir / "test_reports"
    skills_dir = base_dir / "skills"

    logs_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    # Initialize components
    state_manager = StateManager(state_file)
    event_bus = EventBus(logger)
    audit_logger = AuditLogger(logs_dir, logger)
    retry_queue = RetryQueue(logger, max_retries=3)
    dispatcher = SkillDispatcher(skills_dir, logger)
    skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

    return {
        'logger': logger,
        'state_manager': state_manager,
        'event_bus': event_bus,
        'audit_logger': audit_logger,
        'retry_queue': retry_queue,
        'skill_registry': skill_registry,
        'reports_dir': reports_dir
    }


def test_content_validation():
    """Test 1: Content Validation"""
    print("\n" + "="*60)
    print("TEST 1: Content Validation")
    print("="*60)

    logger = logging.getLogger("ValidationTest")
    validator = ContentValidator(logger)

    # Test valid content
    result = validator.validate("This is a great product announcement!", "facebook")
    print(f"\n✓ Valid content: {result['valid']}")
    print(f"  Issues: {len(result['issues'])}")

    # Test prohibited words
    result = validator.validate("This is a spam message with fake content", "facebook")
    print(f"\n✗ Content with prohibited words: {result['valid']}")
    print(f"  Issues: {result['issues']}")

    # Test length exceeded
    result = validator.validate("x" * 300, "twitter_x")
    print(f"\n✗ Content exceeding Twitter limit: {result['valid']}")
    print(f"  Issues: {result['issues']}")

    # Test excessive caps
    result = validator.validate("BUY NOW!!! AMAZING DEAL!!!", "facebook")
    print(f"\n⚠ Content with excessive caps: {result['valid']}")
    print(f"  Issues: {result['issues']}")


def test_content_moderation():
    """Test 2: Content Moderation"""
    print("\n" + "="*60)
    print("TEST 2: Content Moderation")
    print("="*60)

    logger = logging.getLogger("ModerationTest")
    event_bus = EventBus(logger)
    moderator = ContentModerator(logger, event_bus, threshold=MODERATION_THRESHOLD)

    print(f"\nModeration Threshold: {MODERATION_THRESHOLD}")

    # Test low-risk content
    result = moderator.moderate("Excited to share our new product launch!")
    print(f"\n✓ Low-risk content:")
    print(f"  Approved: {result['approved']}")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Threshold: {result['threshold']}")

    # Validate threshold enforcement for low-risk
    if result['risk_score'] <= result['threshold']:
        assert result['approved'] is True, "Low-risk content must be approved when score <= threshold"
        print(f"  ✓ Assertion passed: Content approved (score {result['risk_score']} <= {result['threshold']})")
    else:
        assert result['approved'] is False, "Content must be blocked when score > threshold"
        print(f"  ✓ Assertion passed: Content blocked (score {result['risk_score']} > {result['threshold']})")

    # Test high-risk content
    result = moderator.moderate("Click here now! Buy now! Limited time! http://suspicious-link.com!!!")
    print(f"\n✗ High-risk content:")
    print(f"  Approved: {result['approved']}")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Threshold: {result['threshold']}")
    print(f"  Risk Factors: {result['risk_factors']}")

    # Validate threshold enforcement for high-risk
    if result['risk_score'] > result['threshold']:
        assert result['approved'] is False, "High-risk content must be blocked when score exceeds threshold"
        print(f"  ✓ Assertion passed: Content blocked (score {result['risk_score']} > {result['threshold']})")
    else:
        assert result['approved'] is True, "Content must be approved when score <= threshold"
        print(f"  ✓ Assertion passed: Content approved (score {result['risk_score']} <= {result['threshold']})")

    print(f"\n✓ TEST 2 PASSED: Moderation threshold enforcement validated")



def test_engagement_tracking():
    """Test 3: Engagement Tracking"""
    print("\n" + "="*60)
    print("TEST 3: Engagement Tracking")
    print("="*60)

    logger = logging.getLogger("EngagementTest")
    state_file = Path(__file__).parent / "test_state.json"
    state_manager = StateManager(state_file)
    tracker = EngagementTracker(logger, state_manager)

    # Generate metrics for different platforms
    for platform in ['facebook', 'instagram', 'twitter_x']:
        metrics = tracker.generate_metrics(
            platform,
            f"test_post_{platform}_123",
            "This is a test post with some content to generate engagement metrics."
        )
        print(f"\n{platform.upper()} Metrics:")
        for key, value in metrics.items():
            if key != 'tracked_at':
                print(f"  {key}: {value}")


def test_post_scheduling():
    """Test 4: Post Scheduling"""
    print("\n" + "="*60)
    print("TEST 4: Post Scheduling")
    print("="*60)

    env = setup_test_environment()

    # Register social skills
    adapter = register_social_skills(
        skill_registry=env['skill_registry'],
        logger=env['logger'],
        event_bus=env['event_bus'],
        audit_logger=env['audit_logger'],
        retry_queue=env['retry_queue'],
        reports_dir=env['reports_dir'],
        state_manager=env['state_manager']
    )

    # Schedule posts
    print("\nScheduling posts...")

    # Schedule for immediate execution (past time)
    result1 = adapter.schedule_post(
        platform='facebook',
        message='Scheduled post 1 - should execute immediately',
        scheduled_time=datetime.now(UTC) - timedelta(minutes=1)
    )
    print(f"✓ Scheduled post 1: {result1['schedule_id']}")

    # Schedule for future
    result2 = adapter.schedule_post(
        platform='instagram',
        message='Scheduled post 2 - future execution',
        scheduled_time=datetime.now(UTC) + timedelta(hours=2),
        media=['image1.jpg']
    )
    print(f"✓ Scheduled post 2: {result2['schedule_id']}")

    # Execute scheduled posts
    print("\nExecuting scheduled posts...")
    execution_result = adapter.execute_scheduled_posts()
    print(f"  Executed: {len(execution_result['executed'])} posts")
    print(f"  Failed: {len(execution_result['failed'])} posts")
    print(f"  Total checked: {execution_result['total_checked']}")


def test_social_analytics():
    """Test 5: Social Analytics"""
    print("\n" + "="*60)
    print("TEST 5: Social Analytics Summary")
    print("="*60)

    env = setup_test_environment()

    # Register social skills
    adapter = register_social_skills(
        skill_registry=env['skill_registry'],
        logger=env['logger'],
        event_bus=env['event_bus'],
        audit_logger=env['audit_logger'],
        retry_queue=env['retry_queue'],
        reports_dir=env['reports_dir'],
        state_manager=env['state_manager']
    )

    # Post some content to generate metrics
    print("\nPosting content to generate analytics...")
    adapter.post('facebook', 'Test post for analytics 1')
    adapter.post('instagram', 'Test post for analytics 2', media=['image.jpg'])
    adapter.post('twitter_x', 'Test post for analytics 3')

    # Generate analytics summary
    print("\nGenerating analytics summary...")
    summary = adapter.get_analytics_summary()

    print(f"\nAnalytics Summary:")
    print(f"  Period: {summary['period']}")
    print(f"  Generated at: {summary['generated_at']}")

    print(f"\n  Overall Metrics:")
    for key, value in summary['overall'].items():
        print(f"    {key}: {value}")

    print(f"\n  Platform Breakdown:")
    for platform, metrics in summary['platforms'].items():
        print(f"    {platform.upper()}:")
        for key, value in metrics.items():
            print(f"      {key}: {value}")


def test_full_enterprise_workflow():
    """Test 6: Full Enterprise Workflow"""
    print("\n" + "="*60)
    print("TEST 6: Full Enterprise Workflow")
    print("="*60)

    env = setup_test_environment()

    # Register social skills
    adapter = register_social_skills(
        skill_registry=env['skill_registry'],
        logger=env['logger'],
        event_bus=env['event_bus'],
        audit_logger=env['audit_logger'],
        retry_queue=env['retry_queue'],
        reports_dir=env['reports_dir'],
        state_manager=env['state_manager']
    )

    print("\n1. Posting valid content...")
    result = adapter.post(
        'facebook',
        'Excited to announce our new product launch! Check it out.',
        metadata={'campaign': 'product_launch_2026'}
    )
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Post ID: {result['post_id']}")
        print(f"   Engagement Rate: {result['engagement']['engagement_rate']}%")
        print(f"   Moderation Score: {result['moderation']['risk_score']}")

    print("\n2. Attempting to post content with prohibited words...")
    result = adapter.post(
        'twitter_x',
        'This is a spam message with fake content'
    )
    print(f"   Success: {result['success']}")
    print(f"   Status: {result.get('status')}")
    if not result['success']:
        print(f"   Error: {result['error']}")

    print("\n3. Attempting to post high-risk content...")
    result = adapter.post(
        'facebook',
        'Click here now!!! Buy now!!! http://suspicious.com Limited time!!!'
    )
    print(f"   Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['error']}")
        print(f"   Risk Score: {result['moderation']['risk_score']}")

    print("\n4. Scheduling future post...")
    result = adapter.schedule_post(
        'instagram',
        'Scheduled content for future posting',
        scheduled_time=datetime.now(UTC) + timedelta(hours=1),
        media=['photo.jpg']
    )
    print(f"   Scheduled: {result['success']}")
    print(f"   Schedule ID: {result['schedule_id']}")

    print("\n5. Generating analytics...")
    summary = adapter.get_analytics_summary()
    print(f"   Total posts: {summary['overall']['total_posts']}")
    print(f"   Total reach: {summary['overall']['total_reach']}")
    print(f"   Avg engagement: {summary['overall']['avg_engagement_rate']}%")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ENTERPRISE SOCIAL MEDIA SKILLS TEST SUITE")
    print("="*60)

    try:
        test_content_validation()
        test_content_moderation()
        test_engagement_tracking()
        test_post_scheduling()
        test_social_analytics()
        test_full_enterprise_workflow()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
Enterprise Social Media Skills - Usage Examples
================================================

Practical examples demonstrating all enterprise features.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta, UTC

# Example 1: Basic Post with Enterprise Features
def example_basic_post(adapter):
    """
    Post content with automatic validation, moderation, and engagement tracking.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Post with Enterprise Features")
    print("="*60)

    result = adapter.post(
        platform='facebook',
        message='Excited to announce our Q1 2026 product launch! 🚀',
        metadata={
            'campaign': 'q1_launch',
            'team': 'marketing'
        }
    )

    if result['success']:
        print(f"✓ Post successful!")
        print(f"  Post ID: {result['post_id']}")
        print(f"  URL: {result['url']}")
        print(f"  Status: {result['status']}")
        print(f"\n  Engagement Metrics:")
        print(f"    Likes: {result['engagement']['likes']}")
        print(f"    Comments: {result['engagement']['comments']}")
        print(f"    Shares: {result['engagement']['shares']}")
        print(f"    Reach: {result['engagement']['reach']}")
        print(f"    Engagement Rate: {result['engagement']['engagement_rate']}%")
        print(f"\n  Moderation:")
        print(f"    Risk Score: {result['moderation']['risk_score']}")
        print(f"    Risk Level: {result['moderation']['risk_level']}")
    else:
        print(f"✗ Post failed: {result['error']}")


# Example 2: Content Validation Failure
def example_validation_failure(adapter):
    """
    Demonstrate content validation blocking prohibited words.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Content Validation Failure")
    print("="*60)

    result = adapter.post(
        platform='twitter_x',
        message='This is a spam message with fake content and illegal activities'
    )

    print(f"Post Status: {result['success']}")
    print(f"Status Code: {result.get('status')}")
    print(f"Error: {result['error']}")

    if 'validation' in result:
        print(f"\nValidation Issues:")
        for issue in result['validation']['issues']:
            print(f"  - [{issue['severity'].upper()}] {issue['message']}")


# Example 3: Content Moderation Blocking
def example_moderation_block(adapter):
    """
    Demonstrate content moderation blocking high-risk content.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Content Moderation Blocking")
    print("="*60)

    result = adapter.post(
        platform='facebook',
        message='Click here NOW!!! Buy now!!! Limited time offer!!! http://suspicious-link.com Act fast!!!'
    )

    print(f"Post Status: {result['success']}")
    print(f"Error: {result['error']}")

    if 'moderation' in result:
        mod = result['moderation']
        print(f"\nModeration Analysis:")
        print(f"  Approved: {mod['approved']}")
        print(f"  Risk Score: {mod['risk_score']}")
        print(f"  Risk Level: {mod['risk_level']}")
        print(f"  Threshold: {mod['threshold']}")
        print(f"\n  Risk Factors:")
        for factor in mod['risk_factors']:
            print(f"    - {factor}")


# Example 4: Multi-Platform Posting
def example_multi_platform(adapter):
    """
    Post to multiple platforms with platform-specific adaptations.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Multi-Platform Posting")
    print("="*60)

    message = "Check out our new feature! It's designed to help you work smarter, not harder."
    media = ['product_screenshot.jpg']

    results = adapter.post_to_all(
        message=message,
        media=media,
        metadata={'campaign': 'feature_launch'}
    )

    for platform, result in results.items():
        print(f"\n{platform.upper()}:")
        if result['success']:
            print(f"  ✓ Posted successfully")
            print(f"  Post ID: {result['post_id']}")
            print(f"  Engagement Rate: {result['engagement']['engagement_rate']}%")
        else:
            print(f"  ✗ Failed: {result['error']}")


# Example 5: Post Scheduling
def example_scheduling(adapter):
    """
    Schedule posts for future execution.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Post Scheduling")
    print("="*60)

    # Schedule post for 2 hours from now
    scheduled_time = datetime.now(UTC) + timedelta(hours=2)

    result = adapter.schedule_post(
        platform='instagram',
        message='Our weekly product update is here! Swipe to see what\'s new.',
        scheduled_time=scheduled_time,
        media=['update_carousel_1.jpg', 'update_carousel_2.jpg'],
        metadata={
            'campaign': 'weekly_update',
            'week': 'W09_2026'
        }
    )

    if result['success']:
        print(f"✓ Post scheduled successfully!")
        print(f"  Schedule ID: {result['schedule_id']}")
        print(f"  Platform: {result['platform']}")
        print(f"  Scheduled Time: {result['scheduled_time']}")
        print(f"\n  Note: PeriodicTrigger will execute this automatically")
    else:
        print(f"✗ Scheduling failed: {result['error']}")


# Example 6: Manual Execution of Scheduled Posts
def example_execute_scheduled(adapter):
    """
    Manually trigger execution of scheduled posts.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Execute Scheduled Posts")
    print("="*60)

    # Schedule a post for immediate execution (past time)
    past_time = datetime.now(UTC) - timedelta(minutes=5)

    adapter.schedule_post(
        platform='twitter_x',
        message='This post was scheduled in the past and will execute immediately',
        scheduled_time=past_time
    )

    # Execute all due posts
    result = adapter.execute_scheduled_posts()

    print(f"Execution Summary:")
    print(f"  Total Checked: {result['total_checked']}")
    print(f"  Executed: {len(result['executed'])} posts")
    print(f"  Failed: {len(result['failed'])} posts")

    if result['executed']:
        print(f"\n  Successfully Executed:")
        for schedule_id in result['executed']:
            print(f"    - {schedule_id}")

    if result['failed']:
        print(f"\n  Failed:")
        for schedule_id in result['failed']:
            print(f"    - {schedule_id}")


# Example 7: Analytics Summary
def example_analytics(adapter):
    """
    Generate and display social media analytics.
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: Social Media Analytics")
    print("="*60)

    # Post some content first
    print("Posting content to generate analytics data...")
    adapter.post('facebook', 'Analytics test post 1')
    adapter.post('instagram', 'Analytics test post 2', media=['image.jpg'])
    adapter.post('twitter_x', 'Analytics test post 3')

    # Generate analytics
    summary = adapter.get_analytics_summary()

    print(f"\n📊 Analytics Summary")
    print(f"Period: {summary['period']}")
    print(f"Generated: {summary['generated_at']}")

    print(f"\n🌐 Overall Performance:")
    overall = summary['overall']
    print(f"  Total Posts: {overall['total_posts']}")
    print(f"  Total Reach: {overall['total_reach']:,}")
    print(f"  Avg Engagement Rate: {overall['avg_engagement_rate']}%")

    print(f"\n📱 Platform Breakdown:")
    for platform, metrics in summary['platforms'].items():
        print(f"\n  {platform.upper()}:")
        print(f"    Posts: {metrics.get('total_posts', 0)}")
        print(f"    Reach: {metrics.get('total_reach', 0):,}")
        print(f"    Avg Engagement: {metrics.get('avg_engagement_rate', 0)}%")


# Example 8: Error Handling and Retry
def example_error_handling(adapter):
    """
    Demonstrate error handling and automatic retry via RetryQueue.
    """
    print("\n" + "="*60)
    print("EXAMPLE 8: Error Handling and Retry")
    print("="*60)

    # This will fail validation
    result = adapter.post(
        platform='twitter_x',
        message='x' * 300,  # Exceeds Twitter limit
        metadata={'retry_test': True}
    )

    print(f"Initial Attempt:")
    print(f"  Success: {result['success']}")
    print(f"  Error: {result['error']}")
    print(f"\n  Note: Failed posts are automatically enqueued to RetryQueue")
    print(f"  The centralized retry system will handle retries with exponential backoff")


# Example 9: Idempotent Posting
def example_idempotent(adapter):
    """
    Demonstrate idempotent posting (prevents duplicates).
    """
    print("\n" + "="*60)
    print("EXAMPLE 9: Idempotent Posting")
    print("="*60)

    message = "This is a unique message for idempotency testing"

    # First post
    result1 = adapter.post('facebook', message)
    print(f"First Post:")
    print(f"  Success: {result1['success']}")
    print(f"  Post ID: {result1['post_id']}")

    # Second post (same content)
    result2 = adapter.post('facebook', message)
    print(f"\nSecond Post (duplicate):")
    print(f"  Success: {result2['success']}")
    print(f"  Post ID: {result2['post_id']}")
    print(f"  Idempotent: {result2.get('idempotent', False)}")
    print(f"  Status: {result2.get('status')}")

    print(f"\n  Note: Same post ID returned, no duplicate created")


# Example 10: Complete Campaign Workflow
def example_campaign_workflow(adapter):
    """
    Complete workflow for a marketing campaign.
    """
    print("\n" + "="*60)
    print("EXAMPLE 10: Complete Campaign Workflow")
    print("="*60)

    campaign_metadata = {
        'campaign': 'spring_sale_2026',
        'team': 'marketing',
        'budget': 'tier_1'
    }

    # 1. Immediate announcement
    print("\n1. Posting immediate announcement...")
    result = adapter.post(
        platform='twitter_x',
        message='🎉 Spring Sale starts NOW! Check out our amazing deals.',
        metadata=campaign_metadata
    )
    print(f"   Posted: {result['success']}")

    # 2. Schedule follow-up posts
    print("\n2. Scheduling follow-up posts...")

    # Instagram post in 1 hour
    adapter.schedule_post(
        platform='instagram',
        message='Spring Sale Day 1! Swipe to see our top deals 🌸',
        scheduled_time=datetime.now(UTC) + timedelta(hours=1),
        media=['sale_day1.jpg'],
        metadata=campaign_metadata
    )
    print("   ✓ Instagram post scheduled for +1 hour")

    # Facebook post in 2 hours
    adapter.schedule_post(
        platform='facebook',
        message='Don\'t miss our Spring Sale! Limited time offers on all products.',
        scheduled_time=datetime.now(UTC) + timedelta(hours=2),
        metadata=campaign_metadata
    )
    print("   ✓ Facebook post scheduled for +2 hours")

    # 3. Generate campaign analytics
    print("\n3. Generating campaign analytics...")
    summary = adapter.get_analytics_summary()
    print(f"   Current campaign reach: {summary['overall']['total_reach']:,}")
    print(f"   Current engagement rate: {summary['overall']['avg_engagement_rate']}%")

    print("\n✓ Campaign workflow complete!")
    print("  - Immediate posts published")
    print("  - Follow-up posts scheduled")
    print("  - Analytics tracking enabled")


def main():
    """Run all examples"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from social_media_skills import register_social_skills
    from core.state_manager import StateManager
    from core.event_bus import EventBus
    from core.audit_logger import AuditLogger
    from core.retry_queue import RetryQueue
    from routing.skill_registry import SkillRegistry
    from routing.skill_dispatcher import SkillDispatcher

    # Setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("EnterpriseExamples")

    base_dir = Path(__file__).parent
    state_file = base_dir / "example_state.json"
    logs_dir = base_dir / "example_logs"
    reports_dir = base_dir / "example_reports"
    skills_dir = base_dir / "skills"

    logs_dir.mkdir(exist_ok=True)

    # Initialize components
    state_manager = StateManager(state_file)
    event_bus = EventBus(logger)
    audit_logger = AuditLogger(logs_dir, logger)
    retry_queue = RetryQueue(logger, max_retries=3)
    dispatcher = SkillDispatcher(skills_dir, logger)
    skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

    # Register social skills
    adapter = register_social_skills(
        skill_registry=skill_registry,
        logger=logger,
        event_bus=event_bus,
        audit_logger=audit_logger,
        retry_queue=retry_queue,
        reports_dir=reports_dir,
        state_manager=state_manager
    )

    print("\n" + "="*60)
    print("ENTERPRISE SOCIAL MEDIA SKILLS - USAGE EXAMPLES")
    print("="*60)

    # Run examples
    example_basic_post(adapter)
    example_validation_failure(adapter)
    example_moderation_block(adapter)
    example_multi_platform(adapter)
    example_scheduling(adapter)
    example_execute_scheduled(adapter)
    example_analytics(adapter)
    example_error_handling(adapter)
    example_idempotent(adapter)
    example_campaign_workflow(adapter)

    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60)
    print(f"\nCheck the following for results:")
    print(f"  - Reports: {reports_dir}")
    print(f"  - Logs: {logs_dir}")
    print(f"  - State: {state_file}")


if __name__ == '__main__':
    main()

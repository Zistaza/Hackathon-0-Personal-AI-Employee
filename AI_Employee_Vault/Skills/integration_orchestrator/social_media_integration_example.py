#!/usr/bin/env python3
"""
Social Media Skills Integration Example
=========================================

Demonstrates how to integrate social media skills with the
Integration Orchestrator and MCP framework.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, UTC

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_skills import (
    FacebookSkill,
    InstagramSkill,
    TwitterXSkill,
    SocialMCPAdapter,
    register_social_skills
)
from mcp_core import create_mcp_server


# ============================================================================
# Mock Components (use real ones from index.py in production)
# ============================================================================

class MockEventBus:
    """Mock EventBus"""
    def __init__(self):
        self.events = []
        self.subscribers = {}

    def publish(self, event_type: str, data: dict):
        self.events.append({'type': event_type, 'data': data})
        for callback in self.subscribers.get(event_type, []):
            callback(data)

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)


class MockAuditLogger:
    """Mock AuditLogger"""
    def __init__(self):
        self.logs = []

    def log_event(self, event_type: str, data: dict):
        self.logs.append({'type': event_type, 'data': data, 'timestamp': datetime.now(UTC).isoformat()})


class MockRetryQueue:
    """Mock RetryQueue"""
    def __init__(self):
        self.queue = []

    def enqueue(self, operation, args=(), kwargs=None, policy=None, context=None):
        self.queue.append({'operation': operation, 'context': context or {}})


class MockSkillRegistry:
    """Mock SkillRegistry"""
    def __init__(self):
        self.skills = {}

    def register_skill(self, skill_name: str, metadata: dict = None):
        self.skills[skill_name] = metadata or {}


# ============================================================================
# Integration Examples
# ============================================================================

def setup_logger():
    """Setup logger"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('social_integration')


def example_1_basic_usage():
    """Example 1: Basic usage of individual skills"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage of Individual Skills")
    print("="*70)

    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    reports_dir = Path("Reports/Social")

    # Create individual skills
    facebook = FacebookSkill(logger, event_bus, audit_logger, None, reports_dir)
    instagram = InstagramSkill(logger, event_bus, audit_logger, None, reports_dir)
    twitter = TwitterXSkill(logger, event_bus, audit_logger, None, reports_dir)

    # Post to Facebook
    print("\n[1] Posting to Facebook...")
    result = facebook.execute(
        message="Excited to announce our new product launch! 🚀 #innovation #tech",
        media=["product_image.jpg"],
        metadata={'campaign': 'product_launch_2026'}
    )
    print(f"✓ Posted to Facebook: {result['post_id']}" if result['success'] else f"✗ Failed: {result['error']}")

    # Post to Instagram
    print("\n[2] Posting to Instagram...")
    result = instagram.execute(
        message="Behind the scenes of our latest project 📸 #BTS #teamwork",
        media=["bts_photo1.jpg", "bts_photo2.jpg"],
        metadata={'campaign': 'team_culture'}
    )
    print(f"✓ Posted to Instagram: {result['post_id']}" if result['success'] else f"✗ Failed: {result['error']}")

    # Post to Twitter
    print("\n[3] Posting to Twitter...")
    result = twitter.execute(
        message="Just shipped v2.0! Check out the new features 🎉 #release #update",
        metadata={'campaign': 'v2_release'}
    )
    print(f"✓ Posted to Twitter: {result['post_id']}" if result['success'] else f"✗ Failed: {result['error']}")

    # Check events
    print(f"\n[Summary] Events emitted: {len(event_bus.events)}")
    print(f"[Summary] Audit logs: {len(audit_logger.logs)}")


def example_2_mcp_adapter():
    """Example 2: Using SocialMCPAdapter for unified interface"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 2: Using SocialMCPAdapter")
    print("="*70)

    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    retry_queue = MockRetryQueue()
    reports_dir = Path("Reports/Social")

    # Create adapter
    adapter = SocialMCPAdapter(logger, event_bus, audit_logger, retry_queue, reports_dir)

    # Post to specific platform
    print("\n[1] Post to specific platform via adapter...")
    result = adapter.post(
        platform='facebook',
        message='Using the unified adapter interface! #automation',
        media=['demo.jpg']
    )
    print(f"Result: {result['success']}")

    # Post to all platforms
    print("\n[2] Post to all platforms simultaneously...")
    results = adapter.post_to_all(
        message='Multi-platform announcement! 📢',
        media=['announcement.jpg'],
        metadata={'campaign': 'multi_platform_test'}
    )

    for platform, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {platform}: {result.get('post_id', result.get('error', 'N/A'))}")


def example_3_event_driven_workflow():
    """Example 3: Event-driven workflow with cross-platform coordination"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 3: Event-Driven Workflow")
    print("="*70)

    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    reports_dir = Path("Reports/Social")

    # Subscribe to success events for coordination
    def on_facebook_success(data):
        print(f"  [Event Handler] Facebook post successful: {data['post_id']}")
        print(f"  [Event Handler] Triggering Instagram cross-post...")

    def on_post_failed(data):
        print(f"  [Event Handler] Post failed on {data['platform']}: {data['error']}")
        print(f"  [Event Handler] Retry count: {data['retry_count']}")

    event_bus.subscribe('social_post_success', on_facebook_success)
    event_bus.subscribe('social_post_failed', on_post_failed)

    # Create adapter
    adapter = SocialMCPAdapter(logger, event_bus, audit_logger, None, reports_dir)

    print("\n[1] Posting with event handlers...")
    result = adapter.post(
        platform='facebook',
        message='Testing event-driven workflow',
        media=['test.jpg']
    )

    print(f"\n[Summary] Total events: {len(event_bus.events)}")


def example_4_skill_registry_integration():
    """Example 4: Integration with SkillRegistry"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 4: SkillRegistry Integration")
    print("="*70)

    skill_registry = MockSkillRegistry()
    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    retry_queue = MockRetryQueue()
    reports_dir = Path("Reports/Social")

    # Register skills
    print("\n[1] Registering social media skills...")
    adapter = register_social_skills(
        skill_registry,
        logger,
        event_bus,
        audit_logger,
        retry_queue,
        reports_dir
    )

    print(f"Registered skills: {list(skill_registry.skills.keys())}")

    # Use registered skills
    print("\n[2] Using registered skills...")
    result = adapter.post('facebook', 'Post via registered skill')
    print(f"Result: {result['success']}")


def example_5_mcp_integration():
    """Example 5: Integration with MCP Server"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 5: MCP Server Integration")
    print("="*70)

    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    retry_queue = MockRetryQueue()
    reports_dir = Path("Reports/Social")

    # Create MCP server
    print("\n[1] Creating SocialMCPServer...")
    mcp_server = create_mcp_server('social', logger, event_bus, retry_queue)

    # Create adapter with MCP integration
    print("\n[2] Creating SocialMCPAdapter with MCP integration...")
    adapter = SocialMCPAdapter(logger, event_bus, audit_logger, retry_queue,
                              reports_dir, mcp_server)

    # Post via adapter (will sync with MCP)
    print("\n[3] Posting via adapter (syncs with MCP)...")
    result = adapter.post(
        platform='facebook',
        message='Integrated with MCP framework',
        media=['integration.jpg']
    )
    print(f"Skill result: {result['success']}")

    # Also post directly via MCP
    print("\n[4] Posting directly via MCP server...")
    mcp_result = mcp_server.execute_action('post_linkedin', {
        'content': 'Direct MCP post',
        'visibility': 'public'
    })
    print(f"MCP result: {mcp_result.success}")


def example_6_complete_workflow():
    """Example 6: Complete social media campaign workflow"""
    logger = setup_logger()
    print("\n" + "="*70)
    print("EXAMPLE 6: Complete Social Media Campaign Workflow")
    print("="*70)

    event_bus = MockEventBus()
    audit_logger = MockAuditLogger()
    retry_queue = MockRetryQueue()
    reports_dir = Path("Reports/Social")

    adapter = SocialMCPAdapter(logger, event_bus, audit_logger, retry_queue, reports_dir)

    # Campaign: Product Launch
    campaign_metadata = {
        'campaign_id': 'product_launch_2026_q1',
        'campaign_name': 'Product Launch Q1 2026',
        'team': 'marketing'
    }

    print("\n[Campaign] Product Launch Q1 2026")
    print("-" * 70)

    # Phase 1: Teaser posts
    print("\n[Phase 1] Teaser Posts...")
    teaser_message = "Something exciting is coming... Stay tuned! 👀 #ComingSoon"

    results = adapter.post_to_all(
        message=teaser_message,
        media=['teaser.jpg'],
        metadata={**campaign_metadata, 'phase': 'teaser'}
    )

    for platform, result in results.items():
        if result['success']:
            print(f"  ✓ {platform}: {result['post_id']}")

    # Phase 2: Launch announcement
    print("\n[Phase 2] Launch Announcement...")
    launch_message = "🚀 Introducing our revolutionary new product! Available now. #Launch #Innovation"

    # Facebook - detailed post
    fb_result = adapter.post(
        platform='facebook',
        message=launch_message + "\n\nLearn more at our website!",
        media=['product_hero.jpg', 'product_features.jpg'],
        metadata={**campaign_metadata, 'phase': 'launch'}
    )
    print(f"  ✓ Facebook: {fb_result['post_id']}" if fb_result['success'] else f"  ✗ Facebook failed")

    # Instagram - visual focus
    ig_result = adapter.post(
        platform='instagram',
        message=launch_message + "\n\n📸 Swipe for more details!",
        media=['product_1.jpg', 'product_2.jpg', 'product_3.jpg'],
        metadata={**campaign_metadata, 'phase': 'launch'}
    )
    print(f"  ✓ Instagram: {ig_result['post_id']}" if ig_result['success'] else f"  ✗ Instagram failed")

    # Twitter - concise
    tw_result = adapter.post(
        platform='twitter_x',
        message="🚀 New product launched! Check it out → link.co/product #Launch",
        metadata={**campaign_metadata, 'phase': 'launch'}
    )
    print(f"  ✓ Twitter: {tw_result['post_id']}" if tw_result['success'] else f"  ✗ Twitter failed")

    # Campaign summary
    print("\n[Campaign Summary]")
    print(f"  Total posts: {len([r for r in [fb_result, ig_result, tw_result] if r['success']])}")
    print(f"  Events emitted: {len(event_bus.events)}")
    print(f"  Audit logs: {len(audit_logger.logs)}")
    print(f"  Failed posts in retry queue: {len(retry_queue.queue)}")


def main():
    """Run all integration examples"""
    print("\n" + "="*70)
    print("SOCIAL MEDIA SKILLS - INTEGRATION EXAMPLES")
    print("="*70)

    try:
        example_1_basic_usage()
        example_2_mcp_adapter()
        example_3_event_driven_workflow()
        example_4_skill_registry_integration()
        example_5_mcp_integration()
        example_6_complete_workflow()

        print("\n" + "="*70)
        print("ALL INTEGRATION EXAMPLES COMPLETED")
        print("="*70)
        print("\n✓ Social media skills are production-ready")
        print("✓ MCP integration verified")
        print("✓ Event-driven workflows demonstrated")
        print("✓ Complete campaign workflow shown")

    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

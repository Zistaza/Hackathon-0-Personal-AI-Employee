#!/usr/bin/env python3
"""
Test and demonstration script for MCP Core framework.

Shows how to:
- Create MCP servers
- Integrate with EventBus and RetryQueue
- Execute actions with validation
- Handle results and errors
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_core import (
    BaseMCPServer,
    SocialMCPServer,
    AccountingMCPServer,
    NotificationMCPServer,
    create_mcp_server,
    MCPActionResult
)


def setup_logger():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('mcp_test')


def test_social_server():
    """Test SocialMCPServer functionality."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Testing SocialMCPServer")
    print("="*60)

    # Create server without EventBus/RetryQueue for simplicity
    server = SocialMCPServer(logger)

    # List available actions
    print("\nAvailable actions:")
    for action in server.list_actions():
        print(f"  - {action['name']}: {action['metadata'].get('description', 'N/A')}")

    # Test 1: Post to LinkedIn (valid)
    print("\n[Test 1] Posting to LinkedIn...")
    result = server.execute_action('post_linkedin', {
        'content': 'Excited to share our new AI automation framework! #AI #Automation',
        'visibility': 'public'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")
    else:
        print(f"Error: {result.error}")

    # Test 2: Send WhatsApp (valid)
    print("\n[Test 2] Sending WhatsApp message...")
    result = server.execute_action('send_whatsapp', {
        'recipient': '+1234567890',
        'message': 'Hello from MCP framework!'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 3: Invalid action
    print("\n[Test 3] Testing invalid action...")
    result = server.execute_action('invalid_action', {})
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")

    # Test 4: Missing required field
    print("\n[Test 4] Testing missing required field...")
    result = server.execute_action('post_linkedin', {
        'visibility': 'public'
        # Missing 'content' field
    })
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")

    # Test 5: Schedule post
    print("\n[Test 5] Scheduling a post...")
    result = server.execute_action('schedule_post', {
        'platform': 'linkedin',
        'content': 'Scheduled post content',
        'scheduled_time': '2026-03-01T10:00:00'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")


def test_accounting_server():
    """Test AccountingMCPServer functionality."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Testing AccountingMCPServer")
    print("="*60)

    server = AccountingMCPServer(logger)

    # List available actions
    print("\nAvailable actions:")
    for action in server.list_actions():
        print(f"  - {action['name']}: {action['metadata'].get('description', 'N/A')}")

    # Test 1: Create invoice (valid)
    print("\n[Test 1] Creating invoice...")
    result = server.execute_action('create_invoice', {
        'client_name': 'Acme Corp',
        'amount': 5000.00,
        'items': [
            {'description': 'Consulting services', 'amount': 3000},
            {'description': 'Development work', 'amount': 2000}
        ],
        'due_date': '2026-03-15'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 2: Record expense (valid)
    print("\n[Test 2] Recording expense...")
    result = server.execute_action('record_expense', {
        'amount': 150.00,
        'category': 'software',
        'date': '2026-02-28',
        'description': 'Monthly SaaS subscription',
        'vendor': 'Software Inc'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 3: Generate report (valid)
    print("\n[Test 3] Generating financial report...")
    result = server.execute_action('generate_report', {
        'report_type': 'profit_loss',
        'start_date': '2026-01-01',
        'end_date': '2026-02-28',
        'format': 'pdf'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 4: Invalid amount
    print("\n[Test 4] Testing invalid amount...")
    result = server.execute_action('create_invoice', {
        'client_name': 'Test Client',
        'amount': -100,  # Invalid: negative amount
        'items': [{'description': 'Test', 'amount': -100}]
    })
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")

    # Test 5: Invalid category
    print("\n[Test 5] Testing invalid expense category...")
    result = server.execute_action('record_expense', {
        'amount': 100,
        'category': 'invalid_category',
        'date': '2026-02-28'
    })
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")


def test_notification_server():
    """Test NotificationMCPServer functionality."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Testing NotificationMCPServer")
    print("="*60)

    server = NotificationMCPServer(logger)

    # List available actions
    print("\nAvailable actions:")
    for action in server.list_actions():
        print(f"  - {action['name']}: {action['metadata'].get('description', 'N/A')}")

    # Test 1: Send email (valid)
    print("\n[Test 1] Sending email...")
    result = server.execute_action('send_email', {
        'recipient': 'user@example.com',
        'subject': 'Test Email from MCP',
        'body': 'This is a test email sent via MCP framework.'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 2: Send SMS (valid)
    print("\n[Test 2] Sending SMS...")
    result = server.execute_action('send_sms', {
        'phone_number': '+1234567890',
        'message': 'Test SMS from MCP'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 3: Send push notification (valid)
    print("\n[Test 3] Sending push notification...")
    result = server.execute_action('send_push', {
        'user_id': 'user123',
        'title': 'New Update',
        'message': 'Check out the latest features!',
        'action_url': 'https://example.com/updates'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 4: Broadcast (valid)
    print("\n[Test 4] Broadcasting notification...")
    result = server.execute_action('broadcast', {
        'channels': ['email', 'sms', 'push'],
        'message': 'System maintenance scheduled for tonight',
        'priority': 'high'
    })
    print(f"Result: {result.success}")
    if result.success:
        print(f"Data: {result.data}")

    # Test 5: Invalid email
    print("\n[Test 5] Testing invalid email address...")
    result = server.execute_action('send_email', {
        'recipient': 'invalid-email',
        'subject': 'Test',
        'body': 'Test body'
    })
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")

    # Test 6: SMS too long
    print("\n[Test 6] Testing SMS message too long...")
    result = server.execute_action('send_sms', {
        'phone_number': '+1234567890',
        'message': 'x' * 200  # Exceeds 160 character limit
    })
    print(f"Result: {result.success}")
    print(f"Error: {result.error}")


def test_factory_function():
    """Test the factory function for creating servers."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Testing Factory Function")
    print("="*60)

    # Create servers using factory
    print("\nCreating servers via factory...")
    social = create_mcp_server('social', logger)
    accounting = create_mcp_server('accounting', logger)
    notification = create_mcp_server('notification', logger)

    print(f"Social server: {social.name} with {len(social.actions)} actions")
    print(f"Accounting server: {accounting.name} with {len(accounting.actions)} actions")
    print(f"Notification server: {notification.name} with {len(notification.actions)} actions")

    # Test invalid server type
    print("\nTesting invalid server type...")
    try:
        invalid = create_mcp_server('invalid_type', logger)
    except ValueError as e:
        print(f"Caught expected error: {e}")


def test_with_event_bus():
    """Test MCP servers with EventBus integration."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Testing with EventBus Integration")
    print("="*60)

    # Create a simple mock EventBus
    class MockEventBus:
        def __init__(self):
            self.events = []

        def publish(self, event_type: str, data: dict):
            self.events.append({'type': event_type, 'data': data})
            print(f"  [EventBus] Published: {event_type}")

    event_bus = MockEventBus()

    # Create server with EventBus
    server = SocialMCPServer(logger, event_bus=event_bus)

    print("\nExecuting action with EventBus...")
    result = server.execute_action('post_linkedin', {
        'content': 'Test post with event tracking'
    })

    print(f"\nEvents emitted: {len(event_bus.events)}")
    for event in event_bus.events:
        print(f"  - {event['type']}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MCP Core Framework - Test Suite")
    print("="*60)

    try:
        test_social_server()
        test_accounting_server()
        test_notification_server()
        test_factory_function()
        test_with_event_bus()

        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

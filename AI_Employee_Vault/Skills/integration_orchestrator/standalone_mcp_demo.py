#!/usr/bin/env python3
"""
Standalone MCP Framework Demo
==============================

Complete demonstration of the MCP framework without requiring
the full Integration Orchestrator. This shows how the framework
can be used independently or integrated into any system.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Dict, List, Callable, Any
from collections import deque
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_core import (
    BaseMCPServer,
    SocialMCPServer,
    AccountingMCPServer,
    NotificationMCPServer,
    create_mcp_server,
    MCPActionResult
)


# ============================================================================
# Minimal EventBus and RetryQueue implementations for standalone use
# ============================================================================

class SimpleEventBus:
    """Lightweight EventBus for standalone MCP usage"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event: {event_type}")

    def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all subscribers"""
        with self.lock:
            subscribers = self.subscribers.get(event_type, []).copy()

        if subscribers:
            self.logger.debug(f"Publishing event: {event_type} to {len(subscribers)} subscribers")
            for callback in subscribers:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event subscriber for {event_type}: {e}")


class RetryPolicy(Enum):
    """Retry policy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class SimpleRetryQueue:
    """Lightweight RetryQueue for standalone MCP usage"""

    def __init__(self, logger: logging.Logger, max_retries: int = 3):
        self.logger = logger
        self.max_retries = max_retries
        self.queue: deque = deque()
        self.lock = Lock()

    def enqueue(self, operation: Callable, args: tuple = (), kwargs: dict = None,
                policy: RetryPolicy = RetryPolicy.EXPONENTIAL, context: Dict = None):
        """Add operation to retry queue"""
        with self.lock:
            retry_item = {
                'operation': operation,
                'args': args,
                'kwargs': kwargs or {},
                'policy': policy,
                'context': context or {},
                'attempts': 0,
                'created_at': datetime.utcnow()
            }
            self.queue.append(retry_item)
            self.logger.info(f"Enqueued operation for retry: {context.get('name', 'unknown')}")


# ============================================================================
# Complete Application Example
# ============================================================================

class MCPApplication:
    """
    Complete application demonstrating MCP framework usage.

    This shows a real-world scenario where multiple MCP servers
    work together to handle business operations.
    """

    def __init__(self):
        self.logger = self._setup_logger()
        self.event_bus = SimpleEventBus(self.logger)
        self.retry_queue = SimpleRetryQueue(self.logger)

        # Initialize MCP servers
        self.social = create_mcp_server('social', self.logger, self.event_bus, self.retry_queue)
        self.accounting = create_mcp_server('accounting', self.logger, self.event_bus, self.retry_queue)
        self.notification = create_mcp_server('notification', self.logger, self.event_bus, self.retry_queue)

        # Subscribe to events
        self._setup_event_handlers()

        self.logger.info("MCP Application initialized")

    def _setup_logger(self):
        """Setup application logger"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('mcp_app')

    def _setup_event_handlers(self):
        """Setup event handlers for cross-server coordination"""
        # When invoice is created, send notification
        self.event_bus.subscribe('mcp.action.completed', self._on_action_completed)

        # When action fails, log it
        self.event_bus.subscribe('mcp.action.failed', self._on_action_failed)

    def _on_action_completed(self, data: Dict[str, Any]):
        """Handle action completion events"""
        server = data.get('server')
        action = data.get('action')

        # Cross-server coordination: Invoice created -> Send notification
        if server == 'accounting' and action == 'create_invoice':
            result_data = data.get('result', {}).get('data', {})
            invoice_id = result_data.get('invoice_id')

            self.logger.info(f"Invoice {invoice_id} created, sending notification...")
            self.notification.execute_action('send_email', {
                'recipient': 'accounting@company.com',
                'subject': f'New Invoice: {invoice_id}',
                'body': f'Invoice {invoice_id} has been created.'
            })

    def _on_action_failed(self, data: Dict[str, Any]):
        """Handle action failure events"""
        self.logger.error(
            f"Action failed: {data.get('server')}.{data.get('action')} - {data.get('error')}"
        )

    def run_business_scenario(self):
        """
        Run a complete business scenario demonstrating all MCP servers.

        Scenario: New client onboarding
        1. Create invoice for new client
        2. Send welcome email
        3. Post announcement on LinkedIn
        4. Record initial expense
        5. Generate onboarding report
        """
        print("\n" + "="*70)
        print("BUSINESS SCENARIO: New Client Onboarding")
        print("="*70)

        client_name = "TechStart Inc"
        client_email = "contact@techstart.com"

        # Step 1: Create invoice
        print("\n[Step 1] Creating invoice...")
        invoice_result = self.accounting.execute_action('create_invoice', {
            'client_name': client_name,
            'amount': 15000.00,
            'items': [
                {'description': 'Initial setup fee', 'amount': 5000},
                {'description': 'First month service', 'amount': 10000}
            ],
            'due_date': '2026-03-15'
        })

        if invoice_result.success:
            print(f"✓ Invoice created: {invoice_result.data['invoice_id']}")
        else:
            print(f"✗ Invoice creation failed: {invoice_result.error}")
            return

        # Step 2: Send welcome email
        print("\n[Step 2] Sending welcome email...")
        email_result = self.notification.execute_action('send_email', {
            'recipient': client_email,
            'subject': f'Welcome to our platform, {client_name}!',
            'body': 'Thank you for choosing our services. We look forward to working with you.'
        })

        if email_result.success:
            print(f"✓ Welcome email sent: {email_result.data['message_id']}")
        else:
            print(f"✗ Email failed: {email_result.error}")

        # Step 3: Post LinkedIn announcement
        print("\n[Step 3] Posting LinkedIn announcement...")
        linkedin_result = self.social.execute_action('post_linkedin', {
            'content': f'🎉 Excited to welcome {client_name} to our growing family of clients! '
                      f'Looking forward to an amazing partnership. #NewClient #Growth',
            'visibility': 'public'
        })

        if linkedin_result.success:
            print(f"✓ LinkedIn post published: {linkedin_result.data['post_id']}")
        else:
            print(f"✗ LinkedIn post failed: {linkedin_result.error}")

        # Step 4: Record onboarding expense
        print("\n[Step 4] Recording onboarding expenses...")
        expense_result = self.accounting.execute_action('record_expense', {
            'amount': 500.00,
            'category': 'marketing',
            'date': datetime.utcnow().isoformat(),
            'description': f'Client onboarding materials for {client_name}',
            'vendor': 'Marketing Supplies Co'
        })

        if expense_result.success:
            print(f"✓ Expense recorded: {expense_result.data['expense_id']}")
        else:
            print(f"✗ Expense recording failed: {expense_result.error}")

        # Step 5: Send multi-channel notification to team
        print("\n[Step 5] Notifying team across all channels...")
        broadcast_result = self.notification.execute_action('broadcast', {
            'channels': ['email', 'sms', 'push'],
            'message': f'New client onboarded: {client_name}. Invoice: {invoice_result.data["invoice_id"]}',
            'priority': 'high'
        })

        if broadcast_result.success:
            print(f"✓ Team notified via {len(broadcast_result.data['channels'])} channels")
        else:
            print(f"✗ Broadcast failed: {broadcast_result.error}")

        # Summary
        print("\n" + "="*70)
        print("ONBOARDING COMPLETE")
        print("="*70)
        print(f"Client: {client_name}")
        print(f"Invoice: {invoice_result.data['invoice_id']}")
        print(f"Amount: ${invoice_result.data['amount']}")
        print(f"Status: All systems operational ✓")

    def demonstrate_validation(self):
        """Demonstrate payload validation"""
        print("\n" + "="*70)
        print("DEMONSTRATION: Payload Validation")
        print("="*70)

        # Test 1: Missing required field
        print("\n[Test 1] Missing required field...")
        result = self.social.execute_action('post_linkedin', {
            'visibility': 'public'
            # Missing 'content' field
        })
        print(f"Result: {result.success}")
        print(f"Error: {result.error}")

        # Test 2: Invalid data type
        print("\n[Test 2] Invalid amount (negative)...")
        result = self.accounting.execute_action('create_invoice', {
            'client_name': 'Test',
            'amount': -100,  # Invalid
            'items': []
        })
        print(f"Result: {result.success}")
        print(f"Error: {result.error}")

        # Test 3: Invalid email format
        print("\n[Test 3] Invalid email format...")
        result = self.notification.execute_action('send_email', {
            'recipient': 'not-an-email',
            'subject': 'Test',
            'body': 'Test'
        })
        print(f"Result: {result.success}")
        print(f"Error: {result.error}")

    def demonstrate_event_system(self):
        """Demonstrate event-driven architecture"""
        print("\n" + "="*70)
        print("DEMONSTRATION: Event-Driven Architecture")
        print("="*70)

        event_log = []

        def log_event(data):
            event_log.append(data)
            print(f"  [Event] {data.get('server')}.{data.get('action')} - "
                  f"{data.get('execution_id', 'N/A')[:20]}...")

        # Subscribe to all MCP events
        self.event_bus.subscribe('mcp.action.started', log_event)
        self.event_bus.subscribe('mcp.action.completed', log_event)

        print("\nExecuting action (watch for events)...")
        result = self.social.execute_action('send_whatsapp', {
            'recipient': '+1234567890',
            'message': 'Test message'
        })

        print(f"\nTotal events emitted: {len(event_log)}")

    def list_capabilities(self):
        """List all available MCP capabilities"""
        print("\n" + "="*70)
        print("MCP FRAMEWORK CAPABILITIES")
        print("="*70)

        servers = {
            'Social': self.social,
            'Accounting': self.accounting,
            'Notification': self.notification
        }

        for server_name, server in servers.items():
            print(f"\n{server_name} Server ({server.name}):")
            actions = server.list_actions()
            for action in actions:
                metadata = action['metadata']
                print(f"  • {action['name']}")
                print(f"    Description: {metadata.get('description', 'N/A')}")
                print(f"    Required: {', '.join(metadata.get('required_fields', []))}")
                if metadata.get('optional_fields'):
                    print(f"    Optional: {', '.join(metadata.get('optional_fields', []))}")


def main():
    """Run complete MCP framework demonstration"""
    print("\n" + "="*70)
    print("MCP FRAMEWORK - STANDALONE DEMONSTRATION")
    print("="*70)

    # Create application
    app = MCPApplication()

    # Run demonstrations
    app.list_capabilities()
    app.run_business_scenario()
    app.demonstrate_validation()
    app.demonstrate_event_system()

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nThe MCP framework is ready for integration!")
    print("See INTEGRATION_GUIDE.py for integration instructions.")
    print("See MCP_README.md for complete documentation.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

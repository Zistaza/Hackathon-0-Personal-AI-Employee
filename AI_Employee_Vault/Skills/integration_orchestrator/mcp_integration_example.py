#!/usr/bin/env python3
"""
MCP Integration Example
========================

Demonstrates how to integrate MCP servers with the existing
Integration Orchestrator's EventBus and RetryQueue.

This example shows:
1. Creating MCP servers with orchestrator components
2. Subscribing to MCP events
3. Handling failures with automatic retry
4. Coordinating multiple MCP servers
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_core import (
    SocialMCPServer,
    AccountingMCPServer,
    NotificationMCPServer,
    create_mcp_server
)


def setup_logger():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('mcp_integration')


class MCPOrchestrator:
    """
    Orchestrator for managing multiple MCP servers.

    Integrates with EventBus and RetryQueue from the main orchestrator.
    """

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None):
        self.logger = logger
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.servers = {}

        # Initialize MCP servers
        self._initialize_servers()

        # Subscribe to MCP events
        self._subscribe_to_events()

    def _initialize_servers(self):
        """Initialize all MCP servers."""
        self.logger.info("Initializing MCP servers...")

        # Create servers with shared EventBus and RetryQueue
        self.servers['social'] = SocialMCPServer(
            self.logger,
            event_bus=self.event_bus,
            retry_queue=self.retry_queue
        )

        self.servers['accounting'] = AccountingMCPServer(
            self.logger,
            event_bus=self.event_bus,
            retry_queue=self.retry_queue
        )

        self.servers['notification'] = NotificationMCPServer(
            self.logger,
            event_bus=self.event_bus,
            retry_queue=self.retry_queue
        )

        self.logger.info(f"Initialized {len(self.servers)} MCP servers")

    def _subscribe_to_events(self):
        """Subscribe to MCP events for monitoring and coordination."""
        if not self.event_bus:
            return

        # Subscribe to action lifecycle events
        self.event_bus.subscribe('mcp.action.started', self._on_action_started)
        self.event_bus.subscribe('mcp.action.completed', self._on_action_completed)
        self.event_bus.subscribe('mcp.action.failed', self._on_action_failed)

        self.logger.info("Subscribed to MCP events")

    def _on_action_started(self, data: dict):
        """Handle action started event."""
        self.logger.info(
            f"[Event] Action started: {data['server']}.{data['action']} "
            f"(ID: {data['execution_id']})"
        )

    def _on_action_completed(self, data: dict):
        """Handle action completed event."""
        self.logger.info(
            f"[Event] Action completed: {data['server']}.{data['action']} "
            f"(ID: {data['execution_id']})"
        )

        # Example: Trigger follow-up actions based on completion
        if data['action'] == 'create_invoice':
            self._send_invoice_notification(data)

    def _on_action_failed(self, data: dict):
        """Handle action failed event."""
        self.logger.error(
            f"[Event] Action failed: {data['server']}.{data['action']} "
            f"(ID: {data['execution_id']}) - {data['error']}"
        )

    def _send_invoice_notification(self, invoice_data: dict):
        """Send notification when invoice is created."""
        self.logger.info("Triggering invoice notification...")

        notification_server = self.servers.get('notification')
        if notification_server:
            notification_server.execute_action('send_email', {
                'recipient': 'accounting@example.com',
                'subject': 'New Invoice Created',
                'body': f"Invoice created at {datetime.utcnow().isoformat()}"
            })

    def execute_workflow(self, workflow_name: str, params: dict):
        """
        Execute a predefined workflow across multiple MCP servers.

        Args:
            workflow_name: Name of the workflow to execute
            params: Workflow parameters
        """
        self.logger.info(f"Executing workflow: {workflow_name}")

        workflows = {
            'client_onboarding': self._workflow_client_onboarding,
            'monthly_reporting': self._workflow_monthly_reporting,
            'social_campaign': self._workflow_social_campaign
        }

        workflow_func = workflows.get(workflow_name)
        if not workflow_func:
            self.logger.error(f"Unknown workflow: {workflow_name}")
            return {'success': False, 'error': 'Unknown workflow'}

        return workflow_func(params)

    def _workflow_client_onboarding(self, params: dict):
        """
        Client onboarding workflow:
        1. Create invoice
        2. Send welcome email
        3. Post announcement on LinkedIn
        """
        results = {}

        # Step 1: Create invoice
        self.logger.info("Step 1: Creating invoice...")
        invoice_result = self.servers['accounting'].execute_action('create_invoice', {
            'client_name': params['client_name'],
            'amount': params['amount'],
            'items': params['items']
        })
        results['invoice'] = invoice_result.to_dict()

        if not invoice_result.success:
            return {'success': False, 'error': 'Invoice creation failed', 'results': results}

        # Step 2: Send welcome email
        self.logger.info("Step 2: Sending welcome email...")
        email_result = self.servers['notification'].execute_action('send_email', {
            'recipient': params['client_email'],
            'subject': f"Welcome {params['client_name']}!",
            'body': 'Thank you for choosing our services.'
        })
        results['email'] = email_result.to_dict()

        # Step 3: Post announcement (optional, don't fail workflow if this fails)
        if params.get('announce_on_linkedin', False):
            self.logger.info("Step 3: Posting LinkedIn announcement...")
            social_result = self.servers['social'].execute_action('post_linkedin', {
                'content': f"Excited to welcome {params['client_name']} as our new client! 🎉"
            })
            results['social'] = social_result.to_dict()

        return {'success': True, 'results': results}

    def _workflow_monthly_reporting(self, params: dict):
        """
        Monthly reporting workflow:
        1. Generate financial report
        2. Send report via email
        3. Post summary on social media
        """
        results = {}

        # Step 1: Generate report
        self.logger.info("Step 1: Generating financial report...")
        report_result = self.servers['accounting'].execute_action('generate_report', {
            'report_type': 'profit_loss',
            'start_date': params['start_date'],
            'end_date': params['end_date']
        })
        results['report'] = report_result.to_dict()

        if not report_result.success:
            return {'success': False, 'error': 'Report generation failed', 'results': results}

        # Step 2: Email report
        self.logger.info("Step 2: Emailing report...")
        email_result = self.servers['notification'].execute_action('send_email', {
            'recipient': params['recipient_email'],
            'subject': f"Monthly Report: {params['start_date']} to {params['end_date']}",
            'body': 'Please find attached your monthly financial report.'
        })
        results['email'] = email_result.to_dict()

        return {'success': True, 'results': results}

    def _workflow_social_campaign(self, params: dict):
        """
        Social media campaign workflow:
        1. Schedule posts across platforms
        2. Send notification to team
        """
        results = {}

        # Step 1: Schedule posts
        self.logger.info("Step 1: Scheduling social posts...")
        posts = []
        for platform in params.get('platforms', ['linkedin']):
            post_result = self.servers['social'].execute_action('schedule_post', {
                'platform': platform,
                'content': params['content'],
                'scheduled_time': params['scheduled_time']
            })
            posts.append(post_result.to_dict())
        results['posts'] = posts

        # Step 2: Notify team
        self.logger.info("Step 2: Notifying team...")
        notification_result = self.servers['notification'].execute_action('broadcast', {
            'channels': ['email', 'slack'],
            'message': f"Social campaign scheduled for {params['scheduled_time']}"
        })
        results['notification'] = notification_result.to_dict()

        return {'success': True, 'results': results}

    def get_server(self, server_name: str):
        """Get a specific MCP server by name."""
        return self.servers.get(server_name)

    def list_all_actions(self):
        """List all available actions across all servers."""
        all_actions = {}
        for server_name, server in self.servers.items():
            all_actions[server_name] = server.list_actions()
        return all_actions


def demo_basic_integration():
    """Demonstrate basic MCP integration."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Demo: Basic MCP Integration")
    print("="*60)

    # Create mock EventBus for demonstration
    class MockEventBus:
        def __init__(self):
            self.subscribers = {}

        def subscribe(self, event_type: str, callback):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

        def publish(self, event_type: str, data: dict):
            for callback in self.subscribers.get(event_type, []):
                callback(data)

    event_bus = MockEventBus()

    # Create orchestrator
    orchestrator = MCPOrchestrator(logger, event_bus=event_bus)

    # List all available actions
    print("\nAvailable actions:")
    all_actions = orchestrator.list_all_actions()
    for server_name, actions in all_actions.items():
        print(f"\n{server_name.upper()} Server:")
        for action in actions:
            print(f"  - {action['name']}: {action['metadata'].get('description', 'N/A')}")

    # Execute individual actions
    print("\n" + "-"*60)
    print("Executing individual actions...")
    print("-"*60)

    social_server = orchestrator.get_server('social')
    result = social_server.execute_action('post_linkedin', {
        'content': 'Check out our new MCP framework! #automation'
    })
    print(f"LinkedIn post: {result.success}")


def demo_workflows():
    """Demonstrate workflow execution."""
    logger = setup_logger()
    print("\n" + "="*60)
    print("Demo: Workflow Execution")
    print("="*60)

    # Create mock EventBus
    class MockEventBus:
        def __init__(self):
            self.subscribers = {}

        def subscribe(self, event_type: str, callback):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

        def publish(self, event_type: str, data: dict):
            for callback in self.subscribers.get(event_type, []):
                callback(data)

    event_bus = MockEventBus()
    orchestrator = MCPOrchestrator(logger, event_bus=event_bus)

    # Workflow 1: Client Onboarding
    print("\n" + "-"*60)
    print("Workflow 1: Client Onboarding")
    print("-"*60)

    result = orchestrator.execute_workflow('client_onboarding', {
        'client_name': 'Acme Corp',
        'client_email': 'contact@acme.com',
        'amount': 10000,
        'items': [
            {'description': 'Consulting', 'amount': 10000}
        ],
        'announce_on_linkedin': True
    })
    print(f"Workflow result: {result['success']}")
    print(f"Steps completed: {len(result['results'])}")

    # Workflow 2: Monthly Reporting
    print("\n" + "-"*60)
    print("Workflow 2: Monthly Reporting")
    print("-"*60)

    result = orchestrator.execute_workflow('monthly_reporting', {
        'start_date': '2026-02-01',
        'end_date': '2026-02-28',
        'recipient_email': 'ceo@company.com'
    })
    print(f"Workflow result: {result['success']}")

    # Workflow 3: Social Campaign
    print("\n" + "-"*60)
    print("Workflow 3: Social Media Campaign")
    print("-"*60)

    result = orchestrator.execute_workflow('social_campaign', {
        'platforms': ['linkedin', 'twitter'],
        'content': 'Exciting product launch coming soon!',
        'scheduled_time': '2026-03-01T09:00:00'
    })
    print(f"Workflow result: {result['success']}")


def main():
    """Run integration demos."""
    print("\n" + "="*60)
    print("MCP Integration Examples")
    print("="*60)

    try:
        demo_basic_integration()
        demo_workflows()

        print("\n" + "="*60)
        print("Integration demos completed!")
        print("="*60)

    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

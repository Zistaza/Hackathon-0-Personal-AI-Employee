#!/usr/bin/env python3
"""
Quick Integration Guide: Adding MCP Servers to Integration Orchestrator
========================================================================

This file shows exactly how to integrate the MCP framework into the
existing Integration Orchestrator (index.py).

STEP 1: Import MCP modules at the top of index.py
STEP 2: Initialize MCP servers in IntegrationOrchestrator.__init__
STEP 3: Add MCP event handlers
STEP 4: Add methods to execute MCP actions
"""

# ============================================================================
# STEP 1: Add these imports to index.py
# ============================================================================

"""
Add to the import section of index.py:

from mcp_core import (
    create_mcp_server,
    SocialMCPServer,
    AccountingMCPServer,
    NotificationMCPServer,
    MCPActionResult
)
"""

# ============================================================================
# STEP 2: Initialize MCP servers in IntegrationOrchestrator.__init__
# ============================================================================

"""
Add this code to IntegrationOrchestrator.__init__ method, after EventBus
and RetryQueue are initialized:

    def __init__(self, vault_path: Path):
        # ... existing initialization code ...

        # Initialize EventBus and RetryQueue first
        self.event_bus = EventBus(self.logger)
        self.retry_queue = RetryQueue(self.logger)

        # Initialize MCP servers
        self._initialize_mcp_servers()

        # ... rest of initialization ...

    def _initialize_mcp_servers(self):
        '''Initialize all MCP servers with EventBus and RetryQueue integration'''
        self.logger.info("Initializing MCP servers...")

        self.mcp_servers = {
            'social': create_mcp_server(
                'social',
                self.logger,
                self.event_bus,
                self.retry_queue
            ),
            'accounting': create_mcp_server(
                'accounting',
                self.logger,
                self.event_bus,
                self.retry_queue
            ),
            'notification': create_mcp_server(
                'notification',
                self.logger,
                self.event_bus,
                self.retry_queue
            )
        }

        # Subscribe to MCP events
        self.event_bus.subscribe('mcp.action.completed', self._on_mcp_action_completed)
        self.event_bus.subscribe('mcp.action.failed', self._on_mcp_action_failed)

        self.logger.info(f"Initialized {len(self.mcp_servers)} MCP servers")
"""

# ============================================================================
# STEP 3: Add MCP event handlers
# ============================================================================

"""
Add these methods to the IntegrationOrchestrator class:

    def _on_mcp_action_completed(self, data: Dict[str, Any]):
        '''Handle MCP action completion events'''
        server = data.get('server')
        action = data.get('action')
        execution_id = data.get('execution_id')

        self.logger.info(f"MCP action completed: {server}.{action} (ID: {execution_id})")

        # Audit log the completion
        if hasattr(self, 'audit_logger'):
            self.audit_logger.log_event(
                'mcp_action_completed',
                {
                    'server': server,
                    'action': action,
                    'execution_id': execution_id,
                    'result': data.get('result')
                }
            )

        # Trigger follow-up actions based on completion
        self._handle_mcp_completion(server, action, data)

    def _on_mcp_action_failed(self, data: Dict[str, Any]):
        '''Handle MCP action failure events'''
        server = data.get('server')
        action = data.get('action')
        execution_id = data.get('execution_id')
        error = data.get('error')

        self.logger.error(f"MCP action failed: {server}.{action} - {error}")

        # Audit log the failure
        if hasattr(self, 'audit_logger'):
            self.audit_logger.log_event(
                'mcp_action_failed',
                {
                    'server': server,
                    'action': action,
                    'execution_id': execution_id,
                    'error': error,
                    'reason': data.get('reason')
                }
            )

    def _handle_mcp_completion(self, server: str, action: str, data: Dict[str, Any]):
        '''Handle follow-up actions after MCP action completion'''
        # Example: Send notification when invoice is created
        if server == 'accounting' and action == 'create_invoice':
            result = data.get('result', {}).get('data', {})
            invoice_id = result.get('invoice_id')

            if invoice_id:
                self.execute_mcp_action('notification', 'send_email', {
                    'recipient': 'accounting@company.com',
                    'subject': f'New Invoice Created: {invoice_id}',
                    'body': f'Invoice {invoice_id} has been created and is ready for review.'
                })

        # Add more follow-up logic as needed
"""

# ============================================================================
# STEP 4: Add methods to execute MCP actions
# ============================================================================

"""
Add these public methods to the IntegrationOrchestrator class:

    def execute_mcp_action(self, server_name: str, action_name: str,
                          payload: Dict[str, Any], retry_on_failure: bool = True) -> MCPActionResult:
        '''
        Execute an MCP action.

        Args:
            server_name: Name of the MCP server ('social', 'accounting', 'notification')
            action_name: Name of the action to execute
            payload: Action payload
            retry_on_failure: Whether to retry on failure

        Returns:
            MCPActionResult object

        Raises:
            ValueError: If server_name is invalid
        '''
        server = self.mcp_servers.get(server_name)
        if not server:
            raise ValueError(f"Unknown MCP server: {server_name}. "
                           f"Available: {list(self.mcp_servers.keys())}")

        return server.execute_action(action_name, payload, retry_on_failure)

    def get_mcp_server(self, server_name: str):
        '''Get an MCP server by name'''
        return self.mcp_servers.get(server_name)

    def list_mcp_actions(self) -> Dict[str, List[Dict[str, Any]]]:
        '''List all available MCP actions across all servers'''
        return {
            server_name: server.list_actions()
            for server_name, server in self.mcp_servers.items()
        }
"""

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Once integrated, you can use MCP servers like this:

# Example 1: Post to LinkedIn
orchestrator.execute_mcp_action('social', 'post_linkedin', {
    'content': 'Excited to announce our new feature! #automation',
    'visibility': 'public'
})

# Example 2: Create invoice
result = orchestrator.execute_mcp_action('accounting', 'create_invoice', {
    'client_name': 'Acme Corp',
    'amount': 5000.00,
    'items': [
        {'description': 'Consulting services', 'amount': 3000},
        {'description': 'Development work', 'amount': 2000}
    ]
})

if result.success:
    print(f"Invoice created: {result.data['invoice_id']}")
else:
    print(f"Failed to create invoice: {result.error}")

# Example 3: Send notification
orchestrator.execute_mcp_action('notification', 'send_email', {
    'recipient': 'user@example.com',
    'subject': 'Task Completed',
    'body': 'Your requested task has been completed successfully.'
})

# Example 4: Broadcast notification
orchestrator.execute_mcp_action('notification', 'broadcast', {
    'channels': ['email', 'sms', 'push'],
    'message': 'System maintenance scheduled for tonight at 10 PM'
})

# Example 5: List all available actions
actions = orchestrator.list_mcp_actions()
for server_name, server_actions in actions.items():
    print(f"\n{server_name.upper()} Server:")
    for action in server_actions:
        print(f"  - {action['name']}: {action['metadata'].get('description')}")
"""

# ============================================================================
# INTEGRATION WITH EXISTING WORKFLOWS
# ============================================================================

"""
You can integrate MCP actions into existing orchestrator workflows:

# In your file watcher or event handler:
def handle_new_email_task(self, email_file: Path):
    # ... existing email processing ...

    # Use MCP to send notification
    self.execute_mcp_action('notification', 'send_email', {
        'recipient': 'admin@company.com',
        'subject': 'New Task Received',
        'body': f'New email task: {email_file.name}'
    })

# In your approval workflow:
def handle_approval_granted(self, task_id: str):
    # ... existing approval logic ...

    # Post to LinkedIn about the completed task
    self.execute_mcp_action('social', 'post_linkedin', {
        'content': f'Successfully completed task {task_id}! #productivity'
    })

# In your skill execution:
def execute_skill_with_notification(self, skill_name: str, params: dict):
    result = self.skill_dispatcher.execute(skill_name, params)

    if result['success']:
        # Send success notification via MCP
        self.execute_mcp_action('notification', 'send_push', {
            'user_id': 'admin',
            'title': 'Skill Completed',
            'message': f'{skill_name} executed successfully'
        })

    return result
"""

# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

"""
After integration, test with:

1. Run the test suite:
   python test_mcp_core.py

2. Test integration:
   python mcp_integration_example.py

3. Test in orchestrator:
   # Add this to your main() or test function
   orchestrator = IntegrationOrchestrator(vault_path)

   # Test social action
   result = orchestrator.execute_mcp_action('social', 'post_linkedin', {
       'content': 'Test post from integrated MCP framework'
   })
   print(f"Social test: {result.success}")

   # Test accounting action
   result = orchestrator.execute_mcp_action('accounting', 'create_invoice', {
       'client_name': 'Test Client',
       'amount': 100,
       'items': [{'description': 'Test', 'amount': 100}]
   })
   print(f"Accounting test: {result.success}")

   # Test notification action
   result = orchestrator.execute_mcp_action('notification', 'send_email', {
       'recipient': 'test@example.com',
       'subject': 'Test',
       'body': 'Test email'
   })
   print(f"Notification test: {result.success}")
"""

if __name__ == '__main__':
    print(__doc__)
    print("\nThis is a guide file. Follow the steps above to integrate MCP into index.py")

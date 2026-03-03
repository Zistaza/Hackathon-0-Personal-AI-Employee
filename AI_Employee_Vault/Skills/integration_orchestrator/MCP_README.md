# MCP Core Framework

Modular Component Protocol (MCP) server framework for the AI Employee Vault integration orchestrator.

## Overview

The MCP Core framework provides a standardized way to create modular, event-driven servers that handle specific domain actions with built-in validation, retry logic, and event emission capabilities.

## Architecture

```
BaseMCPServer (Abstract)
├── SocialMCPServer
├── AccountingMCPServer
└── NotificationMCPServer
```

### Key Components

- **BaseMCPServer**: Abstract base class defining the MCP protocol
- **MCPActionResult**: Standardized result object for action execution
- **Event Integration**: Seamless integration with EventBus for pub/sub
- **Retry Support**: Automatic retry with RetryQueue for failed operations

## Features

### Core Capabilities

1. **Action Registration**: Dynamic action registration with metadata
2. **Payload Validation**: Schema validation before execution
3. **Event Emission**: Automatic event publishing for action lifecycle
4. **Retry Logic**: Failed operations automatically enqueued for retry
5. **Error Handling**: Comprehensive error handling with detailed logging
6. **Result Objects**: Standardized result format with success/error info

### Event Types

The framework emits the following events:

- `mcp.action.registered`: When an action is registered
- `mcp.action.started`: When action execution begins
- `mcp.action.completed`: When action completes successfully
- `mcp.action.failed`: When action fails

## Available Servers

### SocialMCPServer

Handles social media integrations.

**Actions:**
- `post_linkedin`: Post content to LinkedIn
- `send_whatsapp`: Send WhatsApp message
- `schedule_post`: Schedule a social media post

### AccountingMCPServer

Handles financial operations and accounting tasks.

**Actions:**
- `create_invoice`: Create a new invoice
- `record_expense`: Record a business expense
- `generate_report`: Generate financial report

### NotificationMCPServer

Handles multi-channel notifications.

**Actions:**
- `send_email`: Send email notification
- `send_sms`: Send SMS notification
- `send_push`: Send push notification
- `broadcast`: Broadcast notification across multiple channels

## Usage

### Basic Usage

```python
from mcp_core import SocialMCPServer
import logging

logger = logging.getLogger('my_app')

# Create server
server = SocialMCPServer(logger)

# Execute action
result = server.execute_action('post_linkedin', {
    'content': 'Hello from MCP!',
    'visibility': 'public'
})

if result.success:
    print(f"Success: {result.data}")
else:
    print(f"Error: {result.error}")
```

### With EventBus and RetryQueue

```python
from mcp_core import create_mcp_server
from index import EventBus, RetryQueue
import logging

logger = logging.getLogger('my_app')
event_bus = EventBus(logger)
retry_queue = RetryQueue(logger)

# Create server with integrations
server = create_mcp_server('social', logger, event_bus, retry_queue)

# Subscribe to events
def on_action_completed(data):
    print(f"Action completed: {data['action']}")

event_bus.subscribe('mcp.action.completed', on_action_completed)

# Execute action (will emit events and retry on failure)
result = server.execute_action('post_linkedin', {
    'content': 'Hello World!'
})
```

### Factory Function

```python
from mcp_core import create_mcp_server

# Create servers using factory
social = create_mcp_server('social', logger)
accounting = create_mcp_server('accounting', logger)
notification = create_mcp_server('notification', logger)
```

### Workflow Orchestration

```python
from mcp_integration_example import MCPOrchestrator

# Create orchestrator
orchestrator = MCPOrchestrator(logger, event_bus, retry_queue)

# Execute workflow
result = orchestrator.execute_workflow('client_onboarding', {
    'client_name': 'Acme Corp',
    'client_email': 'contact@acme.com',
    'amount': 10000,
    'items': [{'description': 'Consulting', 'amount': 10000}],
    'announce_on_linkedin': True
})
```

## Creating Custom MCP Servers

### Step 1: Extend BaseMCPServer

```python
from mcp_core import BaseMCPServer
from typing import Dict, Any, Optional

class CustomMCPServer(BaseMCPServer):
    def __init__(self, logger, event_bus=None, retry_queue=None):
        super().__init__('custom', logger, event_bus, retry_queue)

    def _register_actions(self):
        """Register your custom actions"""
        self.register_action(
            'my_action',
            self._handle_my_action,
            metadata={
                'description': 'My custom action',
                'required_fields': ['field1', 'field2'],
                'optional_fields': ['field3']
            }
        )

    def _validate_payload_schema(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate payload for your actions"""
        metadata = self.action_metadata.get(action_name, {})
        required_fields = metadata.get('required_fields', [])

        # Check required fields
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Add custom validation logic
        if action_name == 'my_action':
            if not payload.get('field1'):
                return False, "field1 cannot be empty"

        return True, None

    def _handle_my_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle your custom action"""
        self.logger.info(f"Executing my_action with {payload}")

        # Your implementation here
        return {
            'status': 'success',
            'result': 'Action completed'
        }
```

### Step 2: Use Your Custom Server

```python
server = CustomMCPServer(logger, event_bus, retry_queue)
result = server.execute_action('my_action', {
    'field1': 'value1',
    'field2': 'value2'
})
```

## Integration with Orchestrator

To integrate MCP servers with the main Integration Orchestrator:

```python
# In index.py or your orchestrator module
from mcp_core import create_mcp_server

class IntegrationOrchestrator:
    def __init__(self):
        # ... existing initialization ...

        # Initialize MCP servers
        self.mcp_servers = {
            'social': create_mcp_server('social', self.logger, self.event_bus, self.retry_queue),
            'accounting': create_mcp_server('accounting', self.logger, self.event_bus, self.retry_queue),
            'notification': create_mcp_server('notification', self.logger, self.event_bus, self.retry_queue)
        }

        # Subscribe to MCP events
        self.event_bus.subscribe('mcp.action.completed', self._on_mcp_action_completed)
        self.event_bus.subscribe('mcp.action.failed', self._on_mcp_action_failed)

    def _on_mcp_action_completed(self, data):
        """Handle MCP action completion"""
        self.logger.info(f"MCP action completed: {data['server']}.{data['action']}")

    def _on_mcp_action_failed(self, data):
        """Handle MCP action failure"""
        self.logger.error(f"MCP action failed: {data['server']}.{data['action']} - {data['error']}")

    def execute_mcp_action(self, server_name: str, action_name: str, payload: dict):
        """Execute an MCP action"""
        server = self.mcp_servers.get(server_name)
        if not server:
            raise ValueError(f"Unknown MCP server: {server_name}")

        return server.execute_action(action_name, payload)
```

## API Reference

### BaseMCPServer

#### Methods

- `register_action(name, handler, metadata)`: Register an action handler
- `validate_payload(action_name, payload)`: Validate action payload
- `execute_action(action_name, payload, retry_on_failure)`: Execute an action
- `list_actions()`: List all registered actions
- `get_action_info(action_name)`: Get information about a specific action

#### Abstract Methods (must implement)

- `_register_actions()`: Register all actions for this server
- `_validate_payload_schema(action_name, payload)`: Validate payload schema

### MCPActionResult

#### Properties

- `success` (bool): Whether the action succeeded
- `data` (Any): Result data if successful
- `error` (str): Error message if failed
- `metadata` (dict): Additional metadata
- `timestamp` (str): ISO timestamp of execution

#### Methods

- `to_dict()`: Convert result to dictionary

## Testing

Run the test suite:

```bash
# Basic tests
python test_mcp_core.py

# Integration examples
python mcp_integration_example.py
```

## Error Handling

The framework provides comprehensive error handling:

1. **Validation Errors**: Caught before execution, no retry
2. **Execution Errors**: Caught during execution, enqueued for retry if enabled
3. **Event Emission Errors**: Logged but don't fail the action

## Best Practices

1. **Always validate payloads**: Implement thorough validation in `_validate_payload_schema`
2. **Use metadata**: Provide clear metadata for each action
3. **Handle errors gracefully**: Don't let exceptions bubble up from handlers
4. **Emit meaningful events**: Include relevant context in event data
5. **Keep actions atomic**: Each action should be a single, focused operation
6. **Use retry wisely**: Only retry transient failures, not validation errors

## Examples

See the following files for examples:

- `test_mcp_core.py`: Basic usage and testing
- `mcp_integration_example.py`: Workflow orchestration and event handling

## License

Part of the AI Employee Vault project.

#!/usr/bin/env python3
"""
MCP Server Framework - Modular Component Protocol
==================================================

Abstract base class and concrete implementations for MCP servers.
Each server handles specific domain actions with validation, retry logic,
and event emission capabilities.

Architecture:
- BaseMCPServer: Abstract base class defining the MCP protocol
- SocialMCPServer: Handles social media integrations (LinkedIn, WhatsApp, etc.)
- AccountingMCPServer: Handles financial operations and accounting tasks
- NotificationMCPServer: Handles notifications across multiple channels
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from enum import Enum


class MCPActionResult:
    """Result object for MCP action execution"""

    def __init__(self, success: bool, data: Any = None, error: str = None, metadata: Dict = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class BaseMCPServer(ABC):
    """
    Abstract base class for MCP servers.

    Each MCP server must implement:
    - Action registration and execution
    - Payload validation
    - Event emission to EventBus
    - RetryQueue integration for failed operations
    """

    def __init__(self, name: str, logger: logging.Logger, event_bus=None, retry_queue=None):
        """
        Initialize MCP server.

        Args:
            name: Server name/identifier
            logger: Logger instance
            event_bus: EventBus instance for event emission (optional)
            retry_queue: RetryQueue instance for retry logic (optional)
        """
        self.name = name
        self.logger = logger
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.actions: Dict[str, Callable] = {}
        self.action_metadata: Dict[str, Dict] = {}

        # Initialize server-specific actions
        self._register_actions()

        self.logger.info(f"MCP Server '{self.name}' initialized with {len(self.actions)} actions")

    @abstractmethod
    def _register_actions(self):
        """Register all actions supported by this server. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _validate_payload_schema(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate payload schema for specific action.

        Args:
            action_name: Name of the action
            payload: Payload to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    def register_action(self, name: str, handler: Callable, metadata: Dict = None):
        """
        Register an action handler.

        Args:
            name: Action name
            handler: Callable that handles the action
            metadata: Optional metadata about the action (description, required_fields, etc.)
        """
        if name in self.actions:
            self.logger.warning(f"Action '{name}' already registered, overwriting")

        self.actions[name] = handler
        self.action_metadata[name] = metadata or {}
        self.logger.debug(f"Registered action: {name}")

        # Emit registration event
        self._emit_event('mcp.action.registered', {
            'server': self.name,
            'action': name,
            'metadata': metadata
        })

    def validate_payload(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate payload for an action.

        Args:
            action_name: Name of the action
            payload: Payload to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if action exists
        if action_name not in self.actions:
            return False, f"Action '{action_name}' not found in server '{self.name}'"

        # Check if payload is a dict
        if not isinstance(payload, dict):
            return False, "Payload must be a dictionary"

        # Delegate to server-specific validation
        return self._validate_payload_schema(action_name, payload)

    def execute_action(self, action_name: str, payload: Dict[str, Any], retry_on_failure: bool = True) -> MCPActionResult:
        """
        Execute an action with validation and error handling.

        Args:
            action_name: Name of the action to execute
            payload: Action payload
            retry_on_failure: Whether to enqueue for retry on failure

        Returns:
            MCPActionResult object
        """
        execution_id = f"{self.name}.{action_name}.{datetime.utcnow().timestamp()}"

        self.logger.info(f"Executing action: {action_name} (ID: {execution_id})")

        # Emit execution start event
        self._emit_event('mcp.action.started', {
            'server': self.name,
            'action': action_name,
            'execution_id': execution_id,
            'payload': payload
        })

        # Validate payload
        is_valid, error_msg = self.validate_payload(action_name, payload)
        if not is_valid:
            self.logger.error(f"Payload validation failed: {error_msg}")
            result = MCPActionResult(
                success=False,
                error=f"Validation error: {error_msg}",
                metadata={'execution_id': execution_id}
            )
            self._emit_event('mcp.action.failed', {
                'server': self.name,
                'action': action_name,
                'execution_id': execution_id,
                'error': error_msg,
                'reason': 'validation_failed'
            })
            return result

        # Execute action
        try:
            handler = self.actions[action_name]
            result_data = handler(payload)

            result = MCPActionResult(
                success=True,
                data=result_data,
                metadata={'execution_id': execution_id}
            )

            self.logger.info(f"Action '{action_name}' completed successfully")

            # Emit success event
            self._emit_event('mcp.action.completed', {
                'server': self.name,
                'action': action_name,
                'execution_id': execution_id,
                'result': result.to_dict()
            })

            return result

        except Exception as e:
            self.logger.error(f"Action '{action_name}' failed: {e}", exc_info=True)

            result = MCPActionResult(
                success=False,
                error=str(e),
                metadata={'execution_id': execution_id}
            )

            # Emit failure event
            self._emit_event('mcp.action.failed', {
                'server': self.name,
                'action': action_name,
                'execution_id': execution_id,
                'error': str(e),
                'reason': 'execution_error'
            })

            # Enqueue for retry if enabled
            if retry_on_failure and self.retry_queue:
                self._enqueue_retry(action_name, payload, execution_id)

            return result

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to EventBus if available."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, data)
            except Exception as e:
                self.logger.error(f"Failed to emit event '{event_type}': {e}")

    def _enqueue_retry(self, action_name: str, payload: Dict[str, Any], execution_id: str):
        """Enqueue failed action for retry."""
        if not self.retry_queue:
            return

        try:
            from index import RetryPolicy  # Import from main module

            self.retry_queue.enqueue(
                operation=lambda: self.execute_action(action_name, payload, retry_on_failure=False),
                args=(),
                kwargs={},
                policy=RetryPolicy.EXPONENTIAL,
                context={
                    'name': f"{self.name}.{action_name}",
                    'execution_id': execution_id,
                    'server': self.name,
                    'action': action_name
                }
            )
            self.logger.info(f"Enqueued action '{action_name}' for retry")
        except Exception as e:
            self.logger.error(f"Failed to enqueue retry: {e}")

    def list_actions(self) -> List[Dict[str, Any]]:
        """List all registered actions with metadata."""
        return [
            {
                'name': name,
                'metadata': self.action_metadata.get(name, {})
            }
            for name in self.actions.keys()
        ]

    def get_action_info(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific action."""
        if action_name not in self.actions:
            return None

        return {
            'name': action_name,
            'metadata': self.action_metadata.get(action_name, {}),
            'registered': True
        }


class SocialMCPServer(BaseMCPServer):
    """MCP Server for social media integrations (LinkedIn, WhatsApp, etc.)"""

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None):
        super().__init__('social', logger, event_bus, retry_queue)

    def _register_actions(self):
        """Register social media actions."""
        self.register_action(
            'post_linkedin',
            self._handle_post_linkedin,
            metadata={
                'description': 'Post content to LinkedIn',
                'required_fields': ['content'],
                'optional_fields': ['media_url', 'visibility']
            }
        )

        self.register_action(
            'send_whatsapp',
            self._handle_send_whatsapp,
            metadata={
                'description': 'Send WhatsApp message',
                'required_fields': ['recipient', 'message'],
                'optional_fields': ['media_url']
            }
        )

        self.register_action(
            'schedule_post',
            self._handle_schedule_post,
            metadata={
                'description': 'Schedule a social media post',
                'required_fields': ['platform', 'content', 'scheduled_time'],
                'optional_fields': ['media_url']
            }
        )

    def _validate_payload_schema(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate payload schema for social actions."""
        metadata = self.action_metadata.get(action_name, {})
        required_fields = metadata.get('required_fields', [])

        # Check required fields
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Action-specific validation
        if action_name == 'post_linkedin':
            if not payload.get('content'):
                return False, "Content cannot be empty"
            if len(payload['content']) > 3000:
                return False, "Content exceeds LinkedIn character limit (3000)"

        elif action_name == 'send_whatsapp':
            if not payload.get('recipient'):
                return False, "Recipient cannot be empty"
            if not payload.get('message'):
                return False, "Message cannot be empty"

        elif action_name == 'schedule_post':
            if payload.get('platform') not in ['linkedin', 'twitter', 'facebook']:
                return False, "Invalid platform"
            # Validate scheduled_time format
            try:
                datetime.fromisoformat(payload['scheduled_time'])
            except (ValueError, TypeError):
                return False, "Invalid scheduled_time format (use ISO format)"

        return True, None

    def _handle_post_linkedin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LinkedIn post action."""
        self.logger.info(f"Posting to LinkedIn: {payload.get('content', '')[:50]}...")

        # Placeholder implementation
        return {
            'platform': 'linkedin',
            'post_id': f"linkedin_{datetime.utcnow().timestamp()}",
            'status': 'posted',
            'url': 'https://linkedin.com/posts/...'
        }

    def _handle_send_whatsapp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WhatsApp message action."""
        self.logger.info(f"Sending WhatsApp to {payload.get('recipient')}")

        # Placeholder implementation
        return {
            'platform': 'whatsapp',
            'message_id': f"whatsapp_{datetime.utcnow().timestamp()}",
            'recipient': payload['recipient'],
            'status': 'sent'
        }

    def _handle_schedule_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle schedule post action."""
        self.logger.info(f"Scheduling post for {payload.get('platform')} at {payload.get('scheduled_time')}")

        # Placeholder implementation
        return {
            'platform': payload['platform'],
            'schedule_id': f"schedule_{datetime.utcnow().timestamp()}",
            'scheduled_time': payload['scheduled_time'],
            'status': 'scheduled'
        }


class AccountingMCPServer(BaseMCPServer):
    """MCP Server for accounting and financial operations."""

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None):
        super().__init__('accounting', logger, event_bus, retry_queue)

    def _register_actions(self):
        """Register accounting actions."""
        self.register_action(
            'create_invoice',
            self._handle_create_invoice,
            metadata={
                'description': 'Create a new invoice',
                'required_fields': ['client_name', 'amount', 'items'],
                'optional_fields': ['due_date', 'notes', 'tax_rate']
            }
        )

        self.register_action(
            'record_expense',
            self._handle_record_expense,
            metadata={
                'description': 'Record a business expense',
                'required_fields': ['amount', 'category', 'date'],
                'optional_fields': ['description', 'receipt_url', 'vendor']
            }
        )

        self.register_action(
            'generate_report',
            self._handle_generate_report,
            metadata={
                'description': 'Generate financial report',
                'required_fields': ['report_type', 'start_date', 'end_date'],
                'optional_fields': ['format', 'filters']
            }
        )

    def _validate_payload_schema(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate payload schema for accounting actions."""
        metadata = self.action_metadata.get(action_name, {})
        required_fields = metadata.get('required_fields', [])

        # Check required fields
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Action-specific validation
        if action_name == 'create_invoice':
            if not isinstance(payload.get('amount'), (int, float)) or payload['amount'] <= 0:
                return False, "Amount must be a positive number"
            if not isinstance(payload.get('items'), list) or len(payload['items']) == 0:
                return False, "Items must be a non-empty list"

        elif action_name == 'record_expense':
            if not isinstance(payload.get('amount'), (int, float)) or payload['amount'] <= 0:
                return False, "Amount must be a positive number"
            if payload.get('category') not in ['travel', 'supplies', 'software', 'marketing', 'other']:
                return False, "Invalid expense category"

        elif action_name == 'generate_report':
            if payload.get('report_type') not in ['income', 'expense', 'profit_loss', 'balance_sheet']:
                return False, "Invalid report type"
            # Validate date formats
            try:
                datetime.fromisoformat(payload['start_date'])
                datetime.fromisoformat(payload['end_date'])
            except (ValueError, TypeError):
                return False, "Invalid date format (use ISO format)"

        return True, None

    def _handle_create_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create invoice action."""
        self.logger.info(f"Creating invoice for {payload.get('client_name')}: ${payload.get('amount')}")

        # Placeholder implementation
        return {
            'invoice_id': f"INV-{datetime.utcnow().strftime('%Y%m%d')}-001",
            'client_name': payload['client_name'],
            'amount': payload['amount'],
            'status': 'draft',
            'created_at': datetime.utcnow().isoformat()
        }

    def _handle_record_expense(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle record expense action."""
        self.logger.info(f"Recording expense: {payload.get('category')} - ${payload.get('amount')}")

        # Placeholder implementation
        return {
            'expense_id': f"EXP-{datetime.utcnow().strftime('%Y%m%d')}-001",
            'amount': payload['amount'],
            'category': payload['category'],
            'status': 'recorded',
            'recorded_at': datetime.utcnow().isoformat()
        }

    def _handle_generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generate report action."""
        self.logger.info(f"Generating {payload.get('report_type')} report")

        # Placeholder implementation
        return {
            'report_id': f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-001",
            'report_type': payload['report_type'],
            'start_date': payload['start_date'],
            'end_date': payload['end_date'],
            'status': 'generated',
            'url': '/reports/...'
        }


class NotificationMCPServer(BaseMCPServer):
    """MCP Server for multi-channel notifications."""

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None):
        super().__init__('notification', logger, event_bus, retry_queue)

    def _register_actions(self):
        """Register notification actions."""
        self.register_action(
            'send_email',
            self._handle_send_email,
            metadata={
                'description': 'Send email notification',
                'required_fields': ['recipient', 'subject', 'body'],
                'optional_fields': ['cc', 'bcc', 'attachments']
            }
        )

        self.register_action(
            'send_sms',
            self._handle_send_sms,
            metadata={
                'description': 'Send SMS notification',
                'required_fields': ['phone_number', 'message'],
                'optional_fields': []
            }
        )

        self.register_action(
            'send_push',
            self._handle_send_push,
            metadata={
                'description': 'Send push notification',
                'required_fields': ['user_id', 'title', 'message'],
                'optional_fields': ['action_url', 'icon']
            }
        )

        self.register_action(
            'broadcast',
            self._handle_broadcast,
            metadata={
                'description': 'Broadcast notification across multiple channels',
                'required_fields': ['channels', 'message'],
                'optional_fields': ['priority', 'metadata']
            }
        )

    def _validate_payload_schema(self, action_name: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate payload schema for notification actions."""
        metadata = self.action_metadata.get(action_name, {})
        required_fields = metadata.get('required_fields', [])

        # Check required fields
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Action-specific validation
        if action_name == 'send_email':
            if '@' not in payload.get('recipient', ''):
                return False, "Invalid email address"
            if not payload.get('subject'):
                return False, "Subject cannot be empty"

        elif action_name == 'send_sms':
            phone = payload.get('phone_number', '')
            if not phone or len(phone) < 10:
                return False, "Invalid phone number"
            if len(payload.get('message', '')) > 160:
                return False, "SMS message exceeds 160 characters"

        elif action_name == 'send_push':
            if not payload.get('user_id'):
                return False, "User ID cannot be empty"

        elif action_name == 'broadcast':
            channels = payload.get('channels', [])
            if not isinstance(channels, list) or len(channels) == 0:
                return False, "Channels must be a non-empty list"
            valid_channels = ['email', 'sms', 'push', 'slack']
            if not all(ch in valid_channels for ch in channels):
                return False, f"Invalid channel. Valid channels: {valid_channels}"

        return True, None

    def _handle_send_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send email action."""
        self.logger.info(f"Sending email to {payload.get('recipient')}: {payload.get('subject')}")

        # Placeholder implementation
        return {
            'message_id': f"email_{datetime.utcnow().timestamp()}",
            'recipient': payload['recipient'],
            'subject': payload['subject'],
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        }

    def _handle_send_sms(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send SMS action."""
        self.logger.info(f"Sending SMS to {payload.get('phone_number')}")

        # Placeholder implementation
        return {
            'message_id': f"sms_{datetime.utcnow().timestamp()}",
            'phone_number': payload['phone_number'],
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        }

    def _handle_send_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send push notification action."""
        self.logger.info(f"Sending push notification to user {payload.get('user_id')}")

        # Placeholder implementation
        return {
            'notification_id': f"push_{datetime.utcnow().timestamp()}",
            'user_id': payload['user_id'],
            'title': payload['title'],
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        }

    def _handle_broadcast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle broadcast notification action."""
        channels = payload.get('channels', [])
        self.logger.info(f"Broadcasting to channels: {', '.join(channels)}")

        # Placeholder implementation
        return {
            'broadcast_id': f"broadcast_{datetime.utcnow().timestamp()}",
            'channels': channels,
            'message': payload['message'],
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat(),
            'results': {ch: 'success' for ch in channels}
        }


# Factory function for easy server creation
def create_mcp_server(server_type: str, logger: logging.Logger, event_bus=None, retry_queue=None) -> BaseMCPServer:
    """
    Factory function to create MCP servers.

    Args:
        server_type: Type of server ('social', 'accounting', 'notification')
        logger: Logger instance
        event_bus: EventBus instance (optional)
        retry_queue: RetryQueue instance (optional)

    Returns:
        MCP server instance

    Raises:
        ValueError: If server_type is invalid
    """
    servers = {
        'social': SocialMCPServer,
        'accounting': AccountingMCPServer,
        'notification': NotificationMCPServer
    }

    if server_type not in servers:
        raise ValueError(f"Invalid server type: {server_type}. Valid types: {list(servers.keys())}")

    return servers[server_type](logger, event_bus, retry_queue)

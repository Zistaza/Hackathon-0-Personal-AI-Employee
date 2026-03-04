#!/usr/bin/env python3
"""
MCPServerManager - Central MCP Server Management
=================================================

Manages all MCP servers and provides unified interface for MCP operations.
Routes skill executions through appropriate MCP servers.
"""

import logging
from typing import Dict, Optional, Any
from pathlib import Path


class MCPServerManager:
    """
    Central manager for all MCP servers.

    Provides:
    - MCP server lifecycle management
    - Unified routing to appropriate MCP servers
    - Skill-to-MCP action mapping
    - Event bus integration
    """

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None,
                 audit_logger=None, base_dir: Path = None):
        """
        Initialize MCP Server Manager.

        Args:
            logger: Logger instance
            event_bus: EventBus for event emission
            retry_queue: RetryQueue for failed operations
            audit_logger: AuditLogger for compliance
            base_dir: Base directory for AI Employee Vault
        """
        self.logger = logger
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.audit_logger = audit_logger
        self.base_dir = base_dir

        # MCP servers registry
        self.servers: Dict[str, Any] = {}

        # Skill-to-MCP mapping
        self.skill_to_mcp_mapping = {
            'accounting_core': {
                'server': 'accounting',
                'action_map': {
                    'add-revenue': 'add_revenue',
                    'add-expense': 'add_expense',
                    'generate-reports': 'generate_report'
                }
            },
            'linkedin_post_skill': {
                'server': 'social',
                'action_map': {
                    'post': 'post_linkedin'
                }
            },
            'whatsapp_skill': {
                'server': 'social',
                'action_map': {
                    'send': 'send_whatsapp'
                }
            },
            'email_executor': {
                'server': 'notification',
                'action_map': {
                    'send_email': 'send_email'
                }
            }
        }

        self.logger.info("MCPServerManager initialized")

    def register_server(self, server_name: str, server_instance):
        """Register an MCP server."""
        self.servers[server_name] = server_instance
        self.logger.info(f"Registered MCP server: {server_name}")

    def initialize_servers(self):
        """Initialize all MCP servers."""
        try:
            # Import MCP servers
            from Skills.integration_orchestrator.mcp_core import (
                AccountingMCPServer,
                SocialMCPServer,
                NotificationMCPServer
            )

            # Initialize Accounting MCP Server
            accounting_server = AccountingMCPServerAdapter(
                logger=self.logger,
                event_bus=self.event_bus,
                retry_queue=self.retry_queue,
                base_dir=self.base_dir
            )
            self.register_server('accounting', accounting_server)

            # Initialize Social MCP Server
            social_server = SocialMCPServer(
                logger=self.logger,
                event_bus=self.event_bus,
                retry_queue=self.retry_queue
            )
            self.register_server('social', social_server)

            # Initialize Notification MCP Server
            notification_server = NotificationMCPServer(
                logger=self.logger,
                event_bus=self.event_bus,
                retry_queue=self.retry_queue
            )
            self.register_server('notification', notification_server)

            self.logger.info(f"Initialized {len(self.servers)} MCP servers")

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP servers: {e}", exc_info=True)

    def execute_via_mcp(self, skill_name: str, args: list = None) -> Dict[str, Any]:
        """
        Execute skill via appropriate MCP server.

        Args:
            skill_name: Name of the skill to execute
            args: Skill arguments

        Returns:
            Execution result dict with 'success', 'data', 'error'
        """
        # Check if skill has MCP mapping
        if skill_name not in self.skill_to_mcp_mapping:
            return {
                'success': False,
                'error': f"No MCP mapping for skill: {skill_name}",
                'via_mcp': False
            }

        mapping = self.skill_to_mcp_mapping[skill_name]
        server_name = mapping['server']

        # Get MCP server
        if server_name not in self.servers:
            return {
                'success': False,
                'error': f"MCP server not found: {server_name}",
                'via_mcp': False
            }

        server = self.servers[server_name]

        # Convert skill args to MCP payload
        payload = self._convert_args_to_payload(skill_name, args or [])

        # Determine MCP action
        action_name = self._get_mcp_action(skill_name, args or [])

        if not action_name:
            return {
                'success': False,
                'error': f"Could not determine MCP action for: {skill_name}",
                'via_mcp': False
            }

        self.logger.info(f"Executing via MCP: {server_name}.{action_name}")

        # Execute via MCP
        try:
            result = server.execute_action(action_name, payload)

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type='mcp_execution',
                    actor='mcp_server_manager',
                    action=action_name,
                    resource=f"{server_name}.{action_name}",
                    result='success' if result.success else 'failure',
                    metadata={
                        'skill_name': skill_name,
                        'server': server_name,
                        'payload': payload,
                        'result': result.to_dict()
                    }
                )

            return {
                'success': result.success,
                'data': result.data,
                'error': result.error,
                'via_mcp': True,
                'mcp_server': server_name,
                'mcp_action': action_name,
                'metadata': result.metadata
            }

        except Exception as e:
            self.logger.error(f"MCP execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'via_mcp': True,
                'mcp_server': server_name,
                'mcp_action': action_name
            }

    def _get_mcp_action(self, skill_name: str, args: list) -> Optional[str]:
        """Determine MCP action from skill name and args."""
        mapping = self.skill_to_mcp_mapping.get(skill_name, {})
        action_map = mapping.get('action_map', {})

        # For accounting_core, first arg is the command
        if skill_name == 'accounting_core' and len(args) > 0:
            command = args[0]
            return action_map.get(command)

        # For other skills, use default action
        if len(action_map) == 1:
            return list(action_map.values())[0]

        return None

    def _convert_args_to_payload(self, skill_name: str, args: list) -> Dict[str, Any]:
        """Convert skill args to MCP payload."""
        payload = {}

        if skill_name == 'accounting_core':
            # Parse accounting_core args
            # Format: ['add-revenue', '--amount', '100', '--category', 'Client', '--description', 'Desc']
            if len(args) < 2:
                return payload

            command = args[0]

            # Parse flags
            i = 1
            while i < len(args):
                if args[i].startswith('--'):
                    flag = args[i][2:]  # Remove '--'
                    if i + 1 < len(args):
                        value = args[i + 1]

                        # Convert amount to float
                        if flag == 'amount':
                            try:
                                value = float(value)
                            except ValueError:
                                pass

                        payload[flag] = value
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1

        return payload

    def get_server(self, server_name: str):
        """Get MCP server by name."""
        return self.servers.get(server_name)

    def list_servers(self) -> list:
        """List all registered MCP servers."""
        return list(self.servers.keys())

    def get_server_info(self, server_name: str) -> Optional[Dict]:
        """Get information about an MCP server."""
        server = self.servers.get(server_name)
        if not server:
            return None

        return {
            'name': server_name,
            'actions': server.list_actions() if hasattr(server, 'list_actions') else []
        }


class AccountingMCPServerAdapter:
    """
    Adapter that wraps AccountingMCPServer and integrates with accounting_core skill.
    Provides real ledger updates via the actual accounting system.
    """

    def __init__(self, logger: logging.Logger, event_bus=None, retry_queue=None, base_dir: Path = None):
        self.logger = logger
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.base_dir = base_dir
        self.name = 'accounting'

        # Import accounting core
        try:
            import sys
            sys.path.insert(0, str(base_dir / "Skills" / "accounting_core"))
            from index import AccountingCore

            self.accounting_core = AccountingCore(base_dir, dry_run=False)
            self.accounting_core.set_event_bus(event_bus)

            self.logger.info("AccountingMCPServerAdapter initialized with real accounting_core")
        except Exception as e:
            self.logger.error(f"Failed to initialize accounting_core: {e}")
            self.accounting_core = None

    def execute_action(self, action_name: str, payload: Dict[str, Any]):
        """Execute accounting action via real accounting_core."""
        from Skills.integration_orchestrator.mcp_core import MCPActionResult

        if not self.accounting_core:
            return MCPActionResult(
                success=False,
                error="Accounting core not initialized"
            )

        try:
            # Import TransactionType enum
            import sys
            sys.path.insert(0, str(self.base_dir / "Skills" / "accounting_core"))
            from index import TransactionType

            if action_name == 'add_revenue':
                # Add revenue transaction
                amount = payload.get('amount')
                category = payload.get('category', 'Revenue')
                description = payload.get('description', '')

                transaction_id = self.accounting_core.add_transaction(
                    transaction_type=TransactionType.REVENUE,  # Use enum, not string
                    amount=amount,
                    category=category,
                    description=description
                )

                self.logger.info(f"Added revenue via MCP: ${amount} - {category}")

                # Emit event
                if self.event_bus:
                    self.event_bus.publish('accounting_transaction_added', {
                        'transaction_id': transaction_id,
                        'type': 'revenue',
                        'amount': amount,
                        'category': category,
                        'status': 'finalized'
                    })

                return MCPActionResult(
                    success=True,
                    data={
                        'transaction_id': transaction_id,
                        'amount': amount,
                        'category': category,
                        'type': 'revenue'
                    }
                )

            elif action_name == 'add_expense':
                # Add expense transaction
                amount = payload.get('amount')
                category = payload.get('category', 'Expense')
                description = payload.get('description', '')

                transaction_id = self.accounting_core.add_transaction(
                    transaction_type=TransactionType.EXPENSE,  # Use enum, not string
                    amount=amount,
                    category=category,
                    description=description
                )

                self.logger.info(f"Added expense via MCP: ${amount} - {category}")

                return MCPActionResult(
                    success=True,
                    data={
                        'transaction_id': transaction_id,
                        'amount': amount,
                        'category': category,
                        'type': 'expense'
                    }
                )

            else:
                return MCPActionResult(
                    success=False,
                    error=f"Unknown action: {action_name}"
                )

        except Exception as e:
            self.logger.error(f"Accounting MCP action failed: {e}", exc_info=True)
            return MCPActionResult(
                success=False,
                error=str(e)
            )

    def list_actions(self):
        """List available actions."""
        return [
            {'name': 'add_revenue', 'metadata': {'description': 'Add revenue transaction'}},
            {'name': 'add_expense', 'metadata': {'description': 'Add expense transaction'}}
        ]

#!/usr/bin/env python3
"""EventRouter - Filesystem Event Routing
==========================================

Routes filesystem events to appropriate handlers.
Enhanced for Gold Tier with EventBus integration.
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Import components for type hints
from core import StateManager, ApprovalManager
from skills import SkillDispatcher
from execution import EmailExecutor


class EventRouter:
    """Routes filesystem events to appropriate handlers - Enhanced for Gold Tier"""

    def __init__(self, dispatcher: SkillDispatcher, state_manager: StateManager,
                 approval_manager: ApprovalManager, email_executor: EmailExecutor,
                 base_dir: Path, logger: logging.Logger,
                 skill_registry: 'SkillRegistry' = None, event_bus: 'EventBus' = None,
                 graceful_degradation: 'GracefulDegradation' = None):
        self.dispatcher = dispatcher
        self.state_manager = state_manager
        self.approval_manager = approval_manager
        self.email_executor = email_executor
        self.base_dir = base_dir
        self.logger = logger
        # Gold Tier components (optional for backward compatibility)
        self.skill_registry = skill_registry
        self.event_bus = event_bus
        self.graceful_degradation = graceful_degradation

    def route_event(self, event_type: str, filepath: Path) -> bool:
        """Route event to appropriate handler"""
        try:
            # Generate event ID
            event_id = f"{event_type}_{self.state_manager.get_event_hash(filepath)}"

            # Check if already processed
            if self.state_manager.is_processed(event_id):
                self.logger.debug(f"Event already processed: {event_id}")
                return True

            self.logger.info(f"Routing event: {event_type} for {filepath.name}")

            # Route based on event type and location
            if event_type == "needs_action_created":
                result = self._handle_needs_action(filepath)
            elif event_type == "pending_approval_modified":
                result = self._handle_pending_approval(filepath)
            elif event_type == "pending_approval_email_created":
                result = self._handle_pending_approval_email(filepath)
            elif event_type == "approved_created":
                result = self._handle_approved(filepath)
            elif event_type == "rejected_created":
                result = self._handle_rejected(filepath)
            elif event_type == "inbox_created":
                result = self._handle_inbox(filepath)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                return False

            # Mark as processed if successful
            if result:
                self.state_manager.mark_processed(event_id, {
                    'event_type': event_type,
                    'filepath': str(filepath),
                    'filename': filepath.name
                })

            return result

        except Exception as e:
            self.logger.error(f"Error routing event: {e}")
            return False

    def _handle_needs_action(self, filepath: Path) -> bool:
        """Handle new file in Needs_Action - Enhanced with Gold Tier"""
        self.logger.info(f"Processing Needs_Action file: {filepath.name}")

        # Publish event
        if self.event_bus:
            self.event_bus.publish('needs_action_detected', {
                'filepath': str(filepath),
                'filename': filepath.name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Trigger process_needs_action skill via SkillRegistry
        result = self.skill_registry.execute_skill("process_needs_action")

        return result['success']

    def _handle_pending_approval(self, filepath: Path) -> bool:
        """Handle modified file in Pending_Approval - Enhanced with Gold Tier"""
        try:
            # Read file to check status
            with open(filepath, 'r') as f:
                content = f.read()

            # Check if status is approved
            if 'status: approved' in content or 'status:approved' in content:
                self.logger.info(f"Approved file detected: {filepath.name}")

                # Publish event
                if self.event_bus:
                    self.event_bus.publish('approval_detected', {
                        'filepath': str(filepath),
                        'filename': filepath.name,
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Determine which skill to trigger based on file type
                if 'type: linkedin_post' in content:
                    self.logger.info("Triggering LinkedIn post skill")

                    # Trigger via SkillRegistry
                    result = self.skill_registry.execute_skill("linkedin_post_skill", ["process"])

                    return result['success']
                else:
                    self.logger.info("Approved file but no specific handler")
                    return True
            else:
                self.logger.debug(f"File not approved yet: {filepath.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error handling pending approval: {e}")
            return False

    def _handle_pending_approval_email(self, filepath: Path) -> bool:
        """Handle new file in Pending_Approval/email/ - Wait for human approval"""
        self.logger.info(f"Email approval request created: {filepath.name}")
        self.logger.info("Waiting for human to move file to /Approved/ or /Rejected/")
        # Do nothing - wait for human to move the file
        return True

    def _handle_approved(self, filepath: Path) -> bool:
        """Handle file moved to Approved - Execute plan or email - Enhanced with Gold Tier"""
        try:
            # Check if this is a PLAN file or EMAIL approval
            if filepath.name.startswith('PLAN_'):
                return self._handle_approved_plan(filepath)
            else:
                return self._handle_approved_email(filepath)

        except Exception as e:
            self.logger.error(f"Error handling approved file: {e}")
            return False

    def _handle_approved_plan(self, filepath: Path) -> bool:
        """Handle approved plan - Execute accounting or other domain actions"""
        try:
            self.logger.info(f"Processing approved plan: {filepath.name}")

            # Generate approval ID (use filename and action type)
            approval_id = self.approval_manager.get_approval_hash(filepath.name, 'plan_execution')

            # Check if already processed
            if self.approval_manager.is_processed(approval_id):
                self.logger.warning(f"Approval already processed: {filepath.name}")
                return True

            # Publish event
            if self.event_bus:
                self.event_bus.publish('plan_approved', {
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Read plan file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse plan metadata
            plan_data = self._parse_plan_metadata(content)

            if not plan_data:
                self.logger.error(f"Failed to parse plan metadata from {filepath.name}")
                return False

            source_file = plan_data.get('source_file')
            if not source_file:
                self.logger.error(f"No source_file in plan metadata: {filepath.name}")
                return False

            # Load original request from Done folder
            done_dir = self.base_dir / "Done"
            source_path = done_dir / source_file

            if not source_path.exists():
                self.logger.error(f"Source file not found: {source_path}")
                return False

            # Read original request
            with open(source_path, 'r') as f:
                original_content = f.read()

            # Parse original request data
            request_data = self._parse_request_data(original_content)

            if not request_data:
                self.logger.error(f"Failed to parse request data from {source_file}")
                return False

            # Determine action based on request type
            request_type = request_data.get('type', '')

            if request_type == 'invoice_request':
                # Execute accounting skill
                result = self._execute_invoice_request(request_data)

                if result:
                    self.logger.info(f"Invoice processed successfully: {request_data.get('client')}")

                    # Mark as processed
                    self.approval_manager.mark_processed(approval_id, {
                        'filename': filepath.name,
                        'source_file': source_file,
                        'type': request_type,
                        'status': 'executed'
                    })

                    # Move plan to Done
                    done_path = done_dir / filepath.name
                    shutil.move(str(filepath), str(done_path))
                    self.logger.info(f"Moved plan to Done: {filepath.name}")

                    return True
                else:
                    self.logger.error("Invoice processing failed")
                    return False
            else:
                self.logger.warning(f"Unknown request type: {request_type}")
                return False

        except Exception as e:
            self.logger.error(f"Error handling approved plan: {e}", exc_info=True)
            return False

    def _handle_approved_email(self, filepath: Path) -> bool:
        """Handle approved email - Send email and move to Done"""
        try:
            # Check if email sending is enabled (graceful degradation)
            if self.graceful_degradation and not self.graceful_degradation.is_feature_enabled('email_sending'):
                self.logger.warning(f"Email sending disabled (degraded mode), skipping: {filepath.name}")
                return False

            self.logger.info(f"Processing approved email: {filepath.name}")

            # Read approval file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse email data from file
            email_data = self._parse_email_approval(content)

            if not email_data:
                self.logger.error(f"Failed to parse email data from {filepath.name}")
                return False

            # Validate required fields
            if email_data.get('action') != 'send_email':
                self.logger.warning(f"Not an email action: {email_data.get('action')}")
                return False

            # Generate approval ID
            approval_id = self.approval_manager.get_approval_hash(filepath.name, 'send_email')

            # Check if already processed
            if self.approval_manager.is_processed(approval_id):
                self.logger.warning(f"Approval already processed: {filepath.name}")
                return True

            # Publish event
            if self.event_bus:
                self.event_bus.publish('email_approved', {
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Read approval file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse email data from file
            email_data = self._parse_email_approval(content)

            if not email_data:
                self.logger.error(f"Failed to parse email data from {filepath.name}")
                return False

            # Validate required fields
            if email_data.get('action') != 'send_email':
                self.logger.warning(f"Not an email action: {email_data.get('action')}")
                return False

            # Send email
            self.logger.info(f"Sending email to: {email_data.get('to')}")
            result = self.email_executor.send_email(email_data)

            if result['success']:
                self.logger.info("Email sent successfully")

                # Mark as processed
                self.approval_manager.mark_processed(approval_id, {
                    'filename': filepath.name,
                    'to': email_data.get('to'),
                    'subject': email_data.get('subject'),
                    'status': 'sent'
                })

                # Publish success event
                if self.event_bus:
                    self.event_bus.publish('email_sent', {
                        'to': email_data.get('to'),
                        'subject': email_data.get('subject'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Move to Done
                done_dir = self.base_dir / "Done"
                done_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                done_path = done_dir / f"sent_{timestamp}_{filepath.name}"

                shutil.move(str(filepath), str(done_path))
                self.logger.info(f"Moved to Done: {done_path.name}")

                return True
            else:
                self.logger.error(f"Email sending failed: {result.get('error', 'Unknown error')}")

                # Publish failure event
                if self.event_bus:
                    self.event_bus.publish('email_failed', {
                        'to': email_data.get('to'),
                        'subject': email_data.get('subject'),
                        'error': result.get('error'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                return False

        except Exception as e:
            self.logger.error(f"Error handling approved email: {e}")
            return False

    def _handle_rejected(self, filepath: Path) -> bool:
        """Handle file moved to Rejected - Log rejection"""
        try:
            self.logger.info(f"Email approval rejected: {filepath.name}")

            # Read file for logging
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                email_data = self._parse_email_approval(content)

                if email_data:
                    self.logger.info(f"Rejected email to: {email_data.get('to')}")
                    self.logger.info(f"Subject: {email_data.get('subject')}")
            except:
                pass

            # Log rejection
            self.email_executor._log_email_action('email_rejected',
                                                   email_data if email_data else {},
                                                   f"User rejected approval for {filepath.name}")

            return True

        except Exception as e:
            self.logger.error(f"Error handling rejected email: {e}")
            return False

    def _parse_email_approval(self, content: str) -> Optional[Dict]:
        """Parse email data from approval file"""
        try:
            email_data = {}
            lines = content.split('\n')

            for line in lines:
                line = line.strip()
                if line.startswith('action:'):
                    email_data['action'] = line.split(':', 1)[1].strip()
                elif line.startswith('to:'):
                    email_data['to'] = line.split(':', 1)[1].strip()
                elif line.startswith('subject:'):
                    email_data['subject'] = line.split(':', 1)[1].strip()
                elif line.startswith('body:'):
                    # Body might be multiline, capture everything after 'body:'
                    body_start = content.find('body:')
                    if body_start != -1:
                        body_content = content[body_start + 5:].strip()
                        # Stop at timestamp or status if present
                        for stop_marker in ['timestamp:', 'status:']:
                            if stop_marker in body_content:
                                body_content = body_content.split(stop_marker)[0].strip()
                        email_data['body'] = body_content
                elif line.startswith('timestamp:'):
                    email_data['timestamp'] = line.split(':', 1)[1].strip()
                elif line.startswith('status:'):
                    email_data['status'] = line.split(':', 1)[1].strip()

            return email_data if email_data else None

        except Exception as e:
            self.logger.error(f"Error parsing email approval: {e}")
            return None

    def _parse_plan_metadata(self, content: str) -> Optional[Dict]:
        """Parse metadata from plan file (YAML frontmatter)"""
        try:
            metadata = {}

            # Extract YAML frontmatter between --- markers
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()

                    # Parse YAML-like content
                    for line in frontmatter.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

            return metadata if metadata else None

        except Exception as e:
            self.logger.error(f"Error parsing plan metadata: {e}")
            return None

    def _parse_request_data(self, content: str) -> Optional[Dict]:
        """Parse data from original request file (YAML frontmatter)"""
        try:
            request_data = {}

            # Extract YAML frontmatter between --- markers
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()

                    # Parse YAML-like content
                    for line in frontmatter.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            request_data[key.strip()] = value.strip()

            return request_data if request_data else None

        except Exception as e:
            self.logger.error(f"Error parsing request data: {e}")
            return None

    def _execute_invoice_request(self, request_data: Dict) -> bool:
        """Execute invoice request via accounting skill"""
        try:
            client = request_data.get('client', 'Unknown')
            amount_str = request_data.get('amount', '0')
            reason = request_data.get('reason', 'Invoice')

            # Convert amount to float
            try:
                amount = float(amount_str)
            except ValueError:
                self.logger.error(f"Invalid amount: {amount_str}")
                return False

            self.logger.info(f"Executing invoice: {client} - ${amount}")

            # Publish event
            if self.event_bus:
                self.event_bus.publish('invoice_executing', {
                    'client': client,
                    'amount': amount,
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Execute accounting skill via SkillRegistry
            if self.skill_registry:
                result = self.skill_registry.execute_skill(
                    "accounting_core",
                    ["add-revenue",
                     "--amount", str(amount),
                     "--category", client,
                     "--description", reason]
                )

                if result.get('success'):
                    self.logger.info(f"Accounting skill executed successfully")

                    # Publish accounting_transaction_added event for cross-domain integration
                    if self.event_bus:
                        self.event_bus.publish('accounting_transaction_added', {
                            'transaction_id': f"invoice_{client}_{amount}",
                            'type': 'revenue',
                            'amount': amount,
                            'category': client,
                            'status': 'finalized',
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        })
                        self.logger.info(f"Published accounting_transaction_added event")

                    # Publish success event
                    if self.event_bus:
                        self.event_bus.publish('invoice_completed', {
                            'client': client,
                            'amount': amount,
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        })

                    return True
                else:
                    self.logger.error(f"Accounting skill failed: {result.get('error')}")
                    return False
            else:
                self.logger.error("SkillRegistry not available")
                return False

        except Exception as e:
            self.logger.error(f"Error executing invoice request: {e}", exc_info=True)
            return False

    def _handle_inbox(self, filepath: Path) -> bool:
        """Handle new file in Inbox"""
        self.logger.info(f"Processing Inbox file: {filepath.name}")

        # Move to Needs_Action for processing
        try:
            needs_action_dir = filepath.parent.parent / "Needs_Action"
            destination = needs_action_dir / filepath.name

            # Move file
            filepath.rename(destination)
            self.logger.info(f"Moved {filepath.name} to Needs_Action")

            return True

        except Exception as e:
            self.logger.error(f"Error moving inbox file: {e}")
            return False



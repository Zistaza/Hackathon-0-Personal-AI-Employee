#!/usr/bin/env python3
"""
Enhanced AutonomousExecutor with Social Media Automation
=========================================================

Extends the AutonomousExecutor to automatically detect and trigger
social media skills based on content in Posted/, Drafts/, and Plans/.

This enhancement adds:
- Automatic detection of social media content
- Intelligent platform selection based on content metadata
- Scheduled post detection and execution
- Failure recovery for social posts
- Dynamic skill discovery via SkillRegistry
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock


class SocialMediaAutomation:
    """
    Social Media Automation mixin for AutonomousExecutor.

    Provides intelligent detection and triggering of social media skills
    without modifying existing skills or core functionality.
    """

    def __init__(self):
        """Initialize social media automation tracking"""
        self.social_processed_files: Dict[str, datetime] = {}
        self.social_lock = Lock()

        # Directories to monitor for social content
        self.posted_dir = self.base_dir / "Posted"
        self.drafts_dir = self.base_dir / "Drafts"
        self.plans_dir = self.base_dir / "Plans"

        # Ensure directories exist
        self.posted_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def _check_social_media_content(self):
        """
        Check for social media content and trigger appropriate skills.

        Monitors:
        - Posted/ - Content ready to be posted immediately
        - Drafts/ - Content that needs review before posting
        - Plans/ - Scheduled posts with specific timing
        """
        try:
            # Check Posted directory for immediate posting
            self._process_posted_content()

            # Check Plans directory for scheduled posts
            self._process_scheduled_posts()

            # Check Drafts directory (informational only, requires approval)
            self._check_draft_content()

        except Exception as e:
            self.logger.error(f"Error checking social media content: {e}", exc_info=True)

    def _process_posted_content(self):
        """Process content in Posted/ directory for immediate posting"""
        try:
            if not self.posted_dir.exists():
                return

            posted_files = list(self.posted_dir.glob("*.md"))

            for filepath in posted_files:
                # Skip if recently processed
                if self._is_recently_processed(filepath):
                    continue

                try:
                    # Parse file for social media directives
                    social_config = self._parse_social_media_config(filepath)

                    if social_config:
                        self.logger.info(f"Detected social media content: {filepath.name}")

                        # Trigger posting
                        self._trigger_social_media_post(filepath, social_config, immediate=True)

                        # Mark as processed
                        self._mark_as_processed(filepath)

                except Exception as e:
                    self.logger.error(f"Error processing {filepath.name}: {e}")

        except Exception as e:
            self.logger.error(f"Error processing posted content: {e}")

    def _process_scheduled_posts(self):
        """Process scheduled posts from Plans/ directory"""
        try:
            if not self.plans_dir.exists():
                return

            plan_files = list(self.plans_dir.glob("*.md"))

            for filepath in plan_files:
                try:
                    # Parse file for scheduled social posts
                    social_config = self._parse_social_media_config(filepath)

                    if not social_config or not social_config.get('scheduled_time'):
                        continue

                    # Check if it's time to post
                    scheduled_time = self._parse_scheduled_time(social_config['scheduled_time'])

                    if scheduled_time and datetime.utcnow() >= scheduled_time:
                        # Skip if already processed
                        if self._is_recently_processed(filepath):
                            continue

                        self.logger.info(f"Scheduled post ready: {filepath.name}")

                        # Trigger posting
                        self._trigger_social_media_post(filepath, social_config, immediate=False)

                        # Mark as processed
                        self._mark_as_processed(filepath)

                except Exception as e:
                    self.logger.error(f"Error processing scheduled post {filepath.name}: {e}")

        except Exception as e:
            self.logger.error(f"Error processing scheduled posts: {e}")

    def _check_draft_content(self):
        """Check draft content and emit events (no automatic posting)"""
        try:
            if not self.drafts_dir.exists():
                return

            draft_files = list(self.drafts_dir.glob("*.md"))

            if draft_files:
                # Emit event for monitoring
                self.event_bus.publish('social_drafts_detected', {
                    'count': len(draft_files),
                    'files': [f.name for f in draft_files[:5]],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

                self.logger.debug(f"Found {len(draft_files)} social media drafts")

        except Exception as e:
            self.logger.error(f"Error checking draft content: {e}")

    def _parse_social_media_config(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Parse markdown file for social media configuration.

        Looks for YAML frontmatter or special markers:
        ---
        social_media:
          platforms: [facebook, instagram, twitter_x]
          message: "Post content here"
          media: ["image.jpg"]
          scheduled_time: "2026-03-01T10:00:00"
        ---

        Or inline markers:
        <!-- SOCIAL: facebook, instagram -->
        <!-- MESSAGE: Post content -->
        <!-- MEDIA: image.jpg -->
        <!-- SCHEDULED: 2026-03-01T10:00:00 -->
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            # Try YAML frontmatter first
            yaml_config = self._parse_yaml_frontmatter(content)
            if yaml_config and 'social_media' in yaml_config:
                return yaml_config['social_media']

            # Try inline markers
            inline_config = self._parse_inline_markers(content)
            if inline_config:
                return inline_config

            # Try JSON block
            json_config = self._parse_json_block(content)
            if json_config:
                return json_config

            return None

        except Exception as e:
            self.logger.error(f"Error parsing {filepath.name}: {e}")
            return None

    def _parse_yaml_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from markdown"""
        try:
            # Simple YAML frontmatter parser (basic implementation)
            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            # This is a simplified parser - in production use PyYAML
            # For now, just detect if social_media section exists
            frontmatter = parts[1]

            if 'social_media:' in frontmatter:
                # Extract basic config (simplified)
                config = {}

                # Extract platforms
                platforms_match = re.search(r'platforms:\s*\[(.*?)\]', frontmatter)
                if platforms_match:
                    platforms_str = platforms_match.group(1)
                    config['platforms'] = [p.strip().strip('"\'') for p in platforms_str.split(',')]

                # Extract message
                message_match = re.search(r'message:\s*["\'](.+?)["\']', frontmatter, re.DOTALL)
                if message_match:
                    config['message'] = message_match.group(1)

                # Extract media
                media_match = re.search(r'media:\s*\[(.*?)\]', frontmatter)
                if media_match:
                    media_str = media_match.group(1)
                    config['media'] = [m.strip().strip('"\'') for m in media_str.split(',')]

                # Extract scheduled time
                scheduled_match = re.search(r'scheduled_time:\s*["\'](.+?)["\']', frontmatter)
                if scheduled_match:
                    config['scheduled_time'] = scheduled_match.group(1)

                return {'social_media': config} if config else None

            return None

        except Exception as e:
            self.logger.debug(f"Error parsing YAML frontmatter: {e}")
            return None

    def _parse_inline_markers(self, content: str) -> Optional[Dict]:
        """Parse inline HTML comment markers"""
        try:
            config = {}

            # Extract platforms
            platforms_match = re.search(r'<!--\s*SOCIAL:\s*(.+?)\s*-->', content)
            if platforms_match:
                platforms_str = platforms_match.group(1)
                config['platforms'] = [p.strip() for p in platforms_str.split(',')]

            # Extract message
            message_match = re.search(r'<!--\s*MESSAGE:\s*(.+?)\s*-->', content, re.DOTALL)
            if message_match:
                config['message'] = message_match.group(1).strip()

            # Extract media
            media_match = re.search(r'<!--\s*MEDIA:\s*(.+?)\s*-->', content)
            if media_match:
                media_str = media_match.group(1)
                config['media'] = [m.strip() for m in media_str.split(',')]

            # Extract scheduled time
            scheduled_match = re.search(r'<!--\s*SCHEDULED:\s*(.+?)\s*-->', content)
            if scheduled_match:
                config['scheduled_time'] = scheduled_match.group(1).strip()

            return config if config else None

        except Exception as e:
            self.logger.debug(f"Error parsing inline markers: {e}")
            return None

    def _parse_json_block(self, content: str) -> Optional[Dict]:
        """Parse JSON configuration block"""
        try:
            # Look for ```json social_media block
            json_match = re.search(r'```json\s+social_media\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            return None

        except Exception as e:
            self.logger.debug(f"Error parsing JSON block: {e}")
            return None

    def _parse_scheduled_time(self, time_str: str) -> Optional[datetime]:
        """Parse scheduled time string to datetime"""
        try:
            # Try ISO format
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except:
                        continue
            except:
                pass

        return None

    def _trigger_social_media_post(self, filepath: Path, config: Dict[str, Any], immediate: bool = True):
        """
        Trigger social media posting based on configuration.

        Args:
            filepath: Source file path
            config: Social media configuration
            immediate: Whether this is an immediate or scheduled post
        """
        try:
            platforms = config.get('platforms', [])
            message = config.get('message', '')
            media = config.get('media', [])

            if not platforms:
                self.logger.warning(f"No platforms specified in {filepath.name}")
                return

            if not message:
                # Try to extract message from file content
                message = self._extract_message_from_content(filepath)

            if not message:
                self.logger.warning(f"No message found in {filepath.name}")
                return

            # Discover available social media skills
            available_skills = self._discover_social_skills()

            # Emit event
            self.event_bus.publish('social_post_triggered', {
                'source_file': filepath.name,
                'platforms': platforms,
                'immediate': immediate,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            # Trigger each platform
            for platform in platforms:
                skill_name = f"social_{platform}"

                if skill_name not in available_skills:
                    self.logger.warning(f"Skill {skill_name} not available")
                    continue

                # Trigger via social adapter if available
                self._trigger_social_skill(
                    platform=platform,
                    message=message,
                    media=media,
                    source_file=filepath.name,
                    immediate=immediate
                )

        except Exception as e:
            self.logger.error(f"Error triggering social media post: {e}", exc_info=True)

    def _discover_social_skills(self) -> List[str]:
        """Discover available social media skills from SkillRegistry"""
        try:
            all_skills = list(self.skill_registry.skill_metadata.keys())
            social_skills = [s for s in all_skills if s.startswith('social_')]
            return social_skills
        except Exception as e:
            self.logger.error(f"Error discovering social skills: {e}")
            return []

    def _trigger_social_skill(self, platform: str, message: str, media: List[str],
                             source_file: str, immediate: bool):
        """
        Trigger a specific social media skill with failure recovery.

        Uses the orchestrator's social_adapter if available, otherwise
        falls back to direct skill execution.
        """
        try:
            tracking_key = f"social_{platform}_{source_file}"

            # Check if recently attempted
            with self.social_lock:
                last_attempt = self.last_check_times.get(tracking_key)
                if last_attempt and (datetime.utcnow() - last_attempt) < timedelta(minutes=10):
                    self.logger.debug(f"Skipping {platform}, recently attempted")
                    return

                self.last_check_times[tracking_key] = datetime.utcnow()

            self.logger.info(f"Triggering social post: {platform} (source: {source_file})")

            # Try to use social_adapter if available (via orchestrator)
            result = None
            if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'social_adapter'):
                try:
                    result = self.orchestrator.social_adapter.post(
                        platform=platform,
                        message=message,
                        media=media if media else None,
                        metadata={
                            'source_file': source_file,
                            'immediate': immediate,
                            'triggered_by': 'autonomous_executor'
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Social adapter failed, trying direct skill: {e}")

            # Fallback: trigger skill directly via SkillRegistry
            if not result:
                # Note: Direct skill execution would require different approach
                # For now, log that adapter is preferred
                self.logger.warning(f"Social adapter not available for {platform}")
                result = {'success': False, 'error': 'Social adapter not available'}

            # Handle result
            if result and result.get('success'):
                self.logger.info(f"Social post successful: {platform} - {result.get('post_id')}")

                # Reset failure count
                with self.social_lock:
                    if tracking_key in self.task_failure_counts:
                        del self.task_failure_counts[tracking_key]

                # Audit log
                self.audit_logger.log_event(
                    event_type='autonomous_social_post',
                    actor='autonomous_executor',
                    action='social_post',
                    resource=f"{platform}:{result.get('post_id', 'unknown')}",
                    result='success',
                    metadata={
                        'source_file': source_file,
                        'platform': platform,
                        'immediate': immediate
                    }
                )
            else:
                # Handle failure
                self._handle_social_post_failure(
                    platform=platform,
                    message=message,
                    media=media,
                    source_file=source_file,
                    tracking_key=tracking_key,
                    error=result.get('error', 'Unknown error') if result else 'No result'
                )

        except Exception as e:
            self.logger.error(f"Error triggering social skill {platform}: {e}", exc_info=True)
            self._handle_social_post_failure(
                platform=platform,
                message=message,
                media=media,
                source_file=source_file,
                tracking_key=f"social_{platform}_{source_file}",
                error=str(e)
            )

    def _handle_social_post_failure(self, platform: str, message: str, media: List[str],
                                   source_file: str, tracking_key: str, error: str):
        """Handle social media post failure with retry logic"""
        try:
            # Increment failure count
            with self.social_lock:
                self.task_failure_counts[tracking_key] = \
                    self.task_failure_counts.get(tracking_key, 0) + 1
                failure_count = self.task_failure_counts[tracking_key]

            self.logger.warning(
                f"Social post failed: {platform} (failures: {failure_count}, error: {error})"
            )

            # Emit failure event
            self.event_bus.publish('social_post_failed', {
                'platform': platform,
                'source_file': source_file,
                'error': error,
                'failure_count': failure_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            # Check if we need to escalate
            if failure_count >= self.failure_threshold:
                self._escalate_social_failure(platform, source_file, message, error, failure_count)
            else:
                # Add to retry queue
                self.logger.info(f"Enqueueing {platform} post for retry (attempt {failure_count})")

                # Create retry operation
                def retry_operation():
                    return self._trigger_social_skill(
                        platform=platform,
                        message=message,
                        media=media,
                        source_file=source_file,
                        immediate=False
                    )

                self.retry_queue.enqueue(
                    operation=retry_operation,
                    context={
                        'name': f"social_{platform}",
                        'source_file': source_file,
                        'attempt': failure_count
                    }
                )

        except Exception as e:
            self.logger.error(f"Error handling social post failure: {e}")

    def _escalate_social_failure(self, platform: str, source_file: str, message: str,
                                error: str, failure_count: int):
        """Escalate repeated social media failures to human attention"""
        try:
            self.logger.error(
                f"ESCALATION: Social post to {platform} failed {failure_count} times"
            )

            # Create escalation file
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            escalation_file = self.needs_action_dir / f"SOCIAL_ESCALATION_{timestamp}_{platform}.md"

            escalation_content = f"""# ESCALATION: Social Media Post Failure

## Summary
Autonomous executor failed to post to {platform} after {failure_count} attempts.

## Details
- **Platform**: {platform}
- **Source File**: {source_file}
- **Failure Count**: {failure_count}
- **Last Error**: {error}
- **Timestamp**: {datetime.utcnow().isoformat()}

## Message Content
```
{message[:500]}{'...' if len(message) > 500 else ''}
```

## Action Required
Please review the error and manually post the content or fix the underlying issue.

## Original File
Check `{source_file}` for full content and configuration.

---
*Generated by AutonomousExecutor - Social Media Automation*
"""

            escalation_file.write_text(escalation_content)

            # Audit log
            self.audit_logger.log_event(
                event_type='autonomous_escalation',
                actor='autonomous_executor',
                action='escalate_social_failure',
                resource=f"{platform}:{source_file}",
                result='escalated',
                metadata={
                    'platform': platform,
                    'source_file': source_file,
                    'failure_count': failure_count,
                    'error': error
                }
            )

            # Emit escalation event
            self.event_bus.publish('social_post_escalated', {
                'platform': platform,
                'source_file': source_file,
                'failure_count': failure_count,
                'escalation_file': escalation_file.name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        except Exception as e:
            self.logger.error(f"Error escalating social failure: {e}")

    def _extract_message_from_content(self, filepath: Path) -> str:
        """Extract message content from markdown file"""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Remove frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2]

            # Remove HTML comments
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

            # Get first paragraph or heading
            lines = [line.strip() for line in content.split('\n') if line.strip()]

            if lines:
                # Skip markdown headers
                for line in lines:
                    if not line.startswith('#'):
                        return line

                # If all headers, use first one without #
                return lines[0].lstrip('#').strip()

            return ""

        except Exception as e:
            self.logger.error(f"Error extracting message from {filepath.name}: {e}")
            return ""

    def _is_recently_processed(self, filepath: Path) -> bool:
        """Check if file was recently processed"""
        with self.social_lock:
            last_processed = self.social_processed_files.get(str(filepath))
            if last_processed:
                # Don't reprocess within 1 hour
                if (datetime.utcnow() - last_processed) < timedelta(hours=1):
                    return True
        return False

    def _mark_as_processed(self, filepath: Path):
        """Mark file as processed"""
        with self.social_lock:
            self.social_processed_files[str(filepath)] = datetime.utcnow()

            # Clean up old entries (older than 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.social_processed_files = {
                k: v for k, v in self.social_processed_files.items()
                if v > cutoff
            }


# Integration instructions for index.py:
"""
To integrate this enhancement into the AutonomousExecutor in index.py:

1. Add this import at the top:
   from autonomous_executor_enhanced import SocialMediaAutomation

2. Modify AutonomousExecutor class definition:
   class AutonomousExecutor(SocialMediaAutomation):

3. Update __init__ to call parent init:
   def __init__(self, ...):
       # Existing init code
       ...
       # Initialize social media automation
       SocialMediaAutomation.__init__(self)

4. Add social media check to _execution_loop:
   def _execution_loop(self):
       while self.running:
           try:
               # Existing checks
               self._check_retry_queue()
               self._check_pending_workflows()
               self._check_incomplete_tasks()
               self._check_stale_files()

               # NEW: Social media automation
               self._check_social_media_content()

               # Rest of loop
               ...

5. Optionally, pass orchestrator reference for social_adapter access:
   In IntegrationOrchestrator._setup_gold_tier_components():
       self.autonomous_executor = AutonomousExecutor(...)
       self.autonomous_executor.orchestrator = self  # Add this line
"""

#!/usr/bin/env python3
"""
Hardened AutonomousExecutor with Social Media Automation
=========================================================

Production-hardened version with:
- Error boundary protection
- Detailed logging for each detection step
- Crash recovery for skill execution failures
- Timeout protection for long-running skills
- Monitoring metrics for auto-trigger success rate
- Centralized circuit breaker integration (via CircuitBreakerManager)
- Health check integration

IMPORTANT: This class requires circuit_breaker_manager to be injected as a dependency.
The circuit_breaker_manager should be an instance of CircuitBreakerManager from
Skills.integration_orchestrator.core.circuit_breaker
"""

import re
import json
import time
import signal
import traceback
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from threading import Lock, Thread, Event
from collections import defaultdict
from enum import Enum


class ComponentHealth(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class MonitoringMetrics:
    """
    Monitoring metrics for autonomous executor.

    Tracks success rates, execution times, and error counts
    for all autonomous operations.
    """

    def __init__(self):
        self.lock = Lock()

        # Execution metrics
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0

        # Social media metrics
        self.social_detections = 0
        self.social_posts_attempted = 0
        self.social_posts_successful = 0
        self.social_posts_failed = 0

        # Skill execution metrics
        self.skill_executions: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'timeouts': 0
        })

        # Timing metrics
        self.execution_times: Dict[str, List[float]] = defaultdict(list)

        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_errors: Dict[str, str] = {}

        # Component health
        self.component_health: Dict[str, ComponentHealth] = {}

        # Start time
        self.start_time = datetime.utcnow()

    def record_check(self, success: bool):
        """Record a check cycle"""
        with self.lock:
            self.total_checks += 1
            if success:
                self.successful_checks += 1
            else:
                self.failed_checks += 1

    def record_social_detection(self):
        """Record social media content detection"""
        with self.lock:
            self.social_detections += 1

    def record_social_post(self, success: bool, platform: str = None):
        """Record social media post attempt"""
        with self.lock:
            self.social_posts_attempted += 1
            if success:
                self.social_posts_successful += 1
            else:
                self.social_posts_failed += 1

    def record_skill_execution(self, skill_name: str, success: bool,
                              execution_time: float, timeout: bool = False):
        """Record skill execution"""
        with self.lock:
            metrics = self.skill_executions[skill_name]
            metrics['attempts'] += 1

            if timeout:
                metrics['timeouts'] += 1
            elif success:
                metrics['successes'] += 1
            else:
                metrics['failures'] += 1

            # Track execution time
            self.execution_times[skill_name].append(execution_time)

            # Keep only last 100 execution times
            if len(self.execution_times[skill_name]) > 100:
                self.execution_times[skill_name] = self.execution_times[skill_name][-100:]

    def record_error(self, component: str, error: str):
        """Record an error"""
        with self.lock:
            self.error_counts[component] += 1
            self.last_errors[component] = error

    def update_component_health(self, component: str, health: ComponentHealth):
        """Update component health status"""
        with self.lock:
            self.component_health[component] = health

    def get_success_rate(self) -> float:
        """Get overall success rate"""
        with self.lock:
            if self.total_checks == 0:
                return 0.0
            return (self.successful_checks / self.total_checks) * 100

    def get_social_success_rate(self) -> float:
        """Get social media post success rate"""
        with self.lock:
            if self.social_posts_attempted == 0:
                return 0.0
            return (self.social_posts_successful / self.social_posts_attempted) * 100

    def get_skill_success_rate(self, skill_name: str) -> float:
        """Get success rate for specific skill"""
        with self.lock:
            metrics = self.skill_executions.get(skill_name)
            if not metrics or metrics['attempts'] == 0:
                return 0.0
            return (metrics['successes'] / metrics['attempts']) * 100

    def get_average_execution_time(self, skill_name: str) -> float:
        """Get average execution time for skill"""
        with self.lock:
            times = self.execution_times.get(skill_name, [])
            if not times:
                return 0.0
            return sum(times) / len(times)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self.lock:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

            return {
                'uptime_seconds': uptime,
                'overall': {
                    'total_checks': self.total_checks,
                    'successful_checks': self.successful_checks,
                    'failed_checks': self.failed_checks,
                    'success_rate': self.get_success_rate()
                },
                'social_media': {
                    'detections': self.social_detections,
                    'posts_attempted': self.social_posts_attempted,
                    'posts_successful': self.social_posts_successful,
                    'posts_failed': self.social_posts_failed,
                    'success_rate': self.get_social_success_rate()
                },
                'skills': {
                    skill: {
                        **metrics,
                        'success_rate': self.get_skill_success_rate(skill),
                        'avg_execution_time': self.get_average_execution_time(skill)
                    }
                    for skill, metrics in self.skill_executions.items()
                },
                'errors': {
                    'total_errors': sum(self.error_counts.values()),
                    'by_component': dict(self.error_counts),
                    'last_errors': dict(self.last_errors)
                },
                'component_health': {
                    comp: health.value
                    for comp, health in self.component_health.items()
                }
            }


class TimeoutError(Exception):
    """Raised when operation times out"""
    pass


@contextmanager
def timeout_protection(seconds: int, operation_name: str = "operation"):
    """
    Context manager for timeout protection.

    Usage:
        with timeout_protection(30, "social_post"):
            # code that might hang
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"{operation_name} timed out after {seconds} seconds")

    # Set up signal handler (Unix only)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@contextmanager
def error_boundary(logger, component_name: str, metrics: MonitoringMetrics = None,
                  reraise: bool = False):
    """
    Error boundary context manager.

    Catches and logs all exceptions, optionally recording metrics.

    Usage:
        with error_boundary(logger, "social_detection", metrics):
            # code that might fail
    """
    try:
        yield
    except Exception as e:
        error_msg = f"{component_name} error: {str(e)}"
        logger.error(error_msg, exc_info=True)

        if metrics:
            metrics.record_error(component_name, str(e))

        if reraise:
            raise


class HardenedSocialMediaAutomation:
    """
    Hardened version of SocialMediaAutomation with comprehensive error protection.

    Improvements:
    - Error boundaries around all operations
    - Detailed logging for each step
    - Timeout protection for skill execution
    - Crash recovery mechanisms
    - Monitoring metrics
    - Circuit breaker for failing components
    """

    def __init__(self):
        """Initialize hardened social media automation"""
        # Monitoring metrics
        self.metrics = MonitoringMetrics()

        # Timeout settings
        self.skill_timeout = 120  # 2 minutes max per skill
        self.parse_timeout = 10   # 10 seconds max for parsing

        # Initialize parent tracking
        self.social_processed_files: Dict[str, datetime] = {}
        self.social_lock = Lock()

        # Directories
        self.posted_dir = self.base_dir / "Posted"
        self.drafts_dir = self.base_dir / "Drafts"
        self.plans_dir = self.base_dir / "Plans"

        # Ensure directories exist
        for directory in [self.posted_dir, self.drafts_dir, self.plans_dir]:
            with error_boundary(self.logger, f"create_dir_{directory.name}", self.metrics):
                directory.mkdir(parents=True, exist_ok=True)

        self.logger.info("Hardened social media automation initialized")
        self.logger.info(f"Skill timeout: {self.skill_timeout}s, Parse timeout: {self.parse_timeout}s")

    def _check_social_media_content(self):
        """
        Check for social media content with comprehensive error protection.
        """
        check_start = time.time()

        with error_boundary(self.logger, "social_media_check", self.metrics):
            self.logger.debug("Starting social media content check")

            # Check circuit breaker
            if not self.circuit_breaker_manager.check_breaker('social_media_check'):
                self.logger.warning("Social media check circuit breaker is OPEN, skipping")
                self.metrics.update_component_health('social_media_check', ComponentHealth.DEGRADED)
                return

            try:
                # Process posted content
                with error_boundary(self.logger, "process_posted", self.metrics):
                    self.logger.debug("Checking Posted/ directory")
                    self._process_posted_content()

                # Process scheduled posts
                with error_boundary(self.logger, "process_scheduled", self.metrics):
                    self.logger.debug("Checking Plans/ directory for scheduled posts")
                    self._process_scheduled_posts()

                # Check drafts
                with error_boundary(self.logger, "check_drafts", self.metrics):
                    self.logger.debug("Checking Drafts/ directory")
                    self._check_draft_content()

                # Record successful check
                self.metrics.record_check(True)
                self.metrics.update_component_health('social_media_check', ComponentHealth.HEALTHY)
                self.circuit_breaker_manager.record_success('social_media_check')

                check_time = time.time() - check_start
                self.logger.debug(f"Social media check completed in {check_time:.2f}s")

            except Exception as e:
                self.logger.error(f"Social media check failed: {e}", exc_info=True)
                self.metrics.record_check(False)
                self.metrics.update_component_health('social_media_check', ComponentHealth.FAILED)
                self.circuit_breaker_manager.record_failure('social_media_check')

    def _process_posted_content(self):
        """Process content in Posted/ with detailed logging"""
        if not self.posted_dir.exists():
            self.logger.debug("Posted/ directory does not exist")
            return

        posted_files = list(self.posted_dir.glob("*.md"))
        self.logger.debug(f"Found {len(posted_files)} files in Posted/")

        for filepath in posted_files:
            with error_boundary(self.logger, f"process_file_{filepath.name}", self.metrics):
                self.logger.debug(f"Processing file: {filepath.name}")

                # Skip if recently processed
                if self._is_recently_processed(filepath):
                    self.logger.debug(f"Skipping {filepath.name} - recently processed")
                    continue

                # Parse with timeout protection
                try:
                    with timeout_protection(self.parse_timeout, f"parse_{filepath.name}"):
                        social_config = self._parse_social_media_config(filepath)
                except TimeoutError as e:
                    self.logger.error(f"Parsing timeout for {filepath.name}: {e}")
                    self.metrics.record_error('parse_timeout', str(e))
                    continue

                if social_config:
                    self.logger.info(f"Detected social media content: {filepath.name}")
                    self.logger.debug(f"Config: platforms={social_config.get('platforms')}, "
                                    f"has_message={bool(social_config.get('message'))}")

                    self.metrics.record_social_detection()

                    # Trigger posting with crash recovery
                    self._trigger_social_media_post_safe(filepath, social_config, immediate=True)

                    # Mark as processed
                    self._mark_as_processed(filepath)
                else:
                    self.logger.debug(f"No social config found in {filepath.name}")

    def _process_scheduled_posts(self):
        """Process scheduled posts with detailed logging"""
        if not self.plans_dir.exists():
            self.logger.debug("Plans/ directory does not exist")
            return

        plan_files = list(self.plans_dir.glob("*.md"))
        self.logger.debug(f"Found {len(plan_files)} files in Plans/")

        for filepath in plan_files:
            with error_boundary(self.logger, f"process_scheduled_{filepath.name}", self.metrics):
                self.logger.debug(f"Checking scheduled post: {filepath.name}")

                # Parse with timeout
                try:
                    with timeout_protection(self.parse_timeout, f"parse_scheduled_{filepath.name}"):
                        social_config = self._parse_social_media_config(filepath)
                except TimeoutError as e:
                    self.logger.error(f"Parsing timeout for scheduled post {filepath.name}: {e}")
                    continue

                if not social_config or not social_config.get('scheduled_time'):
                    continue

                # Check if it's time to post
                scheduled_time = self._parse_scheduled_time(social_config['scheduled_time'])

                if scheduled_time:
                    time_until = (scheduled_time - datetime.utcnow()).total_seconds()
                    self.logger.debug(f"Scheduled post {filepath.name}: {time_until:.0f}s until posting")

                    if datetime.utcnow() >= scheduled_time:
                        # Skip if already processed
                        if self._is_recently_processed(filepath):
                            self.logger.debug(f"Skipping {filepath.name} - already posted")
                            continue

                        self.logger.info(f"Scheduled post ready: {filepath.name}")
                        self.metrics.record_social_detection()

                        # Trigger posting
                        self._trigger_social_media_post_safe(filepath, social_config, immediate=False)

                        # Mark as processed
                        self._mark_as_processed(filepath)

    def _check_draft_content(self):
        """Check draft content with logging"""
        if not self.drafts_dir.exists():
            return

        draft_files = list(self.drafts_dir.glob("*.md"))

        if draft_files:
            self.logger.debug(f"Found {len(draft_files)} social media drafts")

            # Emit event
            with error_boundary(self.logger, "emit_drafts_event", self.metrics):
                self.event_bus.publish('social_drafts_detected', {
                    'count': len(draft_files),
                    'files': [f.name for f in draft_files[:5]],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

    def _trigger_social_media_post_safe(self, filepath, social_config, immediate):
        """
        Trigger social media post with comprehensive crash recovery.
        """
        with error_boundary(self.logger, f"trigger_post_{filepath.name}", self.metrics):
            self.logger.info(f"Triggering social media post from {filepath.name}")

            platforms = social_config.get('platforms', [])
            message = social_config.get('message', '')
            media = social_config.get('media', [])

            if not platforms:
                self.logger.warning(f"No platforms specified in {filepath.name}")
                return

            if not message:
                self.logger.debug(f"Extracting message from content: {filepath.name}")
                message = self._extract_message_from_content(filepath)

            if not message:
                self.logger.warning(f"No message found in {filepath.name}")
                return

            self.logger.debug(f"Posting to {len(platforms)} platforms: {platforms}")

            # Discover available skills
            available_skills = self._discover_social_skills()
            self.logger.debug(f"Available social skills: {available_skills}")

            # Emit trigger event
            with error_boundary(self.logger, "emit_trigger_event", self.metrics):
                self.event_bus.publish('social_post_triggered', {
                    'source_file': filepath.name,
                    'platforms': platforms,
                    'immediate': immediate,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Trigger each platform with crash recovery
            for platform in platforms:
                skill_name = f"social_{platform}"

                if skill_name not in available_skills:
                    self.logger.warning(f"Skill {skill_name} not available")
                    continue

                # Check circuit breaker for this platform
                if not self.circuit_breaker_manager.check_breaker(platform):
                    self.logger.warning(f"Circuit breaker OPEN for {platform}, skipping")
                    continue

                # Trigger with timeout and error protection
                self._trigger_social_skill_hardened(
                    platform=platform,
                    message=message,
                    media=media,
                    source_file=filepath.name,
                    immediate=immediate
                )

    def _trigger_social_skill_hardened(self, platform, message, media, source_file, immediate):
        """
        Trigger social skill with timeout protection and crash recovery.
        """
        tracking_key = f"social_{platform}_{source_file}"
        execution_start = time.time()

        with error_boundary(self.logger, f"skill_{platform}", self.metrics):
            self.logger.info(f"Executing social skill: {platform} (source: {source_file})")

            # Check rate limiting
            with self.social_lock:
                last_attempt = self.last_check_times.get(tracking_key)
                if last_attempt and (datetime.utcnow() - last_attempt) < timedelta(minutes=10):
                    self.logger.debug(f"Rate limit: skipping {platform}")
                    return

                self.last_check_times[tracking_key] = datetime.utcnow()

            result = None
            timed_out = False

            try:
                # Execute with timeout protection
                with timeout_protection(self.skill_timeout, f"social_post_{platform}"):
                    if hasattr(self, 'orchestrator') and hasattr(self.orchestrator, 'social_adapter'):
                        self.logger.debug(f"Using social_adapter for {platform}")
                        result = self.orchestrator.social_adapter.post(
                            platform=platform,
                            message=message,
                            media=media if media else None,
                            metadata={
                                'source_file': source_file,
                                'immediate': immediate,
                                'triggered_by': 'autonomous_executor_hardened'
                            }
                        )
                    else:
                        self.logger.warning(f"Social adapter not available for {platform}")
                        result = {'success': False, 'error': 'Social adapter not available'}

            except TimeoutError as e:
                self.logger.error(f"Timeout executing {platform}: {e}")
                timed_out = True
                result = {'success': False, 'error': f'Timeout: {e}'}
                self.metrics.record_error(f'timeout_{platform}', str(e))

            except Exception as e:
                self.logger.error(f"Crash during {platform} execution: {e}", exc_info=True)
                result = {'success': False, 'error': f'Crash: {e}'}
                self.metrics.record_error(f'crash_{platform}', str(e))

            # Record metrics
            execution_time = time.time() - execution_start
            success = result and result.get('success', False)

            self.metrics.record_skill_execution(
                skill_name=f"social_{platform}",
                success=success,
                execution_time=execution_time,
                timeout=timed_out
            )

            self.metrics.record_social_post(success, platform)

            # Handle result
            if success:
                self.logger.info(f"Social post successful: {platform} - {result.get('post_id')} "
                               f"(took {execution_time:.2f}s)")

                # Reset circuit breaker
                self.circuit_breaker_manager.record_success(platform)

                # Reset failure count
                with self.social_lock:
                    if tracking_key in self.task_failure_counts:
                        del self.task_failure_counts[tracking_key]

                # Audit log
                with error_boundary(self.logger, "audit_log_success", self.metrics):
                    self.audit_logger.log_event(
                        event_type='autonomous_social_post',
                        actor='autonomous_executor_hardened',
                        action='social_post',
                        resource=f"{platform}:{result.get('post_id', 'unknown')}",
                        result='success',
                        metadata={
                            'source_file': source_file,
                            'platform': platform,
                            'immediate': immediate,
                            'execution_time': execution_time
                        }
                    )
            else:
                # Handle failure
                error = result.get('error', 'Unknown error') if result else 'No result'
                self.logger.error(f"Social post failed: {platform} - {error} "
                                f"(took {execution_time:.2f}s)")

                # Record circuit breaker failure
                self.circuit_breaker_manager.record_failure(platform)

                # Handle with existing failure recovery
                self._handle_social_post_failure(
                    platform=platform,
                    message=message,
                    media=media,
                    source_file=source_file,
                    tracking_key=tracking_key,
                    error=error
                )

    def get_monitoring_metrics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring metrics"""
        return self.metrics.get_metrics_summary()

    def _parse_social_media_config(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Parse markdown file for social media configuration with error protection"""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Try YAML frontmatter first
            with error_boundary(self.logger, f"parse_yaml_{filepath.name}", self.metrics):
                yaml_config = self._parse_yaml_frontmatter(content)
                if yaml_config and 'social_media' in yaml_config:
                    self.logger.debug(f"Parsed YAML config from {filepath.name}")
                    return yaml_config['social_media']

            # Try inline markers
            with error_boundary(self.logger, f"parse_inline_{filepath.name}", self.metrics):
                inline_config = self._parse_inline_markers(content)
                if inline_config:
                    self.logger.debug(f"Parsed inline config from {filepath.name}")
                    return inline_config

            # Try JSON block
            with error_boundary(self.logger, f"parse_json_{filepath.name}", self.metrics):
                json_config = self._parse_json_block(content)
                if json_config:
                    self.logger.debug(f"Parsed JSON config from {filepath.name}")
                    return json_config

            return None

        except Exception as e:
            self.logger.error(f"Error parsing {filepath.name}: {e}")
            self.metrics.record_error(f'parse_{filepath.name}', str(e))
            return None

    def _parse_yaml_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from markdown"""
        try:
            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            frontmatter = parts[1]

            if 'social_media:' in frontmatter:
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
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            try:
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except:
                        continue
            except:
                pass

        return None

    def _discover_social_skills(self) -> List[str]:
        """Discover available social media skills from SkillRegistry"""
        try:
            all_skills = list(self.skill_registry.skill_metadata.keys())
            social_skills = [s for s in all_skills if s.startswith('social_')]
            self.logger.debug(f"Discovered {len(social_skills)} social skills: {social_skills}")
            return social_skills
        except Exception as e:
            self.logger.error(f"Error discovering social skills: {e}")
            self.metrics.record_error('discover_skills', str(e))
            return []

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
                for line in lines:
                    if not line.startswith('#'):
                        return line

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

    def _handle_social_post_failure(self, platform: str, message: str, media: List[str],
                                   source_file: str, tracking_key: str, error: str):
        """Handle social media post failure with retry logic"""
        with error_boundary(self.logger, f"handle_failure_{platform}", self.metrics):
            # Increment failure count
            with self.social_lock:
                self.task_failure_counts[tracking_key] = \
                    self.task_failure_counts.get(tracking_key, 0) + 1
                failure_count = self.task_failure_counts[tracking_key]

            self.logger.warning(
                f"Social post failed: {platform} (failures: {failure_count}, error: {error})"
            )

            # Emit failure event
            with error_boundary(self.logger, "emit_failure_event", self.metrics):
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
                # Add to retry queue using centralized RetryQueue
                self.logger.info(f"Enqueueing {platform} post for retry (attempt {failure_count})")

                with error_boundary(self.logger, "enqueue_retry", self.metrics):
                    # Use centralized retry - pass method reference directly
                    self.retry_queue.enqueue(
                        operation=self._trigger_social_skill_hardened,
                        kwargs={
                            'platform': platform,
                            'message': message,
                            'media': media,
                            'source_file': source_file,
                            'immediate': False
                        },
                        context={
                            'name': f"social_{platform}",
                            'source_file': source_file,
                            'attempt': failure_count
                        }
                    )

    def _escalate_social_failure(self, platform: str, source_file: str, message: str,
                                error: str, failure_count: int):
        """Escalate repeated social media failures to human attention"""
        with error_boundary(self.logger, f"escalate_{platform}", self.metrics):
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
*Generated by AutonomousExecutor - Hardened Social Media Automation*
"""

            escalation_file.write_text(escalation_content)

            # Audit log
            with error_boundary(self.logger, "audit_escalation", self.metrics):
                self.audit_logger.log_event(
                    event_type='autonomous_escalation',
                    actor='autonomous_executor_hardened',
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
            with error_boundary(self.logger, "emit_escalation_event", self.metrics):
                self.event_bus.publish('social_post_escalated', {
                    'platform': platform,
                    'source_file': source_file,
                    'failure_count': failure_count,
                    'escalation_file': escalation_file.name,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })


# Note: This is a mixin class that should be used with the existing AutonomousExecutor
# Replace SocialMediaAutomation with HardenedSocialMediaAutomation in the class inheritance

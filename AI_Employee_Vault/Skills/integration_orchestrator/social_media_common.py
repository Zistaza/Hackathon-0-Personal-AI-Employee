#!/usr/bin/env python3
"""
Social Media Common Components - Shared Library
================================================

Shared components for all social media skills:
- ContentValidator
- ContentModerator
- EngagementTracker
- SocialAnalytics
- BaseSocialSkill (abstract base class)

This module is imported by individual social media skill folders.
"""

import logging
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from enum import Enum


# Enterprise moderation threshold
MODERATION_THRESHOLD = 0.5  # Block content with risk_score > 0.5


class SocialPlatform(Enum):
    """Social media platforms"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER_X = "twitter_x"


class PostStatus(Enum):
    """Post status types"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    RETRYING = "retrying"
    REJECTED = "rejected"


class ModerationRisk(Enum):
    """Content moderation risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentValidator:
    """
    Enterprise content validation with prohibited words checking.
    """

    # Simulated prohibited words list
    PROHIBITED_WORDS = [
        "spam", "scam", "fake", "illegal", "hack", "exploit",
        "violence", "hate", "discrimination", "offensive"
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def validate(self, message: str, platform: str) -> Dict[str, Any]:
        """
        Validate content for posting.

        Args:
            message: Content to validate
            platform: Target platform

        Returns:
            Validation result with status and details
        """
        issues = []

        # Check length based on platform
        length_limits = {
            'facebook': 63206,
            'instagram': 2200,
            'twitter_x': 280
        }

        max_length = length_limits.get(platform, 1000)
        if len(message) > max_length:
            issues.append({
                'type': 'length_exceeded',
                'message': f'Content exceeds {platform} limit of {max_length} characters',
                'severity': 'error'
            })

        # Check for prohibited words
        message_lower = message.lower()
        found_prohibited = []
        for word in self.PROHIBITED_WORDS:
            if re.search(r'\b' + re.escape(word) + r'\b', message_lower):
                found_prohibited.append(word)

        if found_prohibited:
            issues.append({
                'type': 'prohibited_content',
                'message': f'Contains prohibited words: {", ".join(found_prohibited)}',
                'severity': 'error',
                'words': found_prohibited
            })

        # Check for empty content
        if not message or len(message.strip()) == 0:
            issues.append({
                'type': 'empty_content',
                'message': 'Content cannot be empty',
                'severity': 'error'
            })

        # Check for excessive capitalization (potential spam)
        if len(message) > 10:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            if caps_ratio > 0.7:
                issues.append({
                    'type': 'excessive_caps',
                    'message': 'Excessive capitalization detected (potential spam)',
                    'severity': 'warning'
                })

        # Check for excessive special characters
        special_chars = sum(1 for c in message if not c.isalnum() and not c.isspace())
        if special_chars > len(message) * 0.3:
            issues.append({
                'type': 'excessive_special_chars',
                'message': 'Excessive special characters detected',
                'severity': 'warning'
            })

        valid = not any(issue['severity'] == 'error' for issue in issues)

        return {
            'valid': valid,
            'issues': issues,
            'validated_at': datetime.now(UTC).isoformat()
        }


class ContentModerator:
    """
    Enterprise content moderation with risk scoring.
    """

    def __init__(self, logger: logging.Logger, event_bus=None, threshold: float = MODERATION_THRESHOLD):
        self.logger = logger
        self.event_bus = event_bus
        self.threshold = threshold

    def moderate(self, message: str, media: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform content moderation and assign risk score.

        Args:
            message: Content to moderate
            media: Optional media items

        Returns:
            Moderation result with risk score and decision
        """
        risk_score = 0.0
        risk_factors = []

        # Simulate risk scoring based on content analysis
        message_lower = message.lower()

        # Check for sensitive keywords
        sensitive_keywords = ['buy now', 'click here', 'limited time', 'act fast', 'guaranteed']
        for keyword in sensitive_keywords:
            if keyword in message_lower:
                risk_score += 0.15
                risk_factors.append(f'Contains marketing keyword: {keyword}')

        # Check for URLs (higher risk)
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, message)
        if urls:
            risk_score += 0.1 * len(urls)
            risk_factors.append(f'Contains {len(urls)} URL(s)')

        # Check for excessive punctuation
        exclamation_count = message.count('!')
        if exclamation_count > 3:
            risk_score += 0.1
            risk_factors.append(f'Excessive exclamation marks ({exclamation_count})')

        # Check message length (very short or very long can be risky)
        if len(message) < 10:
            risk_score += 0.05
            risk_factors.append('Very short message')
        elif len(message) > 1000:
            risk_score += 0.05
            risk_factors.append('Very long message')

        # Simulate random variation (real-world unpredictability)
        import random
        random_factor = random.uniform(-0.1, 0.1)
        risk_score += random_factor

        # Normalize score to 0-1 range
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score < 0.3:
            risk_level = ModerationRisk.LOW
        elif risk_score < 0.5:
            risk_level = ModerationRisk.MEDIUM
        elif risk_score < 0.7:
            risk_level = ModerationRisk.HIGH
        else:
            risk_level = ModerationRisk.CRITICAL

        # Decision: block if score exceeds threshold
        approved = risk_score <= self.threshold

        # Emit content_blocked event if not approved
        if not approved and self.event_bus:
            self.event_bus.publish('content_blocked', {
                'risk_score': round(risk_score, 3),
                'risk_level': risk_level.value,
                'threshold': self.threshold,
                'risk_factors': risk_factors,
                'blocked_at': datetime.now(UTC).isoformat()
            })

        return {
            'approved': approved,
            'risk_score': round(risk_score, 3),
            'risk_level': risk_level.value,
            'risk_factors': risk_factors,
            'threshold': self.threshold,
            'moderated_at': datetime.now(UTC).isoformat()
        }


class EngagementTracker:
    """
    Enterprise engagement tracking with simulated metrics.
    """

    def __init__(self, logger: logging.Logger, state_manager=None):
        self.logger = logger
        self.state_manager = state_manager

    def generate_metrics(self, platform: str, post_id: str, message: str) -> Dict[str, Any]:
        """
        Generate simulated engagement metrics for a post.

        Args:
            platform: Social media platform
            post_id: Post identifier
            message: Post content

        Returns:
            Engagement metrics
        """
        import random

        # Base metrics influenced by content quality
        content_quality = min(1.0, len(message) / 100)

        # Platform-specific metrics
        if platform == 'facebook':
            likes = int(random.randint(10, 500) * content_quality)
            comments = int(random.randint(2, 50) * content_quality)
            shares = int(random.randint(1, 30) * content_quality)
            reach = int(random.randint(100, 5000) * content_quality)

            metrics = {
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'reach': reach,
                'engagement_rate': round((likes + comments + shares) / max(reach, 1) * 100, 2)
            }

        elif platform == 'instagram':
            likes = int(random.randint(50, 1000) * content_quality)
            comments = int(random.randint(5, 100) * content_quality)
            reach = int(random.randint(200, 10000) * content_quality)
            saves = int(random.randint(2, 50) * content_quality)

            metrics = {
                'likes': likes,
                'comments': comments,
                'saves': saves,
                'reach': reach,
                'engagement_rate': round((likes + comments + saves) / max(reach, 1) * 100, 2)
            }

        elif platform == 'twitter_x':
            likes = int(random.randint(20, 800) * content_quality)
            retweets = int(random.randint(5, 100) * content_quality)
            replies = int(random.randint(2, 50) * content_quality)
            views = int(random.randint(500, 20000) * content_quality)

            metrics = {
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'views': views,
                'engagement_rate': round((likes + retweets + replies) / max(views, 1) * 100, 2)
            }

        else:
            metrics = {
                'engagement_rate': 0.0
            }

        metrics['tracked_at'] = datetime.now(UTC).isoformat()

        # Store in state if available
        if self.state_manager:
            self._store_metrics(platform, post_id, metrics)

        return metrics

    def _store_metrics(self, platform: str, post_id: str, metrics: Dict[str, Any]):
        """Store metrics in state manager"""
        try:
            key = f'engagement_{platform}_{post_id}'
            self.state_manager.set_system_state(key, metrics)

            # Update aggregate metrics
            self.state_manager.increment_counter(f'total_posts_{platform}', 1)

        except Exception as e:
            self.logger.error(f"Failed to store engagement metrics: {e}")


class SocialAnalytics:
    """
    Enterprise social analytics summary generator.
    """

    def __init__(self, logger: logging.Logger, state_manager=None):
        self.logger = logger
        self.state_manager = state_manager

    def generate_weekly_summary(self) -> Dict[str, Any]:
        """
        Generate weekly analytics summary from stored metrics.

        Returns:
            Weekly summary with aggregated metrics
        """
        if not self.state_manager:
            return {'error': 'StateManager not available'}

        summary = {
            'period': 'weekly',
            'generated_at': datetime.now(UTC).isoformat(),
            'platforms': {}
        }

        # Aggregate metrics by platform
        for platform in ['facebook', 'instagram', 'twitter_x']:
            platform_metrics = self._get_platform_metrics(platform)
            summary['platforms'][platform] = platform_metrics

        # Calculate overall metrics
        summary['overall'] = self._calculate_overall_metrics(summary['platforms'])

        # Store summary in state
        self.state_manager.set_system_state('social_analytics_weekly', summary)

        return summary

    def _get_platform_metrics(self, platform: str) -> Dict[str, Any]:
        """Get aggregated metrics for a platform"""
        try:
            total_posts = self.state_manager.get_metric(f'total_posts_{platform}')
            post_count = total_posts['value'] if total_posts else 0

            # Collect all engagement metrics for this platform
            all_metrics = []
            system_state = self.state_manager.system_state

            for key, value in system_state.items():
                if key.startswith(f'engagement_{platform}_'):
                    all_metrics.append(value)

            if not all_metrics:
                return {
                    'total_posts': post_count,
                    'avg_engagement_rate': 0.0,
                    'total_reach': 0
                }

            # Calculate averages
            avg_engagement = sum(m.get('engagement_rate', 0) for m in all_metrics) / len(all_metrics)
            total_reach = sum(m.get('reach', 0) for m in all_metrics)

            return {
                'total_posts': post_count,
                'avg_engagement_rate': round(avg_engagement, 2),
                'total_reach': total_reach,
                'metrics_count': len(all_metrics)
            }

        except Exception as e:
            self.logger.error(f"Error getting platform metrics: {e}")
            return {'error': str(e)}

    def _calculate_overall_metrics(self, platforms: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall metrics across all platforms"""
        total_posts = sum(p.get('total_posts', 0) for p in platforms.values())
        total_reach = sum(p.get('total_reach', 0) for p in platforms.values())

        engagement_rates = [p.get('avg_engagement_rate', 0) for p in platforms.values() if 'avg_engagement_rate' in p]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0

        return {
            'total_posts': total_posts,
            'total_reach': total_reach,
            'avg_engagement_rate': round(avg_engagement, 2)
        }


class BaseSocialSkill(ABC):
    """
    Abstract base class for social media skills - Enterprise Edition.

    Provides common functionality for all social media posting skills:
    - Idempotent execution
    - Event emission
    - Audit logging
    - Report generation
    - Error handling
    - Content validation
    - Content moderation
    - Engagement tracking
    """

    def __init__(self, platform: SocialPlatform, logger: logging.Logger,
                 event_bus=None, audit_logger=None, retry_queue=None,
                 reports_dir: Path = None, state_manager=None):
        """
        Initialize social media skill.

        Args:
            platform: Social media platform
            logger: Logger instance
            event_bus: EventBus for event emission (optional)
            audit_logger: AuditLogger for structured logging (optional)
            retry_queue: RetryQueue for retry logic (optional)
            reports_dir: Directory for report generation (optional)
            state_manager: StateManager for persistence (optional)
        """
        self.platform = platform
        self.logger = logger
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.retry_queue = retry_queue
        self.reports_dir = reports_dir or Path("Reports/Social")
        self.state_manager = state_manager

        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Track posted content for idempotency
        self.posted_hashes: Dict[str, str] = {}

        # Enterprise components
        self.validator = ContentValidator(logger)
        self.moderator = ContentModerator(logger, event_bus, threshold=MODERATION_THRESHOLD)
        self.engagement_tracker = EngagementTracker(logger, state_manager)

        self.logger.info(f"{self.platform.value} skill initialized (Enterprise Mode)")

    def execute(self, message: str, media: Optional[List[str]] = None,
                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute social media posting with enterprise features.

        Args:
            message: Post message/content
            media: Optional list of media paths or URLs
            metadata: Optional metadata for the post

        Returns:
            Result dictionary with success status and data
        """
        execution_id = self._generate_execution_id(message, media)
        metadata = metadata or {}

        self.logger.info(f"Executing {self.platform.value} post (ID: {execution_id})")

        # Check for idempotent execution
        if self._is_already_posted(message, media):
            existing_post_id = self.posted_hashes.get(self._content_hash(message, media))
            self.logger.info(f"Post already exists (idempotent): {existing_post_id}")

            return {
                'success': True,
                'post_id': existing_post_id,
                'status': 'already_posted',
                'platform': self.platform.value,
                'execution_id': execution_id,
                'idempotent': True
            }

        # Enterprise: Content validation
        validation_result = self.validator.validate(message, self.platform.value)
        if not validation_result['valid']:
            error_msg = '; '.join([issue['message'] for issue in validation_result['issues']])
            self._handle_failure(execution_id, f"Validation failed: {error_msg}", metadata)

            return {
                'success': False,
                'error': error_msg,
                'validation': validation_result,
                'platform': self.platform.value,
                'execution_id': execution_id,
                'status': PostStatus.REJECTED.value
            }

        # Enterprise: Content moderation
        moderation_result = self.moderator.moderate(message, media)
        if not moderation_result['approved']:
            error_msg = f"Content blocked by moderation (risk score: {moderation_result['risk_score']})"
            self.logger.warning(f"{error_msg} - Factors: {moderation_result['risk_factors']}")

            # Log moderation block
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type='content_moderation',
                    actor='content_moderator',
                    action='block',
                    resource=f"{self.platform.value}:{execution_id}",
                    result='blocked',
                    metadata=moderation_result
                )

            return {
                'success': False,
                'error': error_msg,
                'moderation': moderation_result,
                'platform': self.platform.value,
                'execution_id': execution_id,
                'status': PostStatus.REJECTED.value
            }

        # Platform-specific validation
        platform_validation = self._validate_inputs(message, media)
        if not platform_validation['valid']:
            self._handle_failure(execution_id, platform_validation['error'], metadata)
            return {
                'success': False,
                'error': platform_validation['error'],
                'platform': self.platform.value,
                'execution_id': execution_id
            }

        # Attempt to post
        try:
            post_result = self._simulate_post(message, media, metadata)

            if post_result['success']:
                # Mark as posted for idempotency
                self._mark_as_posted(message, media, post_result['post_id'])

                # Enterprise: Generate engagement metrics
                engagement_metrics = self.engagement_tracker.generate_metrics(
                    self.platform.value,
                    post_result['post_id'],
                    message
                )
                post_result['engagement'] = engagement_metrics

                # Handle success
                self._handle_success(execution_id, post_result, metadata, validation_result, moderation_result)

                return {
                    'success': True,
                    'post_id': post_result['post_id'],
                    'platform': self.platform.value,
                    'execution_id': execution_id,
                    'url': post_result.get('url'),
                    'timestamp': post_result.get('timestamp'),
                    'engagement': engagement_metrics,
                    'moderation': moderation_result,
                    'status': PostStatus.POSTED.value
                }
            else:
                # Handle failure
                self._handle_failure(execution_id, post_result.get('error', 'Unknown error'), metadata)

                return {
                    'success': False,
                    'error': post_result.get('error'),
                    'platform': self.platform.value,
                    'execution_id': execution_id
                }

        except Exception as e:
            self.logger.error(f"Unexpected error in {self.platform.value} post: {e}", exc_info=True)
            self._handle_failure(execution_id, str(e), metadata)

            return {
                'success': False,
                'error': str(e),
                'platform': self.platform.value,
                'execution_id': execution_id
            }

    @abstractmethod
    def _simulate_post(self, message: str, media: Optional[List[str]],
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate posting to the platform.

        Must be implemented by subclasses.

        Returns:
            Dictionary with success status and post details
        """
        pass

    @abstractmethod
    def _validate_inputs(self, message: str, media: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validate inputs for the specific platform.

        Must be implemented by subclasses.

        Returns:
            Dictionary with 'valid' boolean and optional 'error' message
        """
        pass

    def _generate_execution_id(self, message: str, media: Optional[List[str]]) -> str:
        """Generate unique execution ID"""
        timestamp = datetime.now(UTC).timestamp()
        content = f"{self.platform.value}_{message}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _content_hash(self, message: str, media: Optional[List[str]]) -> str:
        """Generate content hash for idempotency"""
        content = f"{message}_{media or []}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _is_already_posted(self, message: str, media: Optional[List[str]]) -> bool:
        """Check if content was already posted"""
        content_hash = self._content_hash(message, media)
        return content_hash in self.posted_hashes

    def _mark_as_posted(self, message: str, media: Optional[List[str]], post_id: str):
        """Mark content as posted"""
        content_hash = self._content_hash(message, media)
        self.posted_hashes[content_hash] = post_id

    def _handle_success(self, execution_id: str, post_result: Dict[str, Any],
                       metadata: Dict[str, Any], validation_result: Dict[str, Any] = None,
                       moderation_result: Dict[str, Any] = None):
        """Handle successful post with enterprise tracking"""
        # Emit success event
        if self.event_bus:
            self.event_bus.publish('social_post_success', {
                'platform': self.platform.value,
                'post_id': post_result['post_id'],
                'timestamp': post_result.get('timestamp', datetime.now(UTC).isoformat()),
                'metadata': metadata,
                'execution_id': execution_id,
                'engagement': post_result.get('engagement', {}),
                'moderation_score': moderation_result.get('risk_score') if moderation_result else None
            })

        # Audit log
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='social_post',
                actor='autonomous_executor',
                action='post',
                resource=f"{self.platform.value}:{post_result['post_id']}",
                result='success',
                metadata={
                    'platform': self.platform.value,
                    'post_id': post_result['post_id'],
                    'execution_id': execution_id,
                    'engagement': post_result.get('engagement', {}),
                    'moderation': moderation_result,
                    **metadata
                }
            )

        # Generate report
        self._generate_report(execution_id, post_result, metadata, validation_result, moderation_result)

        # Update state metrics
        if self.state_manager:
            self.state_manager.increment_counter(f'successful_posts_{self.platform.value}', 1)

        self.logger.info(f"Successfully posted to {self.platform.value}: {post_result['post_id']}")

    def _handle_failure(self, execution_id: str, error: str, metadata: Dict[str, Any],
                       retry_count: int = 0):
        """Handle failed post"""
        # Emit failure event
        if self.event_bus:
            self.event_bus.publish('social_post_failed', {
                'platform': self.platform.value,
                'error': error,
                'retry_count': retry_count,
                'execution_id': execution_id,
                'metadata': metadata
            })

        # Audit log
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='social_post',
                actor='autonomous_executor',
                action='post',
                resource=f"{self.platform.value}:failed",
                result='failure',
                metadata={
                    'platform': self.platform.value,
                    'error': error,
                    'retry_count': retry_count,
                    'execution_id': execution_id
                }
            )

        # Update failure metrics
        if self.state_manager:
            self.state_manager.increment_counter(f'failed_posts_{self.platform.value}', 1)

        self.logger.error(f"Failed to post to {self.platform.value}: {error}")

    def _generate_report(self, execution_id: str, post_result: Dict[str, Any],
                        metadata: Dict[str, Any], validation_result: Dict[str, Any] = None,
                        moderation_result: Dict[str, Any] = None):
        """Generate enterprise summary report"""
        try:
            timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_dir / f"{self.platform.value}_post_{timestamp}.md"

            # Format engagement metrics
            engagement = post_result.get('engagement', {})
            engagement_section = "\n".join([f"- **{k.title()}**: {v}" for k, v in engagement.items() if k != 'tracked_at'])

            # Format validation issues
            validation_section = "✓ Passed"
            if validation_result and validation_result.get('issues'):
                issues = validation_result['issues']
                warnings = [i for i in issues if i['severity'] == 'warning']
                if warnings:
                    validation_section = "⚠ Passed with warnings:\n" + "\n".join([f"  - {w['message']}" for w in warnings])

            # Format moderation
            moderation_section = "N/A"
            if moderation_result:
                risk_level = moderation_result.get('risk_level', 'unknown')
                risk_score = moderation_result.get('risk_score', 0)
                moderation_section = f"**Risk Level**: {risk_level.upper()} (Score: {risk_score})\n"
                if moderation_result.get('risk_factors'):
                    moderation_section += "**Risk Factors**:\n" + "\n".join([f"- {f}" for f in moderation_result['risk_factors']])

            report_content = f"""# {self.platform.value.title()} Post Report - Enterprise Edition

## Execution Details
- **Execution ID**: {execution_id}
- **Platform**: {self.platform.value}
- **Timestamp**: {datetime.now(UTC).isoformat()}
- **Status**: Success ✓

## Post Information
- **Post ID**: {post_result['post_id']}
- **URL**: {post_result.get('url', 'N/A')}
- **Posted At**: {post_result.get('timestamp', 'N/A')}

## Content
{metadata.get('message', 'N/A')}

## Media
{', '.join(metadata.get('media', [])) if metadata.get('media') else 'None'}

## Enterprise Features

### Content Validation
{validation_section}

### Content Moderation
{moderation_section}

### Engagement Metrics
{engagement_section}

## Performance
- **Execution Time**: {post_result.get('execution_time', 'N/A')}
- **API Response Time**: {post_result.get('api_response_time', 'N/A')}

## Metadata
```json
{json.dumps(metadata, indent=2)}
```

---
*Generated by Social Media Skills Module - Enterprise Edition*
"""

            report_path.write_text(report_content)
            self.logger.info(f"Generated enterprise report: {report_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")

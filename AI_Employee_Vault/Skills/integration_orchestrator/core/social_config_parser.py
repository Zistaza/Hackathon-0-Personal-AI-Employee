#!/usr/bin/env python3
"""
Social Media Config Parser - Gold Tier Core Component
======================================================

Parses social media configuration from markdown files.
Supports multiple formats: YAML frontmatter, inline markers, JSON blocks.

This is business logic extracted from AutonomousExecutor to maintain
separation of concerns (orchestration vs parsing).
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class SocialMediaConfigParser:
    """
    Parse social media configuration from markdown files.

    Supports multiple configuration formats:
    - YAML frontmatter
    - Inline HTML comment markers
    - JSON code blocks
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize parser.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def parse(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Parse social media configuration from file.

        Args:
            filepath: Path to markdown file

        Returns:
            Configuration dictionary or None if no config found
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            # Try YAML frontmatter first
            yaml_config = self._parse_yaml_frontmatter(content)
            if yaml_config and 'social_media' in yaml_config:
                self.logger.debug(f"Parsed YAML config from {filepath.name}")
                return yaml_config['social_media']

            # Try inline markers
            inline_config = self._parse_inline_markers(content)
            if inline_config:
                self.logger.debug(f"Parsed inline config from {filepath.name}")
                return inline_config

            # Try JSON block
            json_config = self._parse_json_block(content)
            if json_config:
                self.logger.debug(f"Parsed JSON config from {filepath.name}")
                return json_config

            return None

        except Exception as e:
            self.logger.error(f"Error parsing {filepath.name}: {e}")
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

    def parse_scheduled_time(self, time_str: str) -> Optional[datetime]:
        """
        Parse scheduled time string to datetime.

        Args:
            time_str: Time string in various formats

        Returns:
            datetime object or None if parsing fails
        """
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

    def extract_message_from_content(self, filepath: Path) -> str:
        """
        Extract message content from markdown file.

        Args:
            filepath: Path to markdown file

        Returns:
            Extracted message or empty string
        """
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

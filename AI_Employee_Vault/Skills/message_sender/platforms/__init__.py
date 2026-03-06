"""
Platform Handlers
=================

Message sending platform handlers.
"""

from .base import BaseMessagePlatform
from .gmail import GmailPlatform
from .whatsapp import WhatsAppPlatform

__all__ = [
    'BaseMessagePlatform',
    'GmailPlatform',
    'WhatsAppPlatform',
]

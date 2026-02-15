"""
Integrations Module — OAuth and third-party service integrations
for Microsoft (Outlook + Calendar) and Google (Gmail + Calendar).
"""

from .oauth_manager import OAuthManager
from .microsoft_integration import MicrosoftIntegration
from .google_integration import GoogleIntegration

__all__ = ["OAuthManager", "MicrosoftIntegration", "GoogleIntegration"]

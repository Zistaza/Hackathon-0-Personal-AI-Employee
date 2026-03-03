"""
Social Media Skills Integration Patch
======================================

This patch integrates the social media skills module into the Gold Tier orchestrator.

Apply this patch to index.py:
"""

# ============================================================================
# STEP 1: Add import at the top of index.py (after line 135)
# ============================================================================

IMPORT_ADDITION = """
# Social Media Skills Integration
try:
    from social_media_skills import register_social_skills
    SOCIAL_SKILLS_AVAILABLE = True
except ImportError:
    SOCIAL_SKILLS_AVAILABLE = False
"""

# Add after line 135 (after "import shutil")


# ============================================================================
# STEP 2: Add social_adapter attribute to __init__ (after line 1886)
# ============================================================================

INIT_ATTRIBUTE_ADDITION = """
        self.social_adapter = None  # Social Media Skills Adapter
"""

# Add after line 1886 (after "self.autonomous_executor = None")


# ============================================================================
# STEP 3: Add registration method (after _discover_skills method, around line 2057)
# ============================================================================

NEW_METHOD = """
    def _register_social_media_skills(self):
        \"\"\"Register social media skills with SkillRegistry\"\"\"
        if not SOCIAL_SKILLS_AVAILABLE:
            self.logger.warning("Social media skills module not available")
            return

        try:
            reports_dir = self.base_dir / "Reports" / "Social"
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Register skills and get adapter
            self.social_adapter = register_social_skills(
                skill_registry=self.skill_registry,
                logger=self.logger,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                retry_queue=self.retry_queue,
                reports_dir=reports_dir,
                mcp_server=None  # Can be added later if MCP integration needed
            )

            self.logger.info("Social media skills registered successfully")
            self.logger.info(f"Available platforms: {self.social_adapter.list_platforms()}")

        except Exception as e:
            self.logger.error(f"Failed to register social media skills: {e}", exc_info=True)
"""

# Add after _discover_skills method (around line 2057)


# ============================================================================
# STEP 4: Call registration in _setup_gold_tier_components (after line 2030)
# ============================================================================

SETUP_CALL_ADDITION = """
        # Register social media skills
        self._register_social_media_skills()
"""

# Add after line 2030 (after "self._discover_skills()")


# ============================================================================
# STEP 5: Add helper method to access social adapter (optional, for convenience)
# ============================================================================

HELPER_METHOD = """
    def post_to_social_media(self, platform: str, message: str,
                            media: List[str] = None, metadata: Dict = None):
        \"\"\"
        Post to social media platform.

        Args:
            platform: Platform name ('facebook', 'instagram', 'twitter_x')
            message: Post message
            media: Optional media files
            metadata: Optional metadata

        Returns:
            Result dictionary
        \"\"\"
        if not self.social_adapter:
            return {
                'success': False,
                'error': 'Social media skills not initialized'
            }

        return self.social_adapter.post(platform, message, media, metadata)
"""

# Add as a new method in IntegrationOrchestrator class


# ============================================================================
# Summary of Changes
# ============================================================================

SUMMARY = """
INTEGRATION SUMMARY
===================

Changes to index.py:

1. Import Statement (after line 135):
   - Import register_social_skills from social_media_skills module
   - Add SOCIAL_SKILLS_AVAILABLE flag

2. __init__ Attribute (after line 1886):
   - Add self.social_adapter = None

3. New Method _register_social_media_skills() (after line 2057):
   - Creates Reports/Social directory
   - Calls register_social_skills() with orchestrator components
   - Stores SocialMCPAdapter instance
   - Logs available platforms

4. Call in _setup_gold_tier_components() (after line 2030):
   - Call self._register_social_media_skills()

5. Optional Helper Method post_to_social_media():
   - Convenience method for posting to social media
   - Can be used in workflows and event handlers

Result:
- FacebookSkill, InstagramSkill, TwitterXSkill automatically registered
- Available in SkillRegistry as 'social_facebook', 'social_instagram', 'social_twitter_x'
- SocialMCPAdapter initialized with EventBus, AuditLogger, RetryQueue
- Skills available for autonomous execution
- Reports generated in Reports/Social/
- No code duplication - uses existing implementation
"""

print(SUMMARY)

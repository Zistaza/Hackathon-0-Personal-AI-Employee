#!/bin/bash
# Social Media Skills - Verification Script
# Run this to verify the migration was successful

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Social Media Skills Migration - Verification Script          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PASSED=0
FAILED=0

# Test 1: Check folder structure
echo "📁 Test 1: Checking folder structure..."
if [ -d "Skills/facebook_post_skill" ] && [ -d "Skills/instagram_post_skill" ] && [ -d "Skills/twitter_post_skill" ]; then
    echo "   ✅ All skill folders exist"
    ((PASSED++))
else
    echo "   ❌ Missing skill folders"
    ((FAILED++))
fi

# Test 2: Check shared components
echo "📚 Test 2: Checking shared components..."
if [ -f "Skills/integration_orchestrator/social_media_common.py" ]; then
    echo "   ✅ social_media_common.py exists"
    ((PASSED++))
else
    echo "   ❌ social_media_common.py missing"
    ((FAILED++))
fi

# Test 3: Check wrapper
echo "🔄 Test 3: Checking backward compatibility wrapper..."
if [ -f "Skills/integration_orchestrator/social_media_skills.py" ]; then
    echo "   ✅ social_media_skills.py exists"
    ((PASSED++))
else
    echo "   ❌ social_media_skills.py missing"
    ((FAILED++))
fi

# Test 4: Check skill files
echo "📄 Test 4: Checking skill files..."
SKILL_FILES_OK=true
for skill in facebook_post_skill instagram_post_skill twitter_post_skill; do
    if [ ! -f "Skills/$skill/index.py" ] || [ ! -f "Skills/$skill/skill.json" ] || [ ! -f "Skills/$skill/config.json" ]; then
        SKILL_FILES_OK=false
        break
    fi
done

if [ "$SKILL_FILES_OK" = true ]; then
    echo "   ✅ All skill files present"
    ((PASSED++))
else
    echo "   ❌ Some skill files missing"
    ((FAILED++))
fi

# Test 5: Test Python imports
echo "🐍 Test 5: Testing Python imports..."
cd Skills/integration_orchestrator
if python3 -c "from social_media_skills import FacebookSkill, InstagramSkill, TwitterXSkill, SocialMCPAdapter" 2>/dev/null; then
    echo "   ✅ All imports successful"
    ((PASSED++))
else
    echo "   ❌ Import errors detected"
    ((FAILED++))
fi
cd "$SCRIPT_DIR"

# Test 6: Test Facebook skill
echo "📘 Test 6: Testing Facebook skill..."
cd Skills/facebook_post_skill
if python3 index.py --test >/dev/null 2>&1; then
    echo "   ✅ Facebook skill works"
    ((PASSED++))
else
    echo "   ❌ Facebook skill failed"
    ((FAILED++))
fi
cd "$SCRIPT_DIR"

# Test 7: Test Instagram skill
echo "📷 Test 7: Testing Instagram skill..."
cd Skills/instagram_post_skill
if python3 index.py --test >/dev/null 2>&1; then
    echo "   ✅ Instagram skill works"
    ((PASSED++))
else
    echo "   ❌ Instagram skill failed"
    ((FAILED++))
fi
cd "$SCRIPT_DIR"

# Test 8: Test Twitter skill
echo "🐦 Test 8: Testing Twitter skill..."
cd Skills/twitter_post_skill
if python3 index.py --test >/dev/null 2>&1; then
    echo "   ✅ Twitter skill works"
    ((PASSED++))
else
    echo "   ❌ Twitter skill failed"
    ((FAILED++))
fi
cd "$SCRIPT_DIR"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFICATION RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASSED/8"
echo "Failed: $FAILED/8"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Migration successful!"
    echo ""
    echo "Next steps:"
    echo "  1. Review documentation: SOCIAL_MEDIA_MIGRATION_COMPLETE.md"
    echo "  2. Test skills manually if needed"
    echo "  3. Update any custom code that imports these skills"
    echo "  4. Consider committing changes to git"
    exit 0
else
    echo "⚠️  Some tests failed. Please review the errors above."
    exit 1
fi

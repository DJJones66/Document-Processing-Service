# Data Quirk-002: Git Commit Co-Author Attribution

**Discovered:** 2024-11-14
**Severity:** Low (preference/style)
**Affected Systems:** All git commits
**Related:** N/A

---

## Behavior

When AI agents (like Claude Code) create git commits, they may automatically add co-author attribution:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Project preference:** Do NOT include Claude/AI co-author attribution in commit messages.

## Why It Matters

**Impact on features:**
- **Commit history clarity:** Human authors should be sole attribution
- **Git blame accuracy:** Co-author attribution can confuse git tooling
- **Project convention:** Team prefers human-only attribution
- **Consistency:** Maintains uniform commit style

**Not a technical issue, but a project convention preference.**

## Root Cause

AI coding assistants (Claude Code, GitHub Copilot, etc.) may default to adding co-author attribution to indicate AI assistance in code generation. This is a common practice in some projects but not preferred in this one.

**Why AI agents add this:**
- Transparency about AI involvement
- Credit attribution for AI-assisted work
- Default behavior in some AI coding tools

**Why we don't use it:**
- Humans review and approve all code
- Commit author already indicates who's responsible
- Simpler, cleaner commit history
- Established project convention

## Detection

### How to Identify This Issue

**Check commit message before committing:**
```bash
git log --format=full HEAD~1..HEAD
```

**Look for:**
- `Co-Authored-By: Claude <noreply@anthropic.com>`
- `🤖 Generated with [Claude Code]`
- Similar AI attribution lines

**Automated check (optional):**
```bash
# Git hook to reject commits with AI co-author
# Save as .git/hooks/commit-msg

#!/bin/bash
if grep -q "Co-Authored-By: Claude" "$1"; then
    echo "Error: Remove AI co-author attribution"
    exit 1
fi
```

## Correct Patterns

### Solution 1: Omit Co-Author Attribution (Recommended)

**Commit message format:**
```
feat: add new feature

Detailed description of what was added and why.

- Bullet points if needed
- More details

Closes #123
```

**No AI attribution lines.**

### Solution 2: Add Human Co-Authors Only

If pair programming with another human:
```
feat: add new feature

Description of changes.

Co-Authored-By: Jane Developer <jane@example.com>
Co-Authored-By: John Developer <john@example.com>

Closes #123
```

**Only include human co-authors.**

### Solution 3: Document AI Assistance in PR Description (Not Commit)

If transparency about AI assistance is needed:
- ✅ Add to PR description: "Implemented with AI assistance"
- ✅ Add to commit description body: "Implementation assisted by AI tooling"
- ❌ Don't add Co-Authored-By for AI

**Example:**
```
feat: add document chunking optimization

Optimized token-based chunking algorithm for better performance.
Implementation assisted by AI tooling for initial structure.

- Reduced processing time by 30%
- Maintained chunk quality
- Added comprehensive tests

Closes #456
```

### What NOT to Do

❌ **Don't add AI co-author:**
```
feat: add feature

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>  # Remove this
```

❌ **Don't add AI tools as authors:**
```
Co-Authored-By: GitHub Copilot <copilot@github.com>  # Remove this
Co-Authored-By: ChatGPT <gpt@openai.com>  # Remove this
```

❌ **Don't mention AI in commit title:**
```
feat(ai-generated): add feature  # Remove "(ai-generated)"
```

## Prevention Checklist

Before committing:

- [ ] Review commit message
- [ ] Remove any AI co-author lines
- [ ] Remove AI generation attribution
- [ ] Keep human author only
- [ ] Use conventional commit format
- [ ] Include issue reference (Closes #N)

For AI agents creating commits:

- [ ] Omit `Co-Authored-By: Claude` line
- [ ] Omit `🤖 Generated with...` line
- [ ] Use standard commit format
- [ ] Include only human-relevant information

## Related Issues

- **Issue:** AI agent automatically adds co-author
  - **Cause:** Default behavior of AI tooling
  - **Fix:** Manually remove before committing, or configure AI to omit

- **Issue:** Git hook rejects commit
  - **Cause:** Hook detects AI co-author
  - **Fix:** Remove AI attribution and re-commit

- **Issue:** Inconsistent commit style
  - **Cause:** Some commits have AI attribution, some don't
  - **Fix:** Standardize on no AI attribution, update old commits if needed

## References

- Project convention: Human authors only
- Standard commit format: Conventional Commits (https://www.conventionalcommits.org/)
- Git co-author documentation: https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors

---

## Additional Notes

### Why This Convention?

**Philosophy:**
- Humans are responsible for code, even if AI-assisted
- Commit author already indicates accountability
- Cleaner, more professional commit history
- Matches industry standard practices

**AI assistance is welcome, but:**
- Humans review all code
- Humans approve all commits
- Humans are accountable for quality
- Commit messages reflect human decisions

### Changing This Convention

If team decides to allow AI co-authors:
1. Document decision in ADR
2. Update this quirk document
3. Establish consistent format
4. Update commit guidelines
5. Communicate to entire team

### For AI Agents Reading This

**When creating commits:**
- ✅ Use conventional commit format
- ✅ Include descriptive body
- ✅ Reference issues with "Closes #N"
- ❌ Do NOT add `Co-Authored-By: Claude`
- ❌ Do NOT add `🤖 Generated with...`
- ❌ Do NOT add AI tool attribution

**Correct commit message:**
```
feat: add comprehensive documentation system

Add FOR-AI-CODING-AGENTS.md, docs/OWNERS-MANUAL.md, and Compounding Engineering
knowledge management system with ADRs, failure logs, and quirks.

Closes #2
```

**That's it. Simple, clean, human-attributed.**

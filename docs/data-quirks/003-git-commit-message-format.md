# Data Quirk-003: Git Commit Message Format Convention

**Discovered:** 2024-11-14
**Severity:** Low (convention/style)
**Affected Systems:** All git commits
**Related:** Data-Quirk-002 (Git co-author attribution)

---

## Behavior

**Project convention:** Git commit messages must follow proper format with:
1. **Title (subject line):** ≤50 characters
2. **Blank line**
3. **Body:** Detailed description with proper line wrapping

This follows industry-standard git commit conventions.

## Why It Matters

**Impact:**
- **Git log readability:** Short titles display properly in `git log --oneline`
- **GitHub UI:** Titles display correctly in PR lists, commit history
- **Git blame:** One-line display shows meaningful summary
- **Professional standard:** Matches conventions used across open source
- **Tool compatibility:** Many git tools expect this format

**Examples of issues with incorrect format:**
```bash
# ❌ Bad: Long title gets truncated in git log
git log --oneline
abc123 refactor: rename CLAUDE.md to FOR-AI-CODING-AGENTS.md for broader AI agent compatibility and update all references across...

# ✅ Good: Clear, concise title
git log --oneline
abc123 refactor: rename CLAUDE.md to FOR-AI-CODING-AGENTS.md
```

## Root Cause

**Why this matters:**
- Git designed for 50-char subject lines (GitHub truncates at 72)
- Body provides detailed context that doesn't fit in title
- Blank line separates title from body (required by git format)
- Many git tools parse commits expecting this format

**Common mistakes:**
- Writing entire commit message in subject line
- Including detailed explanations in subject
- Missing blank line between subject and body
- Subject line >72 characters (hard truncation in many UIs)

## Detection

### How to Identify Issues

**Check commit message format:**
```bash
# View commit message
git log -1 --format=full

# Check subject line length
git log -1 --pretty=format:'%s' | wc -c
```

**Look for:**
- Subject line >50 characters (warning threshold)
- Subject line >72 characters (hard limit)
- Missing blank line after subject
- Entire message in subject line

**Automated check (pre-commit hook):**
```bash
#!/bin/bash
# Save as .git/hooks/commit-msg

MSG_FILE=$1
SUBJECT=$(head -n1 "$MSG_FILE")
SUBJECT_LEN=${#SUBJECT}

if [ $SUBJECT_LEN -gt 72 ]; then
    echo "Error: Subject line too long ($SUBJECT_LEN chars, max 72)"
    exit 1
fi

if [ $SUBJECT_LEN -gt 50 ]; then
    echo "Warning: Subject line >50 chars ($SUBJECT_LEN), consider shortening"
fi
```

## Correct Patterns

### Format: Standard Git Commit

**Command format:**
```bash
git commit -m "title: short summary (≤50 chars)" -m "Detailed body

Explanation of changes with proper formatting.

- Bullet points
- Additional details

Closes #123"
```

**Message format:**
```
<type>: <short summary (≤50 chars)>
<blank line>
<detailed description>
<blank line>
<footer: references, breaking changes, etc.>
```

**Key point:** Use separate `-m` flags for title and body!
- First `-m`: Title only (≤50 chars)
- Second `-m`: Body (git adds blank line automatically)

### Example: Correct Format

```
refactor: rename CLAUDE.md to FOR-AI-CODING-AGENTS.md

Rename main documentation file to be inclusive of all AI coding agents
(Claude Code, GitHub Copilot, Cursor, Codeium, etc.) rather than
Claude-specific.

Changes:
- Renamed: CLAUDE.md → FOR-AI-CODING-AGENTS.md
- Updated all references across documentation
- Added testing section
- Enhanced README with AI agents quick start

Rationale: Generic name improves discoverability and signals support
for multiple AI coding assistants.

Files modified: 7 files updated
```

**Key elements:**
- ✅ Title: 53 chars (acceptable, under 72)
- ✅ Blank line after title
- ✅ Body with detailed explanation
- ✅ Organized with bullet points
- ✅ Footer with metadata

### Commit Types (Conventional Commits)

```
feat:     New feature
fix:      Bug fix
refactor: Code refactoring (no behavior change)
docs:     Documentation only
style:    Formatting, missing semicolons, etc.
test:     Adding tests
chore:    Maintenance tasks
perf:     Performance improvements
ci:       CI/CD changes
build:    Build system changes
```

### Title Writing Guidelines

**Do:**
- ✅ Use imperative mood ("add" not "added", "fix" not "fixed")
- ✅ Be specific but concise
- ✅ Include type prefix (feat:, fix:, docs:, etc.)
- ✅ Start with lowercase after colon
- ✅ No period at end

**Don't:**
- ❌ Use past tense ("added feature" → "add feature")
- ❌ Be vague ("update stuff" → "update authentication flow")
- ❌ Exceed 50 chars if possible, never exceed 72
- ❌ Include implementation details in title
- ❌ Use punctuation at end

### Body Writing Guidelines

**Do:**
- ✅ Wrap at 72 characters per line
- ✅ Explain what and why (not how - code shows how)
- ✅ Use bullet points for lists
- ✅ Include context for the change
- ✅ Reference issues/tickets

**Don't:**
- ❌ Repeat information from title
- ❌ Write paragraphs >72 chars wide
- ❌ Include code snippets in body (use PR description instead)

## Examples: Good vs Bad

### ❌ Bad: Everything in subject line

```
docs: add comprehensive documentation and Compounding Engineering system including CLAUDE.md rename to FOR-AI-CODING-AGENTS.md, OWNERS-MANUAL.md operations guide with 16 sections, and complete knowledge management system
```

**Problems:**
- 242 characters (way over limit)
- Gets truncated in git log
- Hard to scan quickly
- No details in body

### ✅ Good: Proper format

```
docs: add comprehensive documentation and Compounding system

Add complete documentation suite including:
- FOR-AI-CODING-AGENTS.md: Architecture & development guide (15KB)
- OWNERS-MANUAL.md: Operations manual (40KB, 16 sections)
- Compounding Engineering: Knowledge management system

Includes ADRs, failure logs, data quirks, and integration docs.

Closes #2
```

**Benefits:**
- Title: 60 chars (under 72)
- Body provides full details
- Organized with bullets
- References issue

### ❌ Bad: No blank line, past tense

```
Added documentation
Updated all the files and added comprehensive documentation including the owner's manual and architecture guide.
```

**Problems:**
- Past tense ("Added" should be "Add")
- No blank line separator
- Body not wrapped properly
- Vague title

### ✅ Good: Imperative mood, proper format

```
docs: add owner's manual and architecture guide

Add comprehensive operational and development documentation:
- OWNERS-MANUAL.md with 16 sections covering ops, deployment,
  monitoring, troubleshooting, and disaster recovery
- FOR-AI-CODING-AGENTS.md with architecture patterns and
  development workflows

Provides complete guidance for maintainers and developers.
```

**Benefits:**
- Imperative mood
- Clear blank line
- Wrapped at 72 chars
- Specific details in body

## Prevention Checklist

Before committing:

- [ ] Subject line ≤50 chars (ideal) or ≤72 chars (max)
- [ ] Subject uses imperative mood ("add", "fix", "update")
- [ ] Subject includes type prefix (feat:, fix:, docs:, etc.)
- [ ] Subject starts with lowercase after colon
- [ ] Subject has no period at end
- [ ] Blank line after subject
- [ ] Body provides detailed explanation
- [ ] Body lines wrapped at 72 characters
- [ ] Body explains what and why (not how)
- [ ] References issues/PRs if applicable (Closes #N)

For AI agents creating commits:

- [ ] Generate concise subject line (≤50 chars)
- [ ] Always include blank line after subject
- [ ] Put detailed explanation in body
- [ ] Use conventional commit format
- [ ] Include issue references

## Related Issues

- **Issue:** Commit message truncated in GitHub UI
  - **Cause:** Subject line >72 characters
  - **Fix:** Shorten subject, move details to body

- **Issue:** `git log --oneline` unreadable
  - **Cause:** Long subject lines
  - **Fix:** Keep subjects ≤50 chars

- **Issue:** Git tools don't parse commit properly
  - **Cause:** Missing blank line between subject and body
  - **Fix:** Always include blank line

## References

- Conventional Commits: https://www.conventionalcommits.org/
- Git commit message guide: https://chris.beams.io/posts/git-commit/
- Linux kernel commit guide: https://www.kernel.org/doc/html/latest/process/submitting-patches.html
- Angular commit convention: https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit

---

## Additional Notes

### Quick Reference

**Template:**
```
<type>: <summary ≤50 chars>

Detailed explanation of the change, wrapped at 72 characters.
Explain what and why, not how.

- Bullet points are helpful
- For listing multiple changes
- Keep them concise

Closes #123
```

### For AI Agents Reading This

**When creating commits:**

1. **Generate short title:**
   - Start with type (feat, fix, docs, refactor, etc.)
   - Summarize change in ≤50 chars
   - Use imperative mood

2. **Add blank line:**
   - Mandatory separator

3. **Write detailed body:**
   - Explain what changed and why
   - Wrap at 72 characters
   - Use bullets for lists
   - Include context

4. **Add footer:**
   - Reference issues (Closes #N)
   - Note breaking changes if any

**Example generation:**
```
docs: add testing documentation

Add comprehensive testing section to FOR-AI-CODING-AGENTS.md
including test structure, running tests, and available samples.

Changes:
- Test structure documentation
- Manual testing instructions
- Sample files location
- Note about pytest integration (pending)

Improves developer onboarding and testing clarity.
```

**Git command format:**
```bash
git commit -m "docs: add testing documentation" -m "Add comprehensive testing section to FOR-AI-CODING-AGENTS.md.

Changes:
- Test structure documentation
- Manual testing instructions
- Sample files location

Improves developer onboarding."
```

**That's it. Use two `-m` flags: one for title, one for body.**

---

## Self-Test

**Scenario:** You added a new feature with 3 files changed and 200 lines added.

**❌ Wrong:**
```
Added new authentication feature with API key support and JWT tokens and updated all the middleware and added tests
```

**✅ Right:**
```
feat: add API key and JWT authentication

Implement dual authentication system supporting both API keys
and JWT tokens. Updates middleware to validate credentials
against environment configuration.

Changes:
- SimpleAuthService for credential validation
- AuthenticateUserUseCase for auth flow
- Authentication middleware with header checks
- Tests for both auth methods

Closes #42
```

**If you wrote the ✅ version automatically, you're following the convention correctly!**

# Documentation Directory

This directory contains **Compounding Engineering** knowledge for the BrainDrive Document AI project.

## 📚 What is Compounding Engineering?

A documentation philosophy where every development session leaves behind structured knowledge for future developers and AI agents, multiplying productivity over time.

**Core Idea:** Don't just write code—compound knowledge by documenting decisions, failures, and discoveries.

---

## 🗂️ Directory Structure

```
docs/
├── README.md                    # This file
├── AI-AGENT-GUIDE.md           # Complete guide for AI coding agents
├── COMPOUNDING-SETUP-COMPLETE.md # Verification checklist
│
├── decisions/                   # Architecture Decision Records (ADRs)
│   ├── 000-template.md         # Template for new ADRs
│   └── 001-docling-for-document-processing.md
│
├── failures/                    # What NOT to do (lessons learned)
│   └── (empty - ready for future learnings)
│
├── data-quirks/                 # Non-obvious data/system behavior
│   └── 001-windows-huggingface-symlinks.md
│
├── integrations/                # External system documentation
│   └── docling.md
│
└── docker_deployment.md         # Pre-existing deployment docs
```

---

## 🚀 Quick Start

### For AI Agents

**Read this first:** [`AI-AGENT-GUIDE.md`](./AI-AGENT-GUIDE.md)

**Before coding:**
```bash
grep -r "keyword" docs/decisions/   # Past decisions
grep -r "keyword" docs/failures/    # Known mistakes
grep -r "keyword" docs/data-quirks/ # Known gotchas
```

**After coding:**
- Made architectural decision? → Create ADR
- Hit error/mistake (>1 hour)? → Create failure log
- Discovered quirk? → Document it
- Integrated service? → Create integration doc

### For Human Developers

**Onboarding:**
1. Read `../CLAUDE.md` - Project architecture and patterns
2. Read `AI-AGENT-GUIDE.md` - Documentation philosophy
3. Browse `decisions/` - Understand architectural choices
4. Browse `data-quirks/` - Learn system gotchas
5. Browse `integrations/` - Understand external services

**During development:**
- Check relevant docs before implementing
- Document decisions as you make them
- Document failures to help others avoid them

---

## 📝 Document Types

### 1. Architecture Decision Records (ADRs)
**Purpose:** Document why architectural choices were made

**When to create:**
- Chose between 2+ implementation approaches
- Selected a library/framework
- Changed core architecture

**Template:** [`decisions/000-template.md`](./decisions/000-template.md)

**Example:** [`decisions/001-docling-for-document-processing.md`](./decisions/001-docling-for-document-processing.md)

### 2. Failure Logs
**Purpose:** Document mistakes to prevent repetition

**When to create:**
- Made incorrect assumption (wasted >1 hour)
- Built feature that didn't work
- Used wrong approach (later fixed)

**Template:** See AI-AGENT-GUIDE.md

**Example:** (None yet - first failure will be documented here)

### 3. Data Quirks
**Purpose:** Document non-obvious behavior

**When to create:**
- Data format different than expected
- System behaves unexpectedly
- Edge cases discovered

**Template:** See AI-AGENT-GUIDE.md

**Example:** [`data-quirks/001-windows-huggingface-symlinks.md`](./data-quirks/001-windows-huggingface-symlinks.md)

### 4. Integration Docs
**Purpose:** Document external system integrations

**When to create:**
- Connected new API/service
- Vendor-specific quirks discovered
- Authentication/setup completed

**Template:** See AI-AGENT-GUIDE.md

**Example:** [`integrations/docling.md`](./integrations/docling.md)

---

## 💡 Philosophy

> **Every documented decision/failure saves 5-10 hours of future work.**

**Think:** "Six months from now, someone (human or AI) will work on this. What do they need to know to avoid my mistakes and build on my success?"

**That's compounding engineering.** 🚀

---

## ✅ Current Knowledge Base

### Decisions
- **ADR-001:** Use Docling for multi-format document processing

### Data Quirks
- **Quirk-001:** Windows HuggingFace symlink permission issues

### Integrations
- **Docling:** Complete reference for document processing library

### Failures
- (None yet - first mistake will be documented here)

---

## 🎯 Success Metrics

**Knowledge compounds when:**
- New developers reference docs instead of asking questions
- AI agents check docs before implementing
- Mistakes are documented and not repeated
- Architectural context is preserved across sessions

**ROI:**
- **ADR-001:** Saves 2-3 hours of library research per developer
- **Quirk-001:** Saves 4-6 hours of Windows debugging per developer
- **Integration: Docling:** Saves 1-2 hours reading upstream docs

**Total:** 7-11 hours saved per developer × number of developers = massive ROI

---

## 🔗 Related Files

- [`../CLAUDE.md`](../CLAUDE.md) - Main project documentation
- [`AI-AGENT-GUIDE.md`](./AI-AGENT-GUIDE.md) - Complete guide for AI agents
- [`COMPOUNDING-SETUP-COMPLETE.md`](./COMPOUNDING-SETUP-COMPLETE.md) - Setup verification

---

## 📖 Further Reading

**Key Principles:**
1. Document discoveries, not processes
2. Be concise (1-2 pages max)
3. Show code examples
4. Link everything
5. Update when wrong

**See:** [`AI-AGENT-GUIDE.md`](./AI-AGENT-GUIDE.md) for complete instructions, examples, and self-test scenarios.

---

**Last Updated:** 2024-11-14
**Status:** ✅ Active - Compounding knowledge with every session

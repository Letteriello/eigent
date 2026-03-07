---
name: wrap-up
description: |
  Autonomous session wrap-up checklist with versioning, memory organization, and self-improvement.
  Use this skill when the user wants to end the current session with automatic versioning,
  memory categorization, and auto-improvement. Triggers: 'wrap up', 'close session', 'end session',
  'wrap things up', 'close out this task', or explicit /wrap-up invocation.
  This skill operates autonomously without asking for user approval at each step.
triggers:
  - wrap up
  - close session
  - end session
  - wrap things up
  - close out this task
  - /wrap-up
---

# Wrap-Up: Autonomous Session Checklist

This skill executes an autonomous end-of-session checklist in 4 phases without interrupting the developer.

---

## Phase 1: Ship It

Execute this first to ensure all work is versioned and published.

### 1.1 Git Status and Versioning

Run `git status` to check for uncommitted changes. If there are changes:
- Auto-commit to main branch with descriptive message
- Run `git push` to the configured remote

### 1.2 File Placement Check

Check for loose files that need organization:

1. **Documentation files in root**: `.md` or `.pdf` files in project root should be moved to `docs/`
2. **Naming conventions**: Validate files follow project standards

For each file found out of place:
- Execute the move automatically
- Document the action in output

### 1.3 Deploy Script

If a deploy script is configured in the project (check package.json scripts or deploy files):
- Run the deploy script

### 1.4 Task Cleanup

If a task list exists (TaskList):
- Mark all items with status 'completed' as 'done'
- Identify pending tasks and document for next session

---

## Phase 2: Remember It

Review session learnings and categorize memory at appropriate levels.

### 2.1 Memory Levels

Review conversation and categorize learnings:

| Level | When to use |
|-------|-------------|
| **Auto memory** | Debug patterns, project quirks, unexpected behaviors |
| **CLAUDE.md** | Permanent conventions, architecture decisions, fixed structures |
| **.claude/rules/** | Focused instructions for specific topics/paths (use frontmatter `paths:`) |
| **CLAUDE.local.md** | Ephemeral notes, WIP, sandbox credentials, temporary local context |

### 2.2 Review Process

For each learning identified:
1. Determine the appropriate level
2. If file for that level doesn't exist, create it
3. Add memory in appropriate format

### 2.3 Auto Memory (if applicable)

If there are new memories for auto memory:
- Edit `~/.claude/projects/[project-name]/memory/MEMORY.md` or create thematic files

---

## Phase 3: Review & Apply

Analyze conversation for patterns that can be improved.

### 3.1 Failure Analysis

Look for:

| Category | What to look for |
|----------|------------------|
| **Skill gaps** | Situations where a skill would exist but wasn't used, or where a skill would be useful |
| **Friction** | Repetitive manual steps that could be automated |
| **Knowledge** | Context gaps that caused confusion or rework |

### 3.2 Auto-Apply Fixes

For each problem identified:
1. Write the fix directly to appropriate file (CLAUDE.md, rules, etc.)
2. Apply immediately - don't ask permission

### 3.3 Consolidated Output

At the end, present:

```
## Findings (applied)
- [Item 1]: Fix applied to [file]
- [Item 2]: Fix applied to [file]

## No action needed
- [Item that doesn't require action]
```

---

## Phase 4: Publish It

Scan session log for material worth publishing.

### 4.1 Milestone Identification

Look for:
- Difficult technical solutions overcome
- Important codebase discoveries
- Significant bug fixes
- New features implemented

### 4.2 Draft Creation

If there's sufficient material:
1. Create a post draft in appropriate format
2. Save to drafts folder (docs/drafts/ or similar)
3. Include:
   - Descriptive title
   - Problem context
   - Implemented solution
   - Relevant code (if applicable)

### 4.3 Output

If there's no material to publish:
```
Nothing worth publishing from this session.
```

If there is material:
```
Published: [file path]
```

---

## Output Format

The skill should produce structured output showing progress in each phase:

```
=== Wrap-Up Session ===
[Timestamp]

--- Phase 1: Ship It ---
✓ Git status checked
✓ Changes committed and pushed
✓ File placement validated
✓ Tasks cleaned up

--- Phase 2: Remember It ---
✓ Memories categorized:
  - [level]: [topic]

--- Phase 3: Review & Apply ---
[Findings applied / No action needed]

--- Phase 4: Publish It ---
[Publication or "Nothing worth publishing"]

=== Complete ===
```

---

## Implementation Notes

- This skill executes autonomously without AskUserQuestion
- All fixes are applied immediately
- Output is informative but not blocking
- If a phase fails, continue to the next and document the error

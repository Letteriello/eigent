# Wrap-Up Plugin

Autonomous session wrap-up checklist for Claude Code.

## Features

- **Phase 1: Ship It** - Git status, auto-commit, file placement validation, deploy scripts, task cleanup
- **Phase 2: Remember It** - Categorize session learnings into Auto memory, CLAUDE.md, .claude/rules/, or CLAUDE.local.md
- **Phase 3: Review & Apply** - Analyze for skill gaps, friction, and knowledge gaps; auto-apply fixes
- **Phase 4: Publish It** - Scan for publishable milestones and create drafts

## Installation

This plugin is not yet published to the marketplace. To test locally:

```bash
# Clone or copy to your plugins directory
cp -r wrap-up ~/.claude/plugins/user-plugins/
```

Then restart Claude Code or use:

```bash
cc --plugin-dir ~/.claude/plugins/user-plugins/wrap-up
```

## Usage

Trigger the wrap-up skill with any of these phrases:

- `/wrap-up`
- "wrap up"
- "close session"
- "end session"
- "wrap things up"
- "close out this task"

The skill executes autonomously without prompting for confirmation at each step.

## Requirements

- Claude Code with plugin support
- Git repository (for Phase 1)
- Optional: TaskList for task cleanup

## License

MIT

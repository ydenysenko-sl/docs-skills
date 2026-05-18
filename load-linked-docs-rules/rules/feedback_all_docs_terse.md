---
name: all-docs-must-be-terse
description: "All documentation Claude writes — design notes, READMEs, skill artifacts, plans, requirements — must be terse; user-stated explicit rule"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d0def4c4-aaa5-4efb-a89d-0673d74fe28e
---

All documentation Claude produces for the user must be terse. Not a hint — an explicit rule.

**Why:** user-stated, reinforced repeatedly during the linked-docs skill design session. Consistent with [[feedback_requirements_delta_terse]] but broader in scope (every doc, not just one file type).

**How to apply:**
- Drop softening words, hedges, restatements.
- Prefer one line over two; one phrase over a sentence.
- Inline small things; don't break a clause across multiple bullets.
- No "Note that...", "It's worth mentioning...", "In other words..." preambles.
- No closing summaries that restate the body.
- Cut every word that doesn't carry information.
- Pseudocode and bullet lists over prose where the fact is structural.
- When in doubt, ship the shorter version.

Applies to: markdown, plans, brainstorming output, skill artifacts (objects/flows/contracts), commit messages, doc comments, README snippets, any user-facing text.

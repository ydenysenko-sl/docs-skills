---
name: load-linked-docs-rules
description: Use when the user wants to apply the linked-docs documentation conventions in the current workspace's memory so future sessions follow them automatically. Copies the seven canonical rule memory files into the workspace's memory directory and adds index entries to MEMORY.md. Idempotent — running it twice overwrites the rule files and skips duplicate index lines.
---

# Load Linked Docs Rules

Apply the seven linked-docs documentation rules to the current workspace's memory. Each rule is a feedback-type memory entry that future sessions in this workspace read on session start.

Pairs with the `linked-docs` skill (the rulebook). The rulebook tells you *how* to write docs; these memory entries make Claude *remember* the conventions across sessions even when the rulebook isn't loaded.

## When to invoke

- User says "load the linked-docs rules into memory", "apply the docs conventions globally for this workspace", "set up linked-docs memory entries", or similar.
- Starting a new workspace where the linked-docs convention will apply.
- After clearing memory and wanting to restore the docs ruleset.

## Steps

1. **Determine the target memory directory.** The current workspace's memory lives at:

   ```
   ~/.claude/projects/<sanitized-cwd>/memory/
   ```

   where `<sanitized-cwd>` is the absolute current working directory with every `/` replaced by `-` (and a leading `-`). For example, CWD `/Users/alice/work/myrepo` → `-Users-alice-work-myrepo`. Compute this with shell: `printf -- '-%s\n' "$(pwd | sed 's|/|-|g')" | sed 's|^--|-|'` or use `pwd | tr '/' '-'`.

2. **Create the directory if missing**: `mkdir -p <memory-dir>`.

3. **Copy each rule file** from this skill's `rules/` folder into the target memory dir. Overwrites any existing rule files with the canonical text.

   ```
   cp ~/.claude/skills/load-linked-docs-rules/rules/*.md <memory-dir>/
   ```

4. **Index in `MEMORY.md`.** Open `<memory-dir>/MEMORY.md` (create if missing — no frontmatter, just bullet lines). For each index entry below, append it if it isn't already present (match on the filename in the link, not the whole line). Don't reorder existing entries.

   Entries to append:

   ```
   - [All documentation must be terse](feedback_all_docs_terse.md) — explicit rule; drop softening words, hedges, restatements; pseudocode over prose; ship the shorter version
   - [Pseudocode must tag canonical object names with storage in parens](feedback_pseudocode_names_storage.md) — `PriorityWhitelistRecord (DDB)`, `PriorityWhitelistApplyEvent (Kafka)`; aliases get no tag
   - [Storage backends are first-class contracts](feedback_storage_is_also_contract.md) — DDB/SQL/Redis/S3 each get a `contracts/<backend>.md`; object Storage sections link to it; pseudocode storage tag links to the contract
   - [Lineage mappings use pseudocode with ... spread, never prose folds](feedback_lineage_no_prose_fold.md) — bad: "(id, s3_key copied; foo added)"; good: `{ ...record, upload_url }`
   - [Spread uses canonical (linked) object name, not the alias](feedback_spread_uses_canonical_object.md) — `{ ...PriorityWhitelistRecord (DDB), upload_url }` not `{ ...record, upload_url }`; storage tag still applies
   - [Cross-app flow pseudocode must inline-link per-repo flows](feedback_cross_app_pseudocode_links_flows.md) — `<service> · <linked-flow>:` introducing every step; external actors stay unlinked
   - [Cross-app storage tag includes owning service](feedback_cross_app_storage_tag_includes_service.md) — `(ingestion-service S3)` with both linked, not bare `(S3)`; per-repo docs keep bare form
   ```

5. **Confirm to the user.** Report:
   - Memory directory path used
   - Number of rule files written / overwritten (always 7)
   - Number of MEMORY.md index entries added (new) vs skipped (already present)

## The seven rules

Stored as standalone files in [rules/](rules/) and referenced from MEMORY.md after install:

- [feedback_all_docs_terse.md](rules/feedback_all_docs_terse.md) — terseness applies to every doc Claude writes
- [feedback_pseudocode_names_storage.md](rules/feedback_pseudocode_names_storage.md) — pseudocode tags canonical objects with their storage in parens
- [feedback_storage_is_also_contract.md](rules/feedback_storage_is_also_contract.md) — DDB/SQL/Redis/S3 each get a `contracts/<backend>.md`
- [feedback_lineage_no_prose_fold.md](rules/feedback_lineage_no_prose_fold.md) — lineage uses spread pseudocode, never prose summaries
- [feedback_spread_uses_canonical_object.md](rules/feedback_spread_uses_canonical_object.md) — spread source is the canonical (linked) object name
- [feedback_cross_app_pseudocode_links_flows.md](rules/feedback_cross_app_pseudocode_links_flows.md) — cross-app pseudocode inline-links the per-repo flow per step
- [feedback_cross_app_storage_tag_includes_service.md](rules/feedback_cross_app_storage_tag_includes_service.md) — cross-app storage tag is `(<service> <storage>)` with both linked

## Notes

- This skill writes only the seven rule files; it does not touch the user's other memories.
- It does not install the `linked-docs` skill itself (that lives separately at `~/.claude/skills/linked-docs/`). The rulebook describes the conventions; these memory entries enforce them across sessions.
- Don't dedupe by replacing existing MEMORY.md lines wholesale — match on the filename inside the link and skip if present, so prior hand-edits to the index line are preserved.

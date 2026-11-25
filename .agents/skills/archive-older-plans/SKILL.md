---
name: archive-older-plans
description: >-
  Use whenever replacing, superseding, or retiring older plans, architecture
  layouts, build guides, or diagrams in this project. Archives superseded files
  into versioned folders (docs/v1/, docs/v2/, etc.) instead of deleting them.
---

# Archive Older Plans & Layouts

Never delete superseded plans, architecture diagrams, build guides, or layout assets when iterating on a design. Always archive them into versioned directories so design history stays intact.

## Procedure

1. **Determine the next archive version folder** under the relevant directory (typically `docs/v1/`, `docs/v2/`, `docs/v3/`, etc.):
   - If the current revision replaces files that belong to the same historical iteration already in `docs/v1/`, place them alongside the other `v1` files.
   - If starting a new superseded iteration, create the next sequential version directory (`docs/v2/`, `docs/v3/`, etc.).
2. **Move, do not delete**:
   - Use `mkdir -p docs/v<N> && mv <old_file> docs/v<N>/` instead of `rm`.
3. **Update references**:
   - Update any active Markdown or HTML links that pointed to the moved files so they point to the new active files (or explicitly note the archived `v<N>` copy if referenced for history).
4. **Verify**:
   - Confirm the archived files exist in `docs/v<N>/` and that no active document has broken links.

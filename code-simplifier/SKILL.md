---
name: code-simplifier
description: Use when asked to simplify, clean up, or refactor recently modified code. Use when reviewing recent commits or PRs for code quality improvements in JavaScript or TypeScript projects.
original: https://github.com/github/gh-aw/blob/main/.github/workflows/code-simplifier.md
---

# Code Simplifier

Analyze recently modified code and simplify it for clarity, consistency, and maintainability while preserving functionality. Optionally create a PR with the changes.

## When to Use

- User asks to simplify or clean up recent code changes
- After a burst of feature work, to tighten up what was merged
- Reviewing recent PRs for refactoring opportunities

**Do NOT use for:** rewriting entire modules, changes older than a few days, adding features or changing behavior.

## Phase 1: Identify Recently Modified Code

```bash
# Recent commits
git log --since="24 hours ago" --pretty=format:"%H %s" --no-merges

# Changed files (source only)
git diff --name-only HEAD~5..HEAD -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

**Include:** `.ts`, `.tsx`, `.js`, `.jsx` in `app/`, `components/`, `hooks/`, `lib/`

**Exclude:** `*.test.*`, `pnpm-lock.yaml`, `deno.lock`, `.contentlayer/`, `components/ui/` (shadcn), `lib/supabase/types.d.ts` (generated), config files

If no source files changed — exit: "No code changes to simplify."

## Phase 2: Analyze and Simplify

### Project Conventions (from biome.jsonc)

This project uses **Biome** (not ESLint/Prettier) with `ultracite` presets. Key enforced rules:

| Convention | Rule |
|---|---|
| Single quotes, 2-space indent, 80-char lines | Biome formatter |
| Trailing commas everywhere | `trailingCommas: all` |
| `interface` over `type` for object shapes | `useConsistentTypeDefinitions` |
| `import type` for type-only imports | `useImportType` / `useExportType` |
| `const` over `let` when not reassigned | `useConst` |
| No inferrable types on variables | `noInferrableTypes` |
| Template literals over string concatenation | `useTemplate` |
| Self-closing JSX elements | `useSelfClosingElements` |
| No parameter reassignment | `noParameterAssign` |
| Default parameters last | `useDefaultParameterLast` |
| No useless else after return | `noUselessElse` |
| `Number.X` over global `isNaN`/`parseInt` | `useNumberNamespace` |

### Additional Patterns

- **Naming:** camelCase variables, PascalCase components/types, UPPER_SNAKE constants
- **Prefer early returns** over deep nesting
- **Prefer `function` keyword** for top-level/exported functions
- **Explicit return types** on exported functions
- **React components:** explicit Props interfaces, `'use client'` directive when needed
- **Next.js App Router:** server components by default, client components only when hooks/interactivity needed
- **Supabase:** use typed client from `lib/supabase/`, never raw SQL strings
- **Run `pnpm clean` (Knip)** to detect unused exports, files, and dependencies

### Simplification Principles

1. **NEVER change behavior** — only how code expresses it
2. **Enhance clarity** — reduce nesting, eliminate dead code, improve names
3. **Avoid nested ternaries** — use if/else or switch
4. **Clarity over brevity** — explicit beats compact
5. **Don't over-simplify** — no clever one-liners, keep helpful abstractions
6. **Don't add complexity** for hypothetical futures

### For Each Changed File

1. Read and understand the file's purpose
2. Identify: long functions, duplicated patterns, complex conditionals, unclear names, non-standard patterns
3. Ask: Is this a real improvement or just preference? Does it maintain all functionality?
4. Apply surgical edits — one logical improvement per change, don't touch unrelated code

## Phase 3: Validate

Run all checks — if any fail, revert the offending change:

```bash
pnpm run lint          # Biome lint
pnpm run type-check    # tsc --noEmit
pnpm test              # Vitest
pnpm run build         # Next.js build
```

Also consider: `pnpm run format` to auto-fix formatting, `pnpm clean` to find unused code.

## Phase 4: Create Pull Request (if requested)

Only create PR if: simplifications were made, all checks pass, no behavior changed.

Title prefix: `[code-simplifier]`, labels: `refactoring`, `code-quality`.

PR body should list files simplified, improvements made, which recent PRs/commits they came from, and validation results.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Refactoring unrelated code | Only touch files from recent commits |
| Changing behavior | Verify with tests before and after |
| Over-simplifying | If readability decreases, revert |
| Nested ternaries | Use if/else or switch |
| Removing types on exports | Keep explicit types on exported functions |
| Using `type` instead of `interface` | Biome enforces `interface` for object shapes |
| Forgetting `'use client'` | Required for components using hooks/browser APIs |
| Editing `components/ui/` | These are shadcn generated — don't touch |

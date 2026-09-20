---
name: github-pr-review
description: "Use this skill when asked to address, fix, or resolve GitHub PR review comments."
---

# GitHub PR Review Comment Resolution

A repeatable process for fetching unresolved PR review comments, evaluating their validity, applying fixes one at a time with proper commit messages, replying on GitHub with agent attribution, and then marking threads as resolved.

Important: if a thread has been addressed, you must leave a reply on GitHub in that thread before resolving it. Do not resolve addressed threads silently.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- On the correct feature branch (`git branch --show-current`)
- Remote tracking set up (`git push -u origin <branch>`)

---

## Step 1 — Fetch Every Review Source

Findings arrive in three places, and only the first one is a thread. Review
agents (Claude Code, pullfrog, Copilot) usually put a numbered list of findings
in a review body or a plain PR comment, with at most one or two of them repeated
inline. Fetch all three before evaluating anything:

```sh
# Inline review comments (threads)
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | {id: .id, author: .user.login, path: .path, line: .line, body: .body}'

# Review bodies (summary findings, nitpicks)
gh pr view {pr} --repo {owner}/{repo} --json reviews \
  --jq '.reviews[] | "== \(.author.login) [\(.state)]\n\(.body)\n"'

# PR comments (bot reports, human follow-ups)
gh pr view {pr} --repo {owner}/{repo} --json comments \
  --jq '.comments[] | "== \(.author.login) \(.createdAt)\n\(.body)\n"'
```

Then write one checklist before touching code:

- one item per unresolved inline thread
- one item per numbered finding inside a review body or PR comment
- a note when the same defect appears in two sources, so one fix closes both

Report the checklist count to the human. If a source was skipped, say so; do
not report a review as handled from threads alone.

---

## Step 2 — Fetch GraphQL Thread IDs and Resolve Status

The REST API comment IDs cannot be used to resolve threads — you need the GraphQL `PRRT_*` node IDs:

```sh
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr}) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              databaseId
              body
            }
          }
        }
      }
    }
  }
}'
```

Map each `databaseId` (from REST) to its `id` (GraphQL `PRRT_*`) so you can reply and resolve it later.

---

## Step 3 — Evaluate Each Comment

For every checklist item, decide:

| Decision | Criteria |
|----------|----------|
| ✅ Apply | Valid bug, inconsistency, performance issue, or clear improvement that fits the PR scope |
| ⏭️ Skip | Out of scope, requires large refactor, contradicts existing patterns, or is purely stylistic preference |
| 🗣️ Discuss | Ambiguous — surface to the human before acting |

Work through comments **one at a time**, in priority order: bugs → performance → consistency → style.

---

## Step 4 — Apply Fix and Commit

For each comment being addressed, make the minimal targeted code change, then commit immediately using commitlint-style messages:

### Commit message format

```
<type>(<scope>): <short description>
```

| Type | When to use |
|------|-------------|
| `fix` | Bug fix, incorrect behaviour |
| `feat` | New functionality added |
| `perf` | Performance improvement |
| `refactor` | Code restructure with no behaviour change |
| `style` | Formatting, naming (no logic change) |
| `chore` | Config, deps, tooling |

Examples:

```sh
git commit -m "refactor(blog): extract DEFAULT_PROMO_KEY constant for blackFridayBanner magic string"
git commit -m "feat(blog): add empty state when no posts are available for current locale"
git commit -m "refactor(db): Drop legacy tables and config paths"
git commit -m "feat: Vapi voice channel + inbound webhook auth hardening (#2)" # where #2 is the GH issue addressed
git commit -m "feat: add WhatsApp channel (WAHA) + Telegram text handler"
```

### Commit command

```sh
git add <file> && git commit -m "<type>(<scope>): <description>"
```

---

## Step 5 — Push to Remote

After all commits are done, push the branch:

```sh
git push origin <branch-name>
```

---

## Step 6 — Reply on GitHub Before Resolving

This step is required for every addressed thread. If you fixed the issue, you must post a reply on the GitHub thread before resolving it.

Before resolving an addressed thread, leave a reply on the inline review comment that:

- states the thread was addressed
- identifies the harness and model that wrote the fix
- includes the commit SHA or a one-line summary whenever possible

Do not skip this reply step for addressed threads. The reply is part of the workflow, not an optional courtesy.

Use the current runtime's harness + model string exactly as it is known in context, for example:

- `Zed`
- `Codex`
- `Claude Code`
- `GPT-5.6` (model) if the harness or software agent is not known, otherwise none

### Reply format

```text
Addressed in <commit_sha>: <short summary in markdown format>

<Harness> - <Model>
```

## Replying to a multi-fact comment

See this example:

```text
Addressed the actionable AI review findings one fix per commit:

- de719ec narrows the research-process regex and preserves legitimate evidence language.
- 2dc78e6 detects leaks using the prompt’s current private-research vocabulary.

The timestamp concern is superseded by the final HEAD run and cleaned history. The `.oxfmtrc.json` note identified only a prior commit-subject typo; the configuration itself was correct, so no code change was needed. The cost/latency concern is addressed by the five-search cap and version tracking.

Zed - GPT-5.6-Astra
```

Don't use back quotes for commit hash. Github will add links if left like in the example.

### Reply command

Use the REST `comment_id` / `databaseId` from Steps 1-2:

```sh
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body=$'<Harness> - <Model>\n\nAddressed in <commit_sha>: <short summary>'
```

For threads that were intentionally deferred, leave the thread open. Add a reply only when that context helps the reviewer understand why it stays open.

### Findings that have no thread

A review body or a PR comment cannot be resolved. Close its findings with one
PR comment in the multi-fact format above, listing the commit per finding and
naming each finding left open with the reason:

```sh
gh pr comment {pr} --repo {owner}/{repo} --body $'...'
```

Post it once, after every item from that source is either committed or
deliberately deferred.

Rule of thumb:

- addressed thread → reply first, then resolve
- deferred thread → usually leave open, optionally reply with context
- skipped thread → leave open

---

## Step 7 — Resolve Threads on GitHub

Use the GraphQL `resolveReviewThread` mutation with the `PRRT_*` node ID from Step 2.

Only do this after Step 6 has been completed for that addressed thread:

- fix committed
- GitHub reply posted on the thread
- then resolve

```sh
gh api graphql -f query='
mutation {
  resolveReviewThread(input: { threadId: "<PRRT_node_id>" }) {
    thread {
      isResolved
    }
  }
}'
```

Repeat for each addressed thread. Verify the response contains `"isResolved": true`.

For threads that were **skipped**, do not resolve them — leave them open so reviewers know they were intentionally deferred.

---

## Process Flow

```
Fetch inline comments + review bodies + PR comments
        │
        ▼
Fetch GraphQL thread IDs + isResolved status
        │
        ▼
Build one checklist (threads + numbered findings)
        │
        ▼
For each item:
  ├── Valid? ──► Apply code fix
  │                  │
  │                  ▼
  │             git add + git commit (commitlint msg)
  │                  │
  │                  ▼
  │             Reply to inline comment with harness/model attribution
  │             (required before resolving)
  │                  │
  │                  ▼
  │             Resolve thread via GraphQL mutation
  │
  ├── Skip? ──► Leave thread open, note reason
  │
  └── Ambiguous? ──► Ask human before proceeding
        │
        ▼
git push origin <branch>
        │
        ▼
One PR comment per threadless source (review body, PR comment)
```

---

## Full Reference — All Commands in Order

```sh
# 1. Check branch
git branch --show-current

# 2. Fetch inline review comments (REST), review bodies, and PR comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | {id: .id, author: .user.login, path: .path, line: .line, body: .body}'
gh pr view {pr} --repo {owner}/{repo} --json reviews --jq '.reviews[] | .body'
gh pr view {pr} --repo {owner}/{repo} --json comments --jq '.comments[] | .body'

# 3. Fetch thread node IDs + resolve status (GraphQL)
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr}) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              databaseId
              body
            }
          }
        }
      }
    }
  }
}'

# 4. Apply fix, then commit (one per comment)
git add <file> && git commit -m "<type>(<scope>): <description>"

# 5. Push
git push origin <branch-name>

# 6. Reply before resolving (repeat per addressed comment)
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body=$'<Harness> - <Model>\n\nAddressed in <commit_sha>: <short summary>'

# 7. Resolve thread (repeat per addressed comment)
gh api graphql -f query='
mutation {
  resolveReviewThread(input: { threadId: "<PRRT_node_id>" }) {
    thread { isResolved }
  }
}'

# 8. Close threadless findings (once per review body or PR comment)
gh pr comment {pr} --repo {owner}/{repo} --body $'<multi-fact reply>'
```

---

## Key Rules

- **Threads are not the review** — a review body or PR comment can hold more findings than every inline thread combined; the checklist covers all three sources
- **One fix, one commit** — never batch multiple fixes into a single commit
- **Commitlint format always** — `type[(scope)]: description`, lowercase
- **Reply before resolve** — every addressed thread gets a GitHub reply before resolution
- **Identify the writer** — the reply must include the harness + model string, such as `Codex` or `Claude Code`
- **Resolve only what you fixed** — do not resolve threads for skipped comments
- **REST IDs ≠ GraphQL IDs** — the `id` from `gh api pulls/{pr}/comments` cannot be used with `resolveReviewThread`; always fetch the `PRRT_*` node ID via GraphQL first
- **Use REST for replies, GraphQL for resolve** — reply with the review comment `databaseId`, resolve with the thread `PRRT_*` ID
- **Verify resolution** — check `"isResolved": true` in the mutation response before moving on

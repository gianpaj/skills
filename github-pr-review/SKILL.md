---
name: github-pr-review
description: "Use this skill when asked to address, fix, resolve, babysit, or watch GitHub PR review comments and review-bot findings."
---

# GitHub PR Review Comment Resolution

A repeatable process for fetching unresolved PR review comments, evaluating their validity, applying fixes one commit at a time, running the project's checks, pushing once, replying on GitHub with agent attribution, marking threads as resolved, and, when asked, babysitting the PR until the next review round comes back clean.

Important: if a thread has been addressed, you must leave a reply on GitHub in that thread before resolving it. Do not resolve addressed threads silently.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- On the feature branch (`git branch --show-current`)
- A PR for that branch: `gh pr view --json number,url` gives `{pr}` and, in the URL, `{owner}/{repo}`

---

## Step 1 — Fetch Every Review Source

Findings arrive in three places, and only the first one is a thread. Review
agents (Claude Code, pullfrog, Copilot) usually put a numbered list of findings
in a review body or a plain PR comment, with at most one or two of them repeated
inline. Fetch all three before evaluating anything.

Leave `SINCE` empty on a first pass; it then matches everything. Step 8 sets
it to skip what an earlier round already handled. Run the block as one command,
since a shell variable does not survive across tool calls.

```sh
SINCE=""

# Inline review threads: unresolved only, every comment in each thread.
# The SINCE filter keys on the last comment, so a new reply in an old thread counts as new.
# The thread id (PRRT_*) resolves the thread in Step 7.
# The comment id (databaseId) receives the reply in Step 6.
gh api graphql --paginate -f query='
query($endCursor: String) {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr}) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          path
          line
          comments(first: 100) {
            nodes { databaseId createdAt author { login } body }
          }
        }
      }
    }
  }
}' --jq ".data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not) | select(.comments.nodes[-1].createdAt > \"$SINCE\") | {thread: .id, path, line, comments: [.comments.nodes[] | {id: .databaseId, at: .createdAt, author: .author.login, body}]}"

# Review bodies (summary findings, nitpicks)
gh pr view {pr} --repo {owner}/{repo} --json reviews \
  --jq ".reviews[] | select(.submittedAt > \"$SINCE\") | \"== \(.author.login) [\(.state)] \(.submittedAt)\n\(.body)\n\""

# PR comments (bot reports, human follow-ups)
gh pr view {pr} --repo {owner}/{repo} --json comments \
  --jq ".comments[] | select(.createdAt > \"$SINCE\") | \"== \(.author.login) \(.createdAt)\n\(.body)\n\""
```

Read each thread to its last comment before listing it. A reviewer's "never
mind" or a human's "done" closes a thread without anyone resolving it.

A review body or PR comment is closed once a later PR comment from the agent
answers it; that is what Step 6 posts for threadless findings. Take findings
only from sources with no such answer.

Then write one checklist before touching code:

- one item per unresolved inline thread
- one item per numbered finding inside an open review body or PR comment
- a note when the same defect appears in two sources, so one fix closes both

Report the checklist count to the human. If a source was skipped, say so; do
not report a review as handled from threads alone.

---

## Step 2 — Evaluate Everything, Then Ask Once

Classify every checklist item before changing any code:

| Decision | Criteria |
|----------|----------|
| ✅ Apply | Valid bug, inconsistency, performance issue, or clear improvement that fits the PR scope |
| ⏭️ Skip | Out of scope, requires large refactor, contradicts existing patterns, or is purely stylistic preference |
| 🗣️ Discuss | Ambiguous — needs a human call |

If any item is Discuss, put all of them into one message and ask the human
before the first fix. With no Discuss items there is nothing to ask; start
fixing. A question raised mid-flow either stalls the round or forces a second
push, and each push costs a review run (Step 5).

Then fix the Apply items one at a time, in priority order: bugs → performance → consistency → style.

---

## Step 3 — Apply Fix and Commit

For each comment being addressed, make the minimal targeted code change, then commit immediately. Commit locally only; pushing is Step 5 and happens once.

### Commit message

Follow the `## Commit messages` section of the project's AGENTS.md or user's AGENTS.md.
In short:

- Conventional Commits syntax: `type(scope): description`
- imperative mood, subject near 50 characters, no trailing punctuation
- a body only when it adds useful context or the diff is large: blank line
  after the subject, wrapped at 72 columns, not repeating the subject

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
git commit -m "fix(auth): reject expired webhook signatures"

git commit -m "refactor(blog): extract DEFAULT_PROMO_KEY constant" \
  -m "Three call sites repeated the string. One constant keeps them in sync."
```

### Commit command

```sh
git add <file> && git commit -m "<type>(<scope>): <description>"
```

---

## Step 4 — Verify Before Pushing

Run the project's checks for the files you touched before the push: tests,
lint, typecheck, whatever the repo's CI runs. Use the repo's own commands from
its package scripts, Makefile, or CI workflow rather than guessing.

A red check after the push wastes a review run and a babysit round. If a
check fails, fix it and amend the commit that broke it; nothing is pushed
yet, so the history is still yours to edit.

---

## Step 5 — Push Once

Push only after every checklist item is committed or deliberately deferred.
Every push starts a Pullfrog review run on the PR, and each run spends AI
credits, so a push per fix multiplies the cost of the review for nothing.

Push before replying: GitHub links a commit SHA in a reply only once the
commit exists on the remote.

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

Use the harness and model exactly as they are known in context, for example
`Claude Code - Claude Fable 5.1`, `Codex - GPT-5.6`, or `Zed - GPT-5.6-Astra`.
If the harness is unknown, use the model alone.

### Reply format

```text
Addressed in <commit_sha>: <short summary in markdown format>

<Harness> - <Model>
```

### Replying to a multi-fact comment

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

Use the comment `id` (the GraphQL `databaseId`) from Step 1:

```sh
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body=$'Addressed in <commit_sha>: <short summary>\n\n<Harness> - <Model>'
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

Use the GraphQL `resolveReviewThread` mutation with the thread `PRRT_*` id from Step 1.

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

## Step 8 — Babysit the PR (only when asked)

Skip this step unless the human asked you to babysit, watch, or follow up on
the PR. Each round costs a Pullfrog review run.

After the push in Step 5, wait for the checks:

```sh
# Blocks until every check finishes, including the Pullfrog review workflow.
# If it reports no checks yet, wait ten seconds and run it again.
gh pr checks {pr} --repo {owner}/{repo} --watch
```

Then re-run the Step 1 block in one command, with `SINCE` set to the pushed
head commit's date instead of empty:

```sh
SINCE=$(gh pr view {pr} --repo {owner}/{repo} --json commits --jq '.commits[-1].committedDate')
# ...followed by the three fetch commands from Step 1, unchanged
```

Your own replies from Step 6 pass this filter too; skip them. A failed check
is a finding too: read its log and add it to the checklist.

Then:

- No new findings and green checks: report that to the human and stop.
- New findings: build a fresh checklist and run Steps 2-7 on it. Valid ones
  get a fix and a commit; invalid ones get a reply with the reason and stay
  open. Push once, after the whole round is committed, then watch again.
- A round with no valid finding ends the loop. Do not push; there is nothing
  new for Pullfrog to review.

Stop after three rounds even if findings keep coming, and hand the open ones
to the human. A reviewer that keeps producing findings is either right about
something structural or looping on style, and both need a human call.

---

## Process Flow

```text
Fetch unresolved threads + review bodies + PR comments
        │
        ▼
Build one checklist (threads + numbered findings)
        │
        ▼
Classify every item; ask the human about all Discuss items in one message
        │
        ▼
For each Apply item: code fix ──► git add + git commit (Conventional Commits)
        │
        ▼
Run the project's checks; amend anything that fails
        │
        ▼
git push origin <branch>   (once, after the whole checklist)
        │
        ▼
Reply to each addressed thread with harness/model attribution
(required before resolving)
        │
        ▼
Resolve each addressed thread via GraphQL mutation
        │
        ▼
One PR comment per threadless source (review body, PR comment)
        │
        ▼
Asked to babysit? ──► gh pr checks --watch ──► new findings? ──► back to the checklist
```

---

## Key Rules

- **Threads are not the review** — a review body or PR comment can hold more findings than every inline thread combined; the checklist covers all three sources
- **Ask once** — classify every item first; if any are Discuss, ask about all of them in one message before the first fix, never one at a time mid-flow
- **One fix, one commit** — never batch multiple fixes into a single commit
- **Verify before push** — run the repo's checks on the touched files; a red check after the push wastes a review run
- **Push once** — every push starts a Pullfrog review run that spends AI credits; push after the whole checklist is committed or deferred, never per fix
- **Babysit only when asked** — watch checks and re-fetch findings after a push only when the human asks; stop after three rounds or after a round with no valid finding
- **Commit style from AGENTS.md** — Conventional Commits, imperative, subject near 50 characters, body only when it adds context
- **Reply before resolve** — every addressed thread gets a GitHub reply before resolution
- **Identify the writer** — the reply ends with the harness and model, such as `Claude Code - Claude Fable 5.1`
- **Resolve only what you fixed** — do not resolve threads for skipped comments
- **Two ids per thread** — the comment `databaseId` receives the reply, the thread `PRRT_*` id goes to `resolveReviewThread`; Step 1 returns both
- **Verify resolution** — check `"isResolved": true` in the mutation response before moving on

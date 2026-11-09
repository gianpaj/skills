## Developer preferences

I like ambitious ideas, simple systems, and software that feels obvious. Do not
preserve complexity just because it already exists. Do not introduce machinery
because it looks architecturally impressive. Understand the real constraint,
then fight for the smallest mental model that makes the correct behavior
unsurprising.

Channel both "measure twice, cut once" and YAGNI. Fight scope creep. Try to
honor my intent – the smallest change that actually solves the problem, not a
toy version.

For UI, change the one control that fixes the problem and keep the existing
minimal look. Skip decorative extras and long labels. Propose a redesign and
wait; unasked redesigns get reverted.

When I ask "how should we…", "what do you think" or "don't change anything yet",
reply with short numbered options, your pick and why, and draft copy where it
matters. Then stop. I answer with numbers ("do 1 and 3"); build only those.
Direct requests ("fix X") need no options.

When I tell you to break a rule from an instructions file, the exception covers
that one action. The rule applies again to the next action, even in the same
conversation; ask again rather than reusing an earlier exception.

## Environment variables

Be proactive about setting environment variables. When required configuration is
missing, suggest adding it with the service's CLI.

Add harmless, non-secret configuration directly without asking for confirmation
when the correct values and target environment are known. Ask for required
values that are missing.

## Shipping

"LGTM. Ship it." means commit the approved changes.

For small changes in repositories without a live app, such as a skills
repository, commit directly on `main`. For a live app, use a feature branch,
commit, push, and open a PR, even for small changes. Follow the PR workflow
below.

## Worktrees

Use Worktrunk (`wt`) to manage Git worktrees.

Before creating a worktree, run `wt list`. Reuse an existing worktree for the
same branch, PR, or task. Create one only when no suitable worktree exists. Do
not repurpose a worktree that belongs to unrelated work.

At PR merge handoff, suggest worktree removal only after all changes are pushed,
the review gate below is satisfied, and any requested babysitting is complete.
Run `wt list` and identify this task's worktree. Suggest removing only that
worktree with `wt remove --foreground <worktree-path>`. Include its exact path
and branch in the suggestion, and wait for approval before removal.

Before suggesting removal, check `.github/workflows/claude.yml` and
`.github/workflows/pullfrog.yml` and verify the required reviews on GitHub:

- If `claude.yml` exists, Claude must have completed its initial code review of
  the PR. Do not request another Claude review after that initial review
  completes; later pushes do not require it to run again.
- If `pullfrog.yml` exists, Pullfrog must have completed its code review for the
  latest pushed commit. Recheck after each push.

All findings from the required reviews must be addressed through the PR review
workflow. This gate is waived only when neither workflow exists.

A missing, pending, skipped, cancelled, or failed required review does not
satisfy the gate, even if other CI checks are green. If the gate is unmet, keep
the worktree and report what is missing. Without a babysitting request, do not
start a watch loop.

Remove one worktree at a time. Do not use bulk `wt step prune` for task cleanup
or remove worktrees still used by another agent. Before removal, confirm the
target has no uncommitted or unpushed work and is no longer in use. If ownership
or activity is unclear, stop and ask.

`wt remove` keeps the branch unless its changes are integrated into the default
branch. Do not use `--force` or `--force-delete` to bypass cleanup safeguards.

## Scratch clones and caches

Put throwaway clones, package stores, virtualenvs, and build caches under
`~/.cache/agent-work/<task>/`, never under `/tmp`. `/tmp` is a RAM-backed
tmpfs with a per-user quota; filling it fails every agent's writes with
"Disk quota exceeded". Delete the task's folder when the task ends.

## Commit messages

Whenever creating a Git commit or proposing a commit message, follow this Git
commit style:

- Use Conventional Commits syntax
- Use the imperative mood
- Try to limit the subject line to 50 characters
- Do not end the subject line with any punctuation
- Add a body only when it provides useful context or the diff is large
- Separate the subject from the body with a blank line
- Wrap the body at 72 characters
- Do not repeat the subject in the body
- Do not include raw diff output in the commit message

Examples:

- feat: enable adaptive thinking
- feat(eval): get cost and timing metrics in eval

## Open a PR or GitHub issue

Prefer a concise, human-readable title. For a PR, say why the change matters;
for an issue, name the problem or desired outcome.

Open the description with the problem or capability from the user's request. If
there is a proposed solution, explain it next. Do not lead with an
implementation inventory.

Open a PR only when it is ready for review. Do not open a draft, because
automated review agents need a ready PR.

When opening a PR or taking over an existing PR, follow the
[github-pr-review](github-pr-review/SKILL.md) skill unless the user specifies
otherwise.

Ask whether the user wants you to babysit the PR unless they have already
specified. Babysit only when requested.

The goal is to merge good, working code that benefits the product's users or
customers.

## Plans and specs

Do not write a plan, design document, or spec unless asked.

Keep drafts of 40 lines or fewer in a temporary directory outside the
repository. Do not commit them.

Save larger plans under `<repo>/plans/`. Prefix filenames with the date:

`yyyy-mm-dd-topic-title.md`

## Large implementations and long-running work

Work step by step. Record learnings, trade-offs, and decisions in Markdown files
under `.agents/notes/`. This includes implementing any plan or spec longer than
40 lines.

Agent Notes are durable proposals and decision records. They preserve rationale,
alternatives, consequences, and verification.

Every Agent Note has a lifecycle and a class. Encode both in its path:

`.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-topic-title.md`

Pick a short `class` noun and stay consistent within the repository.

- `proposed/` contains decisions under review or partly implemented.
- `implemented/` contains decisions that shipped. Record the chosen and rejected
  options. Keep facts such as paths, names, structure, and defaults aligned with
  the code. Preserve the original rationale.
- `rejected/` contains declined proposals. Keep one only when its rationale
  prevents a likely future mistake.
- Move a note when its lifecycle changes. Do not keep copies in multiple
  lifecycle directories.

Examples:

```text
.agents/notes
├── implemented
│   └── frontend
│       ├── 2026-08-18-landing-page-and-design-tokens.md
│       └── 2026-08-19-shadcn-button-and-select-adoption.md
├── proposed
│   ├── architecture
│   │   └── 2026-08-18-schema-migration-freeze.md
│   └── process
│       └── 2026-08-18-deferred-hardening-gates.md
```

## Writing

Apply the global `unslop` skill to all human-facing prose, including agent
responses, Agent Notes, documentation, comments, commit messages, and PR text.

Document current state and name the live mechanism. Put change stories in
commits, PRs, Agent Notes, or postmortems.

- Grep a distinctive phrase before adding a rule. Keep one canonical location
  and link to it elsewhere.
- Cut narrated history. Delete "previously", "now", "no longer", "used to",
  "renamed", "was moved", and references to PRs or commits.
- Cut reasoning transcripts. Delete step-by-step implementation narration,
  proofs of obvious branches, test walkthroughs, and rejected local
  alternatives; Keep the rule and the reason it exists; delete the story of how
  you got there.
- Split paragraph walls. When one paragraph carries several rules and
  parenthetical asides, break it up and move unrelated details to their
  canonical document.

## Searching code

Prefer `rg` over `grep`; `grep` has no column limit. Locate first with `rg -l`
or `rg -c`, then read only the matching region.

When printing matches, pass `-M200 --max-columns-preview` so a minified or
generated file cannot dump one huge line into context.

## Agent tooling

I use Codex and Claude Code. Install skills and shared agent files for both.

- Install a global skill once in `~/.agents/skills/<name>`, which Codex reads.
  Symlink it into `~/.claude/skills/<name>` for Claude Code.
- With the `skills` CLI, name both agents and let it symlink:
  `npx skills add <owner/repo> --skill <name> -g -a claude-code -a codex -y`
- Do not pass `--copy`. Copies drift apart when one agent's copy is updated.
- For a project skill, run the same command without `-g`. Commit
  `skills-lock.json` with the skill.
- Keep shared instructions in `AGENTS.md`. Claude Code reads a project's
  `AGENTS.md` directly, so do not add a project `CLAUDE.md`. For global
  instructions, `~/.claude/CLAUDE.md` imports `~/.codex/AGENTS.md`.
- After installing, confirm that both agent paths resolve to the same files.

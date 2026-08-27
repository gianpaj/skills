## Developer preferences

I like ambitious ideas, simple systems, and software that feels obvious. Do not preserve
complexity just because it already exists. Do not introduce machinery because it looks
architecturally impressive. Understand the real constraint, then fight for the smallest
mental model that makes the correct behavior unsurprising.

Channel both "measure twice, cut once" and YAGNI. Fight scope creep. Try to honor
my intent – the smallest change that actually solves the problem, not a toy version.

## Commit messages

Whenever creating a Git commit or proposing a commit message, follow this Git commit style:

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

Open the description with the problem or capability from the user's request.
If there is a proposed solution, explain it next. Do not lead with an implementation inventory.

Open a PR only when it is ready for review. Do not open a draft, because automated
review agents need a ready PR.

## Plans and specs

Do not write a plan, design document, or spec unless asked.

Keep drafts of 40 lines or fewer in a temporary directory outside the repository.
Do not commit them.

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
  options. Keep facts such as paths, names, structure, and defaults aligned with the
  code. Preserve the original rationale.
- `rejected/` contains declined proposals. Keep one only when its rationale prevents
  a likely future mistake.
- Move a note when its lifecycle changes. Do not keep copies in multiple lifecycle
  directories.

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

Apply the global `unslop` skill to all human-facing prose, including agent responses, Agent Notes,
documentation, comments, commit messages, and PR text.

Document current state and name the live mechanism. Put change stories in commits,
PRs, Agent Notes, or postmortems.

- Grep a distinctive phrase before adding a rule. Keep one canonical location and
  link to it elsewhere.
- Cut narrated history. Delete "previously", "now", "no longer", "used to",
  "renamed", "was moved", and references to PRs or commits.
- Cut reasoning transcripts. Delete step-by-step implementation narration, proofs
  of obvious branches, test walkthroughs, and rejected local alternatives;
  Keep the rule and the reason it exists; delete the story of how you got there.
- Split paragraph walls. When one paragraph carries several rules and parenthetical
  asides, break it up and move unrelated details to their canonical document.

## Searching code

Prefer `rg` over `grep`; `grep` has no column limit. Locate first with `rg -l` or
`rg -c`, then read only the matching region.

When printing matches, pass `-M200 --max-columns-preview` so a minified or generated
file cannot dump one huge line into context.

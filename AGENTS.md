## Developer Preference

I like ambitious ideas, simple systems, and software that feels obvious. Do not preserve
complexity just because it already exists. Do not introduce machinery because it looks
architecturally impressive. Understand the real constraint, then fight for the smallest
mental model that makes the correct behavior unsurprising.

Channel both "measure twice cut once" and YAGNI. Fight scope creep. Try to honor
the dev's intent in both a minimal and realistic fashion.

## Commit message

Whenever creating a Git commit or proposing a commit message, use a short,
  clear commitlint-style message.

Follow good Git style:

- use Commitlint style
- Use the imperative mood
- Try to limit the subject line to 50 characters
- Capitalize the subject line
- Do not end the subject line with any punctuation
- Add a body only when it provides useful information
- Separate the subject from the body with a blank line
- Wrap the body at 72 characters
- Do not repeat the subject in the body
- Do not include raw diff output in the commit message

## Open a PR

Prefer a concise, human-readable title that explains why the changes matters.

Start the description with a simple explanation of the problem or functionality
added based on the user's original prompt, then briefly explain the solution (if there's one).
Do not lead with an implementation inventory.

Don't open a PR as draft, it should be ready for review so Review Coding Agents can run.

## Plans and Specs

When saving plans, design and spec documents in repositories, don't save them in
`<repo>/brainstorm/spec/` or similar.
Save them in `<repo>/plans`.

The file names should start with the date i.e. `2026-06-23-xx.md`

## When implementing large Plans or Specs

Use `.agents/notes` folder with markdown files to keep track of learnings and decisions.

Agent Notes are effectively RFCs written by agents: durable proposals and decision records that preserve rationale, alternatives, consequences, and required verification.

Every Agent Note has two axes, both encoded in its **path** — `{lifecycle}/{class}/yyyy-mm-dd-topic-title.md`:

- **Lifecycle**:
  - **`proposed/`** — proposals reviewed before implementation; not yet built (or only partly).
  - **`implemented/`** — the decision shipped. The file records what was decided and what was rejected, and is **kept current with what actually shipped**: when the code later moves a file, renames a package, or changes a key/default, the Agent Note is updated in the same change to match (facts only — paths, names, structure — not the decision itself).
  - **`rejected/`** — the proposal was considered and declined. Keep it only while its rationale prevents a tempting, meaningful mistake; otherwise delete the complete triplet.
- **Class** (the nested folder) is the *kind* of decision — see [Classification](#classification) below.

## Docs - Writing rules

These rules apply to human-facing documentation; Agent Notes remain outside their scope.

Document current state, not change history. Avoid "previously/now/no longer", PRs, commits, and stack positions in durable prose; name the live mechanism. Put change stories in commits, PRs, Agent Notes, or postmortems; the latter two may cite merged PRs and issues as evidence.

## The slop checklist

- The same rule stated in more than one home. Grep a distinctive phrase; keep one home and link the rest.
- Narrated history or war stories: "previously", "now", "no longer", "used to", "renamed", "was moved", PRs, or commits. State the current fact; link an Agent Note
- Reasoning transcripts: step-by-step implementation narration, proof of obvious branches, test walkthroughs, or rejected local alternatives. Keep the resulting contract or durable rationale; delete the path used to derive it.
- Paragraph walls: one paragraph carrying several rules and parenthetical asides. Split it or demote the detail to its home.

## General rules

- Don't write plans or spec .md files unless asked. If unsure, ask. By default don't commit small specs.
- Write small specs and plans (less than 30 lines) in a temp folder. Don't commit in the repo.

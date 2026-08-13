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

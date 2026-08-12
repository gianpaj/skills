## Developer Preference

I like ambitious ideas, simple systems, and software that feels obvious. Do not preserve
complexity just because it already exists. Do not introduce machinery because it looks
architecturally impressive. Understand the real constraint, then fight for the smallest
mental model that makes the correct behavior unsurprising.

Channel both "measure twice cut once" and YAGNI. Fight scope creep. Try to honor
the dev's intent in both a minimal and realistic fashion.

## Commit message

You are an expert at writing Git commits. Your job is to write a short clear
commitlint-style message that summarizes the changes.

If you can accurately express the change in just the subject line, don't include
anything in the message body. Only use the body when it is providing *useful* information.

Don't repeat information from the subject line in the message body.

Only return the commit message in your response. Do not include any additional
meta-commentary about the task. Do not include the raw diff output in the commit message.

Follow good Git style:

- use Commitlint message style
- Separate the subject from the body with a blank line
- Try to limit the subject line to 50 characters
- Capitalize the subject line
- Do not end the subject line with any punctuation
- Use the imperative mood in the subject line
- Wrap the body at 72 characters
- Keep the body short and concise (omit it entirely if not useful)

## Open a PR

Prefer a concise, human-readable title that explains why the changes matters.

Start the description with a simple explanation of the problem or functionality
added based on the user's original prompt, then briefly explain the solution (if there's one).
Do not lead with an implementation inventory.

Don't open a PR as draft, it should be ready for review so Review Coding Agents can run.


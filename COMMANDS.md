# COMMANDS / PROMPTS

## upgrade package(s)

Look at the changelog between the current and latest major versions. List any
breaking changes and features that our implementation might find useful –
analyse it first.

```sh
❯ pnpm --filter @sexyvoice/web outdated | grep tiptap
│ @tiptap/core                                    │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
│ @tiptap/extensions                              │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
│ @tiptap/pm                                      │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
│ @tiptap/react                                   │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
│ @tiptap/starter-kit                             │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
│ @tiptap/suggestion                              │ 3.22.4                   │ 3.30.5   │ @sexyvoice/web │
```

## Shrink up docker VM

```sh
docker run --rm --privileged --pid=host alpine \
  nsenter -t 1 -m -u -i -n fstrim -v /var/lib/docker
```

Run it after a big prune if
`du -h ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw` still
looks larger than what `docker system df` reports.

## Large work

Take your time. Do it step by step. Use `.agents/notes` to keep track of
learnings and making changes - if this is useful (less is more). Commit as you
go – put chunks of work logically together. When everything is done and
verified, push to the remote. If we have a PR, use
~/.agents/skills/github-pr-review/SKILL.md to baby sit and wait for coding
agents to give review the PR.

## Bug fix

Write a bug fix plan, start a branch, new worktreee, make the fix, add an e2e
test and mocking if need. Do not make real AI API calls that would costs us
money to run or other API calls that are very slow and mocking makes sense.

Take your time. Do it step by step. Use `.agents/notes` to keep track of
learnings and making changes - if this is useful (less is more). Commit as you
go – put chunks of work logically together.

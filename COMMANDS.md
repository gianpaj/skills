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

Work step by step. Verify each step before starting the next. Record learnings,
trade-offs, and decisions as Agent Notes under `.agents/notes/`. Commit as you
go, one logical chunk of work per commit. When everything is done and verified,
push to the remote.

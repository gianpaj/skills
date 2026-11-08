# Five-minute skills repository sync

Use a systemd user timer to pull this repository from GitHub every five minutes.
This is the setup on `gianrtx`, running as `gianpaj`.

This guide applies to Linux with systemd. macOS needs a launchd job instead of
these service and timer files.

## Behavior

- Update only `~/github/gianpaj/skills` on `master`, using `origin/master`.
- Fast-forward only. Never commit, push, stash, rebase, or reset local work.
- Refuse updates when the checkout has local changes, untracked files,
  local-only commits, divergent history, or another branch checked out.
- Refuse to overwrite ignored local files that conflict with incoming files.
- Run every five minutes, with up to 30 seconds of scheduling slack. Retry on
  the next scheduled run after a failure.
- Run after logout and reboot. The machine must be awake and able to reach
  GitHub to stay current.
- Prevent overlapping sync runs with a lock. Log failures to the systemd
  journal. No external failure notifications are configured.

Only committed and pushed changes synchronize. Updating this checkout does not
update separate installed copies of skills. For agent instruction links, see
[README.md](README.md).

## 1. Check the machine and checkout

Run the setup as the user who owns the repository, not as root. Required tools
are Git, Python 3 at `/usr/bin/python3`, `flock` at `/usr/bin/flock`, and a
working systemd user manager.

```sh
command -v git python3 flock systemctl
systemctl --user list-timers --all --no-pager
```

Use the same checkout path on each machine. If it does not exist, clone it:

```sh
mkdir -p ~/github/gianpaj
git clone --branch master git@github.com:gianpaj/skills.git ~/github/gianpaj/skills
```

If a checkout already exists, inspect it instead of cloning or replacing it:

```sh
git --no-optional-locks -C ~/github/gianpaj/skills status --short --branch
git --no-pager -C ~/github/gianpaj/skills remote -v
```

The branch must be `master`, the working tree must be clean, and `origin` must
point to `git@github.com:gianpaj/skills.git`. Resolve any local-only commits or
divergence manually before enabling sync. Do not discard them to make setup
succeed.

### Check unattended GitHub access

The timer must authenticate without an interactive session or a forwarded SSH
agent. Test the same environment used by the sync script:

```sh
env -u SSH_AUTH_SOCK \
  GIT_TERMINAL_PROMPT=0 \
  GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=10' \
  git -C ~/github/gianpaj/skills ls-remote origin refs/heads/master
```

Expect a commit hash followed by `refs/heads/master`, with no password prompt.
If this fails, configure unattended authentication for this user, such as a
repository-scoped read-only deploy key, and retry. Keep private keys outside the
repository.

## 2. Install the sync script

The following steps create three files. If any already exist, inspect them
before replacing them:

- `~/.local/bin/sync-skills`
- `~/.config/systemd/user/skills-sync.service`
- `~/.config/systemd/user/skills-sync.timer`

```sh
mkdir -p ~/.local/bin ~/.config/systemd/user
cat > ~/.local/bin/sync-skills <<'PY'
#!/usr/bin/python3
import os
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
env = os.environ.copy()
env.pop("SSH_AUTH_SOCK", None)
env.update(
    GIT_TERMINAL_PROMPT="0",
    GIT_EDITOR="true",
    GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2",
)


def git(*args):
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), *args],
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "Git command failed"
        )
    return result.stdout.strip()


def check_checkout():
    if git("branch", "--show-current") != "master":
        raise RuntimeError("Checkout is not on master; leaving it untouched")
    if git("--no-optional-locks", "status", "--porcelain"):
        raise RuntimeError("Working tree has local changes; leaving them untouched")


try:
    check_checkout()
    git("fetch", "--no-tags", "origin")
    check_checkout()
    ahead, behind = map(
        int,
        git(
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/master",
        ).split(),
    )
    if ahead:
        raise RuntimeError(
            f"master has {ahead} local-only commits and is {behind} commits "
            f"behind origin/master; reconcile manually"
        )
    if behind:
        print(
            git(
                "merge",
                "--ff-only",
                "--no-edit",
                "--no-overwrite-ignore",
                "refs/remotes/origin/master",
            ),
            flush=True,
        )
    print("Skills sync OK: master at " + git("rev-parse", "--short", "HEAD"), flush=True)
except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
    print("Skills sync stopped: " + str(error), file=sys.stderr, flush=True)
    sys.exit(1)
PY
chmod 755 ~/.local/bin/sync-skills
```

## 3. Install the service and timer

`%h` is the user's home directory. `%t` is the user's runtime directory, where
`flock` holds the sync lock. The service has a three-minute timeout and runs
without an interactive SSH agent.

```sh
cat > ~/.config/systemd/user/skills-sync.service <<'EOF'
[Unit]
Description=Fast-forward skills repository from GitHub

[Service]
Type=oneshot
WorkingDirectory=%h/github/gianpaj/skills
ExecStart=/usr/bin/flock --nonblock %t/skills-sync.lock %h/.local/bin/sync-skills %h/github/gianpaj/skills
TimeoutStartSec=180
EOF

cat > ~/.config/systemd/user/skills-sync.timer <<'EOF'
[Unit]
Description=Sync skills repository every five minutes

[Timer]
OnCalendar=*-*-* *:0/5:00
Persistent=true
AccuracySec=30s
Unit=skills-sync.service

[Install]
WantedBy=timers.target
EOF
```

`Persistent=true` triggers a catch-up run when the timer starts after missing a
scheduled run. It does not keep a sleeping machine awake.

## 4. Enable and verify

Enable lingering so the user manager can run after logout and at boot:

```sh
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger
```

Expect `Linger=yes`. If local policy denies this change, ask an administrator to
enable lingering for your account.

Validate the units, run one sync, then enable the schedule. Stop and inspect the
logs if validation or the first sync fails.

```sh
systemd-analyze --user verify \
  ~/.config/systemd/user/skills-sync.service \
  ~/.config/systemd/user/skills-sync.timer
systemctl --user daemon-reload
systemctl --user start skills-sync.service
systemctl --user enable --now skills-sync.timer
systemctl --user list-timers skills-sync.timer --no-pager
journalctl --user -u skills-sync.service -n 20 --no-pager
```

Check that the timer is enabled and active:

```sh
systemctl --user is-enabled skills-sync.timer
systemctl --user is-active skills-sync.timer
```

Expect `enabled` and `active`. The oneshot service itself is normally inactive
between runs; that is not a failure.

After the next scheduled run, check for a successful journal entry and matching
local and remote-tracking revisions:

```sh
journalctl --user -u skills-sync.service -n 20 --no-pager
git --no-pager -C ~/github/gianpaj/skills rev-parse HEAD refs/remotes/origin/master
```

The two hashes should match after a successful sync. A success entry starts with
`Skills sync OK: master at`.

## Operations and failures

Run an immediate sync through the same service and lock:

```sh
systemctl --user start skills-sync.service
```

To pause scheduled syncs before working in this checkout:

```sh
systemctl --user stop skills-sync.timer
systemctl --user status skills-sync.service --no-pager
```

Let any active service run finish before editing. Stopping the timer does not
interrupt a sync already in progress.

Resume the schedule:

```sh
systemctl --user start skills-sync.timer
```

Disable it across reboots:

```sh
systemctl --user disable --now skills-sync.timer
```

A refusal or authentication failure marks the service failed and records the
reason in the journal. Correct the underlying issue, then start the service
again or wait for the next scheduled attempt. Do not add automatic stashing,
rebasing, resets, or force operations to hide local changes or divergence.

To inspect the installation on `gianrtx` from another computer:

```sh
ssh gianrtx 'systemctl --user list-timers skills-sync.timer --no-pager'
ssh gianrtx 'journalctl --user -u skills-sync.service -n 20 --no-pager'
```

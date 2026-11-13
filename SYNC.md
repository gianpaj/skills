# Five-minute skills repository sync

Pull this repository from GitHub every five minutes with the same sync script on
Linux and macOS:

- Linux uses a systemd user timer, as on `gianrtx` under `gianpaj`.
- macOS uses a system-wide launchd daemon that runs as the checkout owner, as on
  `farmini` under `rose`. It works without a desktop login.

Complete sections 1 and 2 on either platform, then follow the
[Linux setup](#linux-install-the-service-and-timer) or
[macOS setup](#macos-install-the-launchdaemon).

## Behavior

- Update only `~/github/gianpaj/skills` on `master`, using `origin/master`.
- Fast-forward only. Never commit, push, stash, rebase, or reset local work.
- Refuse updates when the checkout has local changes, untracked files,
  local-only commits, divergent history, or another branch checked out.
- Refuse to overwrite ignored local files that conflict with incoming files.
- Run every five minutes while awake. Linux allows up to 30 seconds of
  scheduling slack. Retry on the next scheduled run after a failure.
- Run after logout and reboot. The machine must be awake and able to reach
  GitHub to stay current.
- Prevent overlapping sync runs with a Python file lock. Log failures to the
  systemd journal on Linux or files under `~/Library/Logs/skills-sync` on macOS.
  No external failure notifications are configured.

Only committed and pushed changes synchronize. Updating this checkout does not
update separate installed copies of skills. For agent instruction links, see
[README.md](README.md).

## 1. Check the machine and checkout

Run the setup as the user who owns the repository, not as root. Use `sudo` only
for the macOS daemon installation and launchctl commands shown below. Both
platforms require Git and Python 3. Neither requires the `flock` command.

On Linux, check for Python at `/usr/bin/python3` and a working systemd user
manager:

```sh
command -v git python3 systemctl
/usr/bin/python3 --version
systemctl --user list-timers --all --no-pager
```

On macOS, connect to the target machine and check its tools:

```sh
ssh macos_machine
whoami
command -v git python3 launchctl
```

On `macos_machine`, expect user `mac_user`, Git at `/opt/homebrew/bin/git`, and
Python at `/opt/homebrew/bin/python3`. The macOS setup also supports Intel
Homebrew under `/usr/local/bin`. `systemctl` is not available on macOS.

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

The scheduled job must authenticate without an interactive session or a
forwarded SSH agent. Test the same environment used by the sync script:

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

Install the same script on either platform. If `~/.local/bin/sync-skills`
already exists, inspect it before replacing it. Pause any existing schedule
using the platform's operations section and let an active sync finish first.

The script uses `fcntl.flock` from Python's standard library. It holds
`~/.local/state/skills-sync/sync.lock` until it exits, including on failure. Do
not delete the lock file to unlock a running sync.

```sh
mkdir -p ~/.local/bin
cat > ~/.local/bin/sync-skills <<'PY'
#!/usr/bin/env python3
import fcntl
import os
import shutil
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
git_bin = shutil.which("git")
env = os.environ.copy()
env.pop("SSH_AUTH_SOCK", None)
env.update(
    GIT_TERMINAL_PROMPT="0",
    GIT_EDITOR="true",
    GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2",
)


def git(*args):
    if not git_bin:
        raise RuntimeError("Git is not available on PATH")
    result = subprocess.run(
        [git_bin, "-C", str(repo), *args],
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
    lock_dir = Path.home() / ".local/state/skills-sync"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = (lock_dir / "sync.lock").open("a")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("Another skills sync is running; skipping this run")
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

## Linux: install the service and timer

If either unit file already exists, inspect it before replacing it. `%h` is the
user's home directory. The service has a three-minute timeout and runs without
an interactive SSH agent. The script holds the sync lock.

```sh
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/skills-sync.service <<'EOF'
[Unit]
Description=Fast-forward skills repository from GitHub

[Service]
Type=oneshot
WorkingDirectory=%h/github/gianpaj/skills
ExecStart=/usr/bin/python3 %h/.local/bin/sync-skills %h/github/gianpaj/skills
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

### Enable and verify

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

### Linux operations and failures

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

## macOS: install the LaunchDaemon

Run these steps on `macos_machine` as `mac_user`, after completing sections 1
and 2. A LaunchDaemon runs in the system domain at boot, even without a desktop
login. Its `UserName` setting runs Python and Git as `mac_user`, not root.

The Mac must be awake, have network access, and have its startup disk unlocked.
With FileVault enabled, a restart can require a person to unlock the disk before
macOS starts the daemon. A LaunchDaemon cannot bypass FileVault.

### Create the plist

The setup creates these files. Inspect any existing installation before
replacing it, and pause an existing daemon using the operations section below:

- `~/.local/state/skills-sync/com.gianpaj.skills-sync.plist`
- `/Library/LaunchDaemons/com.gianpaj.skills-sync.plist`

Generate the plist as the checkout owner, without `sudo`. Python writes absolute
paths because launchd does not expand `~`, shell variables, or shell commands in
a plist. The explicit `PATH` includes Homebrew; launchd does not load `.zshrc`
or your interactive SSH environment.

```sh
python3 - <<'PY'
import os
import plistlib
import pwd
import shutil
from pathlib import Path

user = pwd.getpwuid(os.getuid())
if user.pw_uid == 0:
    raise SystemExit("Run this as the checkout owner, not root")
home = Path(user.pw_dir)
path = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
python = shutil.which("python3", path=path)
if not python or not shutil.which("git", path=path):
    raise SystemExit("Python 3 and Git must be available on the daemon PATH")
state = home / ".local/state/skills-sync"
logs = home / "Library/Logs/skills-sync"
state.mkdir(parents=True, exist_ok=True)
logs.mkdir(parents=True, exist_ok=True)
plist = {
    "Label": "com.gianpaj.skills-sync",
    "UserName": user.pw_name,
    "ProgramArguments": [
        python,
        str(home / ".local/bin/sync-skills"),
        str(home / "github/gianpaj/skills"),
    ],
    "WorkingDirectory": str(home / "github/gianpaj/skills"),
    "EnvironmentVariables": {"HOME": str(home), "PATH": path},
    "RunAtLoad": True,
    "StartInterval": 300,
    "StandardOutPath": str(logs / "stdout.log"),
    "StandardErrorPath": str(logs / "stderr.log"),
}
output = state / "com.gianpaj.skills-sync.plist"
with output.open("wb") as file:
    plistlib.dump(plist, file)
print(output)
print("Runs as " + user.pw_name + " using " + python)
PY

plutil -lint ~/.local/state/skills-sync/com.gianpaj.skills-sync.plist
```

On `macos_machine`, check that the output says
`Runs as mac_user using /opt/homebrew/bin/python3` and that `plutil` reports
`OK`.

`RunAtLoad` starts one sync when launchd loads the job. `StartInterval` requests
another every 300 seconds. It does not wake the Mac or replay missed intervals
after sleep. Sync resumes on a later interval while awake. Each Git command has
a 90-second timeout; the Linux-only three-minute service timeout does not apply
here.

### Test, install, and enable

Run one sync as `mac_user`, using the daemon's `PATH`. Do not use `sudo` for
this test. Stop if it fails and resolve the reported problem before installing
the daemon.

```sh
env -u SSH_AUTH_SOCK \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  python3 ~/.local/bin/sync-skills ~/github/gianpaj/skills
```

Expect `Skills sync OK: master at` followed by a commit hash. Install the plist
as root-owned and readable by launchd, then enable and load it:

```sh
sudo install -o root -g wheel -m 644 \
  ~/.local/state/skills-sync/com.gianpaj.skills-sync.plist \
  /Library/LaunchDaemons/com.gianpaj.skills-sync.plist
sudo launchctl enable system/com.gianpaj.skills-sync
sudo launchctl bootstrap system /Library/LaunchDaemons/com.gianpaj.skills-sync.plist
sudo launchctl print system/com.gianpaj.skills-sync
```

`bootstrap` starts the first scheduled sync through `RunAtLoad`. Do not repeat
`bootstrap` while the job is loaded. To replace its configuration, unload it
first using the operations section below, then install and load the plist.

After the first run finishes, and again after five minutes, check the status,
logs, and revisions:

```sh
sudo launchctl print system/com.gianpaj.skills-sync
tail -n 20 ~/Library/Logs/skills-sync/stdout.log
tail -n 20 ~/Library/Logs/skills-sync/stderr.log
git --no-pager -C ~/github/gianpaj/skills rev-parse HEAD refs/remotes/origin/master
```

Expect `last exit code = 0` after a completed successful run and a success line
in `stdout.log`. The two Git hashes should match. `state = not running` is
normal between runs. Error logs retain earlier failures, so use the latest exit
code and success entries to check recovery.

### macOS operations and failures

Start an immediate sync through the loaded daemon:

```sh
sudo launchctl kickstart system/com.gianpaj.skills-sync
```

Do not add `-k`; it kills an active run. launchd runs only one instance of the
job at a time, and the Python lock also prevents overlap with manual syncs.

To pause before editing the checkout or replacing the installation, hold the
sync lock while unloading the daemon. This waits for an active sync to finish
and prevents another run from starting Git work during unloading. Run it as the
checkout owner, not root:

```sh
python3 - <<'PY'
import fcntl
import subprocess
from pathlib import Path

with (Path.home() / ".local/state/skills-sync/sync.lock").open("a") as lock:
    print("Waiting for any active skills sync to finish", flush=True)
    fcntl.flock(lock, fcntl.LOCK_EX)
    subprocess.run(
        [
            "sudo", "launchctl", "bootout", "system",
            "/Library/LaunchDaemons/com.gianpaj.skills-sync.plist",
        ],
        check=True,
    )
PY
```

Unloading pauses the job until it is loaded again or the Mac reboots. Resume
with:

```sh
sudo launchctl bootstrap system /Library/LaunchDaemons/com.gianpaj.skills-sync.plist
```

To disable it across reboots:

```sh
sudo launchctl disable system/com.gianpaj.skills-sync
```

Then use the lock-protected pause command above if the job is still loaded.

To resume a disabled job, run `enable` and `bootstrap` from the installation
section. Check disabled overrides with:

```sh
sudo launchctl print-disabled system
```

A refusal or authentication failure exits with code 1 and records the reason in
`stderr.log`. The next interval retries; `KeepAlive` is not enabled, so a
failure does not trigger a rapid restart loop. Correct the underlying issue,
then use `kickstart` or wait for the next interval. The checkout safeguards in
[Behavior](#behavior) apply on both platforms.

launchd appends to the log files without rotating them. Check their size
periodically and archive or truncate them while the daemon is unloaded.

To read the logs on `macos_machine` from another computer, without `sudo`:

```sh
ssh macos_machine 'tail -n 20 ~/Library/Logs/skills-sync/stdout.log'
ssh macos_machine 'tail -n 20 ~/Library/Logs/skills-sync/stderr.log'
```

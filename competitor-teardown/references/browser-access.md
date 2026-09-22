# Browser access

Use agent-browser for browsing and screenshots. The
[agent-browser requirement and stop condition](../SKILL.md#choose-browser-access-with-a-small-test)
also apply to setup and cleanup. Read the installed CLI's authentication
guidance before choosing an export method.

## Choose the export scope

Prefer built-in `state save` and `--state` for a browser dedicated to the target
app. No custom exporter is needed for that case.

Do not assume `state save` exports only the selected site's cookies. A
controlled two-origin test with agent-browser 0.38.1 exported both sites'
cookies, plus storage for origin A. Importing that file authenticated a fresh
browser to both sites. The result was the same for an owned browser and a
CDP-attached session. See
[Tested workflow](tested-workflow.md#built-in-export-scope-test).

For personal Chrome containing unrelated logins, use a pinned attached session
without export, or the scoped helper below when headless reuse is authorized.
The helper is retained for this demonstrated scope difference, not because
built-in auth reuse fails. If a later CLI version offers origin-scoped export,
test it with the synthetic harness and prefer the built-in option when it meets
the same boundary.

## Built-in export and headless import

Confirm the intended source browser, tab, and organization through
agent-browser. Set these variables from observed values:

```bash
TEARDOWN_URL='https://app.example.com/workspace/dashboard'
TEARDOWN_SOURCE='verified-dedicated-source'
TEARDOWN_SESSION="teardown-$(date +%s)-$$"
TEARDOWN_AUTH_DIR="$(mktemp -d "${TMPDIR:-/tmp}/teardown-auth.XXXXXX")"

# Source must already be connected to the verified dedicated browser.
(umask 077; agent-browser --session "$TEARDOWN_SOURCE" \
  state save "$TEARDOWN_AUTH_DIR/state.json")

agent-browser --session "$TEARDOWN_SESSION" \
  --state "$TEARDOWN_AUTH_DIR/state.json" open "$TEARDOWN_URL"
```

The documented `agent-browser --auto-connect state save <path>` is also valid
when discovery selects the intended browser and its entire export scope is
appropriate. Auto-connect changes how the source is found; it is not an origin
filter. Do not use it blindly with personal Chrome.

Use a fresh destination session name. `--state` is a launch setting; an already
running session can ignore launch options. Do not add `--restore` unless
persistent credentials are requested. Never print exported state, put it in the
research output, commit it, or upload it.

## Scoped export from personal Chrome

The helper requires Node.js with built-in WebSocket support, tested with Node
24, and a loopback CDP connection. It selects exactly one tab by full URL, reads
that origin's localStorage/sessionStorage, and requests cookies applicable to
that URL and origin root. It does not copy the Chrome profile or read its
on-disk cookie database.

```bash
# Use the observed endpoint and exact authorized tab URL.
TEARDOWN_CDP='ws://127.0.0.1:9222/devtools/browser'
node /path/to/competitor-teardown/scripts/export-origin-state.mjs \
  "$TEARDOWN_CDP" "$TEARDOWN_URL" "$TEARDOWN_AUTH_DIR/state.json"

agent-browser --session "$TEARDOWN_SESSION" \
  --state "$TEARDOWN_AUTH_DIR/state.json" open "$TEARDOWN_URL"
```

The helper creates a new file with mode 0600, refuses overwrite, and prints
counts only. It does not export IndexedDB, service workers, other origins, or
browser-bound credentials. A path-specific cookie used only on another endpoint
may be absent.

## Connection setup and verification

If the current setup cannot use agent-browser, stop and require human
confirmation under the main skill's rule. If debugging must be enabled, ask the
user to enable it through Chrome's `chrome://inspect/#remote-debugging` page and
confirm readiness. Do not use Computer Use. If Chrome requires a connection
prompt agent-browser cannot handle, ask the user to complete it.

Record the original debugging state. Do not assume port discovery works: in the
tested Chrome build, `/json/version` returned 404 while the observed
`ws://127.0.0.1:9222/devtools/browser` endpoint worked. This endpoint is not a
universal constant.

After import, verify loaded authenticated content and the intended workspace,
then visit another protected route. A non-login URL alone is insufficient.
Session expiry, token rotation, device binding, anti-bot rules, and
identity-provider dependencies can prevent reuse.

Once import succeeds, restore debugging if this task enabled it. If that
requires browser UI outside agent-browser, ask the user to disable it and record
whether they confirmed completion. Confirm the headless session still loads the
app independently.

## Existing-browser option

```bash
agent-browser --session teardown-attached connect "$TEARDOWN_CDP"
agent-browser --session teardown-attached tab list
# Replace t1 with the verified target tab ID.
agent-browser --session teardown-attached --pin-tab tab t1
agent-browser --session teardown-attached --pin-tab snapshot -i
```

Pinning keeps the user's browsing from redirecting automation into another tab.
This avoids exporting auth but can include extension overlays and viewport
interference. If neither import nor attached agent-browser access works with the
current setup, stop and require human confirmation. Do not switch browsing tools
automatically.

## Cleanup

Remove the temporary export after successful loading if no restart needs it.
Close only the owned destination browser when finished:

```bash
agent-browser --session "$TEARDOWN_SESSION" close
rm -f "$TEARDOWN_AUTH_DIR/state.json"
rmdir "$TEARDOWN_AUTH_DIR"
```

Do not call Close or clear cookies on a session attached to personal Chrome.
Close the owned browser rather than signing out of the app; sign-out may
invalidate the original shared login.

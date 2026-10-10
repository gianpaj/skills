# Capture workflow

Use installed agent-browser documentation for exact syntax. The commands below
were exercised with 0.38.1; check the installed version before copying them.

## Calibrate before batching

Prove one loaded route, one meaningful interaction and one readable capture
before repeating the pattern. Choose a ready condition that proves the content
of interest arrived: a loaded media name, billing meter or data row is stronger
than a heading rendered beside placeholders. Prefer semantic waits to fixed long
sleeps; after a short transition delay, still verify the expected state.

```bash
agent-browser --session "$TEARDOWN_SESSION" open "$PAGE_URL" &&
agent-browser --session "$TEARDOWN_SESSION" wait --text 'A unique loaded value' &&
agent-browser --session "$TEARDOWN_SESSION" screenshot "$SCREENSHOT_PATH"
```

Batch only steps with verified selectors and explicit postconditions. Stop at an
unmatched selector, timeout or unexpected state. Do not run the remaining
captures after a failed interaction, or repeat an unverified helper across
similar forms. Independent local file checks can run together; dependent browser
actions remain sequential.

Use `snapshot -i` to locate controls and refresh refs after navigation or a
substantial state change. Use a scoped snapshot or visible explanatory copy when
the compact version omits context. Read short relevant excerpts instead of
dumping entire pages into the conversation. Keep unrelated personal data out of
public artifacts.

## Check what an interaction changed

After a click, verify the expected selected tab, checked value, expanded menu,
new fields or dialog. Command success alone proves none of those. If unchanged:

1. Check whether the target finished mounting and is the visible control.
2. Refresh the snapshot and match its actual role/name, label or title. Icon
   buttons may use `title`; text and accessible names can differ.
3. Retry with the installed CLI's documented locator action. If needed, inspect
   the observed DOM and use a normal DOM click on one uniquely matched visible
   element. Assert that a match exists; a null optional-chain click can succeed
   without doing anything.
4. Verify the postcondition. If still unchanged, record the failed branch and
   its limit instead of manufacturing a screenshot or repeatedly changing
   interaction techniques.

Timing, hidden duplicate controls and pointer-driven widgets can produce similar
symptoms. Do not diagnose a browser bug from one no-op, dispatch a blanket
sequence of synthetic events, or change application state through internal APIs.

A modal close can be asynchronous. Wait for the specific canceled dialog to
disappear before using the underlying page. If another dialog should remain, do
not wait for every dialog to disappear or read the first dialog in the DOM.
Inspect the active visible dialog and its heading.

```bash
# Appropriate only when this page should have no remaining dialog.
agent-browser --session "$TEARDOWN_SESSION" wait \
  --fn '!document.querySelector("[role=dialog]")'
agent-browser --session "$TEARDOWN_SESSION" snapshot -i
```

Confirm menu dismissal too; Escape may leave a menu open. Hidden catalogue
options can appear in `innerText` without being visible in the active menu. Use
the rendered menu and snapshot to substantiate selectable choices, and record
virtualized or inaccessible portions as unverified.

## Keep tab, URL and viewport aligned

After actions that can open another page, inspect `tab list`, select the
intended owned tab, and verify its actual URL and viewport before continuing. A
blank popup is an observed failure, not a connected integration. Follow the
pinning guidance in [Browser access](browser-access.md) for personal Chrome.

New tabs can have different dimensions. Reapply the intended viewport to the
selected capture tab, then inspect the first image before resuming a batch.
Record the actual capture URL rather than copying the requested URL into every
caption. Include important resource parameters and redirects.

For a loading or connection failure, inspect app-origin request metadata only
when it can resolve the question. Scope to the observed app origin/path and
redact secret query values. Broad matches for `api` can collect analytics and
personal data. Do not dump response bodies or infer a private backend contract
merely to complete a UI teardown.

## Full-page does not mean every scroll panel

Try a normal and `--full` capture on one long page. If the bottom is absent,
inspect scroll geometry rather than repeatedly requesting full-page screenshots:

```bash
agent-browser --session "$TEARDOWN_SESSION" eval '({
  viewport: [innerWidth, innerHeight],
  documentHeight: document.documentElement.scrollHeight,
  scrollContainers: [...document.querySelectorAll("*")]
    .filter(e => e.scrollHeight > e.clientHeight + 5 &&
      /(auto|scroll)/.test(getComputedStyle(e).overflowY))
    .map(e => ({tag:e.tagName, role:e.getAttribute("role"),
      height:e.clientHeight, scrollHeight:e.scrollHeight}))
})'
```

If the document is one viewport high and a child is much taller, the child owns
scrolling. Prefer a taller viewport at a consistent width and scale, or scroll
the actual panel and take overlapping captures.

```bash
agent-browser --session "$TEARDOWN_SESSION" set viewport 1440 1850 1
agent-browser --session "$TEARDOWN_SESSION" screenshot "$SCREENSHOT_PATH"
# For still-longer content, use an observed ref near the lower section.
agent-browser --session "$TEARDOWN_SESSION" scrollintoview @e123
agent-browser --session "$TEARDOWN_SESSION" screenshot "$LOWER_SCREENSHOT_PATH"
```

These dimensions are a starting point, not a completeness test. Verify the last
control or footer in the actual image before calling a capture complete. Keep
enough overlap to establish that upper and lower captures belong to the same
state. A larger image can still clip a nested panel.

## Evidence quality and local checks

Record path, actual URL, section, viewport, state and saved/draft status in the
ledger or screenshot index. Capture menus open, drawers expanded and restored
settings when relevant. Wait for the visible final state after transitions; a
skeleton is not an empty-state finding. Reuse shared evidence and capture
branches that add information, without arbitrary screenshot quotas.

Preserve baseline and historical captures. A restored state belongs in a new
file with its own caption; do not overwrite the baseline with it. Replace a
failed capture only after verifying the same intended state, and update its
references. Retain evidence of a meaningful failure when it supports a finding.

Use a contact sheet to catch blank/loading frames, unexpected dimensions and
repeated states. Inspect dense settings and suspicious thumbnails individually
at readable resolution. A local gallery is optional; captions and links to
original images matter more than its styling.

Run the bundled file checker against the current visit:

```bash
python3 /path/to/competitor-teardown/scripts/check-evidence.py "$OUTPUT_DIR" \
  --expected-width 1440
```

Repeat `--expected-width` for intentionally mixed sizes. The Python 3 helper
checks local Markdown links, HTML `href`/`src` targets, PNG structure/dimensions
and byte-identical PNGs. It reads files without changing them and makes no
network requests. Missing targets or invalid PNG structure fail; width and
duplicate warnings need review. It does not check anchors, full Markdown syntax,
image rendering, semantic coverage, captions, privacy or restoration.
Decode/view the images and review the ledger separately; a clean file check
cannot certify a full assessment.

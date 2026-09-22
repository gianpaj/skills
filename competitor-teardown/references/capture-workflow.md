# Capture workflow

Use installed agent-browser documentation for exact syntax. These patterns were
exercised with 0.38.1.

## Readiness and batching

```bash
agent-browser --session "$TEARDOWN_SESSION" open "$PAGE_URL" &&
agent-browser --session "$TEARDOWN_SESSION" wait --text 'A unique loaded value' &&
agent-browser --session "$TEARDOWN_SESSION" screenshot "$SCREENSHOT_PATH"
```

Choose a ready condition that proves the content of interest arrived. A heading
can render while the data and toggles are still placeholders. Waiting for a
loaded media name, populated billing meter, or specific data row is stronger.
Inspect the result before deciding the next action.

A modal close can be asynchronous. After canceling, wait for the modal to
disappear before using the underlying page. If another dialog is expected to
remain, wait for the specific canceled dialog rather than every dialog.

```bash
agent-browser --session "$TEARDOWN_SESSION" wait \
  --fn '!document.querySelector("[role=dialog]")'
agent-browser --session "$TEARDOWN_SESSION" snapshot -i
```

Use `snapshot -i` to locate controls; use a scoped snapshot or visible text when
the compact version omits explanatory copy. Save a local evidence excerpt if
needed, not repeated whole-page dumps in the conversation. Keep snapshots out of
public artifacts when they include unrelated personal information.

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
scrolling. Prefer:

- A taller viewport at a consistent width and scale, followed by a normal
  screenshot.
- Scrolling the actual panel or bringing an observed lower control into view,
  followed by overlapping captures.

```bash
agent-browser --session "$TEARDOWN_SESSION" set viewport 1440 1850 1
agent-browser --session "$TEARDOWN_SESSION" screenshot "$SCREENSHOT_PATH"
# For still-longer content, use an observed ref near the lower section.
agent-browser --session "$TEARDOWN_SESSION" scrollintoview @e123
agent-browser --session "$TEARDOWN_SESSION" screenshot "$LOWER_SCREENSHOT_PATH"
```

The dimensions above are a tested starting point, not a universal requirement.
Inspect the image at readable resolution. A correct pixel size can still contain
a clipped panel. Keep enough overlap to establish that upper and lower captures
belong to the same state.

## Evidence quality

Record the URL, section, state, and whether edits are saved or draft. Capture
menus open, detail drawers fully expanded, and the final restored state when
settings were changed. A screenshot of a blank skeleton is not an empty-state
finding.

Use a contact sheet to catch blank/loading frames and duplicate states. Inspect
dense settings and suspicious thumbnails individually. Build a local gallery
only if the volume makes it useful; add captions and links to
original-resolution images. Verify links and decode images before delivery. Do
not add arbitrary screenshot quotas or recapture unchanged screens solely to
increase the count.

---
name: competitor-teardown
description:
  Tear down a public or logged-in competitor website or app. Explore product
  features, workflows, settings, and conditional UI, capture screenshots, and
  write an evidence-backed assessment. Supports first-time research and optional
  comparisons with earlier visits; no prior teardown is required. Not for
  finding hidden hosts or auditing source code.
---

# Competitor teardown

Produce a dated product assessment with screenshots that show both the ordinary
pages and the meaningful options hidden behind controls. Separate what the
product exposes from what was exercised successfully.

## Establish the scope

Start from the supplied website, app URL, or accessible browser session. A prior
teardown and a logged-in account are optional. Confirm the requested product,
environment, available access, and output directory from context; identify the
organization only when the app has one. Honor an explicit request to stop if a
particular session is unavailable.

For a first visit, document the product's features, main workflows, navigation,
settings, integrations, and visible plan or access limits. Use public pages and
interactive demos when signed out. Distinguish marketing claims from behavior
observed in the product, and record login-gated areas as uninspected rather than
missing features. Do not require account creation just to begin public research.

Use the supplied date/path when explicit. Otherwise create
`YYYY-MM-DD-<product>` in the project's existing competitive-research directory,
or `competitive-research/` under the current workspace if no convention exists.
Use the local date.

If earlier research is available, read it and the relevant screenshots before
making change claims. Add a comparison without making it a prerequisite for the
teardown. Preserve historical evidence. A feature omitted from an earlier report
is newly observed, not necessarily newly shipped. Production onboarding and a
staging subscription page are different baselines.

## Choose browser access with a small test

Use agent-browser for all website navigation, interaction, and screenshot
capture. Read its version-matched core guide and only the relevant command
references. Do not automatically fall back to Computer Use, desktop automation,
or other manual browsing tools, including for browser setup and permission
prompts.

If the target website and current local setup cannot use agent-browser, stop the
browser walkthrough. State the specific blocker and the checks already made,
explain the proposed setup change or alternative, and require explicit human
confirmation before proceeding. A general teardown request is not approval to
switch tools. If setup needs a browser UI action, ask the user to perform it; do
not operate that UI yourself unless the user explicitly approves that exception.

For a public site, start a fresh headless agent-browser session and inspect the
accessible pages directly. No auth export is needed.

For an authenticated session, prefer a temporary headless browser when
authorized auth reuse passes a smoke test. Use built-in `state save` and
`--state` for a dedicated source browser. For personal Chrome with unrelated
logins, use pinned agent-browser access or the scoped helper: the controlled
test confirmed that built-in export includes unrelated cookies. See
[Browser access](references/browser-access.md) for the tested choices. Verify
the expected tenant and loaded authenticated content, not merely a non-login
URL.

This isolates tabs, extensions, viewport, and browser storage. **It does not
isolate server-side data.** A setting changed headlessly still changes the real
account.

If import fails, try an accessible existing session through agent-browser with a
pinned tab, or an authorized login in a dedicated agent-browser session. These
remain agent-browser workflows. If neither works with the current setup, apply
the stop-and-confirm rule above. Do not spend the teardown reverse-engineering
authentication. Avoid relaunching personal Chrome or copying its live profile.

## Map once, then explore by section

Capture the loaded navigation and make a short coverage ledger as you work:

| Route/view | Loaded state | Conditional states | Evidence | Restoration/limit |
| ---------- | ------------ | ------------------ | -------- | ----------------- |

Map the main product capabilities and user workflows, then visit each distinct
accessible section and its tabs. Include public product pages or demos when that
is the available access. Within a section, inspect the controls that change what
a user can see or do:

- Master switches, dependent switches, advanced sections, accordions.
- Dropdown choices that expose different fields or behaviors.
- Add/edit forms, empty states, filters, detail drawers, and overflow menus.
- Lower scroll regions, previews, integration setup entry points, and plan
  comparisons.

Capture meaningful branches, not every combination of independent choices. One
menu capture can document twenty voice choices; selecting every voice adds
little unless its behavior changes. Stop a branch at the boundary of the
authorized exploration, or when progressing requires unavailable data or a
consequential submission. Record the boundary precisely.

Do not infer absent features from a master-off state, a loading skeleton, or a
disabled control before data arrives. A catalogue entry proves availability in
the UI, not that the integration works.

## Explore settings without losing the original state

Before an authorized toggle, record its loaded value, dependent values, and
visible save/reset behavior. Keep this next to its screenshot reference. A
master toggle can persist immediately while adjacent fields use Save.

For each group: capture baseline, reveal its meaningful states, then
reset/discard and verify the loaded state after reload or revisit. Capture the
verified final state when restoration matters. Do not leave restoration until
the end of a large walkthrough.

Enabling a feature can initialize keys, associations, schedules, or other
configuration. Switching it off may not reverse that initialization. Check
dependencies before enabling; do not invent a placeholder association just to
expose a screen. If an authorized action leaves a value with no UI undo, report
it explicitly and avoid undocumented API workarounds.

A fresh browser is not a rollback mechanism. No Save click is not proof that
nothing persisted. Avoid submitting messages, invitations, purchases,
connections, registrations, or destructive actions merely to inspect the next
screen. If a disposable workflow is explicitly authorized, record what was
created and how it was cleaned up.

## Capture efficiently and verify visually

Use [Capture workflow](references/capture-workflow.md) for command patterns and
scroll diagnostics.

Batch a known navigation, its semantic ready condition, and screenshot in one
invocation. Keep adaptive choices sequential. Use compact snapshots for controls
and scoped/full text only when needed for labels and explanatory copy. Reacquire
refs after navigation or modal transitions; do not carry stale refs across
pages.

Wait for loaded values or unique content, not a nav label shared by every page.
Allow drawer animation to settle. Fixed long sleeps waste time and still fail on
slower pages.

Test `screenshot --full` once on a long page and inspect the image. Nested
scroll panels can remain clipped even in headless Chrome. Use a taller viewport
or overlapping captures of the actual scroll container. Preserve real UI layout;
do not unhide elements or rewrite page CSS to manufacture evidence.

Name captures by section and state, such as `ai-agent-off`, `ai-agent-advanced`,
and `routing-restored`. Give each image a short caption identifying saved,
draft, or final state. Review contact sheets and inspect dense or suspicious
images at full resolution. Replace loading, clipped, or unfinished-animation
captures. Do not equate file count with coverage.

## Deliver the teardown

Adapt the package to the request. Useful outputs for either a first visit or a
repeat teardown are:

- A dated product assessment with linked evidence, a feature and workflow
  inventory, settings and conditional behavior, product implications, and access
  or testing limits. When earlier evidence exists, add confirmed changes and
  newly observed details as a comparison.
- Original screenshots, an index or local gallery, and the coverage/restoration
  ledger.

Keep facts, UI claims, and interpretation distinct. Account values are not
product defaults; staging prices are not verified public pricing. Correct an
earlier conclusion when deeper inspection contradicts it. Make product
recommendations traceable to observed friction or capabilities.

Check image readability, relative links, missing files, and the final account
state. Keep auth exports out of the report and repository. Close only the
browser session created for this work, remove temporary auth files, and restore
debugging if it was enabled for the task. Report saved outputs and any
persistent changes or uninspected branches plainly.

For evidence behind the headless workflow, see
[Tested workflow](references/tested-workflow.md). Its timings and product
observations are a local test, not universal performance guarantees.

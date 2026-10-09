---
name: competitor-teardown
description:
  Tear down a public or logged-in competitor website or app. Explore workflows,
  settings and meaningful UI branches, capture evidence, and write a product
  assessment with access limits and optional comparisons with earlier visits.
  Not for hunting hidden hosts or auditing source code.
---

# Competitor teardown

Explain what the product lets a user accomplish, how its configuration works,
and where access or testing stops. Separate visible controls, published claims
and successfully exercised behavior.

## Establish scope and completion

Start from the supplied URL or accessible session. Identify the requested
product, account/workspace, access level, comparison target and output location
from context. A prior report or authenticated account is optional. Preserve
resource-identifying URL parameters until observed navigation establishes an
alternative. A hostname containing dev, staging or k8s does not prove a sandbox.
When signed out, cover public pages and demos without making registration a
prerequisite.

Use the supplied date/path when explicit. Otherwise use the local date under the
project's existing competitive-research directory, or
`competitive-research/YYYY-MM-DD-<product>/`. Keep distinct visits or account
states in separate subdirectories. Read relevant earlier evidence before making
change claims; omitted features are newly observed, not necessarily newly
shipped.

A full teardown covers distinct accessible sections, meaningful conditional
states and the main user journeys. Record a precise reason for each uninspected
branch. Do not add subdomain hunting, repeated registration, promo-code trials,
source auditing or backend reverse engineering unless requested. Relevant
official documentation can fill evidence gaps, with its source level stated.

## Choose browser access with a small test

Use agent-browser for all website navigation, interaction and screenshot
capture. Read its installed, version-matched guide and relevant references. Do
not automatically switch to Computer Use or another browser tool for setup,
permissions or browsing.

If the current setup cannot run agent-browser against the target, stop the
walkthrough. Report the concrete failure, checks made and proposed setup change
or alternative, and require explicit human confirmation. Honor approval already
given in the conversation; do not ask again for the same authorized workaround.
If a required browser UI action is unavailable through agent-browser, ask the
user to perform it unless they explicitly authorize that exception.

Start a dedicated named session for public access or an authorized login. For
auth reuse, read [Browser access](references/browser-access.md). Prefer built-in
state export from a dedicated source browser; personal Chrome requires pinned
access or the origin-scoped helper. Verify loaded content in the intended
workspace, not just a non-login URL. Never include credentials or auth exports
in research artifacts.

A fresh browser isolates browsing state, not server-side data. Use a stable
session, launch options and selected tab throughout the run. Apply the bounded
setup checks in the browser-access reference instead of repeatedly trying
unrelated launch combinations or reverse-engineering authentication.

## Map, explore and close branches

Read [Assessment workflow](references/assessment-workflow.md) when planning
coverage and writing the report. Start a compact ledger before exploring:

| Route/view | Loaded state | Branch/status | Evidence | Side effect/restoration/limit |
| ---------- | ------------ | ------------- | -------- | ----------------------------- |

Use statuses such as queued, inspected, blocked and intentionally skipped.
Resolve each mapped section once; shared controls need one representative
capture unless their behavior differs. Record redirects and the actual final
URL. A blocked section does not need repeated route guesses. Revisit it when new
access or evidence changes the blocker.

Trace the main journey from setup to test/activation, operational review and
maintenance as access permits. In each section inspect tabs, advanced settings,
menus, dependent fields, add/edit forms, lower scroll regions and limits.
Capture branches that change behavior or available fields. A voice/language menu
can establish choices without selecting every item. Do not treat loading,
master-off, unconnected or empty-history states as missing features.

Before batching, prove one representative navigation and interaction, including
its expected visible result. A CLI success message is not evidence that a tab,
radio, menu or dialog changed. Use the verified interaction and capture patterns
in [Capture workflow](references/capture-workflow.md). Stop a failed batch at
the first unmet condition; diagnose that step before producing more artifacts.

## Preserve account state

Record loaded values and save behavior before changing a setting. Master
switches can persist immediately or initialize resources even when neighboring
fields use Save. Opening a form may expose existing configuration or a new
draft; identify which. Do not enable a feature merely to reveal fields if its
side effects are unknown.

Capture baseline, inspect a meaningful branch, cancel/discard, then reload or
reopen and verify within that section. Check both the field values and whether
an action/resource was created. A regenerated blank draft is not proof that a
saved configuration was rolled back. No Save click is not proof of no writes.

Mandatory onboarding is also a write. Use supplied facts and authorization; ask
for required missing answers instead of inventing a company profile to unlock
the dashboard. Record survey submissions, imports and generated resources
separately from assistant settings. Disclose changes with no UI undo; do not use
undocumented APIs to conceal them.

Do not submit purchases, calls, messages, invitations, connections or
destructive actions merely to inspect the next screen. Continue an explicitly
authorized disposable workflow only within its stated scope, recording creation
and cleanup. An ambiguous payment environment is not a confirmed sandbox.

## Capture and deliver

Capture a representative baseline and the states needed to substantiate
findings. Check the first screenshots before scaling up. Record the actual URL,
account context, viewport and saved/draft state alongside evidence. Nested
scrolling, popup tabs and animation can spoil otherwise successful captures;
diagnose them using the capture reference. Do not unhide elements or rewrite CSS
to create an accessible screen.

Write the assessment while resolving the ledger, rather than reconstructing it
from screenshots at the end. Lead with the product's value, operating model and
material limits. Cover workflows, settings, integrations, packaging, observed
friction, comparison implications and specific unknowns. Keep UI claims,
documentation, runtime tests and interpretation distinct. Account values are not
product defaults, catalogue entries are not working integrations, and a custom
voice name is not a TTS provider/model ID.

Deliver a dated assessment, original screenshots with useful captions, and the
coverage/restoration ledger. A screenshot index can live in the ledger; use a
separate gallery only when it helps review. Preserve historical captures and add
follow-up links when correcting an earlier access conclusion.

Run the local checks described in Capture workflow, review contact sheets and
inspect dense or suspicious images individually. Verify final account state.
Close only the research browser owned by this task, remove its temporary auth
files and restore debugging if this task enabled it. Report outputs, persistent
changes and consequential untested behavior plainly.

[Tested workflow](references/tested-workflow.md) records the experiments behind
these choices. Its observations are local evidence, not universal app or CLI
behavior.

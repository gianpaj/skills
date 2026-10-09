# Tested workflow

Tested September 17, 2026 on macOS with agent-browser 0.38.1, Node.js 24.9.0, an
existing signed-in Chrome tab, and Hello Hotel staging. This records the
evidence behind the access and capture guidance. It does not establish support
for every app or a speedup factor against interactive Chrome.

## Authentication experiment

<!-- prettier-ignore -->
| Check | Observed result |
| --- | --- |
| Fresh headless browser, no import | Protected dashboard redirected to sign-in |
| Scoped export from signed-in personal Chrome | Four applicable cookies, two localStorage entries, one sessionStorage entry; no values printed |
| Fresh headless browser with `--state` | Dashboard loaded with expected organization and loaded attention-queue text |
| Headless verification | User agent contained `HeadlessChrome` |
| Personal Chrome debugging disabled after export | Headless AI settings, Dashboard, Billing, and Organization continued loading |
| Expanded AI settings | Master switch and advanced section revealed the controls seen in attached Chrome |
| Restoration | Reset, reload, and DOM check confirmed the AI master off |
| Cleanup | Both owned headless test browsers closed; three temporary auth/schema exports deleted; personal Chrome debugging checkbox verified off |

The export uses ordinary CDP cookie/storage access to an authorized tab. It does
not copy the Chrome profile or decrypt the on-disk cookie store. A synthetic
unrelated-domain cookie, inserted only into the isolated test browser, was
excluded from a subsequent scoped export.

The helper was checked for mode 0600, one-origin output, rejection of nonlocal
endpoints, rejection of missing arguments and missing exact tabs, and refusal to
overwrite an existing file. Its JavaScript syntax check passed. Existing-file
rejection preserved the file hash.

## Capture timing sample

Each measurement included three sequential CLI commands: navigate to a protected
page, wait for a specific loaded value, and save a screenshot. The browser was
already running with the imported session and a 1440 × 1850 viewport.

<!-- prettier-ignore -->
| Page | Ready condition | Elapsed |
| --- | --- | ---: |
| Dashboard | No missed calls waiting | 1.20 s |
| Billing | AI credits | 1.41 s |
| Organization | Booking.com in the loaded exclusions section | 1.34 s |

Total was 3.95 seconds for nine commands across three pages. This excludes
setup, Chrome permission handling, screenshot inspection, reasoning, and report
writing. There was no controlled timing comparison with attached Chrome. The
demonstrated advantages were independent navigation, no personal-browser
extensions, and predictable capture dimensions.

## Full-page capture experiment

The headless AI settings page had a 1280 × 577 viewport and a document height
of 577. Its inner scrolling div had a client height of 532 and content height
of 1769. `screenshot --full` captured only the upper content.

At 1440 × 1850, a normal screenshot contained the entire expanded AI form,
including the lower transcription selector and Reset/Save buttons. Both images
were inspected. Headless mode does not fix nested scrolling; viewport or
panel-scroll handling is still necessary.

## Scope of the result

The small test supports scoped import as the first option for this app when
reuse is authorized. It does not prove that refresh tokens, MFA,
IndexedDB-backed sessions, device-bound sessions, anti-bot flows, or other
identity providers will transfer. Use the smoke test and fallback described in
[Browser access](browser-access.md).

The broader teardown also demonstrated that a toggle can save immediately and
initialize configuration even when the surrounding form uses Save. Browser
isolation is therefore a convenience for automation, not protection against
changes to the account.

## Built-in export scope test

Tested September 17, 2026 with agent-browser 0.38.1. A temporary local HTTP
server exposed two origins through different hosts, `127.0.0.1` and `localhost`.
Each received a distinct synthetic session cookie, localStorage marker, and
sessionStorage marker. No personal browser or real account participated.

A fresh browser showed Signed out without import. Both an owned browser and a
CDP-attached session exported state using built-in `state save`. A fresh
headless destination then loaded the attached export with `--state`.

<!-- prettier-ignore -->
| Export | Cookies included | Origin storage included | Fresh destination result |
| --- | --- | --- | --- |
| Built-in, owned source | A and B | A | Export scope matched the attached case |
| Built-in, CDP-attached source | A and B | A | Both sites authenticated; A storage restored, B storage absent |
| Scoped helper | A only | A | A authenticated; B remained signed out |

The helper therefore addresses a demonstrated boundary: avoiding unrelated
session-cookie export from personal Chrome. Built-in export remains the
preferred route for a dedicated source browser. Neither method was tested with a
device-bound session or a real third-party identity provider in this experiment.

Run the synthetic regression test with:

```bash
python3 scripts/test-state-scope.py
```

It starts its own local server and named headless sessions, checks the observed
export/import behavior and helper exclusion, then closes its owned browsers and
deletes state exports. It retains a synthetic-only JSON summary in the printed
temporary directory. The assertions intentionally flag changed CLI behavior so
the documented choice can be reassessed after an upgrade. This tests explicit
CDP attachment, not auto-discovery of personal Chrome.

## Fonio assessment review

Reviewed the October 9, 2026 public, payment-gated and accessible-dashboard
runs, including the active-dashboard assessment, coverage ledger and 100 PNG
captures. These are observations from that account and execution environment.
They do not establish a CLI defect, a staging payment environment or runtime
integration support.

<!-- prettier-ignore -->
| Observation | Consequence for the workflow |
| --- | --- |
| A supplied account remained payment-gated; a different working account exposed the editor | Keep account/entitlement evidence separate from host names and product-change claims |
| Some click/Escape commands reported success without the expected tab, radio, dialog or menu change | Verify one interaction and its postcondition before repeating it; the root cause was not established |
| A connection action opened a blank tab with a smaller viewport | Check the selected tab, actual URL and viewport before the next capture batch |
| Tall captures still clipped a nested settings panel | Verify the lowest control and scroll the actual panel; image height is not coverage |
| Overlapping dialogs and hidden menu content confused broad DOM/text reads | Identify the active visible dialog/menu and compare with the rendered image |
| A restored capture and baseline file were byte-identical | Preserve baseline evidence under its original identity; label restoration separately |
| Onboarding survey answers persisted while assistant forms remained unsaved | Report survey writes separately from draft/configuration restoration |
| Connector setup entries and Notify me cards disagreed across views | Record availability per surface; do not count catalogue entries as working integrations |
| UI voice/locale choices differed in scope from marketing counts; the engine/model was unconfirmed | Separate visible choices, published claims and technical unknowns |

A managed-terminal setup required adjusted Chrome runtime settings. Ending its
owning shell also ended the browser. This supports checking process lifetime and
reusing approved settings in that environment, not requiring those settings for
every teardown.

The assessment distinguished draft transfer/email/SMS configuration from actual
execution, and Test Context inputs from a staging environment. Web Search copy
limited the feature to fixed URLs. Existing generated answers described
different businesses, but their ingestion cause was not witnessed. These cases
support reading explanatory copy and reporting evidence strength, rather than
inferring capability from a feature name.

## Local evidence checks

The file checker is deliberately independent of browser access:

```bash
python3 scripts/test-check-evidence.py
python3 scripts/check-evidence.py /path/to/current-visit --expected-width 1440
```

Six synthetic tests exercise valid Markdown/HTML references, external and code
example exclusions, unchanged files, missing targets with query redaction,
corrupt/truncated PNGs, duplicate/width warnings and invalid arguments. They use
no network or accounts.

Against the active-dashboard artifacts, the checker inspected 191 local links
and 100 PNGs with no errors. A 1440-only width expectation flagged two
intentional 390 × 844 mobile captures; allowing both widths removed those
warnings. It also identified byte-identical transfer-entry/restored files. This
confirms the helper can flag structural review items, not that images are
readable, baseline labels are correct or the assessment is complete. No speed
comparison was measured.

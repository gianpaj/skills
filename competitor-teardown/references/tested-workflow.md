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

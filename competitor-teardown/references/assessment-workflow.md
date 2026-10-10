# Assessment workflow

Use this reference to choose coverage, resolve access limits and write the
assessment. The ledger is the working record; the report explains the product.

## Choose the questions before collecting screens

Infer the user's comparison target and decisions from the request. If absent,
assess the competitor on its own. Do not invent a home-product roadmap or write
an implementation plan. Identify the questions that would materially change the
assessment, then cover the navigation and those questions together.

Useful questions for a configured assistant product include:

- What gets a new account from signup to a useful test and live activation?
- Which behavior belongs in structured settings, prompts, knowledge or tools?
- How does a conversation become an owned action, booking or human handoff?
- What can operators review, correct and maintain after activation?
- Which resources, roles, quotas and paid gates constrain those workflows?

Adapt these to the product. A complete accessible walkthrough is not a runtime
validation of every advertised capability.

## Maintain one coverage record

Map distinct routes, tabs and shared resources from observed navigation. Include
baseline values, meaningful branches, actual URLs and screenshot references.
Update the record as each section closes. Record blocked branches with the
condition required to proceed, such as a calendar connection, paid entitlement,
existing conversation or unavailable credentials.

A coverage gap is resolved when it is inspected or its boundary is explicit. Do
not leave queued items hidden behind a large screenshot count. Resume a blocked
branch only when something relevant changes. For example, a working freemium
account justifies revisiting an editor blocked on a different account; a second
visit to the same unchanged payment gate does not.

Write short findings as you work: observation, evidence, implication and limit.
Shared menus and equivalent forms can share evidence. Separate phone, messaging
and web-chat behavior when their limits or setup differ.

## Make evidence strength visible

| Evidence                | What it establishes                            | What it does not establish                                |
| ----------------------- | ---------------------------------------------- | --------------------------------------------------------- |
| Loaded UI               | This account's visible values and controls     | Product defaults, all-account availability or enforcement |
| Exercised draft         | A control revealed fields or changed a preview | Saving, provisioning or successful execution              |
| Saved and reloaded      | A submitted configuration persisted            | That the configured action works                          |
| Runtime test            | The recorded scenario produced an outcome      | Reliability across untested failures or other accounts    |
| Official docs/marketing | A dated vendor claim or published example      | Behavior exercised in this session                        |
| Interpretation          | A conclusion grounded in named evidence        | A confirmed implementation detail                         |

State the level next to ambiguous claims; do not repeat it before every obvious
UI observation. Published screenshots belong under documentation evidence.
Opening a catalogue card establishes a setup entry point. Distinguish Available,
Get Started, early access, paid-only and Notify me/coming soon states. If two
screens disagree, record both and leave availability unresolved.

Numbers need context. Distinguish languages from locale variants, curated voices
from the provider's entire catalogue, included limits from purchasable capacity,
and monthly equivalents from yearly checkout totals. Read rendered input values;
placeholders and example JSON are not saved configuration.

## Follow consequential uncertainty with bounded research

Use official documentation, changelogs and provider disclosures to clarify a
material question left open by the UI. Keep web browsing under the main skill's
agent-browser requirement. Secondary articles can locate a primary source; do
not promote their assertion into a verified technical fact.

For voice/AI products, record the selectable voices, languages, model/provider
controls and any exposed IDs when relevant. If the UI omits provider/model,
check official docs and a primary disclosure or announcement. Separate the TTS
provider, model/version, voice preset or clone, STT and LLM. A provider named in
a processor list establishes a disclosed relationship, not which model powers
every voice. A self-developed-voice claim does not establish an independently
trained synthesis engine. Date conflicting statements and retain the
uncertainty.

Do not spend the rest of a product teardown extracting hidden architecture.
After these targeted checks, state the unknown and the evidence needed to settle
it. Expand into architecture investigation only if the user requests it.

Read explanatory copy, not just feature names. An action called Web Search may
read only fixed URLs. A Test Context may simulate inbound values without being a
staging environment. Check existing generated knowledge for entity/source
mismatches without attributing their cause to an unwitnessed ingestion step.
Inspect integration documentation for lookup, write and confirmation boundaries;
a long connector list does not measure workflow depth.

## Turn coverage into an assessment

Lead with the product's purpose, account access and the few findings that change
a comparison. Explain the main user journey and operating model before listing
settings. Keep the detailed values/branches in tables or the ledger so the prose
does not become a transcript of every click.

The report should answer:

- What is usable with this access, and what blocks the remaining workflow?
- How are setup, testing, activation, operational review and maintenance joined?
- Which settings materially change behavior, and what are their dependencies?
- Which limits, costs, roles and integrations are actually exposed?
- Where did the UI create friction or ambiguous expectations?
- What does the evidence imply for the user's stated comparison?
- What was changed, restored, submitted, or left untested?

Trace each recommendation to observed friction or a sourced capability. Use
concrete examples, such as a greeting lock preventing branding or an imported
answer describing the wrong business. Avoid a generic wish list or claims of
competitive superiority unsupported by common runtime tests.

When comparing visits, separate a changed product from a changed account,
entitlement, host or date. Preserve the old evidence, add a follow-up link, and
state what the new visit establishes. Do not treat omitted coverage as a feature
launch or an account-specific quota as universal pricing.

## Close with honest verification

Report restoration per changed group, including initialized resources and survey
answers. Distinguish values verified through the UI from a server-side audit. A
disabled master or 0 Changes counter alone does not prove that no write
occurred.

Check completion against the ledger. Identify important unknowns by the test
needed: live transfer rejection, recording refusal, ambiguous booking write,
role enforcement or concurrency under load. Never imply those tests ran because
the corresponding configuration form opened.

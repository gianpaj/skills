# Competitor teardown coverage and evidence

The skill uses one coverage/restoration ledger and verified interaction
postconditions to complete an accessible product assessment. Its main workflow
stays in `competitor-teardown/SKILL.md`; browser recovery, capture mechanics and
assessment criteria have focused references.

The Fonio runs exposed successful no-op commands, popup viewport changes,
nested-scroll clipping and ambiguous evidence of restoration. They also showed
that payment gates depend on account access, connector cards can disagree about
availability, and draft forms cannot establish runtime behavior. The dated
observations live in `references/tested-workflow.md` without assuming their
causes apply to every product.

The chosen approach verifies a representative interaction before batching,
resolves coverage gaps explicitly, and distinguishes UI, draft, persisted,
runtime and vendor evidence. It avoids screenshot quotas, exhaustive selection
of equivalent options, a report-generation framework and further authentication
machinery. Existing authentication helpers retain their tested behavior.

`scripts/check-evidence.py` checks local references, PNG structure, expected
widths and exact duplicates using Python's standard library. It cannot assess
image rendering, coverage, privacy or restoration. Six synthetic tests pass; the
Fonio artifact check reports 191 links and 100 PNGs without errors, with
intentional mobile widths and an identical entry/restored pair flagged for
review.

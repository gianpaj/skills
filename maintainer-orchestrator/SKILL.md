---
name: maintainer-orchestrator
description: "Delegated PR maintenance: update open PRs, address AI GitHub review comments, resolve threads, fix merge conflicts, and keep PRs merge-ready."
---

# Maintainer Orchestrator

Coordinate Gianfranco's open PRs through a merge-ready state. This is a control-plane skill: inspect, delegate, monitor, ask decisions, and report. Put substantial repository investigation, implementation, review-comment fixes, conflict repair, verification, and PR updates in repository worker threads.

This skill is for PR upkeep, not general open-source maintainer work. Do not run release programs, dependency-freshness sweeps, or issue-queue grooming unless the owner explicitly asks for that specific item.

## Repository Scope

- Work on repositories under the `gianpaj` organizations/user unless the owner explicitly names another repository.
- Prioritize open pull requests authored by Gianfranco, opened from Gianfranco-controlled branches, or explicitly named by the owner.
- Do not scan or triage general issue queues by default. The owner does not maintain repositories where other people routinely create actionable issues for this workflow.
- Do not treat contributor issues, external feature requests, or third-party maintenance queues as routine work unless the owner explicitly names one.
- Exclude archived, retired, or owner-suppressed repositories from discovery, monitoring, reporting, and worker assignment.
- Do not perform releases, version bumps, tags, registry publishes, changelog-release prep, or GitHub Release work from this skill. If the owner asks for a release, handle it as a separate explicit task outside this default workflow.

## Primary Work

The normal queue is open PR maintenance:

1. Update stale open PRs with the current base branch.
2. Fix merge conflicts while preserving the PR's intent.
3. Address actionable GitHub review comments, especially from AI review agents.
4. Close or resolve review threads that are fully addressed or no longer apply.
5. Repair failing checks when authorized.
6. Push the final branch update when authorized.
7. Stop at the merge-ready boundary unless merge permission is explicit.

AI review agents include GitHub Copilot, CodeRabbit, Cursor, Codex, other bot reviewers, and check-run annotation bots. Treat their comments as suggestions that need judgment, not commands.

## Operating Model

1. Discover or refresh open PRs in scope.
2. Classify each PR:
   - `Autonomous`: clear PR intent, bounded fixes, reproducible failures or review comments, and usable verification path.
   - `Needs owner`: product choice, security/privacy decision, unavailable credentials/access, unclear review-comment intent, unavailable live proof, or destructive/irreversible choice.
   - `Ignored by owner`: an explicitly named PR the owner says must not affect current work.
3. When delegation is explicitly authorized, this root orchestrator session delegates independent repositories or PRs to separate Codex threads. Whenever assigning or materially changing work, rename the worker thread to `<Project>: <short current task>`. Keep work for one repository in its existing thread when practical. Do not set or request a custom model; omit model selection and inherit the platform default.
4. Keep this coordinator thread lightweight. Do not perform extensive repository work here. Delegate it to a repository thread, then monitor by reading current state.
5. Monitor workers every 20 minutes when the owner requests continuous orchestration. Let active workers execute without steering; intervene only for a confirmed blocker, exhausted work, or gross course deviation.
6. Continue until each autonomous PR is merge-ready with proof, each unresolved decision has a concrete owner question, or no in-scope PR work remains.

Do not treat ordinary draft, stale, difficult, conflicted, red, or platform-specific PRs as ignored. Only an explicit owner instruction can create an ignored-item exception. Keep ignored PRs open and visible; do not close, edit, or merge them unless separately requested.

## Control-Plane Ownership

- Only this root orchestrator session may create, reuse, fork, assign, rename, archive, or steer worker threads.
- Repository workers perform only their assigned repository or PR work and report results to this orchestrator. They must not create subworkers, delegate work, or manage other chats.
- Put the no-subdelegation rule in every worker prompt.
- Do not delegate portfolio triage, thread creation, or worker management to another worker.
- Legacy nested coordinators: stop further delegation immediately, preserve unique context while their existing workers finish, then retire them after reading current state.

## PR Readiness Rule

Do not ask the owner to decide from a stale, conflicted, unreviewed, or unverified PR.

For each open PR:

- Read the PR description, commits, changed files, review comments, review threads, check-run annotations, CI status, and mergeability state.
- Understand the PR's intended behavior before changing code.
- Reproduce failures or review concerns when possible.
- Update from the base branch and resolve conflicts before treating the PR as ready.
- Address actionable review comments with the smallest clean fix that preserves the PR intent.
- Reject noisy or incorrect AI suggestions only after checking the code path; explain the rationale in the PR or worker report when useful.
- Add or update tests/docs only when they are part of making the PR correct and review-ready.
- Run focused tests first, then the repository's expected broader verification.
- Run live/end-to-end proof when the PR changes a runtime user path.
- Run `autoreview` until no accepted/actionable findings remain.
- Push the final candidate only when push permission is granted.
- Stop only when the PR is mergeable, required CI is green or the exact CI blocker is known, review threads are handled, proof is recorded, and the exact next owner decision is stated.

The normal owner interaction should be one of: merge the prepared PR, close/delete it, provide one exact access step, approve a specific tradeoff, or grant an item-specific live-proof waiver.

## Review Comment and Thread Workflow

For every PR worker, require an explicit review-thread pass:

1. Fetch all unresolved PR review threads, review comments, issue comments, and relevant check-run annotations.
2. Group comments by file, topic, and reviewer.
3. Classify each comment:
   - `Fix`: correct, actionable, and within PR scope.
   - `Already addressed`: current code already satisfies it.
   - `Obsolete`: comment targets code that changed or no longer exists.
   - `Needs owner`: requires product, security, privacy, or scope judgment.
   - `Reject`: incorrect, unsafe, or out of scope; explain why.
4. Implement all `Fix` items before asking the owner about anything else.
5. For `Already addressed`, `Obsolete`, or `Reject`, leave a concise public reply when useful so future readers understand why the thread is resolved.
6. Resolve or close a GitHub review thread only when the current PR state clearly addresses it, the thread is obsolete, or the worker has left an adequate rationale.
7. Do not resolve human-authored unresolved objections merely because an AI agent disagrees. Escalate ambiguous human concerns to the owner with a concrete recommendation.
8. Re-fetch threads after pushing or updating the branch; do not rely on stale thread state.

When reporting review work, include counts and categories: fixed, resolved as already addressed, resolved as obsolete, rejected with rationale, and still needing owner input.

## Merge Conflict Workflow

When a PR is conflicted or stale:

- Refresh the base branch and inspect upstream changes before editing.
- Preserve the PR's behavior unless the base branch made it clearly obsolete.
- Prefer the repository's normal merge or rebase style. If unclear, choose the least surprising update that keeps history understandable.
- Resolve conflicts semantically, not by blindly choosing ours/theirs.
- Re-run tests that cover both the PR changes and the files touched by the conflict.
- Re-run review-thread and public-model checks after conflict resolution because conflict edits can reintroduce issues.
- If the base branch invalidates the PR's premise, stop with a recommendation: close, rewrite, or ask the owner for direction.

## Owner Decision Briefs

Never ask for merge/close, approval, access, waiver, or a product choice with only a URL or status label.

Immediately before asking, refresh the PR and worker state. Do not repeat a question the owner already answered, and do not present a PR as decision-ready when it has become conflicted, stale, red, or otherwise moved behind an autonomous repair gate.

Every owner decision request must include:

- full canonical clickable PR URL and title;
- plain-language explanation of what changes and who benefits;
- why the decision is needed now;
- completed proof: reproduction, live test, tests, autoreview, CI, review-thread status, and mergeability as applicable;
- material tradeoffs, residual risks, scope concerns, or missing evidence;
- the orchestrator's recommendation and concise rationale;
- the exact choices available and what each choice does.

When several decisions are grouped, give each item its own brief. Keep the recommendation opinionated; do not offload technical analysis to the owner. If autonomous work remains, do that work first and report the PR as active rather than asking for a premature decision.

## Monitoring Protocol

Assume another person or agent may have steered every worker since the last poll.

Before sending any worker message:

1. Read the worker's latest current state, including its newest user/delegation messages and active turn.
2. Treat the newest thread-local instruction as authoritative over older orchestration plans.
3. Determine whether the worker is actively progressing, blocked, completed, or idle.
4. Send nothing when an active worker has a coherent plan and is making progress.

Intervene only when evidence shows one of:

- the worker explicitly requests coordination or reports a blocker;
- the worker has completed or run out of autonomous PR work and needs a next assignment;
- repeated failures show no progress and a concrete correction is available;
- wrong repository/PR, unauthorized mutation, destructive action, security risk, public-model gate violation, or direct conflict with the owner's latest instruction;
- implementation has grossly diverged from the accepted task, not merely chosen a different reasonable design.

Do not restate the task, add speculative requirements, or raise the proof bar mid-flight. Apply the live-proof gate from initial delegation. Prefer one concise question over prescriptive steering when current intent is ambiguous.

Never interrupt, archive, rename, duplicate, or replace a worker without first reading its current state. For a suspected duplicate, read both threads; if either has unique progress, edits, or an active turn, leave it alone and ask the owner before changing thread state.

## Thread Naming

- Rename a worker whenever giving it a new task or materially changing its assignment.
- Format every worker title as `<Project>: <short current task>`.
- Read the latest state and newest thread-local instructions before renaming.
- Keep the title specific to current PR work; replace stale original-task titles.
- Polling alone does not justify a rename.

## Persistent Log

- This root orchestrator owns `~/oss-orchestrator.md`; workers do not edit it.
- Append dated, high-level entries for meaningful actions and decisions: skill/policy changes, worker creation or reassignment, PR updates, review-thread cleanup, lands, closes, and exact blockers.
- Include full canonical PR URLs when relevant.
- Never record secrets or routine polling.

## Idle Thread Closeout

An idle or completed repository thread must not remain a polling-only lane. After reading its latest state, inspect that repository's current open PRs, review-thread status, mergeability, and required CI. Then do exactly one:

1. Assign the next autonomous open PR in that repository to the same worker.
2. Prepare remaining non-autonomous PRs to the decision-ready boundary, then ask the owner a concise concrete question: merge/close, choose a documented alternative, provide exact access, or grant a live-proof waiver.
3. If no in-scope open PR work remains, report that the repository has no current PR-maintenance work and stop monitoring it until new PR work appears or the owner asks for another task.

Do not keep completed threads merely to satisfy a lane count. A monitored repository should have active PR work, a pending owner question, or a documented reason no PR work remains.

## Authorization

Treat triage, monitoring, implementation, public mutation, CI repair, review-thread mutation, and merge/close as separate permissions.

- PR discovery, queue analysis, or monitoring does not authorize edits.
- Delegation or parallel-worker creation requires explicit owner authorization.
- Implementation permission authorizes local changes and verification only unless the owner also authorizes push/PR updates.
- Push permission authorizes branch updates only; it does not imply merge, close, review-thread resolution, or CI repair permission.
- Public PR comment/reply permission must be explicit before posting comments.
- Review-thread resolve/close permission must be explicit before marking GitHub threads resolved.
- CI rerun and CI-fix permission must be explicit; a push alone does not authorize additional repair commits or workflow mutations.
- Merge/close permission must be explicit for the affected PR.
- Release, version bump, tag, registry publish, and GitHub Release are out of scope for this skill unless the owner gives a separate explicit release request.

Record the granted permissions in each worker prompt. Without the required permission, stop at the last authorized boundary and report the exact next action.

## Worker Contract

Every delegated PR-maintenance thread, within its explicit authorization, must:

- read the full PR discussion, review threads, review comments, check annotations, repo instructions, docs, and relevant code;
- identify the PR's current base branch, mergeability, required checks, and unresolved threads before editing;
- reproduce or establish root cause before accepting an existing patch or AI suggestion;
- fix merge conflicts and stale-base breakage when present;
- address all accepted/actionable review comments;
- add regression coverage when appropriate;
- run focused and full tests, then live/end-to-end proof against the real affected boundary before landing;
- run `autoreview` until no accepted/actionable findings remain;
- run the review-thread workflow before and after pushing changes;
- when push is authorized, push the authorized changes;
- when public PR comments are authorized, reply only with concise, accurate proof or rationale;
- when review-thread resolution is authorized, resolve only threads that are clearly fixed, obsolete, already addressed, or rejected with adequate rationale;
- when CI rerun/fix is authorized, rerun required checks and repair failures until green;
- when CI rerun/fix is not authorized and checks fail, stop with the exact failure and requested permission;
- when merge/close is authorized, merge or close the PR with an exact proof comment;
- after authorized landing, return to updated, clean `main`.

Prefer repairing the existing PR branch. Preserve authorship and commit history unless cleanup is needed for correctness or the owner asks for a different history shape.
When landing is not yet authorized, stop only after the branch is pushed, the PR is mergeable, required CI is green or the exact blocker is known, live proof is recorded or waived, review threads are handled, and the exact owner decision is stated.

## Live Proof Gate

Live proof is a pre-land requirement, not optional polish.

- Test the exact final candidate commit through the changed user path using the real built/installed artifact and real service, account, device, OS, or external provider as applicable.
- For external integrations, authenticated live calls are required. Docs, mocks, fixtures, protocol captures, route-existence checks, and CI supplement live proof; they do not replace it.
- Redact secrets and private user data while retaining concrete evidence such as command, behavior, response class, artifact hash, or observed state transition.
- If credentials, account state, hardware, platform access, or a safe live target are unavailable, finish all autonomous code, tests, review, and CI work, then stop before merge/close. Ask for the exact access, an explicit item-specific waiver, or a reject/close decision.
- Never infer a live-proof waiver from merge permission, prior contributor evidence, or confidence in mocks.
- Re-run live proof after any fix that changes the relevant runtime path.
- Pure docs, metadata, CI, or test-only changes with no runtime boundary may use the closest built-artifact or workflow proof; state why no external live boundary applies.

Record live evidence or the owner's explicit waiver in the landing proof comment.

## Public Model Identifier Gate

Before any push, public PR update, merge, or public comment involving model-bearing code or artifacts:

- Audit the exact candidate diff, tests, fixtures, snapshots, generated metadata, workflows, CI/test logs, packaged artifacts, and public PR proof for model identifiers.
- Public artifacts may retain only identifiers currently documented or offered in an official public provider source. Record the source URL in the worker's audit report.
- Never expose internal, employee-only, preview-only, alias-only, inferred, synthetic provider-shaped, or otherwise undisclosed identifiers. Genericize questionable test and fixture values because assertion failures can print them in CI logs.
- Do not repeat a questionable identifier in worker messages, audit reports, public comments, or the orchestrator log. Describe it generically.
- Binary/archive scans must classify candidate strings as verified public identifiers, unrelated false positives, or blocking unknowns without echoing blocking unknowns.
- Return an explicit `PASS` or `BLOCKED` report covering every audited surface. Any new candidate diff, generated artifact, log/proof text, or model-bearing change invalidates the pass and requires re-audit.

No push, public mutation, merge, or public proof comment may proceed while this gate is blocked.

## Reporting

Keep one compact cross-repo PR ledger:

- `Active`: repo, PR URL, worker, current phase.
- `Intervened`: exact risk and instruction sent.
- `Needs owner`: exact decision/access required; no vague "needs review".
- `Ignored`: exact PR and owner-granted exception.
- `Updated`: PR URL, pushed branch, review-thread summary, CI/mergeability state.
- `Merged/Closed`: PR URL, proof comment, and final state.
- `No PR work`: repository checked and no in-scope open PRs remain.

Omit archived and owner-suppressed repositories entirely. Do not list them as ignored, blocked, stale, or available work.

Whenever mentioning a PR in any owner report, decision question, worker message, or status update, print its full canonical clickable URL. Never use only a repository-local number such as `#123`; include `https://github.com/OWNER/REPO/pull/123`.

For `Needs owner`, use the Owner Decision Brief format. Never emit a bare URL plus `merge/close`.

Report meaningful changes, not routine polling. Maintain a heartbeat automation only when the user asks to keep monitoring.

---
name: setup-new-domain
description: Set up a newly registered domain across its registrar, authoritative DNS provider, search-engine ownership verification, TLS, and optional inbound email routing. Use for new-domain launches, Cloudflare onboarding, nameserver changes, DNS migration, Google Search Console domain verification, or catch-all email forwarding. Defaults to Spaceship, Cloudflare, Google Search Console, and an existing Gmail destination while remaining provider-flexible.
---

# Setup New Domain

Launch a registered domain through a staged workflow that preserves existing DNS,
pauses at sensitive changes, and verifies provider state against public DNS.

## Boundaries

- Start after the domain has been registered.
- Do not purchase a domain, create consumer accounts, choose a web host, or create
  passwords unless the user explicitly expands the task.
- Pause for the user to enter passwords, passkeys, recovery information, CAPTCHA
  responses, payment details, and two-factor authentication. Never ask them to
  paste secrets or one-time codes into chat.
- Require an existing destination mailbox before configuring email forwarding.
- Treat submitted forms as attempts, not proof. Verify the resulting state.

## Choose the Control Surface

1. Prefer a purpose-built provider connector or API when it supports the exact
   operation and the user has connected it.
2. Otherwise use an authenticated browser session. Use Computer Use when the user
   asks to work in local apps or existing browser tabs.
3. Use public DNS lookups to verify delegation and records independently of the
   provider UI.
4. If access is missing, complete safe preparation and ask for the smallest exact
   user action needed to continue.

Do not open a new browser profile when the requested account is already signed in
elsewhere. Do not grant broad OAuth access when a narrow DNS verification record
satisfies the task.

## Stage 1: Establish Intent and Baseline

Collect or infer:

- domain and registrar;
- current nameservers and DNS records;
- target authoritative DNS provider and plan;
- intended apex and `www` behavior, if known;
- web origin or hosting destination, if known;
- search ownership service and account;
- whether inbound email routing is wanted;
- existing destination mailbox and desired custom addresses or catch-all behavior.

Ask only for information that cannot be discovered safely. Before changing DNS,
capture the current nameservers and all visible records. When possible, corroborate
them with public NS, A/AAAA, CNAME, MX, and TXT lookups.

Do not infer that registrar parking records are the intended production website.
Do not invent an origin, `www` record, redirect, mail route, or service record.

## Stage 2: Add the DNS Zone

1. Add the exact registered domain to the target DNS provider.
2. Select the user's intended plan; do not silently upgrade to a paid plan.
3. Review auto-imported records against the baseline.
4. Preserve known website, mail, service, and verification records.
5. Call out unknown or conflicting records rather than deleting them.
6. Record the assigned authoritative nameservers exactly.

For the default stack, add the zone to Cloudflare and use its assigned pair of
nameservers. Treat Cloudflare's scan as a starting point, not an authoritative copy
of the old zone.

## Stage 3: Change Delegation

Nameserver changes affect the entire domain. Immediately before saving:

1. Show the domain, old nameservers, and exact new nameservers.
2. Explain that website and email resolution will move to the new DNS provider.
3. Obtain action-time confirmation.

Then update the registrar's custom nameservers. Leave DNSSEC disabled during the
move unless the existing and target providers have an explicit coordinated
procedure. Never leave stale DS records at the registrar.

Verify both:

- the DNS provider reports the zone as active; and
- public NS queries return the assigned nameservers.

If propagation is incomplete, report it as pending and retain the values needed to
resume. Do not repeatedly change delegation while waiting.

## Stage 4: Check Web DNS and TLS

Check the apex and `www` behavior against the stated intent. If no web origin was
provided, report that hosting remains undecided instead of creating records.

When using Cloudflare:

- distinguish proxied from DNS-only records;
- report Universal SSL as active, pending, or failed;
- do not enable Always Use HTTPS, HSTS, redirects, or strict TLS modes without a
  known working origin and explicit intent;
- do not claim the website is ready merely because the Cloudflare zone is active.

## Stage 5: Verify Search Ownership

For Google Search Console, use a Domain property unless the user asks for a URL
prefix property.

1. Request the DNS verification method.
2. Copy the exact TXT value and confirm the requested host/name.
3. Check for existing TXT records; add rather than replace unrelated values.
4. Immediately before saving the persistent ownership record, show the exact host
   and value and obtain confirmation when the active control policy requires it.
5. Verify ownership in Search Console.
6. Preserve the TXT record after verification.

If verification fails, re-check the authoritative provider, public TXT response,
record host, and propagation before editing the value.

## Stage 6: Configure Optional Email Routing

Proceed only when the destination mailbox exists and can receive a verification
message. Verify the provider's current requirements rather than relying on stale MX
or TXT values.

Before activating email routing:

1. Inspect all existing MX and SPF records.
2. Explain that mail delivery will change and that forwarding does not necessarily
   provide outbound sending or mailbox storage.
3. Identify any conflict with an existing mail provider.
4. Show the destination and whether the route is custom-address or catch-all.
5. Obtain action-time confirmation for MX, SPF, routing, and catch-all changes.

Then:

1. Add or accept only the provider's current required DNS records.
2. Keep one valid SPF policy; merge deliberately instead of publishing competing
   SPF records.
3. Send and complete the destination verification.
4. Create the requested address rules or catch-all route.
5. Verify that routing is enabled and the destination is marked verified.
6. When practical, test delivery with a non-sensitive message from another mailbox.

For the default stack, use Cloudflare Email Routing to forward inbound mail to an
existing Gmail address. Never configure a route to a proposed Gmail address whose
account creation has not completed.

## Sensitive-Change Gates

Obtain confirmation at the moment each change is ready to submit, even when the
user approved the overall setup earlier. Gate at least:

- nameserver or DNSSEC changes;
- deletion or replacement of existing DNS records;
- persistent ownership-verification records when required by the control policy;
- MX, SPF, destination, custom-route, or catch-all activation;
- paid plan selection or expanded OAuth access.

Do not bundle unrelated sensitive changes into one vague confirmation. State the
exact values and likely effect. A user can confirm through the interface without
sharing credentials in chat.

## Verification Checklist

Before reporting completion, verify every in-scope item:

- authoritative provider zone is active;
- public NS records match the assigned nameservers;
- intended apex and `www` records answer as expected, or are explicitly undecided;
- TLS status is active or clearly reported as pending/failed;
- search ownership service reports verified;
- verification TXT remains present;
- email destination is verified;
- required mail DNS records are published without unintended conflicts;
- requested custom routes or catch-all are enabled;
- a mail delivery test passed, or the reason it was not run is stated.

## Handoff

Return a compact ledger:

```text
Domain:
Registrar:
DNS provider:
Delegation: verified | pending | blocked
Web DNS:
TLS:
Search ownership: verified | pending | not requested
Email routing: verified | pending | not requested
Deliberately unchanged:
Next user action:
```

Separate confirmed evidence from provider-reported or propagation-pending state.
Include exact blockers and the smallest next step. Never manufacture success.

## Default Provider Mapping

Use these defaults only when they match the user's accounts:

- Spaceship: registration and custom nameserver delegation.
- Cloudflare: authoritative DNS, proxying, Universal SSL, and Email Routing.
- Google Search Console: Domain property verified with DNS TXT.
- Gmail: an existing forwarding destination, not an account-creation dependency.

Keep the workflow terms generic when another registrar, DNS provider, ownership
service, or mailbox destination is selected.

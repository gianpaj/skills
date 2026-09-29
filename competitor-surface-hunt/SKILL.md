---
name: competitor-surface-hunt
description: >
  Find a competitor's staging, demo, free trial, sandbox, or public dashboard.
  Hunt subdomains, alt TLDs, certificate logs, and related product hosts, then
  write a dated competitor-analysis markdown file. Use when the user names a
  company or URL and asks for demo access, staging, subdomains, OSINT, or a
  competitor analysis. Triggers: competitor demo, staging dashboard, find
  sandbox, subdomain hunt, /competitor-surface-hunt.
---

# Competitor surface hunt

Map a competitor's **public product surface**: marketing site vs staff app vs
guest app vs sales calendar. The marketing domain is usually not the product.

Do this from public sources only. Use GET/HEAD for direct HTTP probes. Read
login pages, JS, certs, DNS, and legal pages. Browser checks may trigger normal
page and widget initialization requests. Do not submit registrations, contact
forms, chat messages, or bookings without user authorization. Do not guess
passwords, fuzz authenticated APIs, or write exploits.

Default output: `plans/YYYY-MM-DD-<slug>-competitor-analysis.md` in the current
repo.

## Sequence

Run identity, marketing harvest, and certificate transparency in parallel. CT is
the step that finds the real app. DNS brute force on the marketing domain is the
step that usually finds nothing.

### 1. Identity

From the URL the user gave:

- Apex and `www`
- Company name, product name, possible extra TLDs (`.app`, `.dev`, `.io`, `.co`)
- Brand prefixes: `get`, `try`, `use`, `join`, `go`, `app`, `hello`, `claim`

WHOIS + DNS on the marketing apex: registrar, NS, MX, TXT, CNAME for `www`.
`www` CNAME to Framer / Webflow / Vercel / Shopify means the **site is not the
product**.

### 2. Marketing harvest

Fetch and extract, do not skim titles only:

- `/`, `/robots.txt`, `/sitemap.xml`
- About, contact, pricing, legal, DPA, terms, jobs
- Outbound URLs: Cal.com, HubSpot, Chili Piper, SavvyCal, Notion, Drive,
  YouTube, GitHub, LinkedIn, X
- App Store / Play search for the product name

Follow pricing, demo, trial, and signup links to their actual destination.
"Subscribe Now" can lead to a sales form; "Book a demo" can lead to a calendar.
Record whether the destination is a sales request, self-service registration,
login, guided tour, or usable product demo. Then keep hunting.

Legal/DPA is product intel: subprocessors (AWS region, Stripe, auth, analytics,
LLM vendor), "accessed via web browser", mobile apps, go-live dates.

#### Browser verification

Use the `agent-browser` skill when content depends on JavaScript, cookie
consent, or interaction, or when HTTP extraction returns an empty app shell.
Read its current CLI guide, use an isolated named session, and close that
session when finished.

- Render pricing pages and check billing toggles, allowances, setup fees, and
  the destination of purchase buttons. Check login pages for registration links.
- Open embedded chat or booking widgets. If consent controls their visibility,
  record the consent state used. Inspect iframe URLs and network requests
  during opening, including configuration responses that identify the provider.
- Distinguish a script present on the page, a successfully loaded widget, and
  a working conversation. Record the strongest level actually verified.
  A form requiring visitor details is a stopping point unless submission is
  authorized.
- Attribute each component separately. A booking engine and chatbot on the same
  site can have different providers. Hidden branding, URL paths, and token
  prefixes alone do not establish ownership or backend integrations.
- Record source URLs and concise evidence. Redact cookies, session tokens, and
  personal data from reports; do not publish raw network captures.

Keep DNS, certificate queries, headers, sitemaps, and bundle searches in
shell/HTTP tools. Use the browser to resolve what those checks cannot show.

### 3. Certificate transparency (do not skip)

Query CT for the marketing domain **and** guessed product domains.

```bash
curl -sS --max-time 20 \
  "https://api.certspotter.com/v1/issuances?domain=EXAMPLE.COM&include_subdomains=true&expand=dns_names"
```

crt.sh (`https://crt.sh/?q=%.EXAMPLE.COM&output=json`) works when it is up; Cert
Spotter was the reliable source.

Collect every SAN: `staging`, `prod`, `console`, `guest`, `api`, `media`,
`viewer`, `*.tenant.example.app`. Those names are the product map even when apex
DNS is empty.

### 4. Alt domains

Probe DNS + HTTP for:

- `example.app`, `example.dev`, `example.io`, `example.co`, `example.ai`
- `getexample.com`, `tryexample.com`, `useexample.com`, `appexample.com`
- Founder/org GitHub: `github.com/Example` and founder handles from YC/LinkedIn
- Platform vanity: `example.vercel.app`, `example.framer.app`, and similar.
  **DNS here is a catch-all.** HTTP-check every hit; most are platform 404s.

A domain that 301s to the marketing site is brand protection, not a trial
(`tryexample.com` is often this).

### 5. DNS on each live zone

For the marketing apex, then for every product zone CT revealed
(`prod.example.app`, `staging.example.app`):

```bash
# zsh: use an array. A single unquoted string does not split.
labels=(www app api staging stage demo dashboard login portal admin console
        guest media viewer pos auth spa)

for s in "${labels[@]}"; do
  rec=$(dig +short +time=1 +tries=1 "$s.EXAMPLE.COM" A)
  cname=$(dig +short +time=1 +tries=1 "$s.EXAMPLE.COM" CNAME)
  [ -n "$rec$cname" ] && echo "HIT $s.EXAMPLE.COM A=[$rec] CNAME=[$cname]"
done
```

Also query NS on `staging.` and `prod.` labels. A delegated Route53/Cloud DNS
zone with no apex A record still has children.

If CT showed `*.guest.staging.example.app`, confirm with one dummy name
(`foo.guest.staging.example.app`). Wildcard A/AAAA means **every label
resolves**. HTTP status, not DNS, tells you the tenant exists.

### 6. HTTP classify

For each name that resolves, GET with redirects, headers, and a short body:

```bash
curl -sS -D - -o /tmp/body -L --max-time 12 -A "Mozilla/5.0" "$url" | head -30
```

Record status, `server`, `x-powered-by`, `x-middleware-rewrite`, CSP
(`connect-src` names their APIs), title, visible copy.

Then hit the obvious app paths: `/login`, `/signup`, `/register`, `/demo`,
`/forgot-password`, `/health`, `/docs`, `/openapi.json`.

Classify each URL as one of:

| Class           | Signals                                                          |
| --------------- | ---------------------------------------------------------------- |
| Sales CTA       | Cal.com / HubSpot / "book a demo"                                |
| Staff login     | "Welcome back", workspace, email+password, invite-only `/signup` |
| Guest / booking | "Book with…", tenant host, "booking not found"                   |
| POS / device    | "open the till", store login                                     |
| API             | ALB 404 at `/`, JSON, no HTML                                    |
| Media           | S3/CloudFront 403                                                |
| Empty / down    | NXDOMAIN, 503, platform 404                                      |
| Unrelated       | Other language, other product, parked page                       |

Apply the browser verification checks in step 2 before classifying an app shell
or claiming that self-service access or a working demo exists.

A 200 HTML shell plus an RSC/JSON 404 is a **multi-tenant app with no seeded
tenant**, not a working demo hotel.

### 7. Read the apps you found

On login HTML and `/_next/static` (or equivalent) bundles, grep for product
nouns: workspace, Fortnox, Stripe, OAuth, invite, demo environment. That is how
you learn auth model and market without an account.

urlscan.io and Wayback CDX (`url=*.example.com/*`) catch older positioning
(waitlist, event booking, different host).

### 8. Write the file

Lead with whether a **public, unsigned-in product demo** exists. Then the table
of URLs a human can open. Then company, product, hosts, other domains, stack,
GTM, implications for our product.

Date the research. Say what you did not check (authenticated console, paid CT,
company registry). If prod is 503 today, say so; do not call it dead forever.

## What Zaplar taught (keep this mechanism)

Marketing `zaplar.com` had only `www` → Framer. Product was `zaplar.app`, found
via Cert Spotter (`console.staging`, `*.guest.staging`, `api.prod`). Staging
console login was live; advertised "demo" was Cal.com. Wildcard guest DNS
resolved every guess; only HTTP showed empty tenants.

If the next competitor's marketing DNS is empty, **do not stop**. Run CT on
`.com` and `.app` / `.dev` before concluding they have no public app.

## Out of scope

Credential stuffing, wordlist logins, authenticated scraping, posting findings
as "free access" when the page is a login wall. A login page is a finding. An
account is not.

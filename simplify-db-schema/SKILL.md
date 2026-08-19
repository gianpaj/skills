---
name: simplify-db-schema
description: Review and simplify a database schema — inconsistent naming, dead columns and indexes, missing constraints, wrong types, junk-drawer JSONB, drifting denormalized copies. Use when asked to audit, clean up, simplify, or pay down tech debt in a Postgres schema, or to find unused columns and indexes, missing foreign keys, or tables that should be merged. Produces a findings document, unapplied migration files, and app-code diffs; never applies a migration and never edits code.
---

# Simplify DB Schema

Review a Postgres schema in two passes — cheap whole-schema triage, then a deep dive on one
cluster — and emit a findings document, unapplied migration files, and app-code diffs.

Large schemas produce reports nobody acts on. The triage pass exists so each run ends with a
short list of changes someone will actually make.

## Boundaries

- **Read-only against the database.** Introspection queries only. Never run a migration,
  never write a row, never `ALTER` anything.
- **Never edit app code.** Call-site changes belong in the report as diffs.
- **Write exactly two kinds of files:** one dated doc in `plans/`, and migration files in the
  project's migrations directory. Nothing else on disk changes.
- **Never commit, never open a PR.**
- **Never grep `.env` for credentials and never echo a connection string.** Ask the user which
  environment variable or `psql` invocation to use.
- **No new features.** Do not propose tables or columns for anticipated needs.

## Pass 0 — Orient

Detect the migration tool, the query layer, and the app directories. Then establish whether a
read-only connection is reachable.

| Signal | Tool | Migrations land in |
|---|---|---|
| `supabase/config.toml` | Supabase CLI | `supabase/migrations/<YYYYMMDDHHMMSS>_<name>.sql` |
| `drizzle.config.*` | Drizzle Kit | `drizzle/<NNNN>_<name>.sql` |
| `flyway.conf`, `V*__*.sql` | Flyway | `sql/V<n>__<name>.sql` |
| `knexfile.*` | Knex | `migrations/<timestamp>_<name>.js` |
| `prisma/schema.prisma` | Prisma | derived — see below |
| `alembic.ini` | Alembic | derived — see below |
| `db/migrate/` | Rails | derived — see below |
| nothing found | — | ask the user |

**Declarative tools (Prisma, Alembic, Rails) get no migration files.** Their migrations are
generated from a schema declaration; a hand-written migration leaves the declaration drifted
and the next `migrate` command tries to undo it. For these, put both the SQL and the
declaration diff in the report, plus the generate command the user runs.

For the connection, ask:

> Which environment variable or `psql` command should I use for read-only introspection?
> A replica or read-only role is ideal. If you'd rather not connect, I'll run in INFERRED mode.

Run queries as `psql "$THE_VAR" -f queries/inventory.sql`. Pass the variable through — never
interpolate its value into a command line, a log, or the report.

State the mode before continuing:

- **VERIFIED** — connected. Findings are backed by catalog and data evidence.
- **INFERRED** — no connection. The schema is reconstructed from migration files or a schema
  dump, and every finding that depends on data carries a `verify-first` query instead.

## Pass 1 — Inventory and triage

Stay cheap here. No code grepping, no data probes, no per-column analysis.

1. Run `queries/inventory.sql` (VERIFIED) or reconstruct the schema by replaying migration
   files in order (INFERRED). Both SQL files take a `schemas` regex, defaulting to `^public$` —
   which is also what keeps a Supabase project's `auth` and `storage` schemas out of scope:

   ```
   psql "$DB" -v schemas='^(public|billing)$' -f queries/inventory.sql
   ```

2. Run `queries/suspects.sql` unscoped. Sections A–E cover the whole schema filter and read
   only catalogs, which is what triage needs; ignore F onward until a cluster is chosen.
3. Cluster the tables: connected components of the foreign-key graph, then group whatever is
   left by shared name prefix. A table in no cluster is its own cluster.
4. Score each cluster: `high × 5 + medium × 2 + low × 1`.
5. Print the top clusters — at most eight — and stop for the user to choose.

```
142 tables · 891 columns · 203 indexes · VERIFIED

  1. calls / call_events / call_meta        18 findings   3 high
  2. users / profiles / accounts            11 findings   4 high
  3. billing_invoices / billing_line_items   6 findings   0 high

→ Which cluster? (name, number, or "all")
```

`all` is allowed but say what it costs: on a schema this size it produces a report long enough
that nobody acts on it. Recommend one cluster.

## Pass 2 — Deep dive

Re-run the suspects file scoped to the cluster — sections F onward respect `tables`:

```
psql "$DB" -v tables='^(calls|call_events|call_meta)$' -f queries/suspects.sql
```

Sections I and J emit SQL rather than running it. Read what they emit, run only the probes a
finding actually needs, and never run them all — each one scans a table.

Then work the categories in `references/smell-catalog.md` against every table in the cluster.
For each candidate finding:

1. **Find the call sites.** Grep the app directories for the table and column name, including
   the ORM's own spelling (`camelCase` field names, model attributes, generated types). A
   finding with no call sites is not automatically dead — check for dynamic SQL, string-built
   queries, views, triggers, and jobs before claiming it.
2. **Verify against data** where the claim depends on it — null ratios, distinct counts, index
   scan counts, orphan rows. `queries/suspects.sql` emits these probes for the cluster.
3. **Classify** severity, confidence, and whether the change is breaking.
4. **Drop it** if it fails the restraint rules below.

### Restraint rules

Schema changes cost a coordinated deploy, so the bar is higher than for a code refactor.

- **Propose a rename only when the current name is actively misleading, not merely
  imperfect.** `calls.status` holding a *billing* status is misleading — rename it. `usr_nm`
  is ugly and obvious — leave it. Taste is not a migration.
- **A column with no call sites is a question, not a finding**, until you have checked dynamic
  SQL, views, triggers, jobs, and other services. Say which of those you checked.
- **Never propose dropping something you cannot prove is unused.** In INFERRED mode, nothing
  is provably unused; emit the verify-first query and mark it `INFERRED`.
- **Do not merge tables to reduce the table count.** A one-to-one split is only worth merging
  when the child row always exists and is always read together with the parent.
- **Do not normalize a lookup that never changes**, and do not denormalize for a query nobody
  has complained about.
- **Leave `varchar(n)` alone** unless the cap has actually caused a truncation or the value is
  unbounded in practice.
- Prefer several small findings over one sweeping "redesign this cluster" finding. A finding
  the user can accept or reject on its own is worth more than a grand plan.

## Pass 3 — Emit

Write the report to `plans/YYYY-MM-DD-schema-<cluster>.md`, and migration files to the
detected directory (except for declarative tools). Then print a summary that states plainly
that nothing was applied, and gives the exact command to apply it.

Breaking changes ship as an expand/contract pair — see `references/migration-safety.md`. Write
both files; mark the contract half so it cannot be run by accident:

```sql
-- CONTRACT — DO NOT RUN until the expand migration is deployed, backfilled,
-- and every reader has shipped. See plans/2026-08-19-schema-calls.md § F3.
```

### Report shape

````markdown
# Schema review — calls cluster

Mode: VERIFIED (read-only replica) · 2026-08-19
Tables: calls, call_events, call_meta
Findings: 3 high · 5 medium · 2 low
Nothing in this document has been applied.

## Summary

| # | Finding | Severity | Confidence | Breaking |
|---|---|---|---|---|
| F1 | `calls.user_id` is `text` with no FK to `users.id` | high | VERIFIED | yes |
| F2 | `calls.legacy_meta` is unused and entirely null | medium | VERIFIED | yes |
| F3 | `idx_calls_status` duplicates `idx_calls_status_created` | low | VERIFIED | no |

## F1 — `calls.user_id` is `text` with no FK to `users.id`

**Severity** high · **Confidence** VERIFIED · **Breaking** yes (expand/contract)

`users.id` is `uuid`; `calls.user_id` is `text`. Every join casts, which defeats any index on
`users.id`, and nothing stops a row from pointing at a user that does not exist.

**Evidence**

```
1,402,881 rows · 4 values fail ::uuid · 213 rows reference a missing user
```

**Migration** — `supabase/migrations/20260819103000_calls_user_id_uuid_expand.sql`

```sql
ALTER TABLE calls ADD COLUMN user_id_uuid uuid;
-- backfill in batches; see migration file
```

Contract half: `..._contract.sql` — drops `user_id`, renames, adds the FK `NOT VALID` then
validates. Do not run until every reader below has shipped.

**Call sites** (3)

`call-server/src/db/calls.ts:42`

```diff
-  .eq('user_id', String(userId))
+  .eq('user_id', userId)
```

**Verify before applying**

```sql
SELECT count(*) FROM calls c LEFT JOIN users u ON u.id::text = c.user_id
WHERE c.user_id IS NOT NULL AND u.id IS NULL;
```

**Risk** — the 213 orphan rows must be resolved before the FK validates. Decide: delete,
backfill, or make the column nullable and null them.
````

Every finding carries all eight parts: severity, confidence, breaking, the reason it matters,
evidence, migration SQL, call sites, and what to verify first. A finding missing evidence or
call sites is an opinion — either go get them or drop the finding.

## Scope

**In scope:** naming and conventions · dead schema · types and correctness · redundancy ·
structure · access and RLS. Detail in `references/smell-catalog.md`.

**Out of scope:** query plan tuning beyond redundant indexes, partitioning, sharding,
connection pooling, capacity planning. Say so and move on if asked mid-run.

## Common mistakes

| Mistake | Fix |
|---|---|
| Calling a column dead because grep found nothing | Check dynamic SQL, views, triggers, jobs, other services — then say which you checked |
| Renaming for taste | Only rename what actively misleads |
| Drop and replacement in one migration | Split into expand and contract |
| `CREATE INDEX` on a large table | Use `CONCURRENTLY`, outside a transaction |
| `ADD CONSTRAINT` that scans the whole table | `NOT VALID`, then `VALIDATE CONSTRAINT` |
| `SET NOT NULL` on a large table | Add a `NOT VALID` check, validate, then set — see migration-safety |
| Hand-written migration in a Prisma/Rails/Alembic project | Emit SQL plus the declaration diff and the generate command |
| Reporting 200 findings | One cluster per run |
| Presenting an inference as a fact | Mark it `INFERRED` and attach a verify-first query |
| Interpolating the connection string into a command | Pass the environment variable through |

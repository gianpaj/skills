# Schema smell catalog

Work these categories against the chosen cluster. Each row gives the smell, how to detect it,
**when it is fine** — the column that keeps this skill from generating noise — and the fix.

Severity guidance: **high** means the schema permits or hides wrong data. **medium** means it
costs real work on every read or write. **low** means it only costs comprehension.

---

## 1. Naming and conventions

Consistency matters more than which convention wins. Derive the house style from the majority
of existing tables, and report the minority as the deviation — never impose a style the schema
does not already use.

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Mixed case styles (`userId` beside `user_id`) | Column names against the majority style | The minority came from an external system that owns the shape | Rename the minority — breaking |
| Table name repeated in its columns (`calls.call_status`) | Column starts with the singular table name | The prefix disambiguates two similar columns | Drop the prefix — breaking |
| Inconsistent plurality (`user` beside `calls`) | Table names | Never worth a migration alone; note it and batch with another change | Rename — breaking |
| FK column without `_id` (`calls.user`) | FK constraints whose column lacks the suffix | The column is not a foreign key | Rename — breaking |
| Timestamps not `created_at` / `updated_at` | Columns typed timestamptz | Domain-meaningful names like `started_at` are correct | Rename — breaking |
| Booleans without `is_` / `has_` (`calls.active`) | Boolean columns | The name already reads as a predicate | Rename — breaking |
| Reserved words as identifiers (`order`, `user`, `end`) | Quoted identifiers in the schema dump | The quoting is confined to generated code | Rename — breaking |
| Cryptic abbreviations (`ct`, `flg`, `dt1`) | Names under four characters, or no vowels | Domain jargon a junior on this team already knows | Rename — breaking |

**Severity is low for all of these** unless the name is actively misleading — a column whose
name states one thing and holds another. That is high, because it produces wrong code.

---

## 2. Dead schema

The category with the highest false-positive rate. Every finding here needs both a code-side
and a data-side check before it becomes a proposal.

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Column entirely null | `count(col)` = 0 over the table | Column is newly added and being backfilled | `DROP COLUMN` — breaking |
| Column with no call sites | Grep app dirs for the name and its ORM spelling | Read by dynamic SQL, a view, a trigger, a job, another service, or an export | Ask before proposing |
| Index never scanned | `pg_stat_user_indexes.idx_scan = 0` | Stats were reset recently; the index backs a constraint; it serves a rare-but-critical job | `DROP INDEX CONCURRENTLY` — non-breaking |
| Leftover `_old`, `_tmp`, `_bak`, `_copy`, `legacy_`, `_v2` | Name pattern | A rename in flight — check recent migrations | Drop after confirming |
| Table with zero rows and no writes | `est_rows` = 0 **and** `last_analyzed` is set **and** `total_size` is one page, plus no INSERT call sites | Seeded per environment, or written only in production | Ask before proposing |
| Unreferenced enum type | No column uses the type | Used by a function signature or a cast in app code | `DROP TYPE` — non-breaking |
| View nothing selects from | No call sites, no dependent views | Consumed by BI, analysts, or a dashboard outside the repo | Ask before proposing |
| Sequence owned by nothing | `pg_depend` has no owning column | Called directly by app code | `DROP SEQUENCE` — non-breaking |

**Always report the stats reset time alongside any zero-scan index claim.** An index unused
since a reset yesterday is not an unused index.

**A never-analyzed table reports zero rows.** `est_rows` comes from `ANALYZE`; a table that has
never been analyzed reports 0 no matter how much data it holds — only `total_size` gives it
away. Check `last_analyzed` before calling anything empty.

---

## 3. Types and correctness

Highest-value category. These findings are about data the schema currently allows to be wrong.

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Table without a primary key | No `contype = 'p'` constraint | Append-only event log where a PK adds cost for no benefit — but say so | Add PK — usually non-breaking |
| `_id` column with no FK constraint | Suffix present, no FK, and a plausible target table exists | Points at another database or an external system | Add FK `NOT VALID`, then validate — non-breaking once orphans are resolved |
| `text` holding UUIDs | Every value casts to uuid, target column is uuid | The values come from a system that is not actually a UUID | `ALTER TYPE` — breaking |
| `text` holding a small fixed set | Low `n_distinct` in `pg_stats`, **confirmed by an exact probe** | The set grows at runtime, or `n_distinct` was a bad sample — it under-counts badly on small tables, and will flag a UUID foreign key as an enum | Enum or a lookup table with an FK — breaking |
| `timestamp without time zone` | `atttypid` is `timestamp` | Genuinely local wall-clock time, like a store's opening hour | `timestamptz` — breaking; confirm the stored values' zone first |
| `float` / `real` / `double precision` for money | Type plus a name like amount, price, cost, fee, total, balance | The number is a measurement, not money | `numeric(p, s)`, or integer minor units — breaking |
| Column always populated but nullable | Zero nulls over a large table, and code never handles null | Nulls are legitimately possible and just haven't occurred | `SET NOT NULL` via a validated check — non-breaking, see migration-safety |
| Uniqueness enforced only in app code | A `SELECT`-then-`INSERT` guard in the query layer | Duplicates are tolerable and the check is advisory | `UNIQUE` index built concurrently — non-breaking once duplicates are resolved |
| Boolean encoded as text or integer | `'Y'` / `'N'` / `0` / `1` in a text or int column | The column has a third state — then it wants an enum, not a boolean | `boolean`, or an enum if there are three states — breaking |
| Check constraint duplicated in app code | Same range or format validated in both places | Defence in depth, deliberately | Keep the database constraint; note the redundancy without proposing a change |
| `ON DELETE` unspecified on an FK | FK with default `NO ACTION` | The default is what the domain wants — say which one it is | Set the intended action explicitly — non-breaking |

---

## 4. Redundancy

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Identical indexes | Same table, columns, opclass, predicate | Never | Drop one — non-breaking |
| Index is a leading prefix of another | `(a)` alongside `(a, b)` | The narrow one is much smaller and serves a hot path; a unique constraint needs the exact shape | Drop the prefix index — non-breaking |
| Unique constraint plus a matching unique index | Constraint and index on the same columns | Never — the constraint already owns an index | Drop the extra index — non-breaking |
| Index duplicating the primary key | Index columns equal the PK columns | Never | Drop it — non-breaking |
| Denormalized copy that can drift | Same column name and type on both sides of an FK, with no trigger or generated-column keeping it in sync | Deliberate snapshot: an invoice's price at purchase time must not follow the product's price | Generated column, trigger, or drop the copy — breaking |
| Near-identical sibling tables | Same column set differing by one flag-like column | The tables have different lifecycles, retention, or access rules | Merge with a discriminator — breaking; propose only when all three match |
| Counter column beside a countable relation | `posts.comment_count` alongside a `comments` FK | The count is hot and the trigger keeping it correct exists | Keep it if maintained; flag it if nothing maintains it |

---

## 5. Structure

The findings here are the largest and the easiest to over-reach on. Propose one structural
change per run at most, and only with call-site evidence.

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Junk-drawer JSONB | Same keys present in nearly every row, queried with `->>` in `WHERE` | Genuinely heterogeneous payloads, or a third-party blob stored verbatim | Promote the stable keys to columns; keep the rest in JSONB — breaking |
| JSONB queried without an index | `->>` in a `WHERE` and no GIN or expression index | The table is small | Expression index on the extracted key — non-breaking |
| EAV table | `(entity_id, key, value)` shape with `value` as text | Genuinely user-defined fields | Promote known keys to columns — breaking, large |
| One-to-one table split | FK that is also unique, and every parent has a child | The child is large, rarely read, or has different access rules | Merge into the parent — breaking |
| Nullable column cluster | A group of columns null together, correlated with a type discriminator | Only two variants, and the columns are few | Subtype table per variant — breaking, large |
| Array column used as a relation | An `_id[]` column joined against by unnesting | Small, ordered, and never joined — ordering is the reason arrays win | Join table — breaking |
| Wide table | Far more columns than its siblings, with distinct groups by prefix | The columns are all read together | Split by access pattern — breaking; needs call-site evidence, not a column count |
| Status modelled as several booleans | Two or more mutually exclusive boolean flags | The flags are genuinely independent | Single enum column — breaking |

---

## 6. Access and RLS

Only applies where the schema already uses row-level security. Skip the category otherwise
rather than proposing that a project adopt RLS.

| Smell | Detect | When it's fine | Fix |
|---|---|---|---|
| Table without RLS in an RLS-using schema | `relrowsecurity = false` where sibling tables have it | Reference or lookup data that is public by design | `ENABLE ROW LEVEL SECURITY` plus policies — behaviour-changing, flag as high |
| RLS enabled with no policy | `relrowsecurity` true, zero rows in `pg_policies` | Deliberate deny-all | Add a policy, or note the deny-all as intentional |
| Policy repeated across tables verbatim | Identical `USING` expressions | Fewer than three tables share it | Extract a `SECURITY DEFINER` helper function — non-breaking |
| Policy calling `auth.uid()` per row without an index | Policy references a column with no index | Table is small | Index the column the policy filters — non-breaking |
| Broad grants to a role | `PUBLIC` or an app role with more than it uses | The role is trusted and internal | Narrow the grant — behaviour-changing |

---

## Category scoring

Use these defaults, then adjust with reason stated:

| Category | Default severity |
|---|---|
| Missing PK, missing FK with orphans, wrong type holding wrong data | high |
| RLS gap on a table holding user data | high |
| Dead column or table with a data-backed proof | medium |
| Denormalized copy with no sync mechanism | medium |
| Junk-drawer JSONB filtered in `WHERE` | medium |
| Redundant index | low |
| Naming inconsistency | low |
| Misleading name | high |

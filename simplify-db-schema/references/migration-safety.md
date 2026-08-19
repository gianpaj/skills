# Migration safety

How to shape the SQL this skill writes. Two rules sit above everything else:

1. **A migration that breaks a running reader is two migrations.** Expand now, contract after
   every reader has shipped.
2. **A migration that takes `ACCESS EXCLUSIVE` for the length of a table scan is an outage.**
   Find the variant that does not.

---

## Expand and contract

The phases, and who does each:

| Phase | Migration | Who runs it |
|---|---|---|
| 1. Expand | Add the new column, index, or constraint. Nullable, no default that rewrites. | Migration file — safe now |
| 2. Backfill | Copy data in batches. | Migration file or a job — safe now |
| 3. Dual-write | Application writes both shapes. | App change — in the report as a diff |
| 4. Switch reads | Application reads the new shape. | App change — in the report as a diff |
| 5. Contract | Drop the old column, add `NOT NULL`, rename. | Migration file — **marked DO NOT RUN** |

Every contract file opens with the same header:

```sql
-- CONTRACT — DO NOT RUN until the expand migration is deployed, the backfill has
-- completed, and every reader in plans/<doc>.md § <finding> has shipped.
```

Phases 3 and 4 are app changes, so they stay diffs in the report — this skill does not edit
code. Say in the finding that the contract migration is blocked on them.

---

## Recipes

### Rename a column

A rename is instant and breaks every reader at once. Never rename in place on a table with
live traffic.

```sql
-- EXPAND
ALTER TABLE calls ADD COLUMN billing_status text;
-- backfill (see below), then dual-write in the app
```

```sql
-- CONTRACT — DO NOT RUN until every reader has shipped
ALTER TABLE calls DROP COLUMN status;
```

A view or a generated column can serve the old name during the transition when the readers are
outside your control.

### Change a column's type

```sql
-- EXPAND
ALTER TABLE calls ADD COLUMN user_id_uuid uuid;
CREATE INDEX CONCURRENTLY idx_calls_user_id_uuid ON calls (user_id_uuid);
```

```sql
-- CONTRACT — DO NOT RUN until every reader has shipped
ALTER TABLE calls DROP COLUMN user_id;
ALTER TABLE calls RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE calls ADD CONSTRAINT calls_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES users (id) NOT VALID;
ALTER TABLE calls VALIDATE CONSTRAINT calls_user_id_fkey;
```

`ALTER COLUMN ... TYPE` in place rewrites the whole table under `ACCESS EXCLUSIVE`. It is
acceptable only on a small table, and the finding must state the row count that makes it small.
Widening `varchar(n)`, or `varchar(n)` to `text`, is metadata-only and needs no expand pair.

### Add a foreign key

```sql
ALTER TABLE calls ADD CONSTRAINT calls_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES users (id) NOT VALID;
-- separate migration, or later in the same one:
ALTER TABLE calls VALIDATE CONSTRAINT calls_user_id_fkey;
```

`NOT VALID` skips the scan and still enforces the constraint on new rows. `VALIDATE` takes
`SHARE UPDATE EXCLUSIVE` — it does not block reads or writes. Resolve orphan rows before
validating; the finding must name the orphan count and offer the choice: delete, backfill, or
null them.

### Add `NOT NULL`

`SET NOT NULL` scans the table under `ACCESS EXCLUSIVE`. On Postgres 12 and later a validated
check constraint lets it skip the scan:

```sql
ALTER TABLE calls ADD CONSTRAINT calls_user_id_not_null
  CHECK (user_id IS NOT NULL) NOT VALID;
ALTER TABLE calls VALIDATE CONSTRAINT calls_user_id_not_null;  -- no write block
ALTER TABLE calls ALTER COLUMN user_id SET NOT NULL;           -- no scan on PG 12+
ALTER TABLE calls DROP CONSTRAINT calls_user_id_not_null;
```

### Add a unique constraint

```sql
CREATE UNIQUE INDEX CONCURRENTLY calls_external_ref_key ON calls (external_ref);
ALTER TABLE calls ADD CONSTRAINT calls_external_ref_key
  UNIQUE USING INDEX calls_external_ref_key;
```

Building the index concurrently first keeps writes flowing. Duplicates make the build fail and
leave an invalid index behind — the finding must report the duplicate count and include the
cleanup: `DROP INDEX CONCURRENTLY IF EXISTS calls_external_ref_key;`.

### Add a column with a default

Safe on Postgres 11 and later when the default is not volatile — it is stored as metadata and
no rewrite happens. `DEFAULT gen_random_uuid()` or `DEFAULT now()` **is** volatile and rewrites
the table; add the column nullable, backfill, then set the default.

### Drop a column

Instant metadata change, but it breaks readers, so it belongs in a contract migration. The
space is not reclaimed until the rows are rewritten.

### Drop an index

```sql
DROP INDEX CONCURRENTLY IF EXISTS idx_calls_status;
```

Non-breaking, and cheap to reverse — include the `CREATE INDEX CONCURRENTLY` statement that
restores it in the finding.

### Promote a JSONB key to a column

```sql
-- EXPAND
ALTER TABLE calls ADD COLUMN direction text;
-- backfill: UPDATE ... SET direction = meta->>'direction'
-- dual-write in the app, then switch reads
```

```sql
-- CONTRACT — DO NOT RUN until every reader has shipped
UPDATE calls SET meta = meta - 'direction' WHERE meta ? 'direction';
```

Keep the JSONB column. The finding promotes the stable keys, not the whole column.

### Add an enum value

`ALTER TYPE ... ADD VALUE` cannot run inside a transaction block before Postgres 12, and enum
values cannot be removed. When a set changes at all, a lookup table with an FK is the better
target — say which one the finding is proposing and why.

---

## Batched backfill

One `UPDATE` over millions of rows holds locks and bloats. Batch it, committing per batch:

```sql
CREATE OR REPLACE PROCEDURE backfill_calls_user_id_uuid()
LANGUAGE plpgsql AS $$
DECLARE
  updated integer;
BEGIN
  LOOP
    UPDATE calls SET user_id_uuid = user_id::uuid
    WHERE id IN (
      SELECT id FROM calls
      WHERE user_id IS NOT NULL AND user_id_uuid IS NULL
      ORDER BY id
      LIMIT 5000
      FOR UPDATE SKIP LOCKED
    );
    GET DIAGNOSTICS updated = ROW_COUNT;
    EXIT WHEN updated = 0;
    COMMIT;
    PERFORM pg_sleep(0.1);
  END LOOP;
END $$;

-- CALL backfill_calls_user_id_uuid();
```

`CALL` it outside a transaction so the `COMMIT` works. State the estimated runtime from the row
count in the finding. When a value can fail the cast, the backfill needs a `WHERE` guard and
the finding must say what happens to the rows it skips.

---

## Lock reference

| Operation | Lock | Cost |
|---|---|---|
| `ADD COLUMN`, no default or a constant default (PG 11+) | ACCESS EXCLUSIVE | metadata only |
| `ADD COLUMN` with a volatile default | ACCESS EXCLUSIVE | full rewrite |
| `DROP COLUMN` | ACCESS EXCLUSIVE | metadata only |
| `RENAME COLUMN` / `RENAME TABLE` | ACCESS EXCLUSIVE | instant |
| `ALTER COLUMN TYPE`, rewriting | ACCESS EXCLUSIVE | full rewrite |
| `ALTER COLUMN TYPE`, widening varchar or to text | ACCESS EXCLUSIVE | metadata only |
| `SET NOT NULL` | ACCESS EXCLUSIVE | full scan, unless a validated check exists on PG 12+ |
| `ADD CONSTRAINT` without `NOT VALID` | ACCESS EXCLUSIVE | full scan |
| `ADD CONSTRAINT ... NOT VALID` | ACCESS EXCLUSIVE | brief |
| `VALIDATE CONSTRAINT` | SHARE UPDATE EXCLUSIVE | scan, but reads and writes continue |
| `CREATE INDEX` | SHARE | blocks writes for the build |
| `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | two scans; can leave an invalid index on failure |
| `DROP INDEX` | ACCESS EXCLUSIVE | brief |
| `DROP INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | brief |

`ACCESS EXCLUSIVE` blocks everything, including reads — and a blocked `ALTER` queues behind a
long-running query while every later query queues behind *it*. Open migrations that take it
with a bounded wait:

```sql
SET lock_timeout = '3s';
```

`CONCURRENTLY` cannot run inside a transaction block. Migration tools that wrap each file in
one need an escape hatch: `-- +goose NO TRANSACTION`, Knex's `config.transaction = false`,
Rails' `disable_ddl_transaction!`. Name the project's escape hatch in the finding, or put the
concurrent statement in its own file.

---

## Writing the migration files

- One finding per migration file. Never bundle unrelated changes.
- Name files by the project's existing convention — copy the format from the newest file in the
  migrations directory, and increment or timestamp accordingly.
- Open every file with a comment naming the finding and the plan document.
- `IF EXISTS` and `IF NOT EXISTS` on drops and creates, so a partial run is re-runnable.
- Include the reversal as a comment when the tool has no `down` step, and as a real `down` when
  it does.
- Never write a `down` that silently loses data. Say `-- irreversible: <what is lost>` instead.

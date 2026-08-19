-- suspects.sql — catalog-level findings, plus generators for the exact probes.
--
-- Read-only. Sections A–H read catalogs and statistics only. Sections I–J emit SQL
-- text; they run nothing. Safe on a replica.
--
--   psql "$DATABASE_URL" -f queries/suspects.sql
--   psql "$DATABASE_URL" -v schemas='^public$' -v tables='^(calls|call_events)$' \
--        -f queries/suspects.sql
--
-- :tables narrows sections F onward to one cluster. Sections A–E always cover the
-- whole schema filter, because that is what Pass 1 triage needs.

\pset pager off
\timing off

\if :{?schemas}
\else
\set schemas '^public$'
\endif

\if :{?tables}
\else
\set tables '.*'
\endif

\echo ''
\echo '=== A. Statistics context ================================================'
\echo 'Zero idx_scan means nothing if stats_reset is recent. Report this date.'

SELECT stats_reset, now() - stats_reset AS stats_age
FROM pg_stat_database WHERE datname = current_database();

\echo ''
\echo '=== B. Indexes never scanned ============================================='
\echo 'Constraint-backing and unique indexes are excluded — they are not optional.'

SELECT
  n.nspname                                    AS schema_name,
  ct.relname                                   AS table_name,
  ci.relname                                   AS index_name,
  pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
  COALESCE(s.idx_scan, 0)                      AS idx_scan,
  pg_get_indexdef(i.indexrelid)                AS definition
FROM pg_index i
JOIN pg_class ci     ON ci.oid = i.indexrelid
JOIN pg_class ct     ON ct.oid = i.indrelid
JOIN pg_namespace n  ON n.oid = ct.relnamespace
LEFT JOIN pg_stat_user_indexes s ON s.indexrelid = i.indexrelid
WHERE n.nspname ~ :'schemas'
  AND COALESCE(s.idx_scan, 0) = 0
  AND NOT i.indisunique
  AND NOT i.indisprimary
  AND NOT EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conindid = i.indexrelid)
ORDER BY pg_relation_size(i.indexrelid) DESC;

\echo ''
\echo '=== C. Identical indexes ================================================='

SELECT
  n.nspname                                  AS schema_name,
  ct.relname                                 AS table_name,
  array_agg(ci.relname ORDER BY ci.relname)  AS identical_indexes,
  pg_get_indexdef(min(i.indexrelid))         AS definition
FROM pg_index i
JOIN pg_class ci    ON ci.oid = i.indexrelid
JOIN pg_class ct    ON ct.oid = i.indrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
WHERE n.nspname ~ :'schemas'
GROUP BY
  n.nspname, ct.relname, i.indrelid, ci.relam,
  i.indkey::text, i.indclass::text, i.indisunique,
  COALESCE(pg_get_expr(i.indexprs, i.indrelid), ''),
  COALESCE(pg_get_expr(i.indpred,  i.indrelid), '')
HAVING count(*) > 1
ORDER BY 1, 2;

\echo ''
\echo '=== D. Indexes that are a leading prefix of another index ================'
\echo 'Candidates only: a narrow index can still be worth keeping if it is much'
\echo 'smaller and serves a hot path. Check size and idx_scan before proposing.'

SELECT
  n.nspname                     AS schema_name,
  ct.relname                    AS table_name,
  ci1.relname                   AS narrow_index,
  pg_size_pretty(pg_relation_size(i1.indexrelid)) AS narrow_size,
  COALESCE(s1.idx_scan, 0)      AS narrow_scans,
  ci2.relname                   AS covering_index,
  pg_get_indexdef(i1.indexrelid) AS narrow_def,
  pg_get_indexdef(i2.indexrelid) AS covering_def
FROM pg_index i1
JOIN pg_index i2    ON i2.indrelid = i1.indrelid AND i2.indexrelid <> i1.indexrelid
JOIN pg_class ci1   ON ci1.oid = i1.indexrelid
JOIN pg_class ci2   ON ci2.oid = i2.indexrelid
JOIN pg_class ct    ON ct.oid = i1.indrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
LEFT JOIN pg_stat_user_indexes s1 ON s1.indexrelid = i1.indexrelid
WHERE n.nspname ~ :'schemas'
  AND ci1.relam = ci2.relam
  AND i1.indexprs IS NULL AND i2.indexprs IS NULL
  AND i1.indpred  IS NULL AND i2.indpred  IS NULL
  AND NOT i1.indisunique
  AND NOT i1.indisprimary
  -- i1's column list is a strict leading prefix of i2's
  AND position(i1.indkey::text || ' ' IN i2.indkey::text || ' ') = 1
  AND length(i1.indkey::text) < length(i2.indkey::text)
ORDER BY pg_relation_size(i1.indexrelid) DESC;

\echo ''
\echo '=== E. RLS coverage ======================================================'
\echo 'Only meaningful where the schema already uses RLS. Skip otherwise.'

SELECT
  n.nspname            AS schema_name,
  c.relname            AS table_name,
  c.relrowsecurity     AS rls_enabled,
  c.relforcerowsecurity AS rls_forced,
  (SELECT count(*) FROM pg_policies p
     WHERE p.schemaname = n.nspname AND p.tablename = c.relname) AS policies
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
ORDER BY c.relrowsecurity, 1, 2;

\echo ''
\echo '=== F. Columns named like a foreign key, with no foreign key ============='
\echo 'likely_target is a name guess. Confirm it before proposing a constraint.'

SELECT
  n.nspname                              AS schema_name,
  ct.relname                             AS table_name,
  a.attname                              AS column_name,
  format_type(a.atttypid, a.atttypmod)   AS column_type,
  a.attnotnull                           AS not_null,
  (SELECT string_agg(g.relname, ', ')
     FROM pg_class g
     JOIN pg_namespace gn ON gn.oid = g.relnamespace
     WHERE g.relkind IN ('r', 'p')
       AND gn.nspname = n.nspname
       AND g.relname IN (
         left(a.attname, length(a.attname) - 3),
         left(a.attname, length(a.attname) - 3) || 's')) AS likely_target
FROM pg_attribute a
JOIN pg_class ct    ON ct.oid = a.attrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
WHERE ct.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
  AND ct.relname ~ :'tables'
  AND a.attnum > 0 AND NOT a.attisdropped
  AND a.attname LIKE '%\_id'
  AND NOT EXISTS (
    SELECT 1 FROM pg_constraint k
    WHERE k.conrelid = ct.oid AND k.contype = 'f' AND a.attnum = ANY (k.conkey))
ORDER BY 1, 2, 3;

\echo ''
\echo '=== G. Suspect column types =============================================='
\echo 'timestamp-without-tz, float money, and text holding a foreign key.'

SELECT
  n.nspname                            AS schema_name,
  ct.relname                           AS table_name,
  a.attname                            AS column_name,
  format_type(a.atttypid, a.atttypmod) AS column_type,
  CASE
    WHEN a.atttypid = 'timestamp'::regtype THEN 'timestamp without time zone'
    WHEN a.atttypid IN ('real'::regtype, 'double precision'::regtype)
      THEN 'inexact type on a money-like name'
    WHEN a.atttypid IN ('text'::regtype, 'varchar'::regtype)
      AND a.attname LIKE '%\_id' THEN 'text holding an identifier'
    WHEN a.atttypid IN ('text'::regtype, 'varchar'::regtype)
      AND a.attname ~* '(^|_)(is|has|should|can)_' THEN 'text holding a boolean'
  END AS suspicion
FROM pg_attribute a
JOIN pg_class ct    ON ct.oid = a.attrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
WHERE ct.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
  AND ct.relname ~ :'tables'
  AND a.attnum > 0 AND NOT a.attisdropped
  AND (
    a.atttypid = 'timestamp'::regtype
    OR (a.atttypid IN ('real'::regtype, 'double precision'::regtype)
        AND a.attname ~* '(amount|price|cost|fee|total|balance|salary|revenue|charge|discount|tax)')
    OR (a.atttypid IN ('text'::regtype, 'varchar'::regtype)
        AND (a.attname LIKE '%\_id' OR a.attname ~* '(^|_)(is|has|should|can)_'))
  )
ORDER BY 1, 2, 3;

\echo ''
\echo '=== H. Column statistics from ANALYZE (free — no table scan) ============='
\echo 'null_frac 1 means the sample found only nulls. n_distinct between 1 and ~20'
\echo 'on a text column means it wants an enum or a lookup table. Both are sample'
\echo 'estimates — confirm with section I before dropping or constraining anything.'

SELECT
  s.schemaname   AS schema_name,
  s.tablename    AS table_name,
  s.attname      AS column_name,
  s.null_frac,
  s.n_distinct,
  s.avg_width,
  left(s.most_common_vals::text, 80) AS common_values
FROM pg_stats s
WHERE s.schemaname ~ :'schemas'
  AND s.tablename ~ :'tables'
  AND (s.null_frac > 0.99 OR (s.n_distinct > 0 AND s.n_distinct <= 20))
ORDER BY s.null_frac DESC, s.tablename, s.attname;

\echo ''
\echo '=== I. GENERATED: exact column probes ===================================='
\echo 'Copy and run these before proposing a DROP or a NOT NULL. They scan the'
\echo 'table — run them on a replica, or one at a time on a quiet database.'

SELECT format(
  'SELECT %L AS col, count(*) AS n_rows, count(%I) AS n_non_null, count(DISTINCT %I) AS n_distinct FROM %I.%I;',
  n.nspname || '.' || ct.relname || '.' || a.attname,
  a.attname, a.attname, n.nspname, ct.relname
) AS probe
FROM pg_attribute a
JOIN pg_class ct    ON ct.oid = a.attrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
WHERE ct.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
  AND ct.relname ~ :'tables'
  AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY ct.relname, a.attnum;

\echo ''
\echo '=== J. GENERATED: orphan-row checks for missing foreign keys ============='
\echo 'Run before proposing an FK. A non-zero count blocks VALIDATE CONSTRAINT and'
\echo 'must be resolved first — delete, backfill, or null the rows.'

SELECT format(
  'SELECT %L AS fk, count(*) AS orphan_rows FROM %I.%I c LEFT JOIN %I.%I t ON t.%I::text = c.%I::text WHERE c.%I IS NOT NULL AND t.%I IS NULL;',
  n.nspname || '.' || ct.relname || '.' || a.attname || ' -> ' || tgt.relname,
  n.nspname, ct.relname, n.nspname, tgt.relname,
  pk.attname, a.attname, a.attname, pk.attname
) AS orphan_check
FROM pg_attribute a
JOIN pg_class ct    ON ct.oid = a.attrelid
JOIN pg_namespace n ON n.oid = ct.relnamespace
JOIN pg_class tgt   ON tgt.relnamespace = n.oid
                   AND tgt.relkind IN ('r', 'p')
                   AND tgt.relname IN (
                         left(a.attname, length(a.attname) - 3),
                         left(a.attname, length(a.attname) - 3) || 's')
JOIN pg_constraint pkc ON pkc.conrelid = tgt.oid AND pkc.contype = 'p'
                   AND array_length(pkc.conkey, 1) = 1
JOIN pg_attribute pk   ON pk.attrelid = tgt.oid AND pk.attnum = pkc.conkey[1]
WHERE ct.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
  AND ct.relname ~ :'tables'
  AND a.attnum > 0 AND NOT a.attisdropped
  AND a.attname LIKE '%\_id'
  AND NOT EXISTS (
    SELECT 1 FROM pg_constraint k
    WHERE k.conrelid = ct.oid AND k.contype = 'f' AND a.attnum = ANY (k.conkey))
ORDER BY 1;

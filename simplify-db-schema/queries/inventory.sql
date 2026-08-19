-- inventory.sql — Pass 1 triage input.
--
-- Read-only. Reads system catalogs and statistics views only; writes nothing and
-- takes no locks beyond the catalog reads. Safe on a replica.
--
--   psql "$DATABASE_URL" -f queries/inventory.sql
--   psql "$DATABASE_URL" -v schemas='^(public|billing)$' -f queries/inventory.sql
--
-- Requires psql 10 or later for the \if syntax below.

\pset pager off
\timing off

\if :{?schemas}
\else
\set schemas '^public$'
\endif

\echo ''
\echo '=== 0. Context ==========================================================='
\echo '(idx_scan counts are meaningless if stats were reset recently)'

SELECT
  current_database()                      AS database,
  current_setting('server_version')       AS server_version,
  d.stats_reset                           AS stats_reset,
  :'schemas'                              AS schema_filter
FROM pg_stat_database d
WHERE d.datname = current_database();

\echo ''
\echo '=== 1. Tables ============================================================'
\echo 'est_rows comes from ANALYZE. A 0 with a null last_analyzed means never'
\echo 'analyzed, NOT empty — never call such a table dead.'

SELECT
  n.nspname                                            AS schema_name,
  c.relname                                            AS table_name,
  GREATEST(c.reltuples, 0)::bigint                     AS est_rows,
  GREATEST(s.last_analyze, s.last_autoanalyze)         AS last_analyzed,
  pg_size_pretty(pg_total_relation_size(c.oid))        AS total_size,
  (SELECT count(*) FROM pg_attribute a
     WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped) AS cols,
  (SELECT count(*) FROM pg_index i WHERE i.indrelid = c.oid)           AS idx,
  (SELECT count(*) FROM pg_constraint k
     WHERE k.conrelid = c.oid AND k.contype = 'f')                     AS fks,
  EXISTS (SELECT 1 FROM pg_constraint k
     WHERE k.conrelid = c.oid AND k.contype = 'p')                     AS has_pk,
  c.relrowsecurity                                     AS rls,
  s.seq_scan,
  s.idx_scan
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
ORDER BY pg_total_relation_size(c.oid) DESC;

\echo ''
\echo '=== 2. Foreign-key edges (cluster tables by connected component) ========='

SELECT
  sn.nspname   AS from_schema,
  sc.relname   AS from_table,
  tn.nspname   AS to_schema,
  tc.relname   AS to_table,
  k.conname    AS constraint_name,
  CASE k.confdeltype
    WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' WHEN 'c' THEN 'CASCADE'
    WHEN 'n' THEN 'SET NULL'  WHEN 'd' THEN 'SET DEFAULT'
  END          AS on_delete,
  k.convalidated AS validated
FROM pg_constraint k
JOIN pg_class sc     ON sc.oid = k.conrelid
JOIN pg_namespace sn ON sn.oid = sc.relnamespace
JOIN pg_class tc     ON tc.oid = k.confrelid
JOIN pg_namespace tn ON tn.oid = tc.relnamespace
WHERE k.contype = 'f'
  AND sn.nspname ~ :'schemas'
ORDER BY 1, 2, 4;

\echo ''
\echo '=== 3. Tables with no primary key ========================================'

SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  GREATEST(c.reltuples, 0)::bigint AS est_rows
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND n.nspname ~ :'schemas'
  AND NOT EXISTS (
    SELECT 1 FROM pg_constraint k WHERE k.conrelid = c.oid AND k.contype = 'p')
ORDER BY 3 DESC;

\echo ''
\echo '=== 4. Enum types and how many columns use them =========================='

SELECT
  n.nspname AS schema_name,
  t.typname AS enum_type,
  (SELECT count(*) FROM pg_enum e WHERE e.enumtypid = t.oid) AS n_values,
  count(a.attrelid) AS used_by_columns
FROM pg_type t
JOIN pg_namespace n ON n.oid = t.typnamespace
LEFT JOIN pg_attribute a
       ON a.atttypid = t.oid AND a.attnum > 0 AND NOT a.attisdropped
WHERE t.typtype = 'e'
  AND n.nspname ~ :'schemas'
GROUP BY 1, 2, 3
ORDER BY 4, 2;

\echo ''
\echo '=== 5. Views and materialized views ======================================'

SELECT
  n.nspname AS schema_name,
  c.relname AS view_name,
  CASE c.relkind WHEN 'v' THEN 'view' WHEN 'm' THEN 'matview' END AS kind
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('v', 'm')
  AND n.nspname ~ :'schemas'
ORDER BY 1, 2;

\echo ''
\echo '=== 6. Totals ============================================================'

SELECT
  count(*) FILTER (WHERE c.relkind IN ('r', 'p')) AS tables,
  count(*) FILTER (WHERE c.relkind = 'v')         AS views,
  count(*) FILTER (WHERE c.relkind = 'm')         AS matviews,
  (SELECT count(*) FROM pg_attribute a
     JOIN pg_class ac ON ac.oid = a.attrelid
     JOIN pg_namespace an ON an.oid = ac.relnamespace
     WHERE ac.relkind IN ('r', 'p') AND an.nspname ~ :'schemas'
       AND a.attnum > 0 AND NOT a.attisdropped)   AS columns,
  (SELECT count(*) FROM pg_index i
     JOIN pg_class ic ON ic.oid = i.indrelid
     JOIN pg_namespace inn ON inn.oid = ic.relnamespace
     WHERE inn.nspname ~ :'schemas')              AS indexes,
  pg_size_pretty(sum(pg_total_relation_size(c.oid))) AS total_size
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p', 'v', 'm')
  AND n.nspname ~ :'schemas';

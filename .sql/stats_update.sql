BEGIN TRANSACTION;

-- Example inputs:
-- :mid       = metadata_id for sensor.nimbus_hp_ch_consumed_energy_today
-- :t1        = '2026-04-15 20:00:00'   (local time)
-- :t2        = '2026-04-15 22:00:00'   (local time)
-- :new_08_10 = 0.0                     (or your corrected per-hour value)
-- :new_10_12 = 0.0                     (or your corrected per-hour value)

-- 1) Update the bad hourly state rows
UPDATE statistics
SET state = :new_08_10
WHERE metadata_id = :mid
  AND datetime(start_ts, 'unixepoch', 'localtime') IN (:t1, datetime(:t1, '+1 hour'));

UPDATE statistics
SET state = :new_10_12
WHERE metadata_id = :mid
  AND datetime(start_ts, 'unixepoch', 'localtime') IN (:t2, datetime(:t2, '+1 hour'));

-- 2) Rebuild cumulative sum from first changed hour onward
WITH
first_ts AS (
  SELECT MIN(start_ts) AS ts
  FROM statistics
  WHERE metadata_id = :mid
    AND datetime(start_ts, 'unixepoch', 'localtime') IN (:t1, datetime(:t1, '+1 hour'), :t2, datetime(:t2, '+1 hour'))
),
base AS (
  SELECT COALESCE((
    SELECT "sum"
    FROM statistics
    WHERE metadata_id = :mid
      AND start_ts < (SELECT ts FROM first_ts)
    ORDER BY start_ts DESC, id DESC
    LIMIT 1
  ), 0.0) AS base_sum
),
calc AS (
  SELECT
    s.id,
    (SELECT base_sum FROM base) +
    SUM(s.state) OVER (ORDER BY s.start_ts, s.id) AS new_sum
  FROM statistics s
  WHERE s.metadata_id = :mid
    AND s.start_ts >= (SELECT ts FROM first_ts)
)
UPDATE statistics
SET "sum" = (SELECT new_sum FROM calc WHERE calc.id = statistics.id)
WHERE id IN (SELECT id FROM calc);

COMMIT;
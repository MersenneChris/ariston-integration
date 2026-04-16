WITH target AS (
  SELECT id, statistic_id
  FROM statistics_meta
  WHERE statistic_id IN (
    'sensor.nimbus_hp_ch_produced_energy_today',
    'sensor.nimbus_hp_dhw_produced_energy_today',
    'sensor.nimbus_hp_ch_consumed_energy_today',
    'sensor.nimbus_hp_dhw_consumed_energy_today'
  )
)
SELECT
  t.statistic_id,
  s.id AS row_id,
  datetime(s.start_ts, 'unixepoch', 'localtime') AS local_time,
  s.state,
  s.sum
FROM statistics s
JOIN target t ON t.id = s.metadata_id
WHERE datetime(s.start_ts, 'unixepoch', 'localtime') >= datetime(date('now','localtime'))
  AND datetime(s.start_ts, 'unixepoch', 'localtime') <  datetime(date('now','localtime','+1 day'))
ORDER BY t.statistic_id, s.start_ts;
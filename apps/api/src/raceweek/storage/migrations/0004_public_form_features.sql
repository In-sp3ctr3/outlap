CREATE TABLE IF NOT EXISTS public_form_features (
  feature_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  feature_key TEXT NOT NULL,
  feature_value DOUBLE,
  source_mode TEXT NOT NULL,
  source_snapshot_id TEXT NOT NULL,
  calculated_at TIMESTAMP NOT NULL,
  payload_json JSON NOT NULL
);

CREATE INDEX IF NOT EXISTS public_form_features_event_idx
ON public_form_features(event_id, asset_id, feature_key);

-- Tokyo Rail Town Scale Atlas: canonical logical schema v0.1.0
-- Dialect target: portable SQL; geometry is immutable WKB plus explicit CRS.
-- All dates/timestamps use ISO-8601 UTC text to keep SQLite/DuckDB fixtures portable.

PRAGMA foreign_keys = ON;

CREATE TABLE source_release (
    source_release_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    release_label TEXT NOT NULL,
    reference_start TEXT,
    reference_end TEXT,
    survey_date TEXT,
    published_at TEXT,
    retrieved_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    license_id TEXT NOT NULL,
    correction_note TEXT,
    UNIQUE (source_id, sha256)
);

CREATE TABLE model_run (
    model_run_id TEXT PRIMARY KEY CHECK (model_run_id LIKE 'run_%'),
    model_version TEXT NOT NULL,
    parameter_set_sha256 TEXT NOT NULL CHECK (length(parameter_set_sha256) = 64),
    source_bundle_sha256 TEXT NOT NULL CHECK (length(source_bundle_sha256) = 64),
    created_at TEXT NOT NULL,
    run_status TEXT NOT NULL CHECK (run_status IN ('candidate', 'accepted', 'rejected'))
);

CREATE TABLE line (
    line_id TEXT PRIMARY KEY CHECK (line_id LIKE 'lin_%'),
    display_name_ja TEXT NOT NULL,
    operator_id TEXT,
    line_kind TEXT NOT NULL CHECK (line_kind IN ('infrastructure', 'service_corridor', 'analysis_corridor')),
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('active', 'closed', 'planned', 'unknown')),
    valid_from TEXT,
    valid_to TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE station (
    station_id TEXT PRIMARY KEY CHECK (station_id LIKE 'sta_%'),
    display_name_ja TEXT NOT NULL,
    operator_id TEXT,
    station_kind TEXT NOT NULL CHECK (station_kind IN ('surface', 'underground', 'mixed', 'unknown')),
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('active', 'closed', 'planned', 'unknown')),
    valid_from TEXT,
    valid_to TEXT,
    centroid_wkb BLOB,
    geometry_crs TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE station_line_membership (
    station_id TEXT NOT NULL REFERENCES station(station_id),
    line_id TEXT NOT NULL REFERENCES line(line_id),
    sequence_index INTEGER,
    distance_from_origin_km REAL CHECK (distance_from_origin_km IS NULL OR distance_from_origin_km >= 0),
    valid_from TEXT,
    valid_to TEXT,
    PRIMARY KEY (station_id, line_id, valid_from)
);

CREATE TABLE station_group (
    station_group_id TEXT PRIMARY KEY CHECK (station_group_id LIKE 'stg_%'),
    display_name_ja TEXT NOT NULL,
    group_rule TEXT NOT NULL CHECK (group_rule IN ('source_seed', 'same_facility', 'manual_adjudication')),
    review_status TEXT NOT NULL CHECK (review_status IN ('candidate', 'confirmed', 'rejected', 'deprecated')),
    created_at TEXT NOT NULL
);

CREATE TABLE station_group_member (
    station_group_id TEXT NOT NULL REFERENCES station_group(station_group_id),
    station_id TEXT NOT NULL REFERENCES station(station_id),
    membership_basis TEXT NOT NULL,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    reviewed_by TEXT,
    reviewed_at TEXT,
    PRIMARY KEY (station_group_id, station_id)
);

CREATE TABLE hub (
    hub_id TEXT PRIMARY KEY CHECK (hub_id LIKE 'hub_%'),
    display_name_ja TEXT NOT NULL,
    transfer_basis TEXT NOT NULL CHECK (transfer_basis IN ('official', 'paid_area', 'signed_walk', 'manual')),
    review_status TEXT NOT NULL CHECK (review_status IN ('candidate', 'confirmed', 'rejected', 'deprecated')),
    created_at TEXT NOT NULL
);

CREATE TABLE hub_station_group_link (
    hub_id TEXT NOT NULL REFERENCES hub(hub_id),
    station_group_id TEXT NOT NULL REFERENCES station_group(station_group_id),
    walking_distance_m REAL CHECK (walking_distance_m IS NULL OR walking_distance_m >= 0),
    evidence_json TEXT NOT NULL,
    is_manual INTEGER NOT NULL CHECK (is_manual IN (0, 1)),
    PRIMARY KEY (hub_id, station_group_id)
);

CREATE TABLE center (
    center_id TEXT PRIMARY KEY CHECK (center_id LIKE 'ctr_%'),
    display_name_ja TEXT NOT NULL,
    parent_center_id TEXT REFERENCES center(center_id),
    center_level TEXT NOT NULL CHECK (center_level IN ('parent', 'center', 'subarea')),
    identity_status TEXT NOT NULL CHECK (identity_status IN ('candidate', 'confirmed', 'retired')),
    created_at TEXT NOT NULL,
    retired_at TEXT,
    CHECK (parent_center_id IS NULL OR parent_center_id <> center_id)
);

CREATE TABLE center_version (
    center_id TEXT NOT NULL REFERENCES center(center_id),
    model_run_id TEXT NOT NULL REFERENCES model_run(model_run_id),
    polygon_wkb BLOB,
    centroid_wkb BLOB,
    geometry_crs TEXT NOT NULL,
    boundary_method TEXT NOT NULL,
    boundary_confidence REAL CHECK (boundary_confidence IS NULL OR (boundary_confidence >= 0 AND boundary_confidence <= 1)),
    manual_override_id TEXT,
    geometry_sha256 TEXT CHECK (geometry_sha256 IS NULL OR length(geometry_sha256) = 64),
    PRIMARY KEY (center_id, model_run_id)
);

CREATE TABLE center_lineage (
    predecessor_center_id TEXT NOT NULL REFERENCES center(center_id),
    successor_center_id TEXT NOT NULL REFERENCES center(center_id),
    relation_type TEXT NOT NULL CHECK (relation_type IN ('split_into', 'merged_into', 'superseded_by', 'reidentified_as')),
    effective_model_run_id TEXT NOT NULL REFERENCES model_run(model_run_id),
    rationale TEXT NOT NULL,
    PRIMARY KEY (predecessor_center_id, successor_center_id, effective_model_run_id),
    CHECK (predecessor_center_id <> successor_center_id)
);

CREATE TABLE station_center_link (
    station_center_link_id TEXT PRIMARY KEY CHECK (station_center_link_id LIKE 'scl_%'),
    station_group_id TEXT NOT NULL REFERENCES station_group(station_group_id),
    center_id TEXT NOT NULL REFERENCES center(center_id),
    model_run_id TEXT NOT NULL REFERENCES model_run(model_run_id),
    role TEXT NOT NULL CHECK (role IN ('core', 'auxiliary', 'edge', 'transfer_only', 'multi_entry')),
    link_confidence REAL CHECK (link_confidence IS NULL OR (link_confidence >= 0 AND link_confidence <= 1)),
    evidence_json TEXT NOT NULL,
    is_manual INTEGER NOT NULL CHECK (is_manual IN (0, 1)),
    UNIQUE (station_group_id, center_id, model_run_id, role)
);

CREATE TABLE line_center_link (
    line_center_link_id TEXT PRIMARY KEY CHECK (line_center_link_id LIKE 'lcl_%'),
    line_id TEXT NOT NULL REFERENCES line(line_id),
    center_id TEXT NOT NULL REFERENCES center(center_id),
    model_run_id TEXT NOT NULL REFERENCES model_run(model_run_id),
    first_sequence INTEGER,
    last_sequence INTEGER,
    linked_station_group_count INTEGER NOT NULL CHECK (linked_station_group_count >= 1),
    distance_along_line_km REAL CHECK (distance_along_line_km IS NULL OR distance_along_line_km >= 0),
    link_confidence REAL CHECK (link_confidence IS NULL OR (link_confidence >= 0 AND link_confidence <= 1)),
    UNIQUE (line_id, center_id, model_run_id),
    CHECK (first_sequence IS NULL OR last_sequence IS NULL OR first_sequence <= last_sequence)
);

CREATE TABLE entity_alias (
    entity_alias_id TEXT PRIMARY KEY CHECK (entity_alias_id LIKE 'als_%'),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('station', 'station_group', 'hub', 'line', 'center')),
    entity_id TEXT NOT NULL,
    source_release_id TEXT NOT NULL REFERENCES source_release(source_release_id),
    source_namespace TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_name TEXT,
    valid_from TEXT,
    valid_to TEXT,
    match_method TEXT NOT NULL CHECK (match_method IN ('exact_source_seed', 'crosswalk', 'spatial_name', 'manual')),
    match_confidence REAL CHECK (match_confidence IS NULL OR (match_confidence >= 0 AND match_confidence <= 1)),
    review_status TEXT NOT NULL CHECK (review_status IN ('candidate', 'confirmed', 'rejected')),
    UNIQUE (source_release_id, source_namespace, source_key, entity_type)
);

CREATE TABLE identity_review_queue (
    review_id TEXT PRIMARY KEY CHECK (review_id LIKE 'idr_%'),
    entity_type TEXT NOT NULL,
    source_release_id TEXT NOT NULL REFERENCES source_release(source_release_id),
    source_key TEXT NOT NULL,
    issue_type TEXT NOT NULL CHECK (issue_type IN ('no_match', 'ambiguous_match', 'collision', 'split_candidate', 'merge_candidate')),
    candidate_entity_ids_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'wont_fix')),
    resolution_note TEXT,
    resolved_at TEXT
);

CREATE TABLE metric_definition (
    metric_code TEXT PRIMARY KEY,
    display_name_ja TEXT NOT NULL,
    unit TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (value_type IN ('count', 'ratio', 'currency', 'area', 'distance', 'score', 'category')),
    allowed_score_domain TEXT NOT NULL CHECK (allowed_score_domain IN ('core_scale', 'access', 'type', 'confidence', 'validation', 'none')),
    definition_version TEXT NOT NULL
);

CREATE TABLE feature_observation (
    observation_id TEXT PRIMARY KEY CHECK (observation_id LIKE 'obs_%'),
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metric_code TEXT NOT NULL REFERENCES metric_definition(metric_code),
    numeric_value REAL,
    raw_value TEXT,
    observation_status TEXT NOT NULL CHECK (observation_status IN (
        'observed', 'observed_zero', 'imputed', 'suppressed',
        'aggregation_destination', 'not_public', 'not_surveyed',
        'not_applicable', 'source_absent', 'duplicate_on_other_record',
        'station_absent', 'outside_scope', 'invalid'
    )),
    unit TEXT NOT NULL,
    source_release_id TEXT NOT NULL REFERENCES source_release(source_release_id),
    source_record_key TEXT NOT NULL,
    reference_start TEXT,
    reference_end TEXT,
    published_at TEXT,
    retrieved_at TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    UNIQUE (entity_type, entity_id, metric_code, source_release_id, source_record_key),
    CHECK (
        (observation_status = 'observed' AND numeric_value IS NOT NULL AND numeric_value > 0)
        OR (observation_status = 'observed_zero' AND numeric_value = 0)
        OR (observation_status IN ('imputed', 'aggregation_destination') AND numeric_value IS NOT NULL)
        OR (observation_status IN (
            'suppressed', 'not_public', 'not_surveyed', 'not_applicable',
            'source_absent', 'duplicate_on_other_record', 'station_absent',
            'outside_scope', 'invalid'
        ) AND numeric_value IS NULL)
    )
);

CREATE TABLE manual_override (
    manual_override_id TEXT PRIMARY KEY CHECK (manual_override_id LIKE 'ovr_%'),
    target_table TEXT NOT NULL,
    target_key TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('insert', 'replace', 'retire', 'link', 'unlink')),
    patch_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_urls_json TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at TEXT NOT NULL,
    supersedes_override_id TEXT REFERENCES manual_override(manual_override_id)
);

CREATE TABLE golden_eval (
    golden_eval_id TEXT PRIMARY KEY CHECK (golden_eval_id LIKE 'GE%'),
    registry_version TEXT NOT NULL,
    display_name_ja TEXT NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('calibration', 'holdout')),
    expected_constraints_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'adjudicated', 'retired'))
);

-- Required deduplicated analysis view. A center appears at most once per line/model run.
CREATE VIEW line_center_deduplicated AS
SELECT
    line_id,
    center_id,
    model_run_id,
    MIN(first_sequence) AS first_sequence,
    MAX(last_sequence) AS last_sequence,
    MAX(linked_station_group_count) AS linked_station_group_count,
    MIN(distance_along_line_km) AS distance_along_line_km
FROM line_center_link
GROUP BY line_id, center_id, model_run_id;

-- Crosswalk interface produced after gated N02 acquisition in Phase 1.
CREATE VIEW station_line_crosswalk AS
SELECT
    s.station_id,
    sg.station_group_id,
    hsg.hub_id,
    slm.line_id,
    slm.sequence_index,
    slm.distance_from_origin_km
FROM station s
JOIN station_group_member sgm ON sgm.station_id = s.station_id
JOIN station_group sg ON sg.station_group_id = sgm.station_group_id
JOIN station_line_membership slm ON slm.station_id = s.station_id
LEFT JOIN hub_station_group_link hsg ON hsg.station_group_id = sg.station_group_id;

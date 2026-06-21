CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    run_date TEXT NOT NULL,
    client_brief TEXT,
    n_personas INTEGER,
    n_hooks INTEGER,
    n_images_generated INTEGER DEFAULT 0,
    n_images_failed INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    provider TEXT,
    output_dir TEXT,
    report_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS generation_results (
    id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES campaigns(id),
    persona_name TEXT,
    hooks_text TEXT,
    prompt TEXT,
    negative_prompt TEXT,
    image_path TEXT,
    image_filename TEXT,
    status TEXT,
    error_message TEXT,
    provider TEXT,
    timestamp TEXT,
    generation_time_sec REAL DEFAULT 0.0,
    cost_usd REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT REFERENCES campaigns(id),
    step_number INTEGER,
    feedback_text TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

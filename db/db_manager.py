import os
import sqlite3
from pathlib import Path

from core.models import GenerationResultModel


def _db_path() -> str:
    return os.getenv("SQLITE_PATH", "data/campaigns.sqlite")


def _connect() -> sqlite3.Connection:
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    with _connect() as conn:
        conn.executescript(schema_path.read_text())


def insert_campaign(
    campaign_id: str,
    client_name: str,
    client_brief: str,
    n_personas: int,
    n_hooks: int,
    provider: str,
    output_dir: str,
) -> None:
    from datetime import datetime
    with _connect() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO campaigns
               (id, client_name, run_date, client_brief, n_personas, n_hooks, provider, output_dir)
               VALUES (?,?,?,?,?,?,?,?)""",
            (campaign_id, client_name, datetime.now().isoformat(),
             client_brief, n_personas, n_hooks, provider, output_dir),
        )


def update_campaign_stats(
    campaign_id: str,
    n_generated: int,
    n_failed: int,
    total_cost: float,
    report_path: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """UPDATE campaigns SET n_images_generated=?, n_images_failed=?,
               total_cost_usd=?, report_path=? WHERE id=?""",
            (n_generated, n_failed, total_cost, report_path, campaign_id),
        )


def insert_result(campaign_id: str, result: GenerationResultModel) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO generation_results
               (id, campaign_id, persona_name, hooks_text, prompt,
                negative_prompt, image_path, image_filename, status, error_message,
                provider, timestamp, generation_time_sec, cost_usd)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (result.row_id, campaign_id, result.persona_name, result.hooks_text,
             result.prompt, result.negative_prompt,
             result.image_path, result.image_filename, result.status,
             result.error_message, result.provider, result.timestamp,
             result.generation_time_sec, result.cost_usd),
        )


def insert_feedback(campaign_id: str, step: int, text: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO feedback (campaign_id, step_number, feedback_text) VALUES (?,?,?)",
            (campaign_id, step, text),
        )

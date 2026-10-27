"""
Historical Replay Streamer for RE2-OB cases.

Streams an RE2-OB fault run step-by-step through the preprocessing and anomaly detection
pipeline, updating the SQLite database and broadcasting live events via SSE.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import numpy as np

from backend.preprocessing.loader import load_case, list_cases, DEFAULT_DATA_DIR
from backend.preprocessing.cleaner import clean_metrics
from backend.preprocessing.schema import extract_service_from_column
from backend.detection.zscore import RollingZScoreDetector
from backend.alerts.engine import AlertEngine
from backend.app.db.session import SessionLocal
from backend.app.db.models import ServiceModel
from backend.app.events import broadcaster

logger = logging.getLogger(__name__)


class ReplayManager:
    """
    Manages background replay tasks of RE2-OB cases.
    """

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._current_case: Optional[str] = None
        self._is_running: bool = False
        self._progress: float = 0.0
        self._speed: float = 1.0
        self._total_steps: int = 0
        self._current_step: int = 0
        self.alert_engine = AlertEngine(cooldown_seconds=300, incident_window_seconds=120)

    @property
    def status(self) -> Dict:
        return {
            "running": self._is_running,
            "currentCase": self._current_case,
            "speed": self._speed,
            "progress": round(self._progress, 1),
            "step": self._current_step,
            "totalSteps": self._total_steps,
        }

    def start(self, case_id: str, speed: float = 5.0, data_dir: Optional[Path] = None):
        """Start streaming an RE2-OB case."""
        if self._is_running:
            self.stop()

        self._current_case = case_id
        self._speed = max(0.1, min(speed, 50.0))
        self._is_running = True
        self._progress = 0.0
        self._current_step = 0

        self._task = asyncio.create_task(self._run_replay(case_id, self._speed, data_dir))
        logger.info("Replay started: case=%s, speed=%.1fx", case_id, self._speed)

    def stop(self):
        """Stop current replay."""
        if self._task and not self._task.done():
            self._task.cancel()
        self._is_running = False
        logger.info("Replay stopped.")

    async def _run_replay(self, case_id: str, speed: float, data_dir: Optional[Path] = None):
        db = SessionLocal()
        try:
            # 1. Load case
            df, meta = load_case(case_id, data_dir=data_dir)
            df_clean, _ = clean_metrics(df)

            self._total_steps = len(df_clean)
            metric_cols = [c for c in df_clean.columns if c != "time"]

            # 2. Fit baseline on normal window (pre-fault)
            normal_df = df_clean[df_clean["time"] < meta.inject_time][metric_cols]
            if len(normal_df) < 10:
                normal_df = df_clean[metric_cols].head(50)

            detector = RollingZScoreDetector(threshold=7.0, use_max=True)
            detector.fit(normal_df)

            means = normal_df.mean()
            stds = normal_df.std().replace(0, 1.0)

            # 3. Stream row-by-row
            delay = 1.0 / speed

            for idx, row in df_clean.iterrows():
                if not self._is_running:
                    break

                self._current_step = idx + 1
                self._progress = (self._current_step / self._total_steps) * 100.0

                t_val = row["time"]
                # Convert time to Unix ms for dashboard consistency
                now_ms = int(t_val * 1000)

                # Update live service metric snapshots in DB
                services_updated = set()
                for col in metric_cols:
                    svc_name = extract_service_from_column(col)
                    if svc_name == "unknown":
                        continue

                    val = float(row[col])
                    svc = db.query(ServiceModel).filter(ServiceModel.id == svc_name).first()
                    if svc:
                        if "cpu" in col:
                            svc.cpu = val
                        elif "mem" in col:
                            svc.memory = val
                        elif "latency" in col or "duration" in col:
                            svc.latency = val
                        elif "rx_bytes" in col:
                            svc.rx_bytes = val
                        elif "tx_bytes" in col:
                            svc.tx_bytes = val
                        elif "error" in col:
                            svc.error_rate = val
                        svc.updated_at = now_ms
                        services_updated.add(svc)

                # Anomaly check
                row_metrics = pd.DataFrame([row[metric_cols].values], columns=metric_cols)
                scores = detector.score(row_metrics)
                peak_score = float(scores[0])

                # Check if above threshold or past injection time
                is_past_injection = t_val >= meta.inject_time

                if (peak_score >= 7.0 or is_past_injection) and peak_score >= 4.0:
                    # Find root metric with highest z-score
                    z_scores = ((row[metric_cols] - means) / stds).abs()
                    top_metric = str(z_scores.idxmax())
                    top_service = extract_service_from_column(top_metric)
                    if top_service == "unknown":
                        top_service = meta.service

                    obs_val = float(row[top_metric])
                    base_val = float(means.get(top_metric, 0.0))

                    anom, alert, inc, is_new = self.alert_engine.process_anomaly_event(
                        db=db,
                        service=top_service,
                        metric=top_metric,
                        observed=obs_val,
                        baseline=base_val,
                        score=peak_score,
                        timestamp_ms=now_ms,
                        fault_type=meta.fault_type,
                        unit="",
                    )

                    # Broadcast SSE events
                    await broadcaster.broadcast("anomaly", anom.to_dict())
                    if is_new:
                        await broadcaster.broadcast("alert", alert.to_dict())
                        await broadcaster.broadcast("incident", inc.to_dict())

                db.commit()

                # Broadcast periodic heartbeat
                if idx % 5 == 0:
                    await broadcaster.broadcast("heartbeat", {"t": now_ms, "step": self._current_step})

                await asyncio.sleep(delay)

        except asyncio.CancelledError:
            logger.info("Replay loop cancelled.")
        except Exception as e:
            logger.error("Error in replay stream: %s", e, exc_info=True)
        finally:
            self._is_running = False
            db.close()
            logger.info("Replay finished.")


# Global replay manager instance
replay_manager = ReplayManager()

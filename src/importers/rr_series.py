from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import json

import pandas as pd


@dataclass
class RRSeries:
    session_id: str
    source: str
    file_name: str
    sheet_name: Optional[str]
    rr_ms: list[float]
    time_s: Optional[list[float]] = None
    detected_rr_column: Optional[str] = None
    detected_time_column: Optional[str] = None
    rr_unit: str = "ms"
    n_intervals: int = 0
    duration_s: Optional[float] = None
    rr_min_ms: Optional[float] = None
    rr_max_ms: Optional[float] = None
    rr_mean_ms: Optional[float] = None
    status: str = "unknown"
    notes: str = ""

    def to_frame(self) -> pd.DataFrame:
        df = pd.DataFrame({"rr_ms": self.rr_ms})
        if self.time_s is not None and len(self.time_s) == len(self.rr_ms):
            df.insert(0, "time_s", self.time_s)
        df.insert(0, "source", self.source)
        df.insert(0, "session_id", self.session_id)
        return df

    def metadata(self) -> dict:
        d = asdict(self)
        d.pop("rr_ms", None)
        d.pop("time_s", None)
        return d

    def save(self, out_dir: Path) -> tuple[Path, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"{self.session_id}_{self.source}_rr_normalizado.csv"
        json_path = out_dir / f"{self.session_id}_{self.source}_rr_metadata.json"
        self.to_frame().to_csv(csv_path, index=False, encoding="utf-8-sig")
        json_path.write_text(json.dumps(self.metadata(), ensure_ascii=False, indent=2), encoding="utf-8")
        return csv_path, json_path

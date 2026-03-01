from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Project root: .../<project>/ingest/download.py -> parents[1] = project root
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw" / "siat_stat_uz"
MANIFEST = BASE_DIR / "ingest" / "manifest.csv"


@dataclass
class ManifestRow:
    dataset_id: str
    url: str
    filename: str
    title_uz: str = ""
    metric_key: str = ""
    periodicity: str = ""
    notes: str = ""


def make_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def detect_delimiter(first_line: str) -> str:
    if "\t" in first_line:
        return "\t"
    if ";" in first_line and "," not in first_line:
        return ";"
    return ","


def read_manifest() -> List[ManifestRow]:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST}")

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = detect_delimiter(first_line)

        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Manifest has no header row.")

        # header trim + quote trim
        reader.fieldnames = [h.strip().strip('"') for h in reader.fieldnames]

        required = {"dataset_id", "url", "filename"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise KeyError(f"Manifest missing columns: {sorted(missing)}. Found: {reader.fieldnames}")

        rows: List[ManifestRow] = []
        for r in reader:
            # key/value clean
            r = {k.strip().strip('"'): (v.strip().strip('"') if isinstance(v, str) else v) for k, v in r.items()}

            rows.append(
                ManifestRow(
                    dataset_id=r["dataset_id"],
                    url=r["url"],
                    filename=r["filename"],
                    title_uz=r.get("title_uz", ""),
                    metric_key=r.get("metric_key", ""),
                    periodicity=r.get("periodicity", ""),
                    notes=r.get("notes", ""),
                )
            )
    return rows


def quick_csv_profile(path: Path) -> Dict[str, Any]:
    # minimal profiling: rows/cols/columns
    import pandas as pd

    df = pd.read_csv(path, low_memory=False)
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": df.columns.tolist(),
    }


def write_meta(meta_path: Path, meta: Dict[str, Any]) -> None:
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def download_one(session: requests.Session, item: ManifestRow) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    out_path = RAW_DIR / item.filename
    meta_path = out_path.with_suffix(out_path.suffix + ".meta.json")

    r = session.get(item.url, timeout=(10, 120))
    status = r.status_code
    content = r.content
    digest = sha256_bytes(content)

    meta: Dict[str, Any] = {
        "dataset_id": item.dataset_id,
        "url": item.url,
        "filename": str(out_path),
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": status,
        "bytes": len(content),
        "sha256": digest,
        "title_uz": item.title_uz,
        "metric_key": item.metric_key,
        "periodicity": item.periodicity,
        "notes": item.notes,
        "http_content_type": r.headers.get("content-type"),
        "http_content_length": r.headers.get("content-length"),
    }

    if status == 200:
        out_path.write_bytes(content)
        try:
            meta.update(quick_csv_profile(out_path))
        except Exception as e:
            meta["profile_error"] = str(e)

    write_meta(meta_path, meta)

    if status != 200:
        raise RuntimeError(f"Download failed: dataset_id={item.dataset_id} status={status}")


def main() -> None:
    items = read_manifest()
    session = make_session()

    ok, fail = 0, 0
    for item in items:
        try:
            download_one(session, item)
            print(f"OK   {item.dataset_id} -> {item.filename}")
            ok += 1
        except Exception as e:
            print(f"FAIL {item.dataset_id} -> {e}")
            fail += 1

    print(f"\nDONE ok={ok} fail={fail}")
    print(f"RAW_DIR: {RAW_DIR}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Record hashes and HTTP metadata for official Phase 1 recheck pages.

Only metadata and hashes are committed.  The page bodies are streamed and are
not stored in the repository, so a later check cannot be mistaken for a raw
source archive.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/manifests/official_recheck.phase1.yml"
ALLOWED_HOSTS = {
    "nlftp.mlit.go.jp",
    "www.e-stat.go.jp",
    "www.stat.go.jp",
    "www.mlit.go.jp",
}
URLS = [
    ("n02_catalog", "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html"),
    ("s12_catalog", "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html"),
    ("l01_catalog", "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L01-2026.html"),
    ("ksj_correction_log", "https://nlftp.mlit.go.jp/ksj_error.html"),
    ("ksj_terms", "https://nlftp.mlit.go.jp/ksj/other/agreement_01.html"),
    ("econ_update_information", "https://www.e-stat.go.jp/help/data-definition-information/update-information"),
    ("estat_terms", "https://www.e-stat.go.jp/terms-of-use"),
    ("econ_definition_T001163", "https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001163.pdf"),
    ("census_definition_T001141", "https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf"),
    ("econ_result_page", "https://www.stat.go.jp/data/mesh/r3_w.html"),
    ("census_result_page", "https://www.stat.go.jp/data/mesh/r2_w.html"),
    ("l01_announcement", "https://www.mlit.go.jp/report/press/tochi_fudousan_kensetsugyo17_hh_000001_00078.html"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_metadata(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Unapproved official host: {url}")
    request = Request(url, headers={"User-Agent": "tokyo-rail-town-scale-atlas/phase1-source-audit"})
    digest = hashlib.sha256()
    byte_count = 0
    with urlopen(request, timeout=120) as response:
        final_url = response.geturl()
        final_host = urlparse(final_url).hostname
        if final_host not in ALLOWED_HOSTS:
            raise ValueError(f"Redirect escaped approved official hosts: {url} -> {final_url}")
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
            byte_count += len(block)
        headers = response.headers
        return {
            "url": url,
            "final_url": final_url,
            "status": response.status,
            "content_type": headers.get("Content-Type"),
            "content_length_header": headers.get("Content-Length"),
            "etag": headers.get("ETag"),
            "last_modified": headers.get("Last-Modified"),
            "bytes_read": byte_count,
            "sha256": digest.hexdigest(),
        }


def main() -> int:
    checked_at = utc_now()
    pages = []
    for page_id, url in URLS:
        metadata = fetch_metadata(url)
        metadata["page_id"] = page_id
        metadata["checked_at"] = checked_at
        pages.append(metadata)
        print(f"PASS {page_id} HTTP {metadata['status']} {metadata['bytes_read']} bytes")
    output = {
        "recheck_version": "0.1.0",
        "project_id": "tokyo-rail-town-scale-atlas",
        "checked_at": checked_at,
        "status": "PASS",
        "approved_hosts": sorted(ALLOWED_HOSTS),
        "pages": pages,
        "assertions": {
            "n02_release": "N02-25",
            "s12_release": "S12-25",
            "economic_census_table": "T001163",
            "population_census_table": "T001141",
            "population_census_excluded_lookalike_table": "T001192",
            "l01_correction_date_floor": "2026-04-24",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(output, handle, allow_unicode=True, sort_keys=False)
    print(f"WROTE {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

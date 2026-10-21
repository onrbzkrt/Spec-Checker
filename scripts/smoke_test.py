"""Check that the app can reach the site, read the libraries and download a spec PDF.

Usage:  python -m scripts.smoke_test
"""
from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader

from spec_checker.config import Settings
from spec_checker.graph import GraphClient


def main() -> None:
    settings = Settings.from_env()
    graph = GraphClient(settings.tenant_id, settings.client_id, settings.client_secret)

    site = graph.get_site(settings.site_host, settings.site_path)
    print(f"[1/4] Connected to site: {site['displayName']}")

    drives = list(graph.get_all(f"/sites/{site['id']}/drives"))
    print(f"[2/4] Document libraries: {', '.join(d['name'] for d in drives)}")

    specs = graph.get_drive(site["id"], settings.specs_library)
    files = graph.list_files(specs["id"])
    print(f"[3/4] {len(files)} file(s) in '{settings.specs_library}':")
    for f in files:
        print(f"      - {f['name']}  ({f['size']:,} bytes)")

    if not files:
        print("No files to download. Upload a spec PDF first.")
        return

    first = files[0]
    data = graph.download(specs["id"], first["id"])
    out_dir = Path("downloads")
    out_dir.mkdir(exist_ok=True)
    (out_dir / first["name"]).write_bytes(data)

    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    print(f"[4/4] Downloaded {first['name']} ({len(data):,} bytes). First lines:")
    for line in text.strip().splitlines()[:8]:
        print(f"      {line}")


if __name__ == "__main__":
    main()

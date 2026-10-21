"""Validate spec PDFs in the 'Part Specs' library and write results to the 'Part Register' list.

Usage:
  python -m scripts.validate                      (all PDFs)
  python -m scripts.validate --file INT-DR-2003   (files whose name contains the text)
  python -m scripts.validate --dry-run            (do not write to SharePoint)
"""
from __future__ import annotations

import argparse

from spec_checker.config import Settings, llm_settings
from spec_checker.extract import ClaudeExtractor
from spec_checker.graph import GraphClient
from spec_checker.pipeline import SpecPipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="only process files whose name contains this text")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the Part Register")
    args = parser.parse_args()

    settings = Settings.from_env()
    llm = llm_settings()
    graph = GraphClient(settings.tenant_id, settings.client_id, settings.client_secret)
    pipeline = SpecPipeline(settings, graph, ClaudeExtractor(llm.api_key, llm.model, llm.workspace_id))

    files = pipeline.files()
    if args.file:
        files = [f for f in files if args.file.lower() in f["name"].lower()]
    if not files:
        print("No matching PDF files found.")
        return

    print(f"Validating {len(files)} file(s) with {llm.model}\n")
    for f in files:
        out = pipeline.process(f, dry_run=args.dry_run)
        issues = ", ".join(out.result.issue_names()) or "-"
        print(f"{out.spec.part_number or f['name']:<14} {out.result.status:<8} {issues:<28} [{out.action}]")
        for check in out.result.issues:
            print(f"    {check.name}: {check.message}")


if __name__ == "__main__":
    main()

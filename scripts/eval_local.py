"""Offline evaluation: run extraction + validation on local PDFs and compare with the answer key.

No SharePoint needed, only ANTHROPIC_API_KEY.

Usage:
  python -m scripts.eval_local --pdf-dir ../spec-checker-data/specs --answer-key ../spec-checker-data/answer_key.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from spec_checker.config import llm_settings
from spec_checker.extract import ClaudeExtractor
from spec_checker.rules import validate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--answer-key", required=True, type=Path)
    args = parser.parse_args()

    llm = llm_settings()
    extractor = ClaudeExtractor(llm.api_key, llm.model, llm.workspace_id)
    with args.answer_key.open() as fh:
        key = {row["file"]: row for row in csv.DictReader(fh)}

    correct = 0
    print(f"Model: {llm.model}\n")
    print(f"{'part':<13} {'expected':<9} {'got':<9} {'expected checks':<24} {'got checks':<24} ok")
    for name, row in sorted(key.items()):
        spec = extractor.extract_pdf((args.pdf_dir / name).read_bytes())
        result = validate(spec)
        expected_checks = sorted(c for c in row["failed_checks"].split("; ") if c and c != "-")
        got_checks = sorted(result.issue_names())
        ok = result.status == row["expected_result"] and got_checks == expected_checks
        correct += ok
        print(f"{row['part_number']:<13} {row['expected_result']:<9} {result.status:<9} "
              f"{','.join(expected_checks) or '-':<24} {','.join(got_checks) or '-':<24} "
              f"{'OK' if ok else 'MISMATCH'}")
    print(f"\nAccuracy: {correct}/{len(key)}")


if __name__ == "__main__":
    main()

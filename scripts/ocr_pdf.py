#!/usr/bin/env python3
"""Create a searchable PDF from a scanned PDF using Tesseract OCR."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--language", default="ara")
    parser.add_argument("--tessdata-dir", type=Path)
    args = parser.parse_args()

    source = pymupdf.open(args.input)
    result = pymupdf.open()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="borderline-ocr-") as temp_dir:
        temp = Path(temp_dir)
        for page_number, page in enumerate(source, 1):
            image_path = temp / f"page-{page_number:04d}.png"
            output_base = temp / f"page-{page_number:04d}"
            page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), alpha=False).save(image_path)
            command = [
                "tesseract", str(image_path), str(output_base),
                "-l", args.language, "--psm", "6",
            ]
            if args.tessdata_dir:
                command.extend(["--tessdata-dir", str(args.tessdata_dir)])
            command.append("pdf")
            subprocess.run(command, check=True, capture_output=True, text=True)
            ocr_page = pymupdf.open(output_base.with_suffix(".pdf"))
            result.insert_pdf(ocr_page)
            ocr_page.close()
            print(f"OCR page {page_number}/{len(source)}")

    result.save(args.output, garbage=4, deflate=True)
    result.close()
    source.close()
    print(f"Wrote searchable PDF: {args.output}")


if __name__ == "__main__":
    main()

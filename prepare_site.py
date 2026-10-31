#!/usr/bin/env python3
"""Extract the official PdfCraft web release into a GitHub Pages site."""

import stat
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def prepare(archive_path: Path, destination: Path) -> None:
    with ZipFile(archive_path) as archive:
        entries = archive.infolist()
        indexes = [PurePosixPath(info.filename) for info in entries if info.filename.endswith("index.html")]
        if len(indexes) != 1:
            raise ValueError(f"Expected exactly one index.html in release; found {len(indexes)}")
        root = indexes[0].parent
        destination.mkdir(parents=True, exist_ok=True)

        for info in entries:
            source = PurePosixPath(info.filename)
            if source.is_absolute() or ".." in source.parts:
                raise ValueError(f"Unsafe path in release archive: {info.filename}")
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError(f"Unexpected symlink in release archive: {info.filename}")
            if not source.is_relative_to(root):
                continue
            relative = source.relative_to(root)
            if not relative.parts:
                continue
            target = destination.joinpath(*relative.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as stream, target.open("wb") as output:
                    while chunk := stream.read(1024 * 1024):
                        output.write(chunk)

    if not (destination / "index.html").is_file():
        raise ValueError("index.html is missing from the extracted release")
    if not list(destination.rglob("*.wasm")) or not list(destination.rglob("*.js")):
        raise ValueError("The release did not contain the expected .wasm and .js files")
    # GitHub Pages serves the files as uploaded; no Jekyll processing is needed.
    (destination / ".nojekyll").touch()
    print(f"PdfCraft static site prepared in {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: prepare_site.py release.zip output_folder")
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))

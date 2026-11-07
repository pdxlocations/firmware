#!/usr/bin/env python3
"""Package per-board firmware archives and the MeshOregon flasher catalog."""

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_board(build_dir, output, board, platform, commit):
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in build_dir.iterdir() if p.is_file() and
                   (p.name.startswith(("firmware-", "littlefs-", "mt-", "bleota")) and
                    p.suffix in (".bin", ".uf2", ".hex", ".zip", ".json")))
    binaries = [p for p in files if p.suffix != ".json"]
    if not binaries:
        raise ValueError(f"No firmware binaries for {board}")
    factory = next((p.name for p in binaries if p.name.endswith(".factory.bin")), None)
    uf2 = next((p.name for p in binaries if p.suffix == ".uf2" and ".factory." not in p.name), None)
    manifest_path = next((p for p in files if p.name.endswith(".mt.json")), None)
    manifest = json.loads(manifest_path.read_text()) if manifest_path else {}
    partitions = {part["name"]: part for part in manifest.get("part", [])}
    ota = partitions.get("app1")
    for path in list(binaries):
        if path.name.startswith(("mt-", "bleota")) and (not ota or path.stat().st_size > int(str(ota["size"]), 0)):
            print(f"Omitting companion OTA image unsupported by {board}: {path.name}")
            files.remove(path)
            binaries.remove(path)
    flash = [{"name": factory, "address": 0}] if factory else []
    if factory:
        for binary in binaries:
            part = "spiffs" if binary.name.startswith("littlefs-") else "app1" if binary.name.startswith(("mt-", "bleota")) else None
            if part:
                partition = partitions.get(part)
                if not partition or binary.stat().st_size > int(str(partition["size"]), 0):
                    raise ValueError(f"Missing or undersized {part} partition for {board}")
                flash.append({"name": binary.name, "address": int(str(partition["offset"]), 0)})
        flash.sort(key=lambda image: image["address"])
        sizes = {p.name: p.stat().st_size for p in binaries}
        for previous, current in zip(flash, flash[1:]):
            if previous["address"] + sizes[previous["name"]] > current["address"]:
                raise ValueError(f"Overlapping flash images for {board}")
    archive = output / f"meshoregon-{board}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.name)
    record = {
        "board": board, "platform": platform, "commit": commit,
        "archive": {"name": archive.name, "sha256": digest(archive), "size": archive.stat().st_size},
        "factory": factory, "uf2": uf2, "flash": flash,
        "displayName": manifest.get("displayName", board),
        "files": [{"name": p.name, "sha256": digest(p), "size": p.stat().st_size} for p in binaries],
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def catalog(artifacts, output, expected, commit, version):
    records = [json.loads(p.read_text()) for p in sorted(artifacts.glob("*/record.json"))]
    actual = {r["board"] for r in records}
    wanted = {r["board"] for r in json.loads(expected.read_text())}
    if actual != wanted or len(actual) != len(records):
        raise ValueError(f"Build coverage mismatch: missing={wanted - actual}, unexpected={actual - wanted}")
    if any(r["commit"] != commit for r in records):
        raise ValueError("Firmware was built from inconsistent commits")
    output.mkdir(parents=True, exist_ok=True)
    for record in records:
        source = artifacts / f"meshoregon-{record['board']}" / record["archive"]["name"]
        if digest(source) != record["archive"]["sha256"]:
            raise ValueError(f"Archive checksum mismatch: {source}")
        shutil.copy2(source, output / source.name)
    result = {"schema": 1, "branch": "MeshOregon", "commit": commit, "version": version,
              "generatedAt": datetime.now(timezone.utc).isoformat(), "targets": records}
    (output / "meshoregon.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    board = commands.add_parser("board")
    for name in ("board", "platform", "commit"):
        board.add_argument(f"--{name}", required=True)
    board.add_argument("--build-dir", type=Path, required=True)
    board.add_argument("--output", type=Path, required=True)
    release = commands.add_parser("catalog")
    for name in ("artifacts", "output", "expected"):
        release.add_argument(f"--{name}", type=Path, required=True)
    for name in ("commit", "version"):
        release.add_argument(f"--{name}", required=True)
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "board":
        package_board(**args)
    else:
        catalog(**args)


if __name__ == "__main__":
    main()

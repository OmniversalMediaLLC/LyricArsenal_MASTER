#!/usr/bin/env python3
import os
import argparse
from pathlib import Path

def list_tracks(base):
    """
    Returns a dictionary of track_name → folder_path
    A track folder is considered valid if it contains a `data/lyrics.md`.
    """
    tracks = {}
    if not base.exists():
        return tracks

    for item in sorted(base.iterdir()):
        if not item.is_dir():
            continue

        data_file = item / "data" / "lyrics.md"
        if data_file.exists():
            tracks[item.name] = item
    return tracks


def load_import_tracks(import_root):
    """
    Imports have .ipynb/.md pairs. Extract track base without extensions.
    Example: "01_soft_disclosure.ipynb" → "01_soft_disclosure"
    """
    tracks = set()
    if not import_root.exists():
        return tracks

    for f in import_root.iterdir():
        if f.suffix in [".ipynb", ".md"]:
            name = f.stem
            # remove checkpoint suffixes
            name = name.replace("-checkpoint", "")
            tracks.add(name)

    return tracks


def list_pullbucket_tracks(pb_base):
    """
    Returns a set of track base names from pull-bucket files.
    """
    tracks = set()
    if not pb_base.exists():
        return tracks

    for f in pb_base.iterdir():
        if f.suffix in [".json", ".md"]:
            name = f.stem
            name = name.replace("-checkpoint", "")
            tracks.add(name)

    return tracks


def diff(import_set, workspace_dict, pullbucket_set):
    report = []
    work_set = set(workspace_dict.keys())

    # Missing in workspace
    missing_ws = import_set - work_set
    if missing_ws:
        report.append("❌ Missing in WORKSPACE:")
        for t in sorted(missing_ws):
            report.append(f"   - {t}")
        report.append("")

    # Missing in pull-bucket
    missing_pb = import_set - pullbucket_set
    if missing_pb:
        report.append("❌ Missing in PULL-BUCKET:")
        for t in sorted(missing_pb):
            report.append(f"   - {t}")
        report.append("")

    # Extra/unexpected workspace tracks
    extra_ws = work_set - import_set
    if extra_ws:
        report.append("⚠️ Extra tracks in WORKSPACE (not in imports):")
        for t in sorted(extra_ws):
            report.append(f"   - {t}")
        report.append("")

    # Extra/unexpected pull-bucket tracks
    extra_pb = pullbucket_set - import_set
    if extra_pb:
        report.append("⚠️ Extra tracks in PULL-BUCKET (not in imports):")
        for t in sorted(extra_pb):
            report.append(f"   - {t}")
        report.append("")

    # Per-track file check
    for t in sorted(import_set):
        if t in workspace_dict:
            ws = workspace_dict[t]
            lyr = ws / "data" / "lyrics.md"
            meta = ws / "data" / "metadata.json"
            ipynb = ws / f"{t}.ipynb"

            if not lyr.exists() or not meta.exists() or not ipynb.exists():
                report.append(f"⚠️ Incomplete WORKSPACE for {t}:")
                if not lyr.exists(): report.append("   - missing lyrics.md")
                if not meta.exists(): report.append("   - missing metadata.json")
                if not ipynb.exists(): report.append(f"   - missing {t}.ipynb")
                report.append("")

    if not report:
        report = ["✅ No differences found — album is clean.\n"]

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", required=True)
    parser.add_argument("--album", required=True)
    args = parser.parse_args()

    ROOT = Path.cwd()

    import_root = ROOT / "_imports" / args.sku / args.album
    workspace_root = ROOT / args.sku / "_workspace" / args.album
    pullbucket_root = ROOT / args.sku / "_pull-bucket" / args.album

    print(f"[IMPORT ROOT] {import_root}")
    print(f"[WORKSPACE]   {workspace_root}")
    print(f"[PULL-BUCKET] {pullbucket_root}\n\n")

    import_tracks = load_import_tracks(import_root)
    workspace_tracks = list_tracks(workspace_root)
    pullbucket_tracks = list_pullbucket_tracks(pullbucket_root)

    print(diff(import_tracks, workspace_tracks, pullbucket_tracks))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Builds workspace and pull-bucket track structures from the import folders."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List

TRACK_FILE_RE = re.compile(r"^(\d{2})[_-](.+)\.md$", re.IGNORECASE)

ALBUM_SPECS: List[Dict[str, str]] = [
    {
        "sku": "HAWK-ARS-01",
        "album_code": "01_Singles",
        "import_dir": "_imports/HAWK-ARS-00/01_singles",
        "workspace_album": "01_Singles",
        "pull_album": "01_Singles",
    },
    {
        "sku": "HAWK-ARS-02",
        "album_code": "01_Full_Disclosure",
        "import_dir": "_imports/HAWK-ARS-00/02_mixtape_sessions/01_full_disclosure",
        "workspace_album": "01_Full_Disclosure",
        "pull_album": "01_Full_Disclosure",
    },
    {
        "sku": "HAWK-ARS-02",
        "album_code": "02_Behold_A_Pale_Horse",
        "import_dir": "_imports/HAWK-ARS-00/02_mixtape_sessions/02_behold_a_pale_horse",
        "workspace_album": "02_Behold_A_Pale_Horse",
        "pull_album": "02_Behold_A_Pale_Horse",
    },
    {
        "sku": "HAWK-ARS-02",
        "album_code": "03_MiLabs",
        "import_dir": "_imports/HAWK-ARS-00/02_mixtape_sessions/03_milabs",
        "workspace_album": "03_MiLabs",
        "pull_album": "03_MiLabs",
    },
    {
        "sku": "HAWK-ARS-03",
        "album_code": "01_Malicious_EP",
        "import_dir": "_imports/HAWK-ARS-00/03_phase2/04_malicious",
        "workspace_album": "01_Malicious_EP",
        "pull_album": "01_Malicious_EP",
    },
    {
        "sku": "HAWK-ARS-03",
        "album_code": "02_Shadow_Banned",
        "import_dir": "_imports/HAWK-ARS-00/03_phase2/05_shadow_banned",
        "workspace_album": "02_Shadow_Banned",
        "pull_album": "02_Shadow_Banned",
    },
    {
        "sku": "HAWK-ARS-04",
        "album_code": "01_Sun_Tzu_Secretz_To_War",
        "import_dir": "_imports/HAWK-ARS-00/04_reckoning",
        "workspace_album": "01_Sun_Tzu_Secretz_To_War",
        "pull_album": "01_Sun_Tzu_Secretz_To_War",
    },
]

SUN_TZU_NOTEBOOK = "_imports/HAWK-ARS-00/04_reckoning/Sun_Tzu.ipynb"
SUN_TZU_DEST = "HAWK-ARS-04/_workspace/01_Sun_Tzu_Secretz_To_War/Sun_Tzu.ipynb"


def canonicalize_slug(raw_slug: str) -> str:
    return raw_slug.lower().replace("_", "-")


def apply_track_template(track_dir: Path, template_root: Path) -> None:
    for template_path in sorted(template_root.rglob("*")):
        relative = template_path.relative_to(template_root)
        target_path = track_dir / relative
        if template_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            if not target_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_path, target_path)


def build_workspaces_for_album(
    spec: Dict[str, str], base_dir: Path, template_root: Path
) -> List[Dict[str, object]]:
    import_dir = base_dir / spec["import_dir"]
    workspace_album_dir = base_dir / spec["sku"] / "_workspace" / spec["workspace_album"]
    pull_album_dir = base_dir / spec["sku"] / "_pull-bucket" / spec["pull_album"]
    workspace_album_dir.mkdir(parents=True, exist_ok=True)
    pull_album_dir.mkdir(parents=True, exist_ok=True)

    tracks: List[Dict[str, object]] = []
    if not import_dir.exists():
        print(f"[WARN] Import directory not found: {import_dir}")
        return tracks

    for md_path in sorted(import_dir.rglob("*.md")):
        if "-checkpoint" in md_path.name:
            continue
        match = TRACK_FILE_RE.match(md_path.name)
        if not match:
            continue
        track_num = match.group(1)
        raw_slug = match.group(2)
        canonical_slug = canonicalize_slug(raw_slug)
        folder_name = f"{track_num}_{canonical_slug}"
        workspace_track_dir = workspace_album_dir / folder_name
        workspace_track_dir.mkdir(parents=True, exist_ok=True)
        apply_track_template(workspace_track_dir, template_root)

        lyrics_text = md_path.read_text(encoding="utf-8")
        lyrics_dest = workspace_track_dir / "data" / "lyrics.md"
        lyrics_dest.parent.mkdir(parents=True, exist_ok=True)
        lyrics_dest.write_text(lyrics_text, encoding="utf-8")

        ipynb_source = md_path.with_suffix(".ipynb")
        if ipynb_source.exists():
            ipynb_dest = workspace_track_dir / f"{track_num}_{canonical_slug}.ipynb"
            shutil.copy2(ipynb_source, ipynb_dest)

        metadata = {
            "sku": spec["sku"],
            "album": spec["workspace_album"],
            "track_number": int(track_num),
            "slug": canonical_slug,
            "raw_slug": raw_slug,
            "title": raw_slug.replace("_", " ").title(),
        }
        metadata_path = workspace_track_dir / "data" / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        tracks.append(
            {
                "track_number": track_num,
                "raw_slug": raw_slug,
                "canonical_slug": canonical_slug,
                "workspace_dir": workspace_track_dir,
                "lyrics_path": lyrics_dest,
            }
        )

    return tracks


def build_pull_bucket_for_album(
    spec: Dict[str, str], base_dir: Path, tracks: List[Dict[str, object]]
) -> None:
    pull_album_dir = base_dir / spec["sku"] / "_pull-bucket" / spec["pull_album"]
    pull_album_dir.mkdir(parents=True, exist_ok=True)

    for track in tracks:
        track_num = str(track["track_number"])
        canonical_slug = str(track["canonical_slug"])
        file_root = f"{track_num}_{canonical_slug}"
        lyrics_text = Path(track["lyrics_path"]).read_text(encoding="utf-8")

        pull_md_path = pull_album_dir / f"{file_root}.md"
        pull_md_path.write_text(lyrics_text, encoding="utf-8")

        metadata = {
            "sku": spec["sku"],
            "album": spec["workspace_album"],
            "album_code": spec["album_code"],
            "track_number": int(track_num),
            "slug": canonical_slug,
            "raw_slug": track["raw_slug"],
            "title": str(track["raw_slug"]).replace("_", " ").title(),
            "source_import": str(base_dir / spec["import_dir"]),
            "workspace_track_dir": str(track["workspace_dir"]),
        }
        pull_json_path = pull_album_dir / f"{file_root}.json"
        pull_json_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        print(f"[TRACK] {file_root} → created workspace + pull-bucket")


def copy_sun_tzu_notebook(base_dir: Path) -> None:
    source = base_dir / SUN_TZU_NOTEBOOK
    destination = base_dir / SUN_TZU_DEST
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        print(f"[WARN] Sun Tzu notebook not found at {source}")
        return
    shutil.copy2(source, destination)
    print(f"[SPECIAL] Copied Sun_Tzu.ipynb to {destination}")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    template_root = base_dir / "_templates" / "track"

    for spec in ALBUM_SPECS:
        print(f"[ALBUM] {spec['sku']} / {spec['workspace_album']}")
        tracks = build_workspaces_for_album(spec, base_dir, template_root)
        build_pull_bucket_for_album(spec, base_dir, tracks)

    copy_sun_tzu_notebook(base_dir)


if __name__ == "__main__":
    main()

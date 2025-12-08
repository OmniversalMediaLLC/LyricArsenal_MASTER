#!/usr/bin/env python3
import argparse
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent.parent
IMPORT_ROOT = BASE / "_imports" / "HAWK-ARS-00"

ALBUMS = [
    {
        "name": "Singles",
        "sku": "HAWK-ARS-01",
        "ws_album": "01_Singles",
        "import_subdir": "01_singles",
    },
    {
        "name": "Full Disclosure",
        "sku": "HAWK-ARS-02",
        "ws_album": "01_Full_Disclosure",
        "import_subdir": "02_mixtape_sessions/01_full_disclosure",
    },
    {
        "name": "Behold A Pale Horse",
        "sku": "HAWK-ARS-02",
        "ws_album": "02_Behold_A_Pale_Horse",
        "import_subdir": "02_mixtape_sessions/02_behold_a_pale_horse",
    },
    {
        "name": "MiLabs",
        "sku": "HAWK-ARS-02",
        "ws_album": "03_MiLabs",
        "import_subdir": "02_mixtape_sessions/03_milabs",
    },
    {
        "name": "Malicious EP",
        "sku": "HAWK-ARS-03",
        "ws_album": "01_Malicious_EP",
        "import_subdir": "03_phase2/04_malicious",
    },
    {
        "name": "Shadow Banned",
        "sku": "HAWK-ARS-03",
        "ws_album": "02_Shadow_Banned",
        "import_subdir": "03_phase2/05_shadow_banned",
    },
]

def choose_import_md(import_dir: Path, track_folder_name: str) -> Path | None:
    """
    Given a workspace track folder name like '05_return-of-kings',
    pick the best matching *.md file in import_dir (e.g. '05_return_of_kings.md').
    """
    # grab leading track number (e.g. '05')
    prefix = track_folder_name.split("_", 1)[0]
    candidates = sorted(import_dir.glob(f"{prefix}_*.md"))
    if not candidates:
        # fallback: maybe name is like '01swordfish' (no underscore)
        candidates = sorted(import_dir.glob(f"{prefix}*.md"))

    if not candidates:
        return None

    # Prefer a non "_web" file if there are multiple (e.g. trafficked vs trafficked_web)
    non_web = [c for c in candidates if not c.stem.endswith("_web")]
    if non_web:
        return non_web[0]
    return candidates[0]


def sync_album(album_def: dict, dry_run: bool = False):
    sku = album_def["sku"]
    ws_album = BASE / sku / "_workspace" / album_def["ws_album"]
    pb_album = BASE / sku / "_pull-bucket" / album_def["ws_album"]
    import_dir = IMPORT_ROOT / album_def["import_subdir"]

    print(f"\n[ALBUM] {sku} :: {album_def['name']}")
    print(f"  workspace: {ws_album}")
    print(f"  imports:   {import_dir}")

    if not ws_album.exists():
        print(f"  [WARN] workspace album missing, skipping.")
        return
    if not import_dir.exists():
        print(f"  [WARN] import dir missing, skipping.")
        return

    pb_album.mkdir(parents=True, exist_ok=True)

    for track_dir in sorted(ws_album.iterdir()):
        if not track_dir.is_dir():
            continue
        name = track_dir.name
        if "checkpoint" in name:
            print(f"  [SKIP] {name} (checkpoint)")
            continue

        import_md = choose_import_md(import_dir, name)
        if import_md is None:
            print(f"  [MISS] {name} → no matching .md found in imports")
            continue

        # read lyrics
        lyrics = import_md.read_text(encoding="utf-8", errors="ignore")

        # workspace target
        data_dir = track_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        ws_lyrics = data_dir / "lyrics.md"

        # pull-bucket target
        pb_lyrics = pb_album / f"{name}.md"
        pb_meta = pb_album / f"{name}.json"

        if dry_run:
            print(f"  [DRY] {name}")
            print(f"       import → {import_md}")
            print(f"       ws     → {ws_lyrics}")
            print(f"       pb     → {pb_lyrics}, {pb_meta}")
            continue

        # write workspace lyrics
        ws_lyrics.write_text(lyrics, encoding="utf-8")
        # write pull-bucket lyrics
        pb_lyrics.write_text(lyrics, encoding="utf-8")

        meta = {
            "sku": sku,
            "album": album_def["name"],
            "album_dir": album_def["ws_album"],
            "track_folder": name,
            "source_import_md": str(import_md.relative_to(BASE)),
        }
        pb_meta.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"  [OK] {name}")
        print(f"       import → {import_md.name}")
        print(f"       ws     → {ws_lyrics.relative_to(BASE)}")
        print(f"       pb     → {pb_lyrics.relative_to(BASE)}")

def main():
    ap = argparse.ArgumentParser(description="Sync lyrics from _imports/HAWK-ARS-00 into master workspace + pull-bucket.")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    args = ap.parse_args()

    for album_def in ALBUMS:
        sync_album(album_def, dry_run=args.dry_run)

if __name__ == "__main__":
    main()

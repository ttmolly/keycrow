#!/usr/bin/env python3
import os
import subprocess
import shutil
from pathlib import Path

BASE = Path.home() / "keycrow"
SOURCES = BASE / "splash_sources"
SPLASHES = BASE / "splashes"
SETTINGS_FILE = BASE / "ui" / "settings.py"

SOURCES.mkdir(exist_ok=True)
SPLASHES.mkdir(exist_ok=True)

SUPPORTED = [".mp4", ".mov", ".avi", ".mkv", ".gif", ".png", ".jpg", ".jpeg"]

def clear():
    os.system("clear")

def list_existing():
    return sorted([d.name for d in SPLASHES.iterdir() if d.is_dir()])

def show_supported():
    print("\nSupported formats:")
    print("  Videos : .mp4  .mov  .avi  .mkv  .gif")
    print("  Images : .png  .jpg  .jpeg  (or a folder of images)")
    print()

def convert_to_frames(source_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clean old frames
    for f in output_dir.glob("*.png"):
        f.unlink()

    if source_path.is_dir():
        # Folder of images
        print("Converting image sequence...")
        files = sorted([f for f in source_path.iterdir() if f.suffix.lower() in [".png", ".jpg", ".jpeg"]])
        for i, f in enumerate(files):
            out = output_dir / f"frame_{i:03d}.png"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(f),
                "-vf", "scale=128:64:force_original_aspect_ratio=decrease,pad=128:64:(ow-iw)/2:(oh-ih)/2,format=gray",
                str(out)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Video or single image
        print("Converting with ffmpeg...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(source_path),
            "-vf", "scale=128:64:force_original_aspect_ratio=decrease,pad=128:64:(ow-iw)/2:(oh-ih)/2,format=gray",
            "-r", "10",
            str(output_dir / "frame_%03d.png")
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    count = len(list(output_dir.glob("*.png")))
    print(f"Done → {count} frames created.")
    return count > 0

def set_as_current(name: str):
    # Simple way: update settings.py
    content = f'# Simple in-memory settings\nsplash_style = "{name}"\n'
    SETTINGS_FILE.write_text(content)
    print(f"Set '{name}' as current splash.")

def add_splash():
    clear()
    print("=== Add New Splash ===")
    show_supported()

    print(f"Put your file in: {SOURCES}")
    print("Available files in splash_sources/:\n")

    files = list(SOURCES.iterdir())
    if not files:
        print("  (folder is empty)")
        input("\nPress Enter to go back...")
        return

    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")

    choice = input("\nEnter number of the file (or full path): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(files):
        source = files[int(choice) - 1]
    else:
        source = Path(choice)

    if not source.exists():
        print("File not found.")
        input("Press Enter...")
        return

    name = input("\nName for this splash (example: lips, crow, boot1): ").strip().lower()
    if not name:
        print("Name cannot be empty.")
        input("Press Enter...")
        return

    output_dir = SPLASHES / name
    if output_dir.exists():
        overwrite = input(f"'{name}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != "y":
            return

    success = convert_to_frames(source, output_dir)
    if not success:
        print("Conversion failed.")
        input("Press Enter...")
        return

    set_now = input("\nSet this as the current splash right now? (y/n): ").lower()
    if set_now == "y":
        set_as_current(name)
    else:
        print(f"'{name}' added to available splashes.")

    input("\nPress Enter to continue...")

def rename_splash():
    clear()
    print("=== Rename Splash ===")
    existing = list_existing()
    if not existing:
        print("No splashes found.")
        input("Press Enter...")
        return

    for i, name in enumerate(existing, 1):
        print(f"  {i}. {name}")

    choice = input("\nNumber to rename: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(existing)):
        return

    old_name = existing[int(choice) - 1]
    new_name = input(f"New name for '{old_name}': ").strip().lower()

    if not new_name:
        return

    old_path = SPLASHES / old_name
    new_path = SPLASHES / new_name

    if new_path.exists():
        print("That name already exists.")
        input("Press Enter...")
        return

    old_path.rename(new_path)
    print(f"Renamed '{old_name}' → '{new_name}'")
    input("Press Enter...")

def reformat_splash():
    clear()
    print("=== Re-format / Re-convert Splash ===")
    existing = list_existing()
    if not existing:
        print("No splashes found.")
        input("Press Enter...")
        return

    for i, name in enumerate(existing, 1):
        print(f"  {i}. {name}")

    choice = input("\nNumber to re-format: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(existing)):
        return

    name = existing[int(choice) - 1]
    print(f"\nLooking for original file for '{name}' in splash_sources/...")

    # Try to find a matching source file
    possible = list(SOURCES.glob(f"{name}.*")) + list(SOURCES.glob("*"))
    if not possible:
        print("No source files found. Put the original file in splash_sources/ first.")
        input("Press Enter...")
        return

    print("Available source files:")
    for i, f in enumerate(possible, 1):
        print(f"  {i}. {f.name}")

    src_choice = input("Choose source file number: ").strip()
    if not src_choice.isdigit() or not (1 <= int(src_choice) <= len(possible)):
        return

    source = possible[int(src_choice) - 1]
    output_dir = SPLASHES / name

    convert_to_frames(source, output_dir)
    input("\nPress Enter...")

def main():
    while True:
        clear()
        print("==============================")
        print("   KeyCrow Splash Manager")
        print("==============================")
        print("1. Add new splash")
        print("2. Rename existing splash")
        print("3. Re-format / re-convert a splash")
        print("4. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            add_splash()
        elif choice == "2":
            rename_splash()
        elif choice == "3":
            reformat_splash()
        elif choice == "4":
            print("Bye")
            break
        else:
            print("Invalid option")
            sleep(1)

if __name__ == "__main__":
    from time import sleep
    main()

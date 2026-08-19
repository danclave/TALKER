# models_manager.py
# view and delete downloaded local models (vosk + whisper/HF cache)

import shutil
import sys
from pathlib import Path

from languages import vosk_model_name

ROOT_DIR = Path(getattr(sys, "frozen", False) and sys.executable or __file__).resolve().parent
VOSK_DIR = ROOT_DIR / "vosk_models"
HF_HUB_DIR = Path.home() / ".cache" / "huggingface" / "hub"

VOSK_REPOS = "https://alphacephei.com/vosk/models/"
HF_INFO = "https://huggingface.co/Systran"


def _input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _dir_size_mb(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        try:
            if f.is_file():
                total += f.stat().st_size
        except OSError:
            pass
    return round(total / 1048576)


def list_vosk_models():
    """Return [(name, path, size_mb)] of downloaded vosk models."""
    if not VOSK_DIR.is_dir():
        return []
    return sorted(
        ((d.name, d, _dir_size_mb(d)) for d in VOSK_DIR.iterdir() if d.is_dir()),
        key=lambda e: e[0].lower(),
    )


def list_whisper_models():
    """Return [(name, path, size_mb)] of whisper models in the HF cache."""
    if not HF_HUB_DIR.is_dir():
        return []
    entries = []
    for d in HF_HUB_DIR.iterdir():
        if d.is_dir() and d.name.startswith("models--"):
            # models--Systran--faster-whisper-small -> faster-whisper-small (Systran)
            parts = d.name.split("--")
            friendly = f"{parts[-1]} ({parts[1]})" if len(parts) >= 3 else d.name
            entries.append((friendly, d, _dir_size_mb(d)))
    return sorted(entries, key=lambda e: e[0].lower())


def _delete(path: Path):
    try:
        shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"  [ERROR] Could not delete {path}: {e}")
        return False


def _delete_hf_model(repo_dir: Path):
    """Remove a HF cache model dir and its matching lock dir."""
    ok = _delete(repo_dir)
    lock_dir = repo_dir.parent / ".locks" / (repo_dir.name + ".lock")
    if lock_dir.is_dir():
        _delete(lock_dir)  # best effort
    return ok


def _manage_group(title, entries, delete_func):
    while True:
        print(f"\n  {title} - location: {entries[0][1].parent if entries else '-'}")
        if not entries:
            print("    (nothing downloaded)")
            return
        for i, (name, path, size) in enumerate(entries, 1):
            print(f"    {i}) {name}  ({size} MB)")
        print("    d <n> delete | Enter = back")
        cmd = _input("  > ")
        if cmd == "":
            return
        parts = cmd.split()
        if len(parts) == 2 and parts[0] == "d" and parts[1].isdigit() and 1 <= int(parts[1]) <= len(entries):
            name, path, size = entries[int(parts[1]) - 1]
            confirm = _input(f"    Delete '{name}' ({size} MB)? Type y to confirm: ")
            if confirm.lower() == "y":
                if delete_func(path):
                    print(f"    Deleted {name} ({size} MB freed).")
                    entries = [e for e in entries if e[1] != path]
        else:
            print("    Invalid command.")


def run_manager():
    print()
    print("=" * 50)
    print(" Downloaded model manager")
    print("=" * 50)
    print("Local models are cached on disk after first use. Gemini (proxy)")
    print("keeps no local models. Nothing here affects your saved settings.")

    while True:
        vosk = list_vosk_models()
        whisper = list_whisper_models()
        total = sum(e[2] for e in vosk) + sum(e[2] for e in whisper)
        print(f"\n  Vosk models: {len(vosk)} | Whisper models: {len(whisper)} | Total on disk: ~{total} MB")
        print("  1) View/manage Vosk models")
        print("  2) View/manage Whisper models (HF cache)")
        print("  0) Back")
        choice = _input("  Select: ")

        if choice == "1":
            _manage_group("Vosk models (auto-downloaded per language)", vosk, _delete)
        elif choice == "2":
            _manage_group("Whisper models (Hugging Face cache)", whisper, _delete_hf_model)
        elif choice == "0":
            return
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    run_manager()

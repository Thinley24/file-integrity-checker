import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


# creates fingerprint
def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file: #open file in binary mode
        for chunk in iter(lambda: file.read(65536), b""): #read in chunk. up to 64 KB
            digest.update(chunk)
    return digest.hexdigest()

# error handler for scan()
def raise_scan_error(error):
    raise error

# Build the snapshot
def scan(folder, baseline):
    hashes = {}
    for directory, _, filenames in os.walk(folder, onerror=raise_scan_error): #iterate through the dir tree
        for filename in filenames:
            path = Path(directory) / filename
            if path == baseline or path.is_symlink() or not path.is_file():
                continue
            hashes[path.relative_to(folder).as_posix()] = file_hash(path)
    return hashes


def save_baseline(path, hashes):
    # Write beside the destination so the finished snapshot can replace it atomically.
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                            delete=False) as file:
        temporary_path = Path(file.name)
    try:
        temporary_path.write_text(
            json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)

# compares the snapshots
def report_changes(previous, current):
    added = current.keys() - previous.keys() # set difference
    changed = {
        path for path in current.keys() & previous.keys()
        if current[path] != previous[path]
    }
    deleted = previous.keys() - current.keys()

    for label, paths in (("ADDED", added), ("CHANGED", changed), ("DELETED", deleted)):
        for path in sorted(paths):
            print(f"{label:7} {path}")

    if added or changed or deleted:
        return 1 #return 1 when changes detected
    print("No changes detected.")
    return 0 #return 0 when no changes

# The function handles init and check
def main():
    parser = argparse.ArgumentParser(description="Track file changes with SHA-256.")
    
    # init -> scans the folder. Saves the dictionary as JSON
    # check -> loades the saved snapshot, scans the folder again, pass dictionaries to report_changes()
    parser.add_argument("action", choices=("init", "check"))
    parser.add_argument("folder", type=Path, help="Folder to scan recursively")
    parser.add_argument("baseline", type=Path, help="Path to the JSON baseline")
    args = parser.parse_args()

    try:
        folder = args.folder.resolve()
        baseline = args.baseline.resolve()
        if not folder.is_dir():
            raise ValueError(f"Folder does not exist: {folder}")

        if args.action == "init":
            hashes = scan(folder, baseline)
            save_baseline(baseline, hashes)
            print(f"Saved baseline for {len(hashes)} file(s).")
            return 0

        previous = json.loads(baseline.read_text(encoding="utf-8"))
        if not isinstance(previous, dict) or any(
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            for digest in previous.values()
        ):
            raise ValueError("Invalid baseline. Expected a JSON object of SHA-256 hashes.")
        return report_changes(previous, scan(folder, baseline))
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n") #return 2 when err encountered


if __name__ == "__main__":
    raise SystemExit(main()) # pass the result to terminal

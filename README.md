# File Integrity Checker

A small Python command-line tool that detects added, changed, and deleted files. It saves a baseline, a JSON snapshot of relative file paths and their SHA-256 hashes. On each check it hashes the files again and compares the results with the snapshot.

## Its purpose

The cybersecurity purpose is to spot unexpected changes. Imagine you have a server config you’ve reviewed and trust. You run `init` to record its fingerprint. A week later, you run `check` and see `CHANGED config.txt`, even though you didn’t edit it. That gives you a specific file to investigate.

## Run the demo

Use Python 3.9 or newer. From the project directory, run these commands in a macOS or Linux terminal. The demo works on a temporary copy of the sample files.

```sh
demo_dir=$(mktemp -d)
cp -R sample-files "$demo_dir/files"
python3 integrity.py init "$demo_dir/files" "$demo_dir/baseline.json"
python3 integrity.py check "$demo_dir/files" "$demo_dir/baseline.json"

printf 'mode=updated\n' > "$demo_dir/files/config.txt"
rm "$demo_dir/files/notes.txt"
printf 'A new file\n' > "$demo_dir/files/new.txt"

python3 integrity.py check "$demo_dir/files" "$demo_dir/baseline.json"
```

Expected output:

```text
Saved baseline for 3 file(s).
No changes detected.
ADDED   new.txt
CHANGED config.txt
DELETED notes.txt
```

**NOTE:** _Run these in the same Terminal window to see what the checker actually scanned_

```
echo "$demo_dir"
ls "$demo_dir/files"
cat "$demo_dir/files/config.txt"
```

## How it works

- `init` creates or replaces a baseline. Run it when you trust the current contents of the folder.
- `check` reads the baseline and reports differences. Its exit code is **0** for no changes, **1** for changes, or **2** for an error.
- The checker scans regular files in subfolders, skips symbolic links, and excludes the baseline itself.
- Hashes reflect file contents. A rename appears as a deletion and an addition.
- Keep the baseline somewhere you trust. Someone who can edit both a file and the baseline can hide a change from the checker.

## Its purpose

The cybersecurity purpose is to spot unexpected changes. Imagine you have a server config you’ve reviewed and trust. You run `init` to record its fingerprint. A week later, you run `check` and see `changed config.txt`, even though you didn’t edit it. That gives you a specific file to investigate.

In this demo, you made the changes on purpose to prove the checker would catch them. In real use, the same output would prompt you to check whether the changes were expected.

#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 || ! -d "$1" ]]; then
  echo "Usage: $0 <backup-directory>" >&2
  exit 2
fi
backup_dir="$(cd -- "$1" && pwd)"
for command_name in gpg sha256sum pg_restore python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required verification tool is missing: $command_name" >&2
    exit 2
  fi
done

(
  cd -- "$backup_dir"
  sha256sum --check SHA256SUMS
  gpg --batch --decrypt postgres.dump.gpg | pg_restore --list - >/dev/null
  gpg --batch --decrypt image-references.json.gpg | python3 -m json.tool >/dev/null
)
echo "Checksums, encrypted PostgreSQL archive, and image registry are valid."

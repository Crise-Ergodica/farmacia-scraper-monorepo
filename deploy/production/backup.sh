#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
env_file="${PRECO_BAO_ENV_FILE:-$script_dir/.env.production}"
backup_root="${BACKUP_DIR:-$HOME/preco-bao-backups}"
recipient="${BACKUP_GPG_RECIPIENT:-}"
expected_fingerprint="${BACKUP_GPG_FINGERPRINT:-}"

if [[ ! -f "$env_file" ]]; then
  echo "Missing environment file: $env_file" >&2
  exit 2
fi
if [[ -z "$recipient" || -z "$expected_fingerprint" ]] || ! command -v gpg >/dev/null 2>&1; then
  echo "Set BACKUP_GPG_RECIPIENT and BACKUP_GPG_FINGERPRINT, and install GnuPG." >&2
  exit 2
fi
key_listing="$(gpg --batch --with-colons --fingerprint "$recipient")"
if ! grep -q '^pub:' <<< "$key_listing"; then
  echo "The configured backup recipient key is not available in the local GnuPG keyring." >&2
  exit 2
fi
actual_fingerprint="$(awk -F: '$1 == "fpr" { print toupper($10); exit }' <<< "$key_listing")"
expected_fingerprint="$(tr '[:lower:]' '[:upper:]' <<< "$expected_fingerprint" | tr -d '[:space:]')"
if [[ -z "$actual_fingerprint" || "$actual_fingerprint" != "$expected_fingerprint" ]]; then
  echo "The recipient key fingerprint does not match BACKUP_GPG_FINGERPRINT." >&2
  exit 2
fi

mkdir -p -- "$backup_root"
chmod 700 -- "$backup_root"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
working_dir="$(mktemp -d "$backup_root/.preco-bao-$stamp.XXXXXX")"
final_dir="$backup_root/preco-bao-$stamp"
cleanup() {
  if [[ -d "$working_dir" ]]; then
    rm -rf -- "$working_dir"
  fi
}
trap cleanup EXIT

compose() {
  docker compose --project-directory "$script_dir" --env-file "$env_file" \
    -f "$script_dir/docker-compose.yml" "$@"
}

compose config --quiet
compose exec -T db sh -ec \
  'pg_dump -Fc --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  | gpg --batch --yes --trust-model always --recipient "$recipient" --encrypt \
    --output "$working_dir/postgres.dump.gpg"
compose exec -T api sh -ec \
  'if [ -f "$IMAGE_REFERENCE_STORE_PATH" ]; then cat "$IMAGE_REFERENCE_STORE_PATH"; else printf "%s\n" '\''{"schema":"preco-bao.image-registry","version":1,"records":[]}'\''; fi' \
  | gpg --batch --yes --trust-model always --recipient "$recipient" --encrypt \
    --output "$working_dir/image-references.json.gpg"

revision="$(git -C "$script_dir/../.." rev-parse HEAD 2>/dev/null || printf 'unknown')"
printf '{"created_at_utc":"%s","git_revision":"%s","format":"gpg-encrypted","files":["postgres.dump.gpg","image-references.json.gpg"]}\n' \
  "$stamp" "$revision" > "$working_dir/manifest.json"
(
  cd -- "$working_dir"
  sha256sum postgres.dump.gpg image-references.json.gpg manifest.json > SHA256SUMS
)
chmod 600 -- "$working_dir"/*
if [[ -e "$final_dir" ]]; then
  echo "Backup destination already exists: $final_dir" >&2
  exit 2
fi
mv -- "$working_dir" "$final_dir"
working_dir=""
trap - EXIT
printf 'Encrypted backup written to %s\n' "$final_dir"

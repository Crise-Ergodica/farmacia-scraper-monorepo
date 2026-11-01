#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
env_file="${PRECO_BAO_ENV_FILE:-$script_dir/.env.production}"
if [[ ! -f "$env_file" ]]; then
  echo "Missing environment file: $env_file" >&2
  exit 2
fi
for command_name in docker python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required preflight tool is missing: $command_name" >&2
    exit 2
  fi
done

docker compose --project-directory "$script_dir" --env-file "$env_file" \
  -f "$script_dir/docker-compose.yml" config --format json |
  python3 -c '
import json
import sys
from urllib.parse import urlsplit

config = json.load(sys.stdin)
services = config.get("services", {})
if set(services) != {"db", "api", "web", "proxy"}:
    raise SystemExit("Unexpected production service set; inspect Compose manually.")

db, api, web, proxy = (services[name] for name in ("db", "api", "web", "proxy"))
if db.get("ports") or api.get("ports"):
    raise SystemExit("Database/API host ports must remain unpublished.")
published = {str(port.get("published")) for port in proxy.get("ports", [])}
if published != {"80", "443"}:
    raise SystemExit("Only the proxy may publish ports 80 and 443.")
if set(db.get("networks", {})) != {"data"}:
    raise SystemExit("PostgreSQL must be attached only to the private data network.")
if "data" not in api.get("networks", {}):
    raise SystemExit("API must use the private database network.")
if set(web.get("networks", {})) != {"web_edge"}:
    raise SystemExit("Web must be isolated from PostgreSQL and the API network.")

environment = api.get("environment", {})
required = ("APP_ENV", "DEBUG", "DATABASE_URL", "JWT_SECRET", "BACKEND_CORS_ORIGINS")
if any(not environment.get(name) for name in required):
    raise SystemExit("Required production API configuration is missing.")
if environment["APP_ENV"] != "production" or environment["DEBUG"].casefold() != "false":
    raise SystemExit("API must run with production environment and DEBUG=false.")
secret = environment["JWT_SECRET"]
if len(secret) < 32 or len(set(secret)) < 12 or any(
    secret.casefold().startswith(prefix)
    for prefix in ("replace-", "change-me", "test-", "dev-", "local-", "example-")
):
    raise SystemExit("JWT_SECRET is weak or still contains an example value.")

for name in ("APP_DOMAIN", "API_DOMAIN"):
    domain = config["services"]["proxy"].get("environment", {}).get(name, "")
    if not domain or ".invalid" in domain.casefold():
        raise SystemExit("Replace reserved domains with domains you control.")
api_url = web.get("build", {}).get("args", {}).get("EXPO_PUBLIC_API_URL", "")
if urlsplit(api_url).scheme != "https" or ".invalid" in api_url.casefold():
    raise SystemExit("Web bundle must use a real HTTPS API URL.")
try:
    cors = json.loads(environment["BACKEND_CORS_ORIGINS"])
except json.JSONDecodeError as error:
    raise SystemExit("BACKEND_CORS_ORIGINS must be a JSON array.") from error
if not cors or any(
    urlsplit(origin).scheme != "https"
    or not urlsplit(origin).netloc
    or urlsplit(origin).path not in ("", "/")
    or urlsplit(origin).query
    or urlsplit(origin).fragment
    for origin in cors
):
    raise SystemExit("CORS must contain exact HTTPS web origins.")
print("Preflight passed. No images were built and no services were started.")
'

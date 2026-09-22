# Mellow Heeler Blueprint (Wombat Docker)

This directory contains the heeler wombat application.
It supports two runtime modes:

1. `validator`: Validate and ingest paired capture files
2. `koala`: Build a koala summary from successful JSON captures

## Purpose

The validator reads paired files from a fresh directory (typically one `.json` plus one `.raw`), validates payload structure and business rules, checks idempotency in PostgreSQL, updates scoring tables, then moves processed files to success or failure.

The koala mode reads successful JSON files and writes a compact summary artifact.

## Components

### 1) Application Entrypoint

File: `heeler_app.py`

- Builds database connectivity from environment variables.
- Configures SQLAlchemy engine health/timeouts.
- Routes execution by `stuntbox` mode (`validator` or `koala`).
- Returns explicit process exit codes for scripts/containers.

### 2) Validator Engine

File: `validator.py`

- Groups fresh-directory files by stem and processes deterministic pairs.
- Uses `JsonHelper` for file sanity checks, schema validation, and version/project policy checks.
- Rejects duplicate file names via load-log lookup.
- On success: inserts load-log + updates daily score + moves pair to success.
- On failure: moves pair to failure.

### 3) Koala Generator

File: `koala.py`

- Reads successful JSON files.
- Builds a reduced output structure for downstream consumers.
- Writes output to `KOALA_DIR` and sets ownership from `WOMBAT_UID`/`WOMBAT_GID`.

### 4) Helper Modules

Files: `../helper/json_helper.py`, `../helper/postgres.py`, `../helper/sql_table.py`

- `JsonHelper` performs schema validation and business policy validation.
- `PostGres` provides persistence helpers for load logs, geo loc, and scores.

## Runtime Configuration

Supported variables:

1. `DB_CONN`
2. `PG_CONNECT_TIMEOUT` (default `5`)
3. `PG_STATEMENT_TIMEOUT_MS` (default `5000`)
4. `FRESH_DIR` (default `/var/wombat/fresh/heeler`)
5. `SUCCESS_DIR` (default `/var/wombat/heeler/success`)
6. `FAILURE_DIR` (default `/var/wombat/failure`)
7. `KOALA_DIR` (default `/var/wombat/heeler/koala`)
8. `stuntbox` (default `validator`)
9. `WOMBAT_UID` (koala output owner, default `1000`)
10. `WOMBAT_GID` (koala output group, default `1000`)

## Local Run Pattern

```bash
cd src/wombat_docker
source venv/bin/activate
pip install -r requirements.txt

export DB_CONN="postgresql+psycopg2://heeler_client:batabat@localhost:5432/heeler"
export FRESH_DIR="/var/wombat/fresh/heeler"
export SUCCESS_DIR="/var/wombat/heeler/success"
export FAILURE_DIR="/var/wombat/failure"
export KOALA_DIR="/var/wombat/heeler/koala"
export stuntbox="validator"

python heeler_app.py
```

Run koala mode:

```bash
export stuntbox="koala"
python heeler_app.py
```

## Docker Build and Run

Build from `src/`:

```bash
docker build -f wombat_docker/Dockerfile -t wombat:latest .
```

Linux host DB gateway example:

```bash
docker run \
	-e stuntbox=validator \
	-e DB_CONN="postgresql+psycopg2://heeler_client:batabat@172.17.0.1:5432/heeler" \
	-v /var/wombat:/mnt/wombat \
	--name wombat \
	wombat:latest
```

macOS Docker Desktop host DB example:

```bash
docker run \
	-e stuntbox=validator \
	-e DB_CONN="postgresql+psycopg2://heeler_client:batabat@host.docker.internal:5432/heeler" \
	-v /var/wombat:/mnt/wombat \
	--name wombat \
	wombat:latest
```

Koala mode example:

```bash
docker run \
	-e stuntbox=koala \
	-e WOMBAT_UID=1000 \
	-e WOMBAT_GID=1000 \
	-v /var/wombat:/mnt/wombat \
	--name wombat-koala \
	wombat:latest
```

## Testing

Unit tests are in `test_validator.py` and cover successful ingest, duplicate detection, file-name mismatch, and v1 rejection.

From `src/wombat_docker`:

```bash
source venv/bin/activate
python -m pytest -q test_validator.py
```

Or use:

```bash
./pytest.sh
```

## Notes

1. Validator requires deterministic file pairs by stem (for example `abc.json` + `abc.raw`).
2. Current policy accepts heeler payloads where `version == 2` and `job.project == "heeler-v2"`.

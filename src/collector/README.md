## Heeler Collector Blueprint

This collector ingests iwlist scan output, normalizes observations, and emits timestamped JSON payload files into the fresh-ingest directory.

### Core Design

1. Uses Pydantic models for payload sections: equipment, geoLoc, job, receiver, timeStamp, and observations.
2. Uses snake_case Python model fields with aliases to preserve the existing JSON contract.
3. Generates UTC timestamps from epoch seconds.
4. Creates UUID-based output filenames to avoid collisions.
5. Writes one JSON file and one raw scan copy per execution.
6. Reads runtime configuration from YAML (config.yaml by default).

### Execution Flow

1. Load YAML config.
2. Build typed model objects from config fields.
3. Derive job metadata from receiver.task (project and mode).
4. Copy the raw scan file into freshDir as .raw.
5. Parse scan observations with parser.py.
6. Build and serialize the final payload to freshDir/<uuid>.json.

### Required Configuration Keys

1. crateName
2. freshDir
3. gpsEnable
4. scanFile
5. equipment.hostName
6. equipment.hostType
7. geoLoc.altitude
8. geoLoc.latitude
9. geoLoc.longitude
10. geoLoc.siteName
11. receiver.antenna
12. receiver.receiverId
13. receiver.task
14. receiver.type

### Testing

Run tests with:

`src/collector/pytest.sh`

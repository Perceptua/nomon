# ADR-007: OTA Update Strategy

**Status:** Accepted  
**Date:** 2026-03-08  
**Deciders:** Perceptua  

---

## Context

A device update strategy is needed for the `nomon` fleet. Each Raspberry Pi
runs two software components:

- **`nomothetic`** — this Python package (`nomothetic.service`)
- **`nomopractic`** — a Rust HAT daemon (`nomopractic.service`, Phase 5)

Two approaches were evaluated:

1. **Manual SSH updates** — connect via Tailscale VPN, `git pull`, restart service
2. **Automated OTA daemon** — device-side process polls or subscribes for updates

A Python-based OTA mechanism (`nomothetic.updater.UpdateManager`) was previously
implemented and has been removed.

AWS IoT provides two managed OTA services for when automation is needed:

1. **AWS IoT Jobs** — lightweight task dispatch over MQTT; device subscribes
   to a reserved topic, receives job documents, executes them, reports status
2. **AWS IoT Greengrass v2** — full on-device component runtime with lifecycle
   management; requires a JVM (Java 11+) on the device

## Decision

Use **manual SSH updates via Tailscale VPN** while the fleet is small. When the
fleet grows to the point where manual updates are impractical, adopt **AWS IoT
Jobs** for push-based fleet OTA.

Do **not** maintain a device-side Python OTA daemon in the `nomothetic` package.
Do **not** adopt Greengrass v2 due to its JVM memory requirements on Pi Zero-class hardware.

## Rationale

### Manual updates are sufficient for a small private fleet

For a fleet of a handful of devices managed by one person:
- SSH via Tailscale VPN is always available for admin access
- `git pull && sudo systemctl restart nomon` is a two-command update per device
- No additional process consuming RAM on Pi Zero 2W hardware (~5–10 MB saved)
- No `NOMON_UPDATE_*` environment variables to configure per device
- No manifest server to maintain

### Why the previous Python OTA daemon was removed

The previous `nomothetic.updater.UpdateManager`:
- Added ~350 lines of code + 48 tests to maintain
- Used `git fetch + reset --hard` — deploying to git working directories on
  production devices is fragile
- Could not coordinate updates across both `nomothetic` and `nomopractic`
  without a second manager instance and no atomicity guarantee
- The git-based mechanism would have been replaced entirely by the AWS IoT
  Jobs approach anyway

### Why AWS IoT Jobs when the fleet grows

- **Push-based**: the management server publishes a job — no polling delay.
  Replaces the previously planned `urllib.request` polling loop
- **Multi-repo coordination**: a single job document can specify versions for
  both `nomothetic` (Python) and `nomopractic` (Rust) simultaneously:
  ```json
  {
    "nomon_version": "0.5.0",
    "nomopractic_version": "1.2.0",
    "nomopractic_artifact_url": "s3://...",
    "nomopractic_sha256": "def456"
  }
  ```
  One job = one atomic fleet intent
- **Artifact-based delivery**: updates download pre-built artifacts from S3
  rather than running git on the device
- **Reuses existing infrastructure**: `nomothetic.telemetry` already uses
  `paho-mqtt` (ADR-005); IoT Jobs adds a second topic subscription on the
  same broker connection, pointing to AWS IoT Core with X.509 certificate auth
- **Minimal footprint**: AWS IoT Device SDK for Python adds ~5 MB; no JVM
  or heavy runtime required

### Why not Greengrass v2

- Greengrass Nucleus requires a JVM (Java 11+), consuming ~150–250 MB RAM at
  idle
- On Pi Zero 2W (512 MB total RAM), this leaves insufficient headroom for the
  camera pipeline, FastAPI, and the Rust HAT daemon simultaneously

## Consequences

- Updates are applied manually: `ssh <pi> 'git pull && sudo systemctl restart nomon'`
- The trigger to adopt AWS IoT Jobs is fleet size exceeding what one admin can
  update comfortably in a single session (threshold: ~10–20 devices)
- `nomothetic.updater` is removed from the package; `UpdateManager` is not an
  exported symbol
- REST endpoints `GET /api/system/version`, `GET /api/system/update/status`,
  and `POST /api/system/update/apply` have been removed from the API
- When IoT Jobs is adopted, a new lightweight subscriber module will be
  introduced; `nomothetic.telemetry` may consolidate its MQTT connection with
  the IoT Jobs subscription to use a single AWS IoT Core broker

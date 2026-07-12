# Surge Rule Mirrors

This directory contains local mirrors of the remote rule files used by the Surge profile.

- `sources.json` records each upstream URL and its stable mirror path.
- `sync_rules.py` downloads each source to a temporary file, validates it, and atomically replaces the mirror.
- A failed or invalid download never overwrites the last known good mirror.
- `.github/workflows/sync-surge-rules.yml` runs the sync daily and also supports manual dispatch.

The Surge profile should reference only URLs under:

`https://raw.githubusercontent.com/shaoyou11/Surge-Profiles/main/Surge/Rules/`

# Surge Rules

This directory contains local mirrors of remote rule files and repository-maintained rules used by the Surge profile.

## Repository-maintained rules

### Aidoku

`Aidoku.list` covers source-list delivery plus the site, API, and image domains referenced by these Aidoku lists:

- `Smexhy/yomu-aidoku-sources`
- `suiyuran/aidoku-zh-sources`
- `Skittyblock/aidoku-community-sources` (legacy)
- `WhisperKit/zh-sources` (legacy)

Use it before broad `Global`, `China`, `GEOIP`, and `FINAL` rules:

```ini
RULE-SET,https://raw.githubusercontent.com/shaoyou11/Surge-Profiles/main/Surge/Rules/Aidoku.list,Proxy,update-interval=86400
```

Replace `Proxy` if your profile uses a different policy-group name. Surge iOS does not support per-process matching for Aidoku, so this rule set matches network destinations instead. Source websites and mirrors may change; use the Surge request log to identify and add a newly introduced image host.

## Mirrored upstream rules

- `sources.json` records each upstream URL and its stable mirror path.
- `sync_rules.py` downloads each source to a temporary file, validates it, and atomically replaces the mirror.
- A failed or invalid download never overwrites the last known good mirror.
- `.github/workflows/sync-surge-rules.yml` runs the sync daily and also supports manual dispatch.

The Surge profile should reference only URLs under:

`https://raw.githubusercontent.com/shaoyou11/Surge-Profiles/main/Surge/Rules/`

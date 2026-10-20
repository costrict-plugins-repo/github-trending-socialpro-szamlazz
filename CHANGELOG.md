# Changelog

All notable changes to the socialpro-szamlazz plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-12

### Added
- Initial public release
- `szamlazz` skill with bilingual (Hungarian + English) auto-invoke
- Subcommands: `doctor`, `init`, `invoice`, `storno`, `proforma`, `pdf-fetch`, `xml-fetch`, `taxpayer`
- Cross-platform config resolution (macOS, Linux, Windows)
- Interactive first-run flow with NAV taxpayer auto-lookup
- Hungarian bank name detection from giro prefix (top 15 banks)
- YAML-backed partner cache with upsert-by-tax-id
- Error recovery mapping for the 7 most common szamlazz.hu error codes
- English and Hungarian README
- MIT License

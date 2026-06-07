# Changelog

## 0.3.2 - 2026-06-07

- Fix frontend recovery after upgrading from the single-knob runtime to multi-knob config entries without a full browser reload.
- Retry frontend config/subscription setup after reconnects or early-load failures.

## 0.3.0 - 2026-06-06

### Breaking

- Config entries are now per physical knob instead of singleton. Remove the old entry after upgrading and recreate one entry for each knob.

### Added

- Added multi-knob backend support using ZHA IEEE/device-based unique IDs.
- Added multi-entry websocket configuration and rotation subscriptions.
- Added per-entry frontend state so cooldowns, settings, entities, and navigation result reporting are isolated by knob.
- Added capability profiles. This release includes the `zha_rotate_type` profile for ZHA `rotate_type` events.

### Changed

- Removed the `single_config_entry` manifest flag.
- Diagnostics now include the entry capability profile.

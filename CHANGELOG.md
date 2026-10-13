# Changelog

## Unreleased

- Fixed cached entity IDs after registry renames with Home Assistant's new
  in-place entity lifecycle.
- Preserved rotation and navigation result subscriptions during entity renames.

## 0.3.10 - 2026-09-29

- Added an automatically packaged `knob_swipe_navigation.zip` to GitHub
  releases for HACS installs and updates.
- Standardized HACS and Hassfest validation workflows and README badges and
  support buttons.
- Integration behavior is unchanged.

## 0.3.9 - 2026-08-02

- Simplify HACS installation instructions now that Knob Swipe Navigation is available in the default HACS catalog.

## 0.3.8 - 2026-08-01

- Remove duplicate root-level brand assets while retaining the integration's in-tree brand files.

## 0.3.7 - 2026-06-24

- Add per-knob idle return to the first visible dashboard tab, enabled by default after 60 seconds without knob activity.
- Add `switch.idle_return_enabled` and `number.idle_return_timeout` config entities.

## 0.3.6 - 2026-06-07

- Use Home Assistant theme colors for the tab overlay palette.

## 0.3.5 - 2026-06-07

- Updated icons.

## 0.3.4 - 2026-06-07

- Updated Icons.

## 0.3.3 - 2026-06-07

- Remove the outdated 0.3.0 upgrade note from the README.
- Document the verified working ZHA rotary knob product link.

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

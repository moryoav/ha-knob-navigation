# Knob Swipe Navigation
[![HACS][hacs-badge]][hacs-url] [![release][release-badge]][release-url] ![downloads][downloads-badge] [![hassfest][hassfest-badge]][hassfest-url] [![validate][validate-badge]][validate-url] [![license][license-badge]][license-url]

Knob Swipe Navigation is a Home Assistant custom integration that lets configured ZHA rotary knobs change tabs on configured Lovelace dashboards. Each config entry maps one knob to one dashboard path with its own navigation behavior, idle return, entities, cooldown, browser targeting, and diagnostics. Setup is handled from **Settings -> Devices & services**; no dashboard YAML block or template helper is required.

This version ships with the `zha_rotate_type` capability profile:

- `rotate_type: 0` moves to the next tab.
- `rotate_type: 1` moves to the previous tab.
- Press events are ignored.

## Requirements

- Home Assistant 2026.3.0 or newer.
- Home Assistant with ZHA configured.
- A ZHA rotary knob that fires `zha_event` events with `command: rotate_type`.
- A Lovelace dashboard using storage mode or YAML mode.
- A browser displaying the configured dashboard.

Fully Kiosk Browser is not a hard requirement. The integration runs in the Home Assistant frontend and can work in any browser showing the configured dashboard. Fully Kiosk is useful for wall tablets because it provides a stable always-on browser, kiosk URL handling, screenshots, screensaver control, and device management, but the knob navigation logic itself does not require Fully.

## Supported Devices

Supported devices are ZHA rotary knob devices that emit Home Assistant `zha_event` events in this shape:

Verified working product: [AliExpress ZHA rotary knob](https://s.click.aliexpress.com/e/_c3x3XjtJ). Other ZHA rotary knobs can work if they emit the same `rotate_type` events. If you try another product and confirm it works, please send a link so it can be added here.

```json
{
  "device_id": "YOUR_ZHA_DEVICE_ID",
  "command": "rotate_type",
  "params": {
    "rotate_type": 0
  },
  "args": [0]
}
```

The important parts are `command: rotate_type` and a rotation value of `0` or `1` in either `params.rotate_type` or the first `args` item.

Unsupported devices and modes:

- Zigbee2MQTT, deCONZ, MQTT, Bluetooth, and other non-ZHA sources.
- ZHA devices that do not emit `rotate_type` rotation events.
- Press, double-press, hold, and other button actions.

## Supported Functionality

The integration provides:

- UI setup from **Settings -> Devices & services**.
- Multiple config entries, one per ZHA rotary knob.
- UI reconfiguration for each selected knob and dashboard path.
- One Home Assistant service device per configured knob.
- A frontend module that subscribes to integration-owned rotation events for all configured knobs.
- Per-knob config entities for enablement, overlay, wrap, overlay timeout, cooldown, and idle return.
- Per-knob diagnostic event/sensor entities for rotation and frontend navigation results.
- Diagnostics download with redacted config entry data, capability profile, settings, entity IDs, and selected-device metadata.
- A per-entry repair issue if a configured knob is no longer provided by ZHA.
- Optional browser targeting with a required URL query parameter per knob.

The integration does not create service actions, device triggers, or long-term statistics.

## HACS Installation

[![Open the Knob Swipe Navigation HACS repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moryoav&repository=ha-knob-navigation&category=integration)

Until this repository is accepted as a default HACS repository, add it as a custom repository:

1. Open HACS.
2. Open the three-dot menu.
3. Select **Custom repositories**.
4. Add this repository URL.
5. Select category **Integration**.
6. Install **Knob Swipe Navigation**.
7. Restart Home Assistant.

After restart, add the integration in Home Assistant:

[![Add the Knob Swipe Navigation integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=knob_swipe_navigation)

1. Go to **Settings -> Devices & services -> Add integration**.
2. Search for **Knob Swipe Navigation**.
3. Select the ZHA rotary knob device.
4. Enter the dashboard path to control, for example `lovelace` or `dashboard-home`.
5. Choose overlay, cooldown, idle return, wrap, and optional URL query targeting settings.
6. Finish setup.
7. Repeat **Add integration** for each additional knob.

## Manual Installation

Copy the integration folder into Home Assistant:

```text
config/custom_components/knob_swipe_navigation/
```

The folder must contain at least:

```text
__init__.py
config_flow.py
const.py
diagnostics.py
entity.py
event.py
helpers.py
manifest.json
models.py
number.py
quality_scale.yaml
sensor.py
strings.json
switch.py
translations/en.json
www/knob-swipe-navigation.js
brand/icon.png
brand/logo.png
```

Restart Home Assistant, then add the integration from **Settings -> Devices & services**.

## Configuration

Each entry has one selected knob and one selected dashboard path. Use the first URL segment of the dashboard:

- `/lovelace/home` -> `lovelace`
- `/dashboard-home/default_view?kiosk` -> `dashboard-home`
- A full URL such as `http://homeassistant.local:8123/kitchen/0` -> `kitchen`

All normal, visible tabs in that dashboard are affected. Subviews and hidden views are skipped.

Settings available from setup, reconfigure, and options apply to that entry only:

- **Dashboard path**: The dashboard that reacts to the knob.
- **Enable knob navigation**: Global on/off control for knob navigation.
- **Show tab overlay**: Shows the tab overlay before moving tabs.
- **Overlay display time**: Overlay visibility in milliseconds. Defaults to `2800`.
- **Rotation cooldown**: Ignores repeated rotations for this many milliseconds. Defaults to `2000` (2 seconds).
- **Wrap from last tab to first**: Allows moving from last to first tab and first to last tab.
- **Required URL query parameter**: Optional browser targeting guard.
- **Return to first tab after inactivity**: Returns the matching dashboard browser to the first visible tab when the selected knob has not been touched. Enabled by default.
- **Inactivity return delay**: Seconds to wait before returning to the first visible tab. Defaults to `60`.

## Entities

The integration creates these entities on each entry's service device:

- `switch.navigation_enabled`: Main enable/pause control.
- `switch.overlay_enabled`: Shows or hides the tab overlay.
- `switch.wrap_tabs`: Enables tab wrapping.
- `switch.idle_return_enabled`: Enables returning to the first tab after knob inactivity.
- `number.overlay_timeout`: Overlay timeout in milliseconds.
- `number.cooldown`: Rotation cooldown in milliseconds.
- `number.idle_return_timeout`: Idle return delay in seconds.
- `event.rotation`: Fires `next` or `previous` when the selected knob rotates.
- `sensor.last_rotation`: Last selected-knob rotation direction.
- `sensor.last_navigation_result`: Last frontend navigation result reported by a browser.

Entity IDs can be renamed by Home Assistant and may include suffixes when multiple knobs are configured. Use the entity registry values from your system when creating automations.

## Browser Targeting

If only one kiosk, tablet, or browser URL should react, configure **Required URL query parameter**.

For example, set the required query parameter to `kiosk`, then open the intended dashboard as:

```text
/dashboard-home/default_view?kiosk
```

Both `?kiosk` and `?kiosk=1` match. The value is not checked. This is a browser-targeting guard, not a security feature; any browser opened with the same query parameter can react.

## Reconfiguration and Removal

To select a different knob or dashboard for one entry:

1. Go to **Settings -> Devices & services**.
2. Open **Knob Swipe Navigation**.
3. Choose **Reconfigure** or **Configure**.
4. Update the ZHA knob, dashboard path, or navigation settings. The same physical knob cannot be selected by two entries.

To remove the integration:

1. Remove **Knob Swipe Navigation** from **Settings -> Devices & services**.
2. If installed with HACS, uninstall it from HACS and restart Home Assistant.
3. If installed manually, delete `config/custom_components/knob_swipe_navigation/` and restart Home Assistant.
4. Reload any browser or wall tablet that previously displayed the configured dashboard.

## Data Updates

The backend stores the selected ZHA device ID, capability profile, and navigation settings in each config entry. It listens to each selected knob's profile event stream and forwards normalized `next`/`previous` rotations to subscribed dashboard browsers through an integration-owned WebSocket subscription. Rotation handling is event-driven; the frontend uses per-entry timers only for the optional idle return.

The backend also updates `event.rotation` and `sensor.last_rotation` even when no browser navigates. Browsers report navigation results back to the backend for `sensor.last_navigation_result`.

Dashboard tab metadata is read from the currently loaded Lovelace config. If you rename tabs, change paths, change icons, change the selected dashboard path, change the selected knob, or change URL query targeting, reload the browser that is showing the dashboard. The switch and number entities are read live from Home Assistant state and do not need a browser reload.

## Diagnostics

Diagnostics can be downloaded from the integration entry in **Settings -> Devices & services**. The diagnostics include:

- Redacted config entry data and options.
- Frontend module URL.
- Capability profile and navigation settings.
- Integration entity IDs.
- Whether the selected device is configured and found.
- Selected device name, manufacturer, model, and linked config entry domains.

Diagnostics do not include tokens, passwords, coordinates, or the raw configured Home Assistant device ID.

## How It Works

The frontend module:

1. Loads in Home Assistant as a frontend JavaScript module.
2. Reads all configured ZHA knob entries, dashboard paths, capability profiles, settings, and entity IDs from the backend.
3. Subscribes to integration-owned rotation events for every configured entry.
4. Matches each rotation to the correct entry by `entry_id` and `device_id`.
5. Ignores browsers that are not displaying the matching entry's configured dashboard path.
6. Reads the real Lovelace tab names, paths, and icons from the current dashboard.
7. Shows an overlay using those real tab names and icons when enabled.
8. Moves to the next or previous tab.
9. Resets that entry's idle-return timer when the knob is touched and, when enabled, returns to the first visible tab after the configured delay.
10. Reports the navigation result back to Home Assistant.

Because tab metadata is read from the loaded Lovelace dashboard, renaming tabs or changing icons automatically updates the overlay after the dashboard is reloaded.

## Testing

After setup, rotate the knob while the configured dashboard is visible.

Expected behavior:

- Rotating right moves to the next dashboard tab.
- Rotating left moves to the previous dashboard tab.
- The overlay appears immediately and highlights the target tab when overlay is enabled.
- If idle return is enabled, the dashboard returns to the first visible tab after the configured delay without knob activity.
- Browsers outside the configured dashboard path do not react.
- Browsers missing the configured URL query parameter do not react.

You can also simulate a rotation event from **Developer Tools -> Events** by firing `zha_event` with data like:

```json
{
  "device_id": "YOUR_ZHA_DEVICE_ID",
  "command": "rotate_type",
  "params": {
    "rotate_type": 0
  },
  "args": [0]
}
```

Use `rotate_type: 1` to test previous-tab navigation.

## Troubleshooting

If the integration does not appear:

- Confirm the folder is at `config/custom_components/knob_swipe_navigation`.
- Confirm `manifest.json` exists.
- Restart Home Assistant.

If setup or startup reports that the selected knob device is unavailable:

- Confirm ZHA is loaded.
- Confirm the knob still appears under the ZHA integration.
- Reconfigure Knob Swipe Navigation and select the ZHA knob again.

If rotation does nothing:

- Confirm the integration is configured and loaded in Devices & services.
- Confirm `switch.navigation_enabled` is on.
- Confirm the selected device is the actual ZHA knob.
- Confirm the browser is showing the configured dashboard path.
- If using URL query targeting, confirm the browser URL contains that query parameter.
- Use **Developer Tools -> Events** to listen for `zha_event` and confirm the knob emits `command: rotate_type`.
- Check `event.rotation`, `sensor.last_rotation`, and `sensor.last_navigation_result`.

If multiple browsers react:

- Configure a required query parameter such as `kiosk`.
- Open only the intended browser with that query parameter.

If tab names or icons look wrong:

- Reload the dashboard browser.
- Confirm the Lovelace views have `title`, `path`, and `icon` configured.

If you need to report a problem:

- Download diagnostics from the integration entry.
- Include the simulated `zha_event` payload, with the `device_id` redacted if desired.
- Include the configured dashboard path and relevant entity states.

## Current Limitations

- ZHA only.
- Rotation only.
- Press actions are not handled.
- Each config entry supports one dashboard path; add another entry for another knob/dashboard pair.
- URL query targeting identifies browser URLs only; it does not identify a physical device.
- The integration does not update knob firmware or software; ZHA and the device manufacturer handle that.

## Quality Scale

The integration declares `quality_scale: gold` in its manifest and tracks the Home Assistant Integration Quality Scale rules in `custom_components/knob_swipe_navigation/quality_scale.yaml`.

## License

Knob Swipe Navigation is released under the [MIT License](LICENSE).

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/moryoav/ha-knob-navigation?style=flat-square
[release-url]: https://github.com/moryoav/ha-knob-navigation/releases
[downloads-badge]: https://img.shields.io/github/downloads/moryoav/ha-knob-navigation/total?style=flat-square
[hassfest-badge]: https://img.shields.io/github/actions/workflow/status/moryoav/ha-knob-navigation/hassfest.yaml?branch=main&style=flat-square&label=hassfest
[hassfest-url]: https://github.com/moryoav/ha-knob-navigation/actions/workflows/hassfest.yaml
[validate-badge]: https://img.shields.io/github/actions/workflow/status/moryoav/ha-knob-navigation/validate.yaml?branch=main&style=flat-square&label=validate
[validate-url]: https://github.com/moryoav/ha-knob-navigation/actions/workflows/validate.yaml
[license-badge]: https://img.shields.io/github/license/moryoav/ha-knob-navigation?style=flat-square
[license-url]: https://github.com/moryoav/ha-knob-navigation/blob/main/LICENSE

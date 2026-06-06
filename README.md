# Knob Swipe Navigation
[![HACS][hacs-badge]][hacs-url] [![release][release-badge]][release-url] ![downloads][downloads-badge] [![hassfest][hassfest-badge]][hassfest-url] [![validate][validate-badge]][validate-url] [![license][license-badge]][license-url]

Knob Swipe Navigation is a Home Assistant custom integration that lets a ZHA rotary knob change Lovelace dashboard tabs. It listens for `zha_event` rotation events from one configured ZHA device and performs in-browser dashboard navigation on dashboards that explicitly opt in.

This version supports ZHA rotation only:

- `rotate_type: 0` moves to the next tab.
- `rotate_type: 1` moves to the previous tab.
- Press events are ignored.

## Requirements

- Home Assistant 2026.3.0 or newer.
- Home Assistant with ZHA configured.
- A ZHA rotary knob that fires `zha_event` events with `command: rotate_type`.
- A Lovelace dashboard using storage mode or YAML mode.
- A browser displaying the dashboard.

Fully Kiosk Browser is not a hard requirement. The integration runs in the Home Assistant frontend and can work in any browser that has the enabled dashboard open. Fully Kiosk is useful for wall tablets because it provides a stable always-on browser, kiosk URL handling, screenshots, screensaver control, and device management, but the knob navigation logic itself does not require Fully.

The classic `hass-swipe-navigation` component is also not a hard requirement. This integration includes its own event listener, overlay, tab metadata lookup, and navigation fallback. If `hass-swipe-navigation` is already installed, this integration can coexist with its existing `swipe_nav` dashboard config.

## Supported Devices

Supported devices are ZHA rotary knob devices that emit Home Assistant `zha_event` events in this shape:

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
- UI reconfiguration so the selected knob can be changed without removing the integration.
- One Home Assistant service device for the navigation bridge.
- Diagnostics download with redacted config entry data and selected-device metadata.
- A repair issue if the configured knob is no longer provided by ZHA.
- A frontend module that subscribes to ZHA events and navigates enabled dashboards.
- Optional tab overlay using real Lovelace tab names and icons.
- Optional browser targeting with a required URL query parameter.
- Optional suppression while a chosen Home Assistant entity is `on`.

The integration does not create entities, service actions, device triggers, or long-term statistics.

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
4. Finish setup.

The only installation parameter is **ZHA knob device**. It must be a device already owned by the ZHA integration.

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
helpers.py
manifest.json
models.py
quality_scale.yaml
strings.json
translations/en.json
www/knob-swipe-navigation.js
brand/icon.png
brand/logo.png
```

Restart Home Assistant, then add the integration from **Settings -> Devices & services**.

## Reconfiguration and Removal

To select a different knob:

1. Go to **Settings -> Devices & services**.
2. Open **Knob Swipe Navigation**.
3. Choose **Reconfigure**.
4. Select another ZHA rotary knob device.

To remove the integration:

1. Remove `knob_swipe_navigation` or `swipe_nav.knob` blocks from every dashboard.
2. Remove **Knob Swipe Navigation** from **Settings -> Devices & services**.
3. If installed with HACS, uninstall it from HACS and restart Home Assistant.
4. If installed manually, delete `config/custom_components/knob_swipe_navigation/` and restart Home Assistant.
5. Reload any browser or wall tablet that previously displayed an enabled dashboard.

## Dashboard Setup

The frontend module loads globally, but it only reacts on dashboards that opt in.

For a new installation, use the standalone root config:

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 2800
```

If the dashboard already uses `hass-swipe-navigation`, you can instead place the knob config under the existing `swipe_nav` block:

```yaml
swipe_nav:
  wrap: true
  animate: swipe
  knob:
    enable: true
    overlay: true
    overlay_timeout: 2800
```

After saving the dashboard, reload the browser showing that dashboard.

## Browser Targeting

If you only want a specific kiosk, tablet, or browser URL to react to the knob, add a URL query requirement.

Standalone config:

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 2800
  require_query_param: kiosk
```

Then open the dashboard on the intended browser with `?kiosk` in the URL, for example:

```text
/dashboard-home/default_view?kiosk
```

`require_query_param: kiosk` means: only react if the current browser URL contains a query parameter named `kiosk`. Both `?kiosk` and `?kiosk=1` match. The value is not checked.

This is a browser-targeting guard, not a security feature. Any browser opened with the same query parameter can react.

## Configuration Parameters

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 2800
  cooldown_ms: 2000
  require_query_param: kiosk
  suppress_if_entity_on: input_boolean.pause_knob_navigation
```

- `enable`: Required. Turns knob handling on for this dashboard.
- `overlay`: Shows the tab overlay before moving tabs. Defaults to `true`.
- `overlay_timeout`: Overlay visibility in milliseconds. Defaults to `2800`.
- `cooldown_ms`: Ignores additional rotation events during this period. Defaults to `0`.
- `require_query_param`: Only react when the current browser URL contains this query parameter name.
- `suppress_if_entity_on`: Ignore knob events while the named Home Assistant entity is `on`.

## Use Cases

- Wall tablet dashboard navigation without touching the tablet.
- Kitchen, hallway, or bedside dashboards where a small rotary control is easier than swiping.
- Family dashboards where tab names and icons should appear briefly before navigation.
- Migration from an old knob automation while keeping a suppression guard available.
- Shared dashboards where only a kiosk URL should react to the knob.

## Examples

Dashboard with a short overlay and a kiosk-only URL:

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 1800
  require_query_param: kiosk
```

Dashboard that pauses knob navigation while a helper is on:

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  suppress_if_entity_on: input_boolean.pause_knob_navigation
```

Example helper and automations for pausing navigation while a tablet screen is off:

```yaml
input_boolean:
  pause_knob_navigation:
    name: Pause knob navigation

automation:
  - alias: Pause knob navigation while tablet screen is off
    triggers:
      - trigger: state
        entity_id: binary_sensor.wall_tablet_screen
        to: "off"
    actions:
      - action: input_boolean.turn_on
        target:
          entity_id: input_boolean.pause_knob_navigation

  - alias: Resume knob navigation while tablet screen is on
    triggers:
      - trigger: state
        entity_id: binary_sensor.wall_tablet_screen
        to: "on"
    actions:
      - action: input_boolean.turn_off
        target:
          entity_id: input_boolean.pause_knob_navigation
```

## Data Updates

The backend stores the selected ZHA device id in the config entry. That value changes only when the integration is set up, migrated, or reconfigured.

The frontend receives the selected device id through a Home Assistant WebSocket command, then subscribes to `zha_event`. Rotation handling is event-driven; there is no polling interval.

Dashboard tab metadata is read from the currently loaded Lovelace config. If you rename tabs, change paths, change icons, or change the dashboard knob config, reload the browser that is showing the dashboard.

## Diagnostics

Diagnostics can be downloaded from the integration entry in **Settings -> Devices & services**. The diagnostics include:

- Redacted config entry data and options.
- Frontend module URL.
- Whether the selected device is configured and found.
- Selected device name, manufacturer, model, and linked config entry domains.

Diagnostics do not include tokens, passwords, coordinates, or the raw configured Home Assistant device id.

## How It Works

The backend integration stores the selected ZHA device id and exposes it to the frontend through a Home Assistant WebSocket command.

The frontend module:

1. Loads in Home Assistant as a frontend JavaScript module.
2. Reads the configured ZHA knob device id from the backend.
3. Subscribes to `zha_event`.
4. Ignores events from every other device.
5. Checks whether the current dashboard has `knob_swipe_navigation.enable: true` or `swipe_nav.knob.enable: true`.
6. Reads the real Lovelace tab names, paths, and icons from the current dashboard.
7. Shows an overlay using those real tab names and icons.
8. Moves to the next or previous tab.

Because tab metadata is read from the loaded Lovelace dashboard, renaming tabs or changing icons automatically updates the overlay after the dashboard is reloaded.

## Testing

After setup, rotate the knob while the enabled dashboard is visible.

Expected behavior:

- Rotating right moves to the next dashboard tab.
- Rotating left moves to the previous dashboard tab.
- The overlay appears immediately and highlights the target tab.
- Browsers that do not match the dashboard opt-in or query requirement do not react.

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
- Confirm the selected device is the actual ZHA knob.
- Confirm the dashboard has `knob_swipe_navigation.enable: true` or `swipe_nav.knob.enable: true`.
- If using `require_query_param`, confirm the browser URL contains that query parameter.
- Confirm any entity listed in `suppress_if_entity_on` is not `on`.
- Use **Developer Tools -> Events** to listen for `zha_event` and confirm the knob emits `command: rotate_type`.

If multiple browsers react:

- Add `require_query_param: kiosk` or another unique query parameter.
- Open only the intended browser with that query parameter.

If tab names or icons look wrong:

- Reload the dashboard browser.
- Confirm the Lovelace views have `title`, `path`, and `icon` configured.

If you need to report a problem:

- Download diagnostics from the integration entry.
- Include the simulated `zha_event` payload, with the `device_id` redacted if desired.
- Include the dashboard knob config block.

## Current Limitations

- ZHA only.
- Rotation only.
- Press actions are not handled.
- The configured knob is global, while dashboard activation is per dashboard.
- `require_query_param` targets browsers by URL only; it does not identify a physical device.
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

# Knob Swipe Navigation

Knob Swipe Navigation is a Home Assistant custom integration that lets a ZHA rotary knob change Lovelace dashboard tabs. It listens for `zha_event` rotation events from one configured ZHA device and performs in-browser dashboard navigation on dashboards that explicitly opt in.

This version supports ZHA rotation only:

- `rotate_type: 0` moves to the next tab.
- `rotate_type: 1` moves to the previous tab.
- Press events are ignored.

## Requirements

- Home Assistant 2026.3.0 or newer.
- Home Assistant with ZHA.
- A ZHA rotary knob that fires `zha_event` events with `command: rotate_type`.
- A Lovelace dashboard using storage mode or YAML mode.
- A browser displaying the dashboard.

Fully Kiosk Browser is not a hard requirement. The integration runs in the Home Assistant frontend and can work in any browser that has the enabled dashboard open. Fully Kiosk is useful for wall tablets because it provides a stable always-on browser, kiosk URL handling, screenshots, screensaver control, and device management, but the knob navigation logic itself does not require Fully.

The classic `hass-swipe-navigation` component is also not a hard requirement. This integration includes its own event listener, overlay, tab metadata lookup, and navigation fallback. If `hass-swipe-navigation` is already installed, this integration can coexist with its existing `swipe_nav` dashboard config.

## HACS Installation

Until this repository is accepted as a default HACS repository, add it as a custom repository:

1. Open HACS.
2. Open the three-dot menu.
3. Select **Custom repositories**.
4. Add this repository URL.
5. Select category **Integration**.
6. Install **Knob Swipe Navigation**.
7. Restart Home Assistant.

After restart, add the integration in Home Assistant:

1. Go to **Settings -> Devices & services -> Add integration**.
2. Search for **Knob Swipe Navigation**.
3. Select the ZHA rotary knob device.
4. Finish setup.

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
manifest.json
translations/en.json
www/knob-swipe-navigation.js
brand/icon.png
brand/logo.png
```

Restart Home Assistant, then add the integration from **Settings -> Devices & services**.

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

If you only want a specific kiosk/tablet/browser URL to react to the knob, add a URL query requirement.

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

## Optional Settings

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 2800
  cooldown_ms: 2000
  require_query_param: kiosk
  suppress_if_entity_on: automation.example_old_knob_automation
```

- `enable`: Required. Turns knob handling on for this dashboard.
- `overlay`: Shows the tab overlay before moving tabs. Defaults to `true`.
- `overlay_timeout`: Overlay visibility in milliseconds. Defaults to `2800`.
- `cooldown_ms`: Ignores additional rotation events during this period. Defaults to `0`.
- `require_query_param`: Only react when the current browser URL contains this query parameter name.
- `suppress_if_entity_on`: Ignore knob events while the named Home Assistant entity is `on`. This is useful during migration from an old automation.

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

If rotation does nothing:

- Confirm the integration is configured and loaded in Devices & services.
- Confirm the selected device is the actual ZHA knob.
- Confirm the dashboard has `knob_swipe_navigation.enable: true` or `swipe_nav.knob.enable: true`.
- If using `require_query_param`, confirm the browser URL contains that query parameter.
- Confirm any entity listed in `suppress_if_entity_on` is not `on`.

If multiple browsers react:

- Add `require_query_param: kiosk` or another unique query parameter.
- Open only the intended browser with that query parameter.

If tab names or icons look wrong:

- Reload the dashboard browser.
- Confirm the Lovelace views have `title`, `path`, and `icon` configured.

## Current Limitations

- ZHA only.
- Rotation only.
- Press actions are not handled.
- The configured knob is global, while dashboard activation is per dashboard.
- `require_query_param` targets browsers by URL only; it does not identify a physical device.

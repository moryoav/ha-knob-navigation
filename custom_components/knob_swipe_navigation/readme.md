# Knob Swipe Navigation

Knob Swipe Navigation lets one configured ZHA rotary knob change tabs on one configured Lovelace dashboard. The ZHA knob, dashboard path, overlay, cooldown, wrap behavior, and optional URL query targeting are configured from **Settings -> Devices & services**.

No dashboard YAML block or template helper is required.

## Setup

1. Install the integration and restart Home Assistant.
2. Go to **Settings -> Devices & services -> Add integration**.
3. Search for **Knob Swipe Navigation**.
4. Select the ZHA rotary knob device.
5. Enter the dashboard path to control, for example `lovelace` or `dashboard-home`.
6. Choose the navigation settings and finish setup.

The dashboard path is the first URL segment:

- `/lovelace/home` -> `lovelace`
- `/dashboard-home/default_view?kiosk` -> `dashboard-home`
- `http://homeassistant.local:8123/kitchen/0` -> `kitchen`

All normal, visible tabs in the selected dashboard are affected. Subviews and hidden views are skipped.

## Entities

The integration creates these entities on its service device:

- `switch.navigation_enabled`: Main enable/pause control.
- `switch.overlay_enabled`: Shows or hides the tab overlay.
- `switch.wrap_tabs`: Enables tab wrapping.
- `number.overlay_timeout`: Overlay timeout in milliseconds.
- `number.cooldown`: Rotation cooldown in milliseconds.
- `event.rotation`: Fires `next` or `previous` when the selected knob rotates.
- `sensor.last_rotation`: Last selected-knob rotation direction.
- `sensor.last_navigation_result`: Last frontend navigation result reported by a browser.

Entity IDs can be renamed by Home Assistant. Use the entity registry values from your system when creating automations.

Reload already-open dashboard browsers after changing the selected dashboard path, selected knob, or URL query targeting. The switch and number entities are read live from Home Assistant state and do not need a browser reload.

## Browser Targeting

To limit reactions to one kiosk or tablet, configure **Required URL query parameter**. For example, set it to `kiosk` and open the intended dashboard with:

```text
/dashboard-home/default_view?kiosk
```

Both `?kiosk` and `?kiosk=1` match. This targets browser URLs only; it is not a security feature.

## Supported Devices

Supported devices are ZHA rotary knob devices that emit `zha_event` events with:

- `command: rotate_type`
- `params.rotate_type: 0` or first `args` item `0` for next tab
- `params.rotate_type: 1` or first `args` item `1` for previous tab

Unsupported:

- Zigbee2MQTT, deCONZ, MQTT, Bluetooth, and other non-ZHA sources.
- ZHA devices that do not emit `rotate_type` rotation events.
- Press, double-press, hold, and other button actions.

## Troubleshooting

If rotation does nothing:

- Confirm the integration is loaded in Devices & services.
- Confirm `switch.navigation_enabled` is on.
- Confirm the browser is showing the configured dashboard path.
- If URL query targeting is configured, confirm the browser URL contains that query parameter.
- Listen for `zha_event` in **Developer Tools -> Events** and confirm the selected knob emits `command: rotate_type`.
- Check `event.rotation`, `sensor.last_rotation`, and `sensor.last_navigation_result`.

If multiple browsers react, configure a required query parameter such as `kiosk` and open only the intended browser with that query parameter.

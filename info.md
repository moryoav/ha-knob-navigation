# Knob Swipe Navigation

Use a ZHA rotary knob to move between Lovelace dashboard tabs.

- Frontend-only tab switching once the dashboard is loaded.
- Dynamic tab names and icons from the active Lovelace dashboard.
- Optional overlay showing the selected tab.
- Optional URL query guard so only a chosen tablet/browser reacts.
- No Fully Kiosk dependency and no dependency on the classic swipe-navigation component.

After installation and restart, add the integration from **Settings -> Devices & services**, select the ZHA knob device, then opt in per dashboard with:

```yaml
knob_swipe_navigation:
  enable: true
  overlay: true
  overlay_timeout: 2800
```

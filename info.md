# Knob Swipe Navigation

Use one or more ZHA rotary knobs to move between Lovelace dashboard tabs.

- Frontend-only tab switching once the dashboard is loaded.
- Dynamic tab names and icons from the active Lovelace dashboard.
- One config entry per knob/dashboard pair.
- Optional overlay showing the selected tab.
- Optional idle return to the first visible tab after knob inactivity.
- Optional URL query guard so only a chosen tablet/browser reacts.
- Built-in switch, number, event, and sensor entities for controls and diagnostics.
- No Fully Kiosk dependency and no dependency on the classic swipe-navigation component.

After installation and restart, add the integration from **Settings -> Devices & services**, select the ZHA knob device, and enter the dashboard path to control, for example `lovelace` or `dashboard-home`. Repeat **Add integration** for each additional knob.

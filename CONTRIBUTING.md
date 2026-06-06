# Contributing

Thank you for helping improve Knob Swipe Navigation. This project is a Home Assistant custom integration, so small, well-scoped changes with clear tests and documentation are the easiest to review.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Repository Layout

- `custom_components/knob_swipe_navigation/` contains the Home Assistant integration.
- `custom_components/knob_swipe_navigation/www/` contains the frontend dashboard module.
- `custom_components/knob_swipe_navigation/translations/` contains translated strings.
- `custom_components/knob_swipe_navigation/quality_scale.yaml` tracks the Home Assistant Integration Quality Scale checklist.
- `tests/` contains the pytest test suite.
- `README.md` contains user-facing installation, configuration, and troubleshooting documentation.

## Reporting Bugs

Before opening an issue, check the README troubleshooting section and search existing issues.

When reporting a bug, include:

- Knob Swipe Navigation version or commit.
- Home Assistant version.
- Installation method, such as HACS custom repository or manual install.
- ZHA knob model, manufacturer, and the shape of the `zha_event` payload.
- Dashboard configuration block for `knob_swipe_navigation` or `swipe_nav.knob`.
- Relevant Home Assistant logs and diagnostics with device ids, dashboard URLs, and private configuration redacted.

## Requesting Features

Feature requests are welcome when they fit the scope of this integration. Please describe the user workflow, the device or dashboard behavior you need, and whether the feature should apply globally or per dashboard.

Knob Swipe Navigation currently focuses on ZHA rotary knob rotation events and Lovelace tab navigation. Support for other protocols or button actions should include example events and a clear compatibility plan.

## Development Setup

Use a Home Assistant-compatible Python environment and install the test dependencies:

```bash
python -m pip install -r requirements-test.txt
```

Run the focused validation commands before submitting a pull request:

```bash
python -m compileall custom_components tests
python -m pytest -q
```

For frontend changes, also test in a real Home Assistant dashboard with an enabled `knob_swipe_navigation` or `swipe_nav.knob` block.

## Pull Requests

- Keep changes focused on one bug fix or feature.
- Update tests when behavior changes.
- Update README or support documentation when setup, configuration, troubleshooting, or security behavior changes.
- Keep diagnostics and logs redacted.
- Do not include generated caches, Home Assistant config directories, or personal dashboard exports.

## Documentation

User-facing behavior should be documented in `README.md`. Security-sensitive behavior should also be documented in `SECURITY.md`. Support workflows should stay in `SUPPORT.md`.

# Support

## Documentation

Start with the project documentation:

- [README.md](README.md) for installation, configuration, examples, diagnostics, and troubleshooting.
- [quality_scale.yaml](custom_components/knob_swipe_navigation/quality_scale.yaml) for the Home Assistant Integration Quality Scale checklist.
- [SECURITY.md](SECURITY.md) for private vulnerability reporting.

## Getting Help

For usage questions or bug reports, open a GitHub issue in this repository.

Please include:

- Knob Swipe Navigation version or commit.
- Home Assistant version.
- Whether the integration was installed with HACS or manually.
- ZHA knob model, manufacturer, and example `zha_event` payload.
- Dashboard configuration block for `knob_swipe_navigation` or `swipe_nav.knob`.
- Relevant logs and diagnostics with private data redacted.

Helpful details include whether the dashboard uses storage mode or YAML mode, whether `require_query_param` is configured, and whether `suppress_if_entity_on` is currently active.

## Before Opening an Issue

- Confirm the integration appears in **Settings -> Devices & services**.
- Confirm the selected device belongs to ZHA.
- Confirm the dashboard has knob navigation enabled.
- Listen for `zha_event` in **Developer Tools -> Events** and verify that the knob emits `command: rotate_type`.
- Reload the browser or wall tablet showing the dashboard after changing dashboard YAML.

## Security Reports

Do not open a public issue for security vulnerabilities or private Home Assistant data exposure. Follow [SECURITY.md](SECURITY.md) instead.

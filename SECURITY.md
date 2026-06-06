# Security Policy

## Supported Versions

Security fixes are applied to the current `main` branch. If release branches are added in the future, this policy will be updated with supported versions.

## Reporting a Vulnerability

Please do not open a public issue for a security vulnerability.

Report security concerns privately through GitHub by contacting the maintainer. Include a clear description, reproduction steps, affected versions or commits, and the impact you believe the issue has.

Avoid sharing unredacted Home Assistant data. Logs, diagnostics, dashboard URLs, entity ids, device ids, screenshots, and configuration snippets can reveal private information.

## Sensitive Areas

Security-sensitive areas for this integration include:

- Diagnostics and config entry redaction.
- WebSocket commands that expose selected integration metadata to the frontend.
- Filtering of `zha_event` payloads by the configured ZHA device id.
- Frontend dashboard navigation and URL query parameter handling.
- Logging around configuration, diagnostics, and frontend setup.

## Scope

Knob Swipe Navigation does not authenticate users, expose a network service, or control Home Assistant permissions. It runs inside an existing Home Assistant instance and relies on Home Assistant for authentication, authorization, device registry access, and frontend module loading.

The `require_query_param` option is a browser-targeting guard only. It is not an authentication or authorization control.

## Disclosure

After a vulnerability is confirmed and fixed, the maintainer may publish a release note or advisory with enough information for users to understand the impact and upgrade path without exposing private reporter details.

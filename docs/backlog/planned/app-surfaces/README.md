# App surfaces backlog track

## Status
Planned

## Purpose
Follow-ups left at the seams between the gateway (which now installs, opens and signs in the
apps; see `completed/0864_gateway_engines_apps_tray_and_network_settings.md`) and the individual
apps: AbstractAssistant, the gateway's terminal console, AbstractContinuum and AbstractEntity.
Each item is owned by the app's repository; the root backlog tracks them because they surfaced in
the 2026-09-24 waves and the 2026-09-25 docs pass and cross package boundaries.

## Items
- `0875_assistant_one_time_sign_in_handover.md`: the Assistant opens from the console without a sign-in.
- `0876_gateway_console_tui_release_binaries.md`: `abstractgateway-console` has crates.io only, so no one-click terminal install.
- `0877_continuum_server_settings_as_launch_flags.md`: Continuum's server is configured by environment variables only.
- `0878_continuum_hub_seat_default_is_a_personal_name.md`: the Team page acts as seat `laurent` by default.
- `0879_app_dev_ports_match_the_stack_map.md`: `npm run dev` ports clash with the stack map (Continuum 3003, Entity 3007).
- `0880_entity_observer_url_is_a_dead_variable.md`: `ABSTRACTENTITY_OBSERVER_URL` is injected and never read.
- `0881_assistant_linux_input_dependency_with_wheels.md`: `pynput` pulls the `evdev` sdist on Linux.

## Reading order
0875 and 0876 first (they complete the one-click story), then 0881 (install matrix), then the
small Continuum/Entity cleanups in any order.

## Governing ADRs
ADR-0038 (script bootstrap and gateway console install) for the install paths; otherwise none
identified after review.

## Scope
Seams between the gateway's apps manager and each app; release artifacts the gateway consumes.

## Non-goals
No new apps, no change to the gateway's apps contract beyond what an item names, no env-var
instructions in user-facing text (operator rule applied in mission Z).

## Notes for future agents
The gateway side of every handover exists (`POST /apps/tui-handover`, browser single-use codes in
`apps_manager.py`); reuse it rather than inventing a second mechanism.

# Docs hygiene backlog track

## Status
Planned

## Purpose
Code-vs-docs conflicts and publishing gaps found by the 2026-09-25 `coredoc` pass over the repos
released on 2026-09-24 (`untracked/coredoc-2026-09-25/STATUS.md`). The pass changed docs only; these
items need code, tooling or release-workflow changes, or a cleanup the pass kept out of its file
list. Grouped because they share one validation habit: regenerate the llms files and rebuild the
docs site in the same change.

## Items
- `0882_core_llms_sources_cover_every_user_page.md`: abstractcore `update_llms.py` SOURCES missed topic pages (fix on local `main`, unreleased).
- `0883_root_llms_full_generator_file_list.md`: root `gen_llms_full.py` lacks troubleshooting, inlines backlog/research files, has no `--check`.
- `0884_gateway_docs_site_excludes_the_backlog.md`: abstractgateway `mkdocs.yml` publishes `docs/backlog/**`.
- `0885_gateway_console_ships_no_internal_html_comments.md`: maintainer HTML comments reach every browser.
- `0886_docs_sites_redeploy_on_main.md`: core site never deployed since 2026-05-27; runtime/gateway only on release tags.
- `0887_changelog_histories_without_maintainer_narrative.md`: ui-kit 0.1.9 and Entity pre-release CHANGELOG narrative.
- `0888_runtime_roadmap_is_stale.md`: AbstractRuntime `ROADMAP.md` says v0.4.2 and links a dead backlog path.

## Reading order
0884 and 0885 first (they publish internal material), then 0886, then the generators (0882, 0883),
then the cleanups (0887, 0888).

## Governing ADRs
None identified after review; the `coredoc` skill defines the doc standard.

## Scope
Docs publishing, generators and user-facing doc accuracy in abstractcore, abstractruntime,
abstractgateway, abstractuic, abstractentity and the root.

## Non-goals
No behaviour changes, no rewrites of released CHANGELOG sections beyond removing maintainer
narrative.

## Notes for future agents
Check each repo's `main` before starting: other seats were already fixing coredoc follow-ups on
2026-09-25 (abstractcore commits `cb2c160`, `4407015`).

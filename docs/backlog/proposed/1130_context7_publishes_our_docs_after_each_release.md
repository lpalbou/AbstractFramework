# 1130 — Context7 serves each package's current docs after every release

> Package: abstractframework (release), every package repo
> Type: task
> Created: 2026-11-05
> Priority: normal
> Labels: docs, llms, context7, release, automation

## Summary

The operator asks whether `llms.txt` / `llms-full.txt` and the user docs can be published to Context7 (context7.com,
Upstash) automatically, so that coding agents using the Context7 MCP read the version we just released. They can,
through Context7's documented refresh API. This item sets it up for every package repository.

## What Context7 offers today (read from its docs on 2026-11-05)

- **Registration.** A public GitHub repository is added at `context7.com/add-library` (GitHub tab); its library id is
  `/owner/repo`. Context7 indexes `.md`, `.mdx`, `.markdown`, `.rst`, `.txt` and `.ipynb` files, and only English.
  A standalone `llms.txt` / `llms-full.txt` URL can also be added as its own library (`POST /api/v2/add/llmstxt`
  with `llmstxtUrl`), separate from the repository library.
- **`context7.json`** at the repository root controls parsing (schema `https://context7.com/schema/context7.json`):
  `projectTitle` (≤ 100 chars), `description` (≤ 500), `branch`, `folders` (empty = whole repo; root-level markdown is
  always included), `excludeFolders` (wins over `folders`; globs allowed), `excludeFiles` (file names only),
  `includeExtensions`, `rules` (guidance for agents; one rejected rule drops them all), `previousVersions`
  (`[{"tag": "v1.2.1"}]`) and `branchVersions` (`[{"branch": "..."}]`). Setting `excludeFiles`/`excludeFolders`
  replaces the default exclusions (`CHANGELOG.md`, `LICENSE.md`, `CODE_OF_CONDUCT.md`, archive/legacy/i18n folders).
- **Claiming** (optional, recommended): the library's admin page generates a `context7.json` with `url` and
  `public_key`; committed at the repository root, it proves ownership. Claiming unlocks the admin panel (settings,
  versions, analytics, team members) and higher refresh limits. The public key is meant to be committed; it is not a
  secret.
- **Refresh.** Three ways:
  - automatic, only when the library is requested and its docs are older than a threshold set by popularity rank (top
    100: 1 day … other libraries: 45 days), never for private libraries;
  - the library page's refresh, for a signed-in user;
  - the API: `POST https://context7.com/api/v1/refresh` with `Authorization: Bearer <CONTEXT7_API_KEY>` (keys start
    with `ctx7sk`) and body `{"libraryName": "/owner/repo"}`, optional `branch` (must already exist on the library) and
    `gitToken` (private repositories). Answers `200 {"message": "Refresh started successfully"}`; `401`, `403`, `404
    library_not_found`, `429 rate_limit_exceeded` with `Retry-After` and `RateLimit-*` headers, `502 refresh_failed`.
    Context7's own "GitHub Actions" page is this call as a `curl` step on push, with the key in the repository secret
    `CONTEXT7_API_KEY`; there is no packaged action.
- **Versions.** A refresh re-parses the configured branch. When a refresh sees a new major version tag (`0.x`: a new
  minor), it keeps the last release of the previous one as an extra version; patch and minor releases replace
  "latest". Older tags are offered by listing them in `previousVersions`, or in the admin panel once claimed. The
  refresh endpoint takes no version or tag field.

## What is NOT possible (as documented today)

- Refreshing one specific tag: the refresh API re-parses a branch, not a tag. "Context7 serves 0.20.1" means "the
  default branch at the time of the refresh", so the refresh must run after the release commit is on that branch.
- Knowing when indexing finished: the API only answers "refresh started"; completion is seen by querying the library.
- Published rate-limit numbers: none are documented ("owners have dedicated refresh limits"); the step must honour
  `429` and `Retry-After`.
- Private repositories need a paid plan (Pro or Enterprise) and are never refreshed automatically. Ours are public.

## Current state

- `/lpalbou/abstractcore` is already indexed (133,626 tokens, 720 snippets, "updated 1 year ago", no versions listed):
  agents reading it through Context7 today get year-old AbstractCore docs. `abstractframework` also answers the
  library search; `abstractruntime` and `abstractgateway` do not.
- Every package repository is its own Context7 library (`/lpalbou/<Repo>`): 23 repositories in
  `scripts/lib/packages.txt` (the root included), all public (checked with `gh repo view`).

## Scope

### In scope

- One `context7.json` per public package repository:
  - `projectTitle`, `description` from the package's README first line;
  - `folders: ["docs"]` (root-level `README.md`, `llms.txt` and `llms-full.txt` are included as root files);
  - `excludeFolders`: `docs/backlog`, `docs/adr`, the internal folders the llms rule names (`claude`, `prompts`,
    `reports`, `research`), `untracked`, and the source folders;
  - `excludeFiles`: the internal process pages the llms rule names (`ci-local.md`, `workspace-scripts.md`,
    `implementation-plan.md`, `release-and-manifest.md` in the root; each package's own), plus `CHANGELOG.md`;
  - `rules`: none at first (a rejected rule drops them all);
  - claim each library (the claim `url` and `public_key` go in the same file).
- A refresh after each publish, two ways, one of them chosen when this item is planned:
  - a step in each package's release workflow, after the publish job succeeds, that calls the refresh API for
    `/lpalbou/<Repo>` with the key from the repository secret `CONTEXT7_API_KEY`, retrying once after `Retry-After` on
    `429` and failing visibly (no `curl -s` that hides errors);
  - or one root script (`scripts/context7_refresh.sh <repo>…`) called by the `abstract-release` skill after the
    visibility gate, with the key passed by the operator at run time.
- The key is a secret: repository or organisation secret, or the operator's own shell; never in docs, workflow files,
  hints or the backlog.

### Out of scope

- Registering standalone `llms.txt` libraries (one library per repository is enough and versions with it).
- Paid plans and private repositories.

## Acceptance criteria

- [ ] Every public package repository has a `context7.json`; its library on Context7 is claimed; no internal page (the
      llms rule) is indexed (checked on the library page or by a query).
- [ ] After a package's release reaches its default branch, the refresh runs, and within N minutes (N decided when
      planned, from the first measured runs) a query through the Context7 MCP for that library returns text that exists
      only in the new version (for example the new version number in `llms.txt`).
- [ ] A refresh that fails (`4xx`/`5xx`) is visible in the release run or the script output, never silent.
- [ ] The release skill (`abstract-release`) names the step.

## Receipts

- Context7 docs read on 2026-11-05: `context7.com/docs/adding-libraries`, `/docs/library-owners`,
  `/docs/library-updates`, `/docs/howto/claiming-libraries.md`, `/docs/api-reference/refresh/refresh-a-library`,
  `/docs/integrations/github-actions.md`, `/docs/api-reference/add-library/add-an-llmstxt-file.md`.
- `context7.com/lpalbou/abstractcore` (state on 2026-11-05).

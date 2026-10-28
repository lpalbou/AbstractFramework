# ADR-0043: End-User Interfaces Show Readable Labels, Never Computer Ids

- Status: Accepted
- Date: 2026-10-28
- Scope: every end-user surface of the framework (the web apps, the shared kit AbstractUIC, the
  desktop, iPhone and watch AbstractAssistant, the terminal clients, the gateway console's user pages)

## Context

The operator's QA pass on the redeployed release set (2026-10-28) found the same defect in four
places, each written by a different seat for a local reason:

- AbstractCode web's voice settings ("Engines" row of the kit's `AfVoiceSection`) named the chosen
  voice "250b665e…": the summary joined `provider · model · voice id`, and a cloned voice's id is a
  32-hex string.
- The AbstractAssistant desktop route editor's info banner read "… · voice 41576236…", styled like a
  warning, for the same reason (`ui/settings/route_editor.py` `_route_value_summary`).
- The desktop message footer showed two raw hex artifact ids as chips ("7c8efef…", "f738932…") that
  did not open.
- AbstractFlow's On Flow End "notify" pin carried an in-node self-comment instead of a label and help.

Each id is correct data and useless to a person: it cannot be read aloud, compared, remembered or
acted on, and it makes a working feature look broken. The gateway serves the readable name next to
almost every id (a voice's `name`/`label`, an artifact's `title`/`filename`, a run's workflow name).

## Decision

1. **Every end-user interface shows a clearly readable, concise label** for anything it names: a
   voice by its name ("Sisko", "Aiden"), an artifact by its title or file name, a run by its workflow
   and time, a model by its model name. The label comes from what the gateway serves (catalogs,
   records); a client never invents one by heuristics on the id.
2. **Computer ids are never the label.** An opaque id (a UUID, a hex digest, a run, artifact,
   voice or session id) appears only:
   - in developer or diagnostic views (Observer's ledger, the gateway console's diagnostics,
     logs, an "advanced"/"details" disclosure), or
   - as copyable detail: a "Copy id" action, a tooltip or detail line explicitly offered for
     support, never in the primary text of a row, a chip, a banner or a sentence.
3. **When the readable name is unknown** (not loaded yet, deleted, a gateway that does not serve
   it), the interface says so in words ("a saved voice", "an attachment that is no longer
   available") and keeps the id for the copyable detail. A readable id (a preset voice "aiden", a
   provider "qwen3-tts", a model name) may be shown as it is.
4. **The fix lives where the shared component lives**: a shared primitive is fixed in AbstractUIC
   (AbstractUIC ADR 0001) and adopted by pin bump; a native app fixes its own surface.
5. **Informational notes are styled as information.** A note that names the current setting is
   neutral; warning styling is reserved for something that needs the person's action.

## Consequences

- Components resolve names from the records they already read (the voice catalog, the artifact
  list); when a name needs another request, it is one request per change, never per render.
- Where the gateway does not serve a name next to an id, that is a gateway gap, raised to the
  gateway seat and recorded in its backlog; it is never papered over client-side.
- Developer surfaces keep ids: Observer and the console's diagnostics are where they belong.

## Enforcement

- Shared components pin the rule in their checks (AbstractUIC: `ui-kit/scripts/check_voice_library.mjs`
  C8/C9, mutation-checked: putting the id back in the Engines row or the saved choice is red).
- Code review refuses a user-facing string, chip or banner built from an id field (`*_id`,
  `$artifact`, `voice`) without a name lookup.
- AbstractUIC ADR 0001 carries the same rule for every kit component (section "Readable labels").

### Enforcement backlog (known violations on 2026-10-28)

| Surface | Violation | Owner | State |
|---|---|---|---|
| AbstractCode web (kit `AfVoiceSection` Engines row) | voice shown as "250b665e…" | AbstractUIC | fixed in AbstractUIC 0.8.3 (ui-kit 0.9.5), adopted by AbstractCode web 0.13.2 |
| Kit `VoiceSettings` saved choice not in the catalog | "<id> (saved)" | AbstractUIC | fixed in 0.8.3 ("Saved voice (not listed)") |
| AbstractAssistant desktop route editor banner | "· voice 41576236…", warning-styled | AbstractAssistant | open (QA (i)): resolve the name from the voice catalog, neutral tone |
| AbstractAssistant desktop message footer | raw hex artifact chips, unclickable | AbstractAssistant | open (QA (b)): artifact title/file name, opens the artifact |
| AbstractFlow On Flow End "notify" pin | in-node self-comment instead of a label and help | AbstractFlow | open (QA (c)) |
| AbstractCode web failed-run reply | "The agent failed … (run d217dac5-…)" in the reply text | AbstractCode / gateway | open: the run id belongs in a copyable detail |

## Validation

- The kit checks above are red when the id is put back.
- The operator's QA screenshots (before/after) under the release-closing QA folder for the Engines
  row; each open row is closed with its own before/after evidence.

## Related

- AbstractUIC ADR 0001 (shared primitives; amended 2026-10-28 with "Readable labels").
- ADR-0039 (loading states: say what is happening in words, never a bare spinner).
- AbstractVoice: a cloned voice's record carries `name` and the Base checkpoint it was made with.

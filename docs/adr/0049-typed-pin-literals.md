# ADR 0049: A Value Typed on an Input Takes the Input's Type

Status: Accepted — operator ruling 2026-11-02.

## Context

A Flow node card lets a person type a value into an input that has no wire. Since Flow 0.13.0 a
value typed into an input of type `any` was always stored as text. On Compare, whose `a` and `b`
are `any`, wiring `a` to the number 5 and typing `5` in `b` stored the text `"5"`, and the runtime
compared `5 == "5"`: false, with nothing on screen to say why. `>` and `<` between a number and a
text are false as well (the runtime's Compare returns false when Python refuses the comparison).

Guessing the type from the text ("5 looks like a number") would trade this for the opposite
surprise: a person who means the text "5" cannot have it. The type has to come from the graph, the
way a compiler gives a type variable the type of what it is unified with, never from the wording
of the value.

## Decision

1. **A value typed on an unwired input takes the input's type.** A `number` input stores a JSON
   number, a `boolean` input a JSON boolean, a `string` input a JSON string. Object and list inputs
   keep their JSON editors. The saved flow stores each pin default as a JSON value with its type
   (`5`, `"5"`, `true`, `[]`), and the runtime executes it exactly as stored. Execution never
   guesses a type.
2. **Generic inputs share a type variable, resolved from the wires.** A node template may give
   pins of type `any` a type variable (`Pin.typeVar`, for example `T`): the pins of one node that
   name the same variable carry one type. Today: Compare `a`/`b`; Coalesce `a`/`b`/`result`;
   `default` with the read value of Get Property, Get Element, Get Random Element and Get Variable.
   The variable resolves, in order, from a pin of the variable the node already types itself (Get
   Variable's `value`, typed by its variable), else from what is wired into its pins, else from
   what its outputs are wired to, through other generic nodes. Each step must agree on one type;
   wires that disagree leave it unresolved. The declaration is read from the node template, never
   from a saved pin, so flows saved before the declaration resolve too.
3. **Nothing to resolve from: typed text is text.** An unresolved type variable, or an `any`
   input with no type variable (Make Array's elements), stores what is typed as text. A value
   already stored with its own JSON type (a generator's `[]`, a `5` typed while `a` was wired)
   keeps it while no wire says otherwise.
4. **The type is visible.** The box of an `any` input carries a small tag: number, text,
   true/false, JSON or list. A value that is not of its input's type (`abc` on a number input, or
   on `b` next to a wired number) stays as typed, is outlined and explained under its row, and the
   run checks refuse the run until it is fixed. It is never silently stored as another type.
5. **Rewiring converts exactly or flags.** When the wiring changes an input's type, its value is
   converted if the conversion is exact (`"5"` and `5`, `"true"` and `true`); otherwise it is
   flagged as in 4. One function owns this (`withTypedPinLiterals`), applied by the editor store
   whatever changed the wiring and by `loadFlow`.
6. **Compatibility.** A flow saved by Flow 0.13.0 with such a value stored as text is converted
   when it is opened in the editor, with a notice naming the values; the returned document stays
   the flow as stored, so the flow shows unsaved changes until it is saved. A flow run without
   being opened and saved again executes what it stored: the runtime does not convert (a second
   resolver in Python would duplicate the editor's rule and the node templates, and drift). It
   refuses instead: Compare meeting a number or true/false on one side and text on the other
   (every operator), or an order between values Python cannot order, stops the run with an error
   that names the node and pins and says "One side is a number and the other is text. Open the
   flow in the editor and save it to store typed values." It never answers False silently.
   true/false compares with numbers as Python's booleans do (`True == 1`, `False < 1`); equality
   of any other pair is Python's.
7. **Declared-type exceptions are explicit.** A node whose own setting changes what an input holds
   says so in the resolver: Wait Until's `duration` is text when the node waits for a timestamp.

## Consequences

Positive: Compare, Coalesce and the getters behave as a person reading the card expects; the saved
JSON says what runs; the rule is one module with one resolver, and the runtime stays a faithful
executor of stored values.

Negative: a typed value can change type when the wiring changes, and a value that cannot follow
blocks the run until it is edited. Two typed values on an unwired Compare are both text, so
`"10" > "9"` compares text; the tag says so. A flow published to a gateway keeps its stored text
until it is opened and saved in the editor, and its Compare on a number and a text fails the run
until then. A Compare that ordered an unset value against a number (`None > 3`), which used to
answer False, now fails the run too. A whole number beyond 2^53 typed on a number input stays text
and is flagged (the browser cannot store it exactly).

Neutral: the authoring assistant's `pin_defaults` go through the same store path and are converted
or flagged like typed values. The node catalog marks shared-type pins `[type T]`.

## Enforcement

- New generic nodes declare `typeVar` on their template pins; a node that compares, merges or
  falls back between values of one type without it is rejected in review.
- Code review rejects any type decision taken from the text of a value (no "looks like a number"
  parsing on an unresolved input) and any runtime coercion of stored pin defaults.
- A node setting that changes an input's type is added to `pinLiteralType`, next to Wait Until,
  never handled by relaxing the check.
- Search `typeVar`, `pinLiterals`, `pinLiteralProblem` to find the enforcement points.

## Validation

- AbstractFlow `src/utils/pinLiterals.test.ts`: Compare `b` next to a wired number becomes 5; a
  number input holding `abc` is flagged and refused by the run checks; an unresolved variable keeps
  text; rewiring `a` from a number to a text to a boolean converts and then flags; resolution
  through Coalesce and from an output's consumer; a cycle of generic nodes terminates; opening the
  Flow 0.13.0 fixture converts it to exactly the typed fixture, with the notice.
- AbstractFlow `src/components/nodes/typedLiteral.test.tsx`: the card shows the tag and the
  problem line.
- AbstractFlow `scripts/typed_literals_smoke.py` (CI smokes, AbstractRuntime from PyPI): the
  typed fixture runs `5 == 5` and `10 > 9` as true.
- AbstractRuntime `tests/test_visual_compare_typed_values.py` (same fixtures): the typed flow is
  true; the 0.13.0 flow fails with the error naming `'Is five' (node same)`; number against text
  is refused for all six operators, true/false against text too; same-type and Python equality
  unchanged; unorderable pairs refused.
- The shipped example and bundled flows load with no value converted and none flagged.

## Backlog links

- Originating work: the 2026-11-02 operator ruling on Flow `any` inputs (open decision recorded in
  the 0.12.0 release wave), AbstractFlow PR `fix/typed-pin-literals`.
- Runtime half: AbstractRuntime PR `fix/typed-pin-literals` (Compare refuses number against text
  and unorderable pairs, naming the node). Follow-up: once that runtime is published, raise the
  AbstractFlow CI floor and re-add the 0.13.0 fixture's loud failure to its smoke.
- Optional follow-up: a one-shot command that re-types a gateway's stored flows with the editor's
  own module (no second resolver).

## Related

- ADR 0041 (No Hidden Effects After a Flow): the same "say it, never do it silently" posture.
- AbstractFlow `src/utils/pinLiterals.ts`, `src/components/pins/TypedLiteralInput.tsx`,
  `docs/web-editor.md#values-typed-on-a-card`, `docs/visualflow.md`.

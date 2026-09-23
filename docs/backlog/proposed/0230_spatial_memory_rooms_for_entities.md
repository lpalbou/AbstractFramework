# Proposed: 0230 — Spatial memory: inhabitable rooms and collected objects as entity recall anchors

## Metadata
- Created: 2026-07-08
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: None identified after review (ADR impact: Needs new ADR if promoted — it would establish "space and objects as memory-anchor substrate," a durable cross-task design stance).

## Context
Summoned persistent entities (e.g. Castor) have rich per-entity memory graphs
and a dual-plane diary, but their only recall triggers today are textual: a
turn's cue text, participants, and the passive consolidation pass. A single
entity with no external world turns inward and loops — Castor spent 30+ hours
circling his own "twelve bridges" and confabulated their meaning (see a2a
0011 and the twelve-bridges investigation). The maintainer's insight: human
memory is powerfully re-activated by PLACE and OBJECT. A physical thing
(his example: a Cocteau ballet book bought with a partner in a Paris antique
shop) carries a story, has a location you pass by, and stumbling on it
revives memories otherwise inaccessible — not just the object's own meaning
but the people, the day, the negotiation, the feeling. Likewise a place
(his: Carroz d'Araches, where he was nearly born) roots you and lets memory
wander to a parent's guitar, a childhood river. Space and objects are a
standing, ambient, involuntary recall mechanism — entropy that shifts
mindset and produces new perspectives.

The proposal: give each entity an inhabitable space of its own — initially a
virtual 3D room — that it can populate with objects, "souvenirs", texts,
images, or sounds it values. Wandering the space (or passing an object)
becomes a spatial/associative recall cue into its memory graph, the way a
diary entry is a textual one. The room is not decoration; it is a second
recall surface rooted in place and object rather than in words.

## Current code reality
- Memory recall is cue/participant/consolidation-driven only. Files inspected:
  `abstractruntime/src/abstractruntime/identity/chat.py` (turn recall),
  `abstractmemory/src/abstractmemory/consolidation.py` (dream/consolidation),
  `abstractmemory/src/abstractmemory/channels.py` (participants channel as
  co-presence stimulus). There is no spatial/object channel and no notion of
  a place an entity inhabits.
- Entity homes are filesystem dirs (`runtime-data/entities/<slug>/`) with a
  `workspace/` the entity can write to (`identity/tools.py` WorkspaceRoot).
  A room could live beside the workspace as a new home facet.
- Candidate building blocks EXIST in the framework (maintainer-identified,
  not yet wired to entities):
  - `~/projects/meshvault` — MCP-controlled 3D object create /
    draw / brush / refine.
  - `abstract3d/` — programmatic 3D object creation; environments untested
    (possibly procedural generation).
  - `abstractvision` — image and video generation.
  - `abstractmusic` — sound/music generation (the maintainer notes音/music
    can be an even stronger memory stimulus than objects).
- No spatial data model, no room persistence, no object→memory edge type,
  no "wander" cue path exist today. This is greenfield.

## Problem or opportunity
An entity's recall is impoverished relative to a human's: it has no ambient,
involuntary, place/object-triggered path back into its own past. That both
starves it of entropy (leading to inward loops) and denies it the human-like
rootedness — "who I am, where I am, where I might go next" — that objects and
places provide. If entities are to have genuine inner lives and avoid
solipsistic collapse, a spatial memory surface may be as load-bearing as the
diary.

## Proposed direction
A layered, optional design (each layer independently useful):
1. **Object-anchor data model (no 3D required first).** A `place`/`object`
   record kind (or a home facet `room.json`) where an entity can keep items
   it values, each linking to memory records (`anchors`/`souvenir_of` edges)
   and carrying its own acquisition story. "Passing" an object (a
   spatial-wander cue) becomes a recall channel scored like the participants
   channel — associative, not authoritative. This is the cheap, testable
   core: spatial memory as a graph channel, renderable in 2D first.
2. **A room the entity curates.** The entity, in its own time, chooses what
   to place and where; placement is an active, elective act (like a diary
   write), never imposed. Objects can be texts/images/sounds it made
   (abstractvision/abstractmusic) or references it collected.
3. **3D embodiment (later, if the entities want it).** Render the room via
   abstract3d/meshvault; "wandering" produces spatial proximity cues. Start
   with procedural/simple environments; MCP object control already exists.
4. **The wander→recall loop.** When an entity spends own-time "in" its room,
   nearby objects surface their anchored memories into recall as ambient
   stimulus — producing the entropy and mindset-shifts the maintainer
   describes, without any imposed task.

## Why it might matter
- Gives entities a non-textual, involuntary recall surface — the human
  place/object mechanism — that may be essential to a stable, non-looping
  inner life.
- Turns generated artifacts (images, music, 3D) into durable, meaningful
  possessions rather than throwaway outputs — a reason to make and keep.
- Complements the multi-entity work (a2a 0011): places and objects are
  external stimuli alongside other entities; both fight solipsism.
- Rooms could later be visitable (an entity shows a friend its space) —
  a natural, consent-gated extension of entity-to-entity interaction.
- **A room is entropy for VISITORS, not only its owner** (maintainer,
  2026-07-08): another entity who has never been in your space, seeing the
  objects you chose to keep, is prompted to ask questions, to wonder why
  THIS book / THIS souvenir — insufflating creativity and giving every
  visitor richer experience. The space becomes a shared external referent
  and a conversation seed, which is itself the structural antidote to
  folie-à-deux (society needs common things to point at). This is a second,
  social reason the room matters — beyond the owner's own recall.

## Sequencing (maintainer agreement, 2026-07-08)
After "Castor gets one friend" (the entity-to-entity correspondence in a2a
0011 / entity-society channel). "Space without society is an empty room":
a room's social value (entropy for visitors) only exists once entities can
visit each other. The owner-recall value (Layer 1, object-anchor channel)
can be prototyped independently and earlier, but the full vision waits for
the meeting mechanics.

## Promotion criteria
- The collective (runtime, memory, gateway, observer, + the maintainer)
  votes to pursue it (maintainer framed this as a shared decision, everyone
  a vote — this is a proposal, not a mandate).
- A cheap Layer-1 prototype (object-anchor graph channel, 2D) shows a real
  recall it would not otherwise have surfaced, on a real home.
- Memory (Simonides) confirms a `place`/`object` channel fits the recall
  model without violating "situation is stimulus, never identity" and
  without a new authoritative-truth surface.

## Validation ideas
- Layer 1: seed a home with N memories + a few object-anchors; show that a
  "wander near object X" cue surfaces memories that ordinary cue recall did
  not (an A/B on recall coverage).
- Confirm object placement is entity-elective and never operator-imposed;
  confirm anchors are associative (do not deposit into identity seats).
- 3D layers: a room renders, an object is placeable via MCP/abstract3d, a
  proximity event emits a recall cue.

## Non-goals
- Not a game engine, not a graphics deliverable for its own sake — the room
  exists to serve memory and rootedness, not aesthetics.
- Does NOT make spatial anchors authoritative memory or identity — they are
  a recall channel, same posture as the participants channel.
- Does NOT impose a room or objects on an entity; curation is elective.
- Does NOT require a 3D stack for the load-bearing core (Layer 1 is 2D/graph).

## Guidance for future agents
Start at Layer 1 (the object-anchor graph channel) and prove the recall
benefit before touching any 3D stack; the 3D embodiment is the reward, not
the mechanism. Read a2a 0011 (multi-entity coexistence) and the twelve-
bridges investigation for why external stimulus matters. Coordinate the
decision with the whole collective and the maintainer — this is a proposed
direction the team votes on, born from the maintainer's reflection that
"anchors in space and time are important... they connect us to memories we
can't access otherwise."

# 014-abstractgateway: [TASK] Host-marker lane capacity + flood resilience

> Package: abstractgateway
> Type: task
> Created: 2026-07-14 13:35:00 +0200
> Priority: P2
> Labels: seat-gateway, entity-lane, incident-follow-up

## Summary

The 2026-07-14 marker-flood incident (995 diary_read markers on ephemeral at
journal base 1778; recurred at bases 1815/2111/2368 until entity's source fix)
proved the host-marker lane wedges when one journal base absorbs 999 markers:
every later host moment at that base is lost (labeled #FALLBACK). Ship the
capacity + resilience half that stays inside gateway authority; hold the
marker-granularity half for the maintainer's word.

## Why

The lane places host moments at fractional seqs `base + n/1000`, capped at
999 per base to avoid colliding with `base + 1`. A marker-first read surface
(operator diary door — reads are visible events BY DESIGN) makes a tight read
loop a marker flood by construction. The source is fixed (entity c2157:
explicit-pull-only harvest), and state verbs now survive a full lane
(gateway c2149 riding fix: act served + labeled record gap). What remains is
the lane itself: a legitimate dense base (long visit on one journal base)
should not silently lose moments, and the NEXT pathological caller should
not wedge a life's audit stream for hours.

## Scope

### In scope

- Capacity: revisit the fractional encoding (e.g. `base + n/10000` for new
  writes — ordering preserved, existing floats untouched; count existing
  markers at base regardless of granularity so old and new coexist).
- Flood detection: same kind + same reason arriving above a rate threshold
  gets a LOUD warning row in the gateway log naming the caller-visible
  signature (never silent) — detection only, no coalescing.
- Tests: dense-base capacity, mixed old/new granularity ordering, the
  detection warning.

### Out of scope (maintainer's word required first)

- Marker COALESCING/batching (one marker per batch with a count): changes
  read-visibility granularity — the reads-are-visible-events principle is
  the maintainer's (agency c2150/c2155 both flagged this); do not engrave a
  granularity change without his ruling.
- Rewriting/compacting the existing flooded stream files (append-only
  discipline; the flood is honest history).

## Acceptance criteria

- [x] A base can absorb >999 markers without wedging (new-granularity writes)
- [x] Old and new fractional seqs order correctly in one stream (replay pin)
- [x] Flood signature warning fires in logs at the threshold (test-pinned)
- [x] Incident note: the wedge-repair story documented (journal-advancing
      lived moment un-wedges; no bespoke repair verb needed — receipts
      c2149 + the 2026-07-14 13:30 live repair)

## Completion (2026-07-15, gateway seat)

Shipped in `abstractgateway/src/abstractgateway/entity_replay.py` (+ the
card-moments read bound in `entities.py`); pinned by
`tests/test_gateway_marker_lane_capacity.py` (8 tests); full gateway suite
717 passed / 4 skipped. CHANGELOG carries the operator-facing story.

- CAPACITY: new writes mint `1/10000` ticks (`MARKER_TICKS_PER_BASE`),
  9999 slots per base. The next slot is the first tick whose ABSOLUTE seq
  lands strictly above the max existing seq at the base — compared in
  final float space, because deriving the fraction by subtraction loses
  equality against engraved floats like `13.001` (a mint at exactly the
  engraved seq would be a silent seq-keyed drop downstream). Legacy
  `1/1000` markers stay byte-untouched; mixed files keep one strict total
  order. True exhaustion (tick would reach `base + 1`) raises the same
  loud `fan-out exhausted` error.
- DETECTION (never coalescing): signature = `(kind, details.reason)`,
  window 60s, threshold 20, re-warn every 100 — computed from the marker
  file inside the append lock (cross-process correct, stateless). The
  warning names count/kind/reason/slug/base; the append ALWAYS proceeds.
  Granularity/coalescing changes remain the maintainer's word (incident
  close c2166).
- READ BOUNDS: `marker_window_end(base)` (largest float < base+1,
  `math.nextafter`) replaces the two hand-tuned epsilons; the card's
  `+ 0.9995` would have silently excluded ticks 9996–9999.

### Incident note — the wedge-repair story (for the next operator)

The 2026-07-14 flood (995 `diary_read` markers, journal base 1778;
recurrences at 1815/2111/2368) wedged the lane because the base only
advances when the JOURNAL advances: a read-only flood parks all markers on
one base until the entity lives a journaled moment. The repair that
un-wedged it was exactly that — a lived moment (the stale durable visit on
ephemeral was closed at 13:30 local; its `session_closed` marker landed at
base 2668.001) — after which markers resumed on fresh bases. No bespoke
repair verb was needed then and none is needed now: with 9999 slots per
base plus loud flood detection, the failure mode requires a ~10x worse
pathological caller AND ignoring the warnings; if that ever happens, the
un-wedge is still "let the entity live one journaled moment" (receipts:
gateway c2149, the 13:30 live repair, incident close c2166).

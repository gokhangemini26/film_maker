# Intent and rationale

## Intent is not implementation

Intent says what an effect on the audience should be:
> *The protagonist should feel isolated.*

Implementation says how this film achieves it here:
> 50mm lens at mid distance, subject in the lower third, 70% negative space;
> cold ambient light with no practicals near her; empty street.

Intent is captured first (`canon/intent.yaml`), locked at G1, and rarely
changes. Implementations point to it with `serves:` and can be revised freely
(through the normal gates) without losing what they were for.

Write intents as audience effects, not techniques:
- good: "The ending should open a small door of hope, not resolve her loneliness."
- bad: "Use warm light at the end." (that is an implementation)

## What a rationale must contain

1. **The choice** — specific enough to check.
2. **How it serves the intent** — name the mechanism (compression separates
   planes; practical-only warmth becomes a motif; a held wide lets silence land).
3. **The alternative rejected, and why** — one line is enough.
4. **The cost or risk**, when there is one (e.g. "long lens makes blocking
   geography harder to read; SH010 establishes it first").

One to four sentences. No adjectives without mechanisms ("cinematic",
"striking", "powerful" explain nothing).

## Shots

Every shot carries both halves:

```yaml
serves: [intent.isolation]
creative_intent:
  narrative_purpose: Show that nobody else is on the street.
  emotional_purpose: A quiet loneliness, not danger.
  visual_purpose: A small figure in a large, cold frame.
  audience_effect: The viewer notices how far she is from any light.
rationale:
  camera: 35mm from 12m, eye height - wide enough to show the empty street, not so wide it becomes a vista.
  composition: Mara lower-right third; the dark street fills two thirds of the frame.
  lighting: No light source near her; the nearest practical is out of reach at frame left.
  movement: Locked-off; she walks through the frame and it does not follow her.
```

## When revising

Change the implementation, keep `serves`, and rewrite the rationale so it
explains how the new choice serves the same intent. If you believe the intent
itself should change, say so in the handoff - only the human changes intent.

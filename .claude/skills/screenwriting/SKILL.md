---
name: screenwriting
description: "Write a Fountain-compatible screenplay and its machine-readable scene index (SCENES.yaml) from the approved story. Used by the screenwriter in the SCREENPLAY phase."
user-invocable: false
---

# Screenwriting

## Purpose
Turn the story structure into scenes that can be filmed: what we see and hear,
in screen order, with timing — and index them so storyboards and continuity can
be checked mechanically.

## When to use
SCREENPLAY phase (`/film-script`), and revisions to scenes or dialogue.

## Required inputs
- `01_story/STORY_BIBLE.md`, `STORY_STRUCTURE.md`, `canon/story.yaml`.
- Tone canon and CREATIVE_DIRECTION (register, anti-goals).

## Process
1. Map beats to scenes: a new scene when place or continuous time changes.
   Assign `SC01`, `SC02`... in screen order.
2. Write in Fountain: `EXT./INT. LOCATION - TIME` headings, present-tense
   action lines describing only what can be seen or heard, CHARACTER cues,
   parentheticals sparingly, transitions only when they carry meaning.
3. Show, don't explain: in short film, prefer image and sound over dialogue.
   Every line of dialogue must do something the image cannot.
4. Write for proxy characters: action and posture, not micro-expressions.
5. Time it: roughly one page per minute is too coarse for short films —
   estimate each scene from its action (count the actions and holds).
   Totals must match the story structure.
6. Build `SCENES.yaml` from the template: heading exactly as written, summary,
   est_duration_s, characters (canon ids), location, time_of_day, weather.
7. Do not add canon. If the script needs something the story canon doesn't
   allow, report it.

## Output format
- `02_screenplay/SCREENPLAY.md`: `fm:` block, then Fountain text. Put the scene
  id in a note after each heading: `EXT. HARBOUR - NIGHT [[SC01]]`.
- `02_screenplay/SCENES.yaml` (`kind: scene_index`), derived_from the screenplay.

## Validation rules
- Every scene in SCENES.yaml appears in SCREENPLAY.md with the same heading and id.
- Scene durations sum to the brief duration ±10%.
- Every character named exists (or is proposed) in character canon by G3.
- No camera directions (that is the cinematographer's job) except where the
  story truly depends on what the audience sees ("We see only her hands").

## Failure conditions
- Story beats cannot fit the duration → report with a proposed cut, don't rush.
- The script needs a location/character the story bible excludes → report.

## Examples
```
EXT. HARBOUR STREET - NIGHT [[SC01]]

Rain on dark water. The street is empty except for MARA (34), hood up,
walking against the wind. A shop sign flickers behind her and dies.

Her phone buzzes. She doesn't look.
```

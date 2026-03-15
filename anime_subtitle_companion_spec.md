# Anime Subtitle Companion — Repo Planning Spec

## Overview

This project is a companion app for watching Japanese media with interactive, AI-annotated subtitles in a separate window alongside a streaming platform such as Crunchyroll or Netflix.

The app does **not** need to inject into the streaming site. Instead, it runs its own subtitle timeline locally using subtitle timestamps from `.ass` / `.ssa` files and allows the user to manually adjust sync with an offset control.

The core idea is:

1. Find or load a Japanese subtitle file for a title / episode.
2. Parse subtitle events into a normalized timed structure.
3. Use an LLM to transform subtitle lines into a learner-friendly annotated representation.
4. Render the result in a web UI with clickable tokens, grammar notes, translations, and external dictionary links.
5. Run the app in parallel with a streaming window and auto-scroll based on a local timer.

This should feel like an “AI subtitle IDE” for Japanese learners.

---

## Product Goal

Build a web-based companion interface that lets a user:

- watch anime or Japanese video content in one window
- keep a subtitle companion panel open in another window
- auto-scroll subtitles based on local timer + manual sync offset
- click words to inspect meaning, reading, lemma, part of speech, and grammar role
- read sentence-level explanations and translations
- jump around the subtitle timeline
- optionally export useful lines for flashcards later

The initial target is a practical MVP that is useful without requiring deep integration with video platforms.

---

## Why this approach

### Avoid streaming-site integration in the first version

Direct integration with Netflix / Crunchyroll is brittle and probably unnecessary for a strong MVP.

A parallel-window companion app is much simpler:

- no DOM injection into streaming sites
- no fighting platform-specific player behavior
- no need to depend on subtitle tracks provided by the platform
- easier iteration and debugging

### Why `.ass` / `.ssa` files are valuable

ASS/SSA subtitle files are not just raw text. They provide:

- timestamps
- line structure
- styles
- sometimes speaker-related hints
- formatting that can help infer dialogue pacing

That makes them a strong input format for timed companion rendering and LLM-based annotation.

### Why an LLM-first analysis pipeline makes sense

Anime dialogue is full of:

- omitted subjects
- casual contractions
- sentence fragments
- slang
- emotional tone
- context-dependent meaning

A conventional parser can help, but an LLM can often do a better job transforming dialogue into a pedagogical representation because it can use surrounding subtitle context to interpret the line.

The project should lean into an LLM-centric transform pipeline, with strong structured outputs rather than treating the model as a freeform tutor.

---

## Initial Architecture

### Backend

Use Python for the backend and subtitle processing / annotation pipeline.

Potential stack:

- **Python 3.11+**
- **FastAPI** for API layer
- **Pydantic** for schemas
- **httpx** or **aiohttp** for external calls
- optional task queue later if preprocessing becomes heavier

Backend responsibilities:

- subtitle file ingestion
- ASS/SSA parsing
- subtitle block normalization / merging
- annotation generation
- storage / caching of annotated results
- search / retrieval for subtitle blocks
- dictionary linking helpers
- subtitle source lookup agent later

### Frontend

Use a Node-based frontend with a modern SPA framework.

Potential stack:

- **React + TypeScript**
- **Vite**
- simple CSS or Tailwind
- possibly a component library later, but not required for MVP

Frontend responsibilities:

- transcript rendering
- active-line highlighting
- auto-scroll behavior
- local timer controls
- offset controls
- token click interaction
- grammar / translation side panel
- outward dictionary links

---

## MVP Feature Set

### 1. Subtitle loading

The app should support:

- loading a local `.ass` / `.ssa` file
- later supporting `.srt` as fallback
- optionally associating subtitle files with title / episode metadata

Initial MVP can start with user-supplied files.

### 2. Subtitle timeline playback

The app maintains its own local playback clock.

Core state:

- `currentTimeMs`
- `isPlaying`
- `globalOffsetMs`
- `currentBlockIndex`

Behavior:

- a local timer advances when playback is active
- effective subtitle time = local timer + user offset
- the matching subtitle block becomes active
- the transcript auto-scrolls to the active block

Controls:

- play / pause
- jump to previous / next subtitle block
- seek timeline
- offset slider
- fine sync buttons like `-250ms / +250ms`
- optional “sync to current line” action

### 3. Subtitle preprocessing

Raw ASS subtitle events should be transformed into cleaner display / analysis blocks.

Reasons:

- visual line breaks are not always sentence breaks
- adjacent lines may belong to one spoken utterance
- analysis quality improves when the unit is more linguistically natural

Preprocessing steps:

1. Parse dialogue events.
2. Strip formatting tags where appropriate.
3. Merge adjacent events when they likely belong to one sentence or utterance.
4. Preserve timing windows.
5. Build a contextual neighborhood for each block.

### 4. Annotation generation

Use an LLM to transform each subtitle block into a structured learner-facing representation.

The important design principle is:

**Use the LLM as a structured transformation engine, not just a chat explainer.**

The output should be a stable JSON object that the frontend can render directly.

### 5. Interactive transcript UI

The transcript should render each subtitle block with:

- original Japanese line
- optional furigana display
- current active highlight
- hover / click token interactions
- expandable grammar notes
- literal and natural translation

### 6. Dictionary links

Each token or line should be able to link outward to a dictionary/reference site.

Good initial external targets:

- **Jisho**
- **Wiktionary**
- possibly **jpdb** later
- possibly **Weblio** later depending on UX and appropriateness

Even if the app provides its own LLM-generated definition, outward links are useful for verification and alternative viewpoints.

---

## Core Data Model

A useful normalized subtitle block may look like this:

```json
{
  "id": "ep01-000123",
  "start_ms": 192450,
  "end_ms": 194100,
  "raw_text": "そういうことか",
  "display_text": "そういうことか",
  "normalized_text": "そういうことか",
  "tokens": [
    {
      "surface": "そう",
      "lemma": "そう",
      "reading": "そう",
      "part_of_speech": "adverb / pronoun-like expression",
      "gloss": "that way; like that; so",
      "grammar_role": "refers to previously discussed situation",
      "conjugation": null,
      "dictionary_links": {
        "jisho": "https://jisho.org/search/%E3%81%9D%E3%81%86",
        "wiktionary": "https://en.wiktionary.org/wiki/%E3%81%9D%E3%81%86"
      }
    },
    {
      "surface": "いう",
      "lemma": "言う",
      "reading": "いう",
      "part_of_speech": "verb",
      "gloss": "to say; to mean",
      "grammar_role": "modifies the expression as 'that kind of'",
      "conjugation": "dictionary form",
      "dictionary_links": {
        "jisho": "https://jisho.org/search/%E8%A8%80%E3%81%86",
        "wiktionary": "https://en.wiktionary.org/wiki/%E8%A8%80%E3%81%86"
      }
    },
    {
      "surface": "こと",
      "lemma": "こと",
      "reading": "こと",
      "part_of_speech": "noun",
      "gloss": "thing; matter",
      "grammar_role": "nominalizes the situation",
      "conjugation": null,
      "dictionary_links": {
        "jisho": "https://jisho.org/search/%E3%81%93%E3%81%A8",
        "wiktionary": "https://en.wiktionary.org/wiki/%E3%81%93%E3%81%A8"
      }
    },
    {
      "surface": "か",
      "lemma": "か",
      "reading": "か",
      "part_of_speech": "particle",
      "gloss": "question / realization marker",
      "grammar_role": "marks realization or rhetorical question nuance",
      "conjugation": null,
      "dictionary_links": {
        "jisho": "https://jisho.org/search/%E3%81%8B",
        "wiktionary": "https://en.wiktionary.org/wiki/%E3%81%8B"
      }
    }
  ],
  "grammar_notes": [
    "The line expresses realization: 'So that's what this is / I see how it is.'",
    "The exact natural translation depends on scene context."
  ],
  "literal_translation": "Is it that kind of thing?",
  "natural_translation": "I see. So that's what's going on.",
  "ambiguity_notes": [
    "Could also be understood as 'So that's how it is.' depending on prior context."
  ],
  "confidence": 0.88,
  "context_window": {
    "previous": ["..."],
    "next": ["..."]
  }
}
```

---

## Annotation Strategy

### Preferred approach

Use the LLM to generate the entire learner-facing structured annotation for each subtitle block.

That includes:

- tokenization
- readings
- lemmas
- parts of speech
- context-sensitive glosses
- grammar notes
- literal translation
- natural translation
- ambiguity notes
- confidence estimate

### Why this is attractive

This avoids a brittle multi-stage pipeline like:

tokenizer -> dictionary -> grammar rules -> explanation

Instead, the app can ask the model to interpret the subtitle block in context and produce a single structured representation.

This is especially useful for anime dialogue where interpretation matters as much as raw morphology.

### Important constraints

The LLM output must be:

- strictly schema-constrained
- cached
- inspectable
- versioned if prompts or models change

This should not be an unstructured prose response.

### Context window design

For each target subtitle block, send:

- previous N subtitle blocks
- current subtitle block
- next N subtitle blocks

A good initial value might be 2–5 lines on each side depending on line density.

This helps the model:

- infer omitted subjects
- resolve ambiguous particles
- interpret tone and stance
- choose a more accurate natural translation

### Optional future hybrid mode

Even though the current design is LLM-first, it may still be useful later to support a hybrid verification mode where conventional NLP tools can be used as a secondary check, not as the primary interface layer.

That is optional and not required for MVP.

---

## Timer and Sync Model

The initial cut should use a local timer and manual sync adjustment.

### Core idea

The app does not know the true playback position of Netflix / Crunchyroll.

Instead:

- user starts the companion timer
- app auto-scrolls based on subtitle timestamps
- user adjusts offset manually until the lines line up

### Effective time formula

```text
effective_time_ms = local_timer_ms + global_offset_ms
```

The active subtitle block is whichever block contains `effective_time_ms`.

### Why this is enough for MVP

Most subtitle mismatch issues fall into one of these categories:

1. **Constant offset**  
   A single global adjustment solves most of the episode.

2. **Drift over time**  
   For MVP, occasional resync is acceptable.

### Future sync improvement

A later enhancement can support **piecewise sync anchors**:

- user sets sync points at multiple moments
- the system interpolates timing adjustments between anchor points

That would handle nonlinear drift more gracefully.

---

## UI Concept

### Layout

A strong first layout:

- center / main pane: transcript
- right pane: token detail + grammar notes
- top bar: playback and sync controls
- optional bottom mini timeline

### Transcript behavior

For each subtitle block:

- show Japanese text prominently
- optionally show furigana
- highlight active block
- auto-scroll active block into view
- allow click to expand details

### Token interaction

Each token can be rendered as a clickable `<span>` with attached metadata.

On click:

- open token detail card in side panel
- show lemma
- reading
- part of speech
- meaning in context
- grammar role
- outward dictionary links

### Sentence interaction

For the whole subtitle block:

- show literal translation
- show natural translation
- show grammar notes
- show ambiguity / nuance notes
- possibly allow “explain more simply” or “explain at N5 level” later

---

## External Dictionary / Reference Linking

The app should support outward links at both token and line level.

### Good first targets

#### Jisho
Easy and familiar for many learners.

Token search URL pattern:

```text
https://jisho.org/search/{url_encoded_query}
```

#### Wiktionary
Useful as a secondary reference.

Search URL pattern:

```text
https://en.wiktionary.org/wiki/{url_encoded_query}
```

### Additional options later

- jpdb
- Weblio
- Goo Dictionary
- Tofugu grammar references
- Bunpro grammar pages if appropriate and linkable
- Tae Kim or other grammar references if a mapping layer is added

### Strategy

The simplest approach is:

- generate links from token `surface` and/or `lemma`
- store them in token metadata
- let the UI open them in a new tab

LLM-generated definitions are still useful, but external links improve trust and give users a second reference path.

---

## Subtitle Source Lookup Agent

This is a later-phase capability, but it fits the product idea well.

### Agent responsibilities

Given a title / season / episode request, the agent should try to:

- find candidate subtitle files
- rank likely matches
- retrieve or present options to the user
- associate subtitle file metadata with the episode

### Important caveats

Subtitle retrieval introduces non-technical concerns:

- copyright / licensing
- source quality
- timing mismatch across releases

From a product and legal perspective, the safest MVP is likely:

- user-supplied subtitle files
- or clearly licensed subtitle sources only

Still, architecturally, the app can be built so that source lookup is a pluggable module later.

---

## Suggested Repo Structure

```text
anime-subtitle-companion/
├─ README.md
├─ docs/
│  ├─ product-spec.md
│  ├─ architecture.md
│  ├─ annotation-schema.md
│  └─ prompts.md
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/
│  │  ├─ models/
│  │  ├─ services/
│  │  ├─ subtitle/
│  │  ├─ annotation/
│  │  ├─ sync/
│  │  └─ utils/
│  ├─ tests/
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ hooks/
│  │  ├─ lib/
│  │  ├─ types/
│  │  └─ styles/
│  ├─ package.json
│  └─ vite.config.ts
└─ sample-data/
   └─ subtitles/
```

---

## Backend Components

### ASS parser module

Responsibilities:

- parse subtitle files
- extract dialogue events
- strip formatting tags
- preserve timing
- preserve style info where useful

Possible libraries:

- `ass`
- `pysubs2`

### Block merger / normalizer

Responsibilities:

- merge split display lines into more natural utterance blocks
- preserve mapping to original events
- generate block IDs
- attach context windows

### Annotation service

Responsibilities:

- build model prompts
- call LLM
- validate schema output
- retry on invalid output
- cache results

### Dictionary link helper

Responsibilities:

- generate outbound URLs from token text / lemma
- optionally generate multiple target links

### Project storage

Possible MVP storage options:

- JSON files
- SQLite
- later Postgres if needed

Likely simplest starting point:

- SQLite for metadata and annotations
- local file storage for raw subtitle files

---

## Frontend Components

### Transcript view

Responsibilities:

- render subtitle blocks
- highlight active block
- auto-scroll into view
- allow block selection

### Tokenized subtitle line component

Responsibilities:

- render tokens as clickable spans
- show optional furigana
- indicate selected token

### Side panel

Responsibilities:

- render selected token details
- render selected line grammar notes
- render translations
- render ambiguity notes
- show outward links

### Player controls

Responsibilities:

- play / pause local timer
- seek
- offset adjustments
- current time display
- current offset display

### Episode/session panel

Responsibilities:

- load subtitle file
- view metadata
- possibly save per-episode sync settings

---

## API Sketch

### Upload / load subtitles

```http
POST /api/subtitles/upload
```

### List parsed blocks

```http
GET /api/subtitles/{subtitle_set_id}/blocks
```

### Trigger annotation

```http
POST /api/subtitles/{subtitle_set_id}/annotate
```

### Get annotated block list

```http
GET /api/subtitles/{subtitle_set_id}/annotations
```

### Save sync preferences

```http
POST /api/subtitles/{subtitle_set_id}/sync
```

### Get sync preferences

```http
GET /api/subtitles/{subtitle_set_id}/sync
```

---

## LLM Prompting Notes

The model should be instructed to behave like a transformation engine.

It should:

- use surrounding subtitle context
- avoid inventing unsupported details
- mark ambiguity explicitly
- produce token-level analysis and sentence-level notes
- keep output within schema
- prefer concise, learner-useful explanations

The prompt design should distinguish between:

1. **Structural analysis**
   - token list
   - lemmas
   - readings
   - parts of speech
   - translations
   - ambiguity

2. **Pedagogical explanation**
   - grammar notes
   - nuance notes
   - learner-facing explanation

A good implementation detail is to store the prompt version and model version alongside each annotation output.

---

## Reliability Notes

### Main risk areas

- subtitle timing mismatch
- wrong subtitle file match
- LLM hallucinated morphology or readings
- overly confident grammar explanations
- inconsistent analysis across runs if outputs are not cached

### Mitigations

- cache all annotation results
- validate schema strictly
- store confidence / ambiguity notes
- expose outward dictionary links
- let users inspect original subtitle text directly
- store prompt/model version metadata
- allow re-annotation later if desired

---

## Development Phases

### Phase 1: MVP

- local subtitle file upload
- ASS parsing
- block normalization
- local timer + manual offset
- transcript rendering
- token click interaction
- LLM annotation generation
- Jisho and Wiktionary links

### Phase 2: Better sync and usability

- saved offset per episode
- sync anchors / piecewise drift correction
- subtitle search
- search within transcript
- keyboard shortcuts
- better furigana display
- explanation level controls

### Phase 3: Power features

- flashcard export
- known-word tracking
- difficulty filters
- subtitle source lookup agent
- richer grammar reference linking
- batch episode preprocessing
- user profiles / learner settings

---

## First Implementation Priorities

If starting this repo from scratch, the most useful order is probably:

1. Parse `.ass` files into normalized blocks.
2. Render timed transcript in frontend.
3. Add local playback timer and offset controls.
4. Define annotation JSON schema.
5. Implement backend annotation endpoint.
6. Render clickable token details and line notes.
7. Add outward dictionary links.
8. Add persistence and per-episode sync storage.

This gets to a usable experience quickly.

---

## Open Questions

These are worth keeping in mind as implementation begins:

- What exact heuristics should be used to merge subtitle events into display blocks?
- Should annotations be generated eagerly for a whole episode or lazily per block / viewport?
- What model should be used for initial annotation generation?
- How should confidence be represented: numeric score, labels, or both?
- How much of the UI should show furigana by default?
- Should grammar explanations be globally configurable by learner level?

---

## Summary

This repo should implement a separate-window subtitle companion for Japanese learning that:

- consumes timed subtitle files such as `.ass`
- uses an LLM to produce rich structured annotations
- renders clickable, inspectable subtitle lines in a web UI
- auto-scrolls based on a local timer
- supports manual sync offset to align with streaming playback
- links outward to dictionary/reference sites such as Jisho

The guiding principle is:

**use AI to transform subtitles into a learner-friendly interactive representation, without depending on deep integration with the streaming platform.**

# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan their day of pet
care. The owner enters their info and pets, adds care tasks (with a time,
duration, priority, and how often they repeat), and PawPal+ builds a daily plan
that fits the available time, puts the most important tasks first, flags timing
conflicts, and explains its choices.

## ✨ Features

- **Owner & pets** — store an owner, their available minutes, and one or more pets.
- **Rich tasks** — each task has a title, duration, priority, time (`HH:MM`),
  repeat frequency (`once` / `daily` / `weekly`), and a completed flag.
- **Smart daily plan** — sorts by priority (then time) and only schedules tasks
  that fit within the owner's available minutes; completed tasks are skipped.
- **Conflict detection** — warns when two tasks share the same start time.
- **Recurring tasks** — completing a daily/weekly task generates its next occurrence.
- **Plain-English explanation** — the scheduler explains why each task was chosen.
- **🤖 AI Pet-Care Assistant (local RAG, no API key)** — retrieves general
  care guidance from a local knowledge base using the pet's species, age
  (life stage), needs, and the owner's question. Retrieved guidance is shown
  with source/category labels, is woven into the schedule explanation, and is
  wrapped in guardrails (no diagnosis, emergency warning, graceful fallback).
  See [AI Pet-Care Assistant](#-ai-pet-care-assistant).
- **Data persistence (bonus)** — save/load owner, pets, and tasks to `data.json`
  so they persist between runs (see [Data Persistence](#-data-persistence)).
- **Professional Streamlit UI** — structured `st.table()` displays, sidebar
  controls, color-coded warnings/success messages, and plain-English explanations
  (see [Professional UI and Output Formatting](#-professional-ui-and-output-formatting)).
- **Readable CLI output** — `main.py` prints clearly labeled section headings.
- **Two front ends** — a CLI demo (`main.py`) and a Streamlit UI (`app.py`).
- **Tested** — 72 automated `pytest` tests covering the core behaviors, edge
  cases, strict `HH:MM` time validation, and the AI assistant (retrieval,
  guardrails, life-stage/age handling, invalid input, response ordering).

## ▶️ Quick start (exact commands)

```bash
# 1. Set up an isolated environment and install dependencies.
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Run the tests (should report "72 passed").
python -m pytest

# 3a. Run the Streamlit web app (opens http://localhost:8501).
streamlit run app.py

# 3b. Or run the CLI demo (prints an example plan and scheduling features).
python main.py
```

The AI Pet-Care Assistant runs fully offline — **no API key or internet
connection is required**.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` builds an example owner with two pets and several
tasks, then demonstrates the smarter scheduling features — time sorting,
filtering, conflict detection, and recurring tasks:

```
Today's Schedule (priority, then time)
======================================
1. 08:00 Morning walk (20 min) [priority: high]
2. 08:00 Feeding (10 min) [priority: high]
3. 18:00 Evening walk (30 min) [priority: high]

All Tasks Sorted by Time
========================
08:00 - Morning walk
08:00 - Feeding
12:00 - Grooming
15:00 - Play time
18:00 - Evening walk

Filtered: Incomplete Tasks Only
===============================
- Evening walk (18:00)
- Morning walk (08:00)
- Feeding (08:00)
- Play time (15:00)

Conflict Warnings
=================
! Conflict at 08:00: Morning walk, Feeding

Recurring Task Example
======================
Marked complete: Morning walk (completed=True)
Next occurrence created: Morning walk (next daily) at 08:00

Explanation
===========
Jordan has 60 minutes available.
Chose 3 task(s) using 60 minute(s), highest priority first:
  1. 08:00 Morning walk (20 min, high priority)
  2. 08:00 Feeding (10 min, high priority)
  3. 18:00 Evening walk (30 min, high priority)
```

Note how "Grooming" (completed) is skipped from the plan, and the medium
"Play time" (15 min) doesn't fit because the three high-priority tasks already
fill all 60 available minutes.

## 🧪 Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

The 72 tests span two files — `tests/test_pawpal.py` (core scheduling,
persistence, and time validation) and `tests/test_assistant.py` (the AI
Pet-Care Assistant).

**Core behaviors (`tests/test_pawpal.py`):**

- **Priority ranking** — a high-priority task ranks higher than a low-priority one.
- **Adding tasks** — adding a task to a pet increases that pet's task count.
- **Task completion** — calling `mark_complete()` flips a task's `completed` flag to True.
- **Time budget** — the generated plan never exceeds the owner's available minutes.
- **Time sorting** — `sort_by_time()` returns tasks in chronological order.
- **Filtering** — `filter_tasks()` can select/exclude completed tasks and filter by pet name.
- **Conflict detection** — duplicate task times are flagged by `detect_conflicts()`,
  and non-overlapping times produce no warnings.
- **Recurring tasks** — completing a daily *or* weekly task creates a fresh next
  occurrence; a one-time task returns `None`.
- **Skipping completed tasks** — completed tasks never appear in the generated plan.
- **Edge cases** — a pet with no tasks yields an empty plan (no crash), and a task
  too long to fit the time budget is skipped while shorter ones still get scheduled.
- **JSON persistence** — saving an owner (with a pet and task) to a temporary file
  and loading it back preserves the data; loading a missing file returns `None`.
- **Strict time validation** — `is_valid_hhmm()` accepts only zero-padded 24-hour
  `HH:MM` (e.g. `09:00`, `18:30`) and rejects `9:00`, `0900`, `25:00`, `12:60`,
  empty, and non-string values.

**AI Pet-Care Assistant (`tests/test_assistant.py`):**

- **Life stage** — species-aware age thresholds map to puppy/kitten/adult/senior,
  and unknown/invalid ages fall back to a neutral stage.
- **Retrieval** — returns relevant, species-specific guidance; prefers
  life-stage-appropriate advice; folds the pet's stated needs into the query;
  respects `top_k`; and always attaches category/source labels.
- **Age-neutral fallback** — when the age is unknown, retrieval returns *only*
  age-neutral guidance (never a mix of puppy/adult/senior advice), and `assist()`
  adds an "enter the age" suggestion for dogs/cats; a known age excludes advice
  meant for other life stages.
- **Honest sources** — every knowledge-base source is labelled as local PawPal+
  guidance (verified in tests), not a fake external citation.
- **Guardrails & ordering** — emergency keywords trigger an urgent warning that
  `response_blocks()` always places *before* any guidance; diagnosis-style
  questions get a "see a vet" note (never a diagnosis); every response ends with
  the non-diagnostic disclaimer.
- **Schedule integration** — `explain_plan_with_guidance()` weaves retrieved
  guidance into the scheduler's own explanation while preserving the base text.
- **Invalid input / fallback** — empty, whitespace, `None`, or non-string questions
  return a friendly fallback (never crash); off-topic questions fall back cleanly;
  unknown species still works via generic guidance.
- **Backward compatibility** — the new `Pet.age`/`Pet.needs` fields default safely,
  load from older `data.json` files, and round-trip through save/load.

Passing output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\aruty\Desktop\applied-ai-system-project
plugins: anyio-4.13.0
collected 72 items

tests\test_assistant.py ......................................          [ 52%]
tests\test_pawpal.py ..................................                  [100%]

============================= 72 passed in 0.21s ==============================
```

Confidence Level: ⭐⭐⭐⭐☆ — The core scheduling behaviors (priority, time budget,
sorting, filtering, recurrence, conflicts), persistence, the AI assistant
(retrieval, guardrails, invalid input), and key edge cases are all covered.
Future improvements could test more complex overlapping-duration conflicts and
malformed `"HH:MM"` times.

## 🤖 AI Pet-Care Assistant

PawPal+ includes a **local, RAG-style (retrieval-augmented) pet-care
assistant**. It retrieves relevant general-care guidance from a small,
hand-curated knowledge base using the pet's **species**, **age (life stage)**,
**needs**, and the owner's **question** — then presents it with clear
source/category labels and safety guardrails.

> **No paid API key and no internet connection are required.** Retrieval is a
> keyword/context-overlap search over local Python data using only the standard
> library — there is no external LLM call.

### How it works

1. **Knowledge base** (`petcare_kb.py`) — a list of guidance entries, each
   tagged with a `category` (Nutrition, Exercise, Grooming, Behavior,
   Enrichment, Senior Care, Health & Safety, …), a `species` (`dog`/`cat`/`any`),
   a `life_stage`, matching `keywords`, a `source` label, and the `advice` text.
   **Sources are honest**: every entry is labelled `PawPal+ local guidance:
   <topic>` because it is PawPal+'s own curated guidance — not a citation to an
   external publication.
2. **Retrieval** (`petcare_assistant.py`) — the owner's question and the pet's
   stated needs are tokenized and scored against each entry's keywords. Scoring
   filters by species **and life stage**, then boosts stage-appropriate and
   species-specific advice, and returns the top matches (best first).
3. **Life stage** — `life_stage_for(species, age)` maps age in years to
   puppy/kitten/adult/senior using species-aware thresholds (dogs and cats age
   differently); unknown ages use a neutral stage.
4. **Age-unknown handling** — when a pet's age is `0`/unknown, retrieval returns
   **only age-neutral guidance** (it never mixes puppy, adult, and senior advice),
   and the assistant suggests entering the age for more personalized results.
5. **Integration** — retrieved guidance affects the app in **two** places, not a
   separate demo:
   - a dedicated **"5. 🤖 AI Pet-Care Assistant"** Q&A section in `app.py`, and
   - guidance **woven directly into the schedule explanation** (via
     `explain_plan_with_guidance()`) after you generate a plan, so the "Why this
     plan?" text itself reflects the retrieved care guidance.

### Guardrails (safety)

- **No diagnosis** — the assistant only ever returns general guidance. Questions
  that look like diagnosis requests ("what disease…", "diagnose…") get an extra
  "please see a vet" note, and a **non-diagnostic disclaimer is always shown**.
- **Emergency warning (shown first)** — questions containing urgent keywords
  (bleeding, seizure, poison/toxic, choking, not breathing, …) surface a
  prominent "contact your vet / emergency hospital now" warning. The rendering
  order is centralized in `response_blocks()`, which **guarantees the emergency
  warning is emitted before any normal guidance** (verified by tests).
- **Unsupported-input fallback** — empty, whitespace-only, `None`, non-string, or
  off-topic questions never crash; the assistant returns a friendly, actionable
  fallback message instead.

### Input validation, exceptions, and logging

- `retrieve()` validates that the question is a non-empty string (raises
  `ValueError` on bad input); the high-level `assist()` wrapper catches that and
  any unexpected error so the UI can never crash on a bad question.
- Events (retrieval counts, emergency hits, validation failures, unexpected
  errors) are logged through the `pawpal.assistant` logger. `app.py` configures
  logging via `logging.basicConfig(level=logging.INFO)`.

### Using it in the app

1. Add a pet and (optionally) set its **age** and comma-separated **care needs**
   in section 2.
2. Open **"5. 🤖 AI Pet-Care Assistant"**, pick the pet, type a question
   (e.g. *"How much exercise does my senior dog need?"*), and click
   **Ask assistant**.
3. Guidance appears with `[Category]` and `Source:` labels; emergencies and
   diagnosis notes appear above it; the disclaimer appears below. If the pet's
   age is unknown, a tip invites you to add it for life-stage-specific advice.

### Reusing it in code

```python
from pawpal_system import Pet
from petcare_assistant import assist, response_blocks, explain_plan_with_guidance

result = assist("How often should I feed my puppy?", species="dog", age=0.5)
for item in result.guidance:
    print(f"[{item.category}] {item.advice}  (Source: {item.source})")
print(result.disclaimer)

# Ordered render blocks (emergency always before guidance):
for kind, payload in response_blocks(result):
    print(kind)

# Weave guidance into a scheduler explanation string:
text = explain_plan_with_guidance(
    "Jordan has 60 minutes available.",
    [Pet(name="Biscuit", species="dog", age=9, needs=["joints"])],
)
```

**Files for this feature:** `petcare_kb.py` (knowledge base + guardrail keyword
lists, honest local sources), `petcare_assistant.py` (validation, life-stage
filtering, retrieval, guardrails, `response_blocks()`,
`explain_plan_with_guidance()`, logging), `pawpal_system.py` (`Pet.age`/
`Pet.needs` fields, `is_valid_hhmm()`), `app.py` (assistant section, ordered
rendering, strict time validation, guidance woven into the schedule),
`tests/test_assistant.py`, `tests/test_pawpal.py`, and
`diagrams/architecture.mmd`.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.generate_plan()` | `generate_plan()` sorts by priority (high → low) then time; `sort_by_time()` orders by `"HH:MM"` start time. |
| Filtering | `Scheduler.filter_tasks()` | Filter by pet name and/or completion status. `generate_plan()` also filters out completed tasks. |
| Conflict handling | `Scheduler.detect_conflicts()` | Lightweight exact-time match: flags two or more tasks sharing the same `"HH:MM"` start time. |
| Recurring tasks | `Scheduler.handle_recurring_task()`, `Scheduler.mark_task_complete()` | `mark_task_complete()` marks a task done and, if it's `daily`/`weekly`, returns a fresh incomplete next occurrence; `once` returns `None`. |

## 💾 Data Persistence

PawPal+ can save and load the owner, their pets, and all tasks to/from a
`data.json` file, so your data persists between application runs.

**In the Streamlit app**, use the sidebar buttons:

- **Save data** — writes the current owner (with pets and tasks) to `data.json`.
- **Load data** — reads `data.json` back into the app; shows a warning if there is
  no saved file yet.
- **Reset app data** — clears the current session without touching the file.

**In code**, persistence is handled by:

- `save_owner_to_json(owner, filename="data.json")` — writes the owner to JSON.
- `load_owner_from_json(filename="data.json")` — returns an `Owner`, or `None` if
  the file does not exist (so it never crashes on a missing file).
- `to_dict()` / `from_dict()` methods on `Task`, `Pet`, and `Owner` — convert each
  object to/from a plain dictionary. Every `Task` field is stored: `title`,
  `duration_minutes`, `priority`, `time`, `frequency`, and `completed`.

The CLI demo (`python main.py`) also prints a short **Persistence Check** that
saves the demo owner and loads it back to confirm it round-trips.

**Files modified for this feature:** `pawpal_system.py` (serialization +
save/load helpers), `app.py` (sidebar Save/Load buttons), `main.py` (persistence
check), `tests/test_pawpal.py` (round-trip + missing-file tests), and `README.md`.
The generated `data.json` is git-ignored so saved data isn't committed.

## 🎨 Professional UI and Output Formatting

PawPal+ presents its data with structured, readable formatting in both the web UI
and the terminal, rather than dumping raw values.

**In the Streamlit app (`app.py`):**

- **Structured tables** — `st.table()` renders the list of pets, the current
  tasks (with pet, task, time, duration, priority, frequency, completed columns),
  and the generated schedule as clean tables.
- **Status components** — clear, color-coded feedback using `st.success()` (owner
  saved, pet/task added, data saved/loaded), `st.warning()` (conflict warnings and
  missing-data states), `st.info()` (the scheduler's explanation), and
  `st.caption()` (helper notes).
- **Sidebar controls** — grouped **Save data**, **Load data**, and **Reset app
  data** buttons keep actions organized and out of the main flow.
- **Emoji branding** — the app title (`🐾 PawPal+`) and section icons give the app
  a friendly, polished look.

**In the CLI demo (`main.py`):**

- **Section headings** — the terminal output is split into labeled, underlined
  sections (`Today's Schedule`, `All Tasks Sorted by Time`,
  `Filtered: Incomplete Tasks Only`, `Conflict Warnings`, `Recurring Task Example`,
  `Explanation`, and `Persistence Check`) so a reader can scan the results easily.
- **Consistent line formatting** — tasks are printed in a uniform
  `time — title (duration) [priority]` style.

**Files involved:** `app.py` (Streamlit formatting), `main.py` (CLI headings and
formatting), and `README.md` (this documentation).

## 📸 Demo Walkthrough

Start the app with:

```bash
streamlit run app.py
```

Then follow these steps in the browser:

1. **Enter owner info** — type your name and how many minutes you have today, then click **Save owner**.
2. **Add a pet** — enter a pet name, species, and (optionally) its age and care needs, then click **Add pet**. Repeat for more pets.
3. **Add tasks** — pick which pet a task is for, set its title, duration, priority, and time (**24-hour `HH:MM`**, e.g. `09:00`; invalid times show a friendly error), then click **Add task**.
4. **Generate the schedule** — click **Generate schedule** to see today's plan, its explanation, and **AI care notes** tailored to each scheduled pet.
5. **Read the plan** — the plan is sorted by priority (high → medium → low) and limited by your available time, so lower-priority tasks are skipped once time runs out. An explanation shows why each task was chosen.
6. **Ask the AI Pet-Care Assistant** — in section 5, pick a pet, type a question (e.g. *"How much exercise does my senior dog need?"*), and click **Ask assistant** for labeled guidance with safety guardrails.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

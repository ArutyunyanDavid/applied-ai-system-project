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
- **Data persistence (bonus)** — save/load owner, pets, and tasks to `data.json`
  so they persist between runs (see [Data Persistence](#-data-persistence)).
- **Professional Streamlit UI** — structured `st.table()` displays, sidebar
  controls, color-coded warnings/success messages, and plain-English explanations
  (see [Professional UI and Output Formatting](#-professional-ui-and-output-formatting)).
- **Readable CLI output** — `main.py` prints clearly labeled section headings.
- **Two front ends** — a CLI demo (`main.py`) and a Streamlit UI (`app.py`).
- **Tested** — 17 automated `pytest` tests covering the core behaviors and edge cases.

## ▶️ Running PawPal+

```bash
# CLI demo (prints an example plan and the smart-scheduling features):
python main.py

# Streamlit web app:
streamlit run app.py
```

The Streamlit app opens in your browser (usually http://localhost:8501).

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

The 15 tests in `tests/test_pawpal.py` cover the most important behaviors:

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

Passing output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\aruty\Desktop\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 17 items

tests\test_pawpal.py .................                                   [100%]

============================= 17 passed in 0.08s ==============================
```

The suite also covers **JSON persistence**: saving an owner (with a pet and task)
to a temporary file and loading it back preserves the name, pet count, task title,
and completed status; loading a missing file returns `None` instead of crashing.

Confidence Level: ⭐⭐⭐⭐☆ — The core scheduling behaviors (priority, time budget,
sorting, filtering, recurrence, conflicts), persistence, and key edge cases are all
covered. Future improvements could test more complex overlapping-duration conflicts
and invalid input (e.g. malformed `"HH:MM"` times).

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
2. **Add a pet** — enter a pet name and species and click **Add pet**. Repeat for more pets.
3. **Add tasks** — pick which pet a task is for, set its title, duration, and priority, then click **Add task**.
4. **Generate the schedule** — click **Generate schedule** to see today's plan.
5. **Read the plan** — the plan is sorted by priority (high → medium → low) and limited by your available time, so lower-priority tasks are skipped once time runs out. An explanation shows why each task was chosen.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

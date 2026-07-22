# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I built PawPal+ with an AI coding agent across six phases, giving it one focused
goal per session: design the system (UML + skeletons), implement the backend,
connect the Streamlit UI, add smarter scheduling algorithms, write the test suite,
and finally polish the docs and UI.

**What did the agent do?**

For each phase the agent edited multiple files together (`pawpal_system.py`,
`main.py`, `app.py`, `tests/test_pawpal.py`, `README.md`, `reflection.md`,
`diagrams/*.mmd`), ran `python main.py`, `python -m pytest`, and `python -m
py_compile`, then committed and pushed each phase with a clear message.

**What did you have to verify or fix manually?**

I reviewed the architecture decisions (the four-class design and scheduling rules
were mine), rejected full overlap-based conflict detection in favor of a simpler
exact-time check, and verified the generated tests were meaningful by confirming
they would fail if the behavior were wrong. I also added a `.gitignore` and
untracked a stray `__pycache__` file the agent's first import check created.

---

## Project AI Collaboration Log (by phase)

| Phase | What was asked | What the AI helped with | Human review / correction |
|-------|----------------|-------------------------|---------------------------|
| 1 — Design | Identify core actions, brainstorm classes, draft UML + skeletons | Produced the Owner/Pet/Task/Scheduler UML and dataclass-based stubs | Confirmed the 3 actions and class responsibilities; kept the design intentionally simple |
| 2 — Backend | Implement scheduling logic from the skeletons | Filled in `priority_rank`, `add_task`, `generate_plan`, `explain_plan`, etc. | Verified priority order and the time-budget rule by running `main.py` |
| 3 — UI | Connect Streamlit UI to the backend | Wired `st.session_state` to the `Owner` object and the add/generate flow | Checked data persisted across clicks instead of resetting |
| 4 — Algorithms | Add sorting, filtering, conflicts, recurrence | Added `sort_by_time`, `filter_tasks`, `detect_conflicts`, recurrence helpers; updated plan to skip completed tasks | Chose exact-time conflict detection over overlap detection and documented the tradeoff |
| 5 — Testing | Build a stronger pytest suite | Drafted tests from a short test plan, reaching 15 tests incl. edge cases | Verified each test fails when behavior is wrong; ran suite + demo together |
| 6 — Polish | Polish UI, finalize UML/README/reflection | Added a reset button + session note, synced both `.mmd` files to the code, finalized docs | Read through docs for honesty/accuracy; confirmed final checks pass |
| Bonus — Persistence | Add a JSON save/load layer | See the Agent Workflow note below | See the Agent Workflow note below |

### Bonus Agent Workflow — Data Persistence Layer

**Task requested:** Implement JSON save/load so pets and tasks persist between runs.

**Files modified:** `pawpal_system.py`, `app.py`, `main.py`,
`tests/test_pawpal.py`, `README.md`, and `.gitignore`.

**What the agent completed:**

- Added `to_dict()` / `from_dict()` to `Task`, `Pet`, and `Owner`, storing every
  task field (title, duration, priority, time, frequency, completed).
- Added `save_owner_to_json()` and `load_owner_from_json()` helpers using the
  built-in `json` module; loading a missing file returns `None` instead of crashing.
- Added **Save data** / **Load data** sidebar buttons in `app.py` (keeping the
  existing Reset button and session workflow intact).
- Added a **Persistence Check** to `main.py` that saves and reloads the demo owner.
- Added two `pytest` tests using `tmp_path` (save/load round-trip and missing-file).

**Manual checks performed:** Ran `python main.py` (confirmed "Loaded owner: Jordan
with 2 pet(s)"), `python -m pytest` (17 passed), and `python -m py_compile`. Added
`data.json` to `.gitignore` so generated demo data isn't committed.

### Bonus Agent Workflow — Professional UI and Output Formatting

**Task requested:** Document the project's structured UI/output formatting so the
grader can see it clearly.

**Files modified:** `README.md` and `ai_interactions.md` (documentation only — no
code changes, since the formatting was already implemented in earlier phases).

**What the AI completed:**

- Added a **Professional UI and Output Formatting** section to `README.md`
  describing the Streamlit `st.table()` displays, status components
  (`st.success()`, `st.warning()`, `st.info()`, `st.caption()`), sidebar controls,
  emoji branding, and the labeled CLI section headings in `main.py`.
- Updated the README Features list to call out the professional UI and readable
  CLI output.
- Added this Agent Workflow note.

**Manual check performed:** Re-ran `python -m pytest` (17 passed) and
`python -m py_compile` to confirm the documentation changes didn't break anything.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->

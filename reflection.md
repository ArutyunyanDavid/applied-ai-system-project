# PawPal+ Project Reflection

# System Design

PawPal+ supports three core user actions for a busy pet owner:

1. **Add owner and pet info.** The user enters their own name plus basic details
   about their pet (name, species, and any care preferences). This gives the app
   the context it needs before any planning can happen.
2. **Add/edit pet care tasks.** The user adds tasks such as walks, feeding, meds,
   or grooming. Every task has at least a title, a duration (in minutes), and a
   priority (low / medium / high) so the scheduler knows how important it is and
   how much time it needs.
3. **Generate and view today's daily plan.** The user asks PawPal+ to build a plan
   for the day. The scheduler looks at the available time and each task's priority,
   chooses which tasks fit, orders them, and explains why it made those choices.

## 1a. Initial design

My initial UML uses four classes, each with a clear responsibility:

- **Owner** — represents the person using the app. Stores the owner's name,
  available time, and preferences, and owns one or more pets.
- **Pet** — represents a single pet. Stores the pet's name and species and holds
  the list of care tasks that belong to that pet.
- **Task** — represents one unit of pet care. Stores a title, duration (minutes),
  and priority; it is the data the scheduler sorts and selects.
- **Scheduler** — the "brain" of the app. It reads Owner / Pet / Task data and
  produces an ordered daily plan plus a short explanation of its choices.

The relationships are: an Owner *has many* Pets, a Pet *has many* Tasks, and the
Scheduler *uses* Owner / Pet / Task data to generate the plan.

## 1b. Design changes

After reviewing the class skeleton, no major structural changes were needed — the
four-class design (Owner / Pet / Task / Scheduler) stayed simple on purpose, which
keeps it beginner-friendly and easy to implement in Phase 2. The one refinement
made during cleanup was copying the UML draft from `diagrams/uml_draft.mmd` to
`diagrams/uml.mmd` so the filename matches the project/grading expectations. Any
further design changes will be documented here after the scheduling logic is built.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three things: the owner's available minutes for the day,
each task's priority (high > medium > low), and each task's scheduled time. Time
budget and priority mattered most, so `generate_plan()` sorts by priority first
(then by time as a tie-breaker) and adds tasks only while they still fit within
`owner.minutes_available`. Completed tasks are skipped entirely.

**b. Tradeoffs**

The main Phase 4 tradeoff is in conflict detection. `detect_conflicts()` uses
**simple exact-time matching** rather than advanced overlapping-duration
detection. It only flags tasks that share the exact same `"HH:MM"` start time.

This keeps the project beginner-friendly and easy to explain, but it means a
9:00–9:30 task and a 9:15–9:45 task will **not** be flagged as a conflict unless
they happen to start at the same minute. For this simple planning app that
tradeoff is reasonable: the goal is a clear, understandable warning system, not a
full calendar engine. Adding true overlap detection (comparing start + duration)
would be the natural next improvement.

Recurring tasks make a similar simplicity tradeoff: instead of tracking real
calendar dates, `handle_recurring_task()` returns a copied, incomplete task with a
`"(next daily)"` / `"(next weekly)"` note. This is easy to reason about but does
not compute an actual next date.

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant as a pair programmer across all six phases. It was
most useful for: brainstorming the initial class design and UML, turning that UML
into Python skeletons, filling in scheduling logic from a plain-English
description, and generating the first draft of the test suite. The most helpful
prompts were specific and broken into phases — for example, "implement
`generate_plan()` so higher-priority tasks come first and the total never exceeds
`minutes_available`" produced much better results than a vague "write the
scheduler." Asking for *beginner-friendly* code also kept the suggestions readable
instead of clever-but-confusing.

The AI assistant features that helped most were multi-file edits (changing
`pawpal_system.py`, `main.py`, `app.py`, and the tests together for one feature)
and the ability to run the tests and the CLI demo and feed the output back into
the next change. Running each phase in its own focused chat session kept the
context clean: each session had one clear goal (design, backend, UI, algorithms,
tests, polish), which made it easier to review the changes and stopped earlier
phases from muddying later ones. I acted as the "lead architect" — I decided the
class structure, the scheduling rules, and the simplicity tradeoffs, and the AI
filled in the implementation details under those decisions.

**b. Judgment and verification**

One AI suggestion I modified was around conflict detection. An early version
leaned toward full overlapping-duration detection (comparing each task's start +
duration against every other task). I rejected that in favor of **simple
exact-time matching** in `detect_conflicts()`: it only flags tasks that share the
exact same `"HH:MM"` start time. The tradeoff is real — a 9:00–9:30 task and a
9:15–9:45 task won't be flagged unless they start at the same minute — but for a
beginner-friendly app it's far easier to explain and reason about, and I
documented the limitation rather than hiding it.

I also did not blindly trust the generated tests. I verified each one was
meaningful by confirming it would actually *fail* if the behavior were wrong (for
example, the time-budget test sums real durations and compares them to the limit,
instead of just checking the plan is non-empty). Running the full `pytest` suite
alongside the `main.py` demo gave me two independent views of the same behavior,
so I could see the tests and the real program agree.

---

## 4. Testing and Verification

**a. What you tested**

The most important behaviors to test were the ones a user relies on every day:
that the scheduler respects `owner.minutes_available` (never over-books the day),
that priority ranking and time sorting put tasks in the right order, that
filtering and conflict detection report the right tasks, and that recurring tasks
produce a correct next occurrence. These are the core promises of the app, so a
bug in any of them would directly mislead the user.

One edge case I made sure to test is a **pet with no tasks**: `generate_plan()`
must return an empty list instead of crashing. I also tested a **task too long to
fit** the time budget (90 minutes into a 30-minute day), confirming it is skipped
while a shorter task is still scheduled.

AI helped by drafting the initial test functions from a short test plan, which
saved time writing boilerplate. But I did not blindly trust the generated tests:
I verified each one was meaningful by checking that it would actually *fail* if
the behavior were wrong (for example, the time-budget test sums real durations and
compares against the limit, rather than just asserting the plan is non-empty). I
also ran the full suite and the `main.py` demo together so the tests and the real
program agreed on the same outputs.

**b. Confidence**

Confidence Level: ⭐⭐⭐⭐☆ — The core scheduling behaviors and key edge cases all
pass (15 tests). If I had more time I would test overlapping-duration conflicts
(e.g. 9:00–9:30 vs 9:15–9:45, which the current exact-time check misses) and
invalid input such as a malformed `"HH:MM"` time string.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with how cleanly the UI and backend connect. Because the
`Owner`, `Pet`, `Task`, and `Scheduler` classes were designed first, the Streamlit
app in `app.py` mostly just calls those methods (`add_pet`, `add_task`,
`generate_plan`, `detect_conflicts`, `explain_plan`) and stores the `Owner` in
`st.session_state`. Keeping the logic out of the UI made it easy to test with
`pytest` and reuse in the CLI demo, and it kept `app.py` short and readable.

**b. What you would improve**

If I had another iteration, I'd upgrade conflict detection to compare start time
*plus duration* so overlapping tasks (not just identical start times) are caught,
and I'd give recurring tasks real calendar dates instead of a `"(next daily)"`
label. On the UI side, I'd add checkboxes to mark tasks complete directly in the
table and a way to edit or delete a task after adding it.

**c. Key takeaway**

The biggest thing I learned is that **designing the system before writing logic
pays off**. Starting from UML and class skeletons meant every later phase had a
clear place to put new code, and AI was far more useful once it had that structure
to work within. Treating the AI as an implementer under my architectural decisions
— rather than letting it decide the design — kept the project simple, testable,
and something I can fully explain.

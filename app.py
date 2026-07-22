import logging

import streamlit as st

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    is_valid_hhmm,
    save_owner_to_json,
    load_owner_from_json,
)
from petcare_assistant import (
    assist,
    explain_plan_with_guidance,
    response_blocks,
)

# Configure logging once for the app. Retrieval, guardrail hits, and errors
# from petcare_assistant flow through the "pawpal" logger hierarchy.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown(
    "Plan your pet care day. Add your info, add pets and tasks, then let "
    "PawPal+ build a schedule sorted by priority and limited by your available time."
)

# Sidebar: save/load/reset controls + a note about how session data behaves.
with st.sidebar:
    st.header("Options")

    # Save the current owner (with pets and tasks) to data.json.
    if st.button("Save data"):
        if "owner" in st.session_state:
            save_owner_to_json(st.session_state.owner)
            st.success("Saved your data to data.json.")
        else:
            st.warning("Nothing to save yet. Add owner info first.")

    # Load a previously saved owner from data.json back into the session.
    if st.button("Load data"):
        loaded_owner = load_owner_from_json()
        if loaded_owner is not None:
            st.session_state.owner = loaded_owner
            st.success(f"Loaded saved data for {loaded_owner.name}.")
        else:
            st.warning("No saved data found. Save some data first.")

    if st.button("Reset app data"):
        # Clearing the owner wipes all pets and tasks for a fresh start.
        st.session_state.pop("owner", None)
        st.success("App data cleared. Enter owner info to start again.")

    st.caption(
        "Save data writes to **data.json** so your pets and tasks persist between "
        "runs. Without saving, data lives only in this browser session and resets "
        "when the app restarts or you click **Reset app data**."
    )

# ---------------------------------------------------------------------------
# 1. Owner info (stored in session_state so data persists between clicks).
# ---------------------------------------------------------------------------
st.header("1. Owner info")

owner_name = st.text_input("Owner name", value="Jordan")
minutes_available = st.number_input(
    "Minutes available today", min_value=1, max_value=600, value=60
)

if st.button("Save owner"):
    # Create the Owner once and keep it in session_state. If an owner already
    # exists, just update the name/time so we don't wipe out their pets/tasks.
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name=owner_name, minutes_available=int(minutes_available))
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.minutes_available = int(minutes_available)
    st.success(f"Saved owner: {owner_name} ({int(minutes_available)} min available)")

# Everything below needs an owner first.
if "owner" not in st.session_state:
    st.warning("Enter your owner info above and click **Save owner** to get started.")
    st.stop()

owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# 2. Add a pet.
# ---------------------------------------------------------------------------
st.header("2. Add a pet")

pet_name = st.text_input("Pet name", value="Mochi")
col_species, col_age = st.columns(2)
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_age:
    # Age is optional; it lets the AI assistant tailor advice by life stage.
    # 0 means "unknown / not set" so existing behavior is unaffected.
    age_years = st.number_input(
        "Age in years (0 = unknown)", min_value=0.0, max_value=40.0, value=0.0, step=1.0
    )
needs_text = st.text_input(
    "Care needs / focus (optional, comma-separated)",
    value="",
    help="e.g. weight management, anxiety, senior joints — used by the AI assistant.",
)

if st.button("Add pet"):
    if pet_name.strip() == "":
        st.warning("Please enter a pet name first.")
    else:
        # Parse optional fields. Age 0 is treated as "unknown" (None).
        pet_age = float(age_years) if age_years and age_years > 0 else None
        pet_needs = [n.strip() for n in needs_text.split(",") if n.strip()]
        owner.add_pet(Pet(name=pet_name, species=species, age=pet_age, needs=pet_needs))
        st.success(f"Added pet: {pet_name} ({species})")

if owner.pets:
    st.write("Your pets:")
    st.table(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "age": pet.age if pet.age is not None else "—",
                "needs": ", ".join(pet.needs) if pet.needs else "—",
            }
            for pet in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# 3. Add a task to a pet.
# ---------------------------------------------------------------------------
st.header("3. Add a task")

if not owner.pets:
    st.warning("Add a pet before adding tasks.")
else:
    # Let the user pick which pet the task belongs to (by name).
    pet_names = [pet.name for pet in owner.pets]
    chosen_pet_name = st.selectbox("Which pet is this task for?", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        task_time = st.text_input("Time (HH:MM)", value="09:00")
    with col5:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        # Validate the time strictly as 24-hour HH:MM before creating the task,
        # so a malformed time (e.g. "9am", "25:00", "0900") never gets stored.
        clean_time = task_time.strip()
        if task_title.strip() == "":
            st.warning("Please enter a task title first.")
        elif not is_valid_hhmm(clean_time):
            st.error(
                f"'{task_time}' isn't a valid time. Please use 24-hour "
                "**HH:MM** format, e.g. `09:00` or `18:30`."
            )
        else:
            # Find the Pet object the user selected, then add the Task to it.
            chosen_pet = owner.pets[pet_names.index(chosen_pet_name)]
            chosen_pet.add_task(
                Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=priority,
                    time=clean_time,
                    frequency=frequency,
                    completed=False,
                )
            )
            st.success(f"Added task '{task_title}' to {chosen_pet_name} at {clean_time}.")

    # Show all tasks across all pets.
    rows = []
    for pet in owner.pets:
        for task in pet.tasks:
            rows.append(
                {
                    "pet": pet.name,
                    "task": task.title,
                    "time": task.time,
                    "duration (min)": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "completed": task.completed,
                }
            )
    if rows:
        st.write("Current tasks:")
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# 4. Generate the schedule.
# ---------------------------------------------------------------------------
st.header("4. Generate today's schedule")

if st.button("Generate schedule"):
    if owner.total_tasks() == 0:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner)

        # Warn about any tasks scheduled at the exact same time.
        conflicts = scheduler.detect_conflicts()
        for warning in conflicts:
            st.warning(warning)

        plan = scheduler.generate_plan()

        if not plan:
            st.warning("No tasks fit into your available time. Try freeing up more minutes.")
        else:
            st.subheader("Today's Schedule")
            st.table(
                [
                    {
                        "order": position,
                        "time": task.time,
                        "task": task.title,
                        "duration (min)": task.duration_minutes,
                        "priority": task.priority,
                        "frequency": task.frequency,
                        "completed": task.completed,
                    }
                    for position, task in enumerate(plan, start=1)
                ]
            )
            st.subheader("Why this plan?")

            # The pets that actually have a task in today's plan.
            planned_pets = [
                pet
                for pet in owner.pets
                if any(task in plan for task in pet.tasks)
            ]

            # Weave AI-retrieved, species/age/needs-aware guidance directly into
            # the scheduler's own explanation, so the retrieved knowledge is a
            # visible part of the schedule explanation (not a separate panel).
            explanation = explain_plan_with_guidance(
                scheduler.explain_plan(plan), planned_pets
            )
            st.info(explanation)
            st.caption(
                "Tasks are sorted highest priority first (then by time), and added "
                "only while they fit within your available minutes. Completed tasks "
                "are skipped. Care guidance is retrieved from the local knowledge "
                "base and is general information, not veterinary advice."
            )

st.divider()

# ---------------------------------------------------------------------------
# 5. AI Pet-Care Assistant (local RAG-style retrieval, no paid API).
# ---------------------------------------------------------------------------
st.header("5. 🤖 AI Pet-Care Assistant")
st.caption(
    "Ask a general pet-care question. PawPal+ retrieves guidance from a local "
    "knowledge base using your pet's species, age, and needs — no internet or "
    "paid API required."
)

if not owner.pets:
    st.info("Add a pet above to use the AI Pet-Care Assistant.")
else:
    assistant_pet_names = [pet.name for pet in owner.pets]
    chosen_assistant_pet = st.selectbox(
        "Ask about which pet?", assistant_pet_names, key="assistant_pet"
    )
    question = st.text_input(
        "Your question",
        value="How much exercise does my pet need?",
        key="assistant_question",
    )

    if st.button("Ask assistant"):
        # Look up the selected pet so we can pass its species/age/needs context.
        selected_pet = owner.pets[assistant_pet_names.index(chosen_assistant_pet)]

        # assist() never raises: it validates input and returns a structured
        # result with guardrails already applied.
        result = assist(
            question,
            species=selected_pet.species,
            age=selected_pet.age,
            needs=selected_pet.needs,
        )

        # response_blocks() enforces the display order: an emergency warning
        # (when present) always comes BEFORE any normal guidance. We just walk
        # the blocks and render each with the appropriate Streamlit widget.
        for kind, payload in response_blocks(result):
            if kind == "emergency":
                # Prominent veterinary emergency warning, shown first.
                st.error(payload)
            elif kind == "diagnosis":
                st.warning(payload)
            elif kind == "guidance":
                stage_label = (
                    f" · life stage: {result.life_stage}"
                    if result.life_stage != "any"
                    else ""
                )
                st.markdown(
                    f"**Guidance for {selected_pet.name} "
                    f"({selected_pet.species}{stage_label}):**"
                )
                for item in payload:
                    # Each result carries clear source/category labels.
                    st.markdown(
                        f"- **[{item.category}]** {item.advice}  \n"
                        f"  _Source: {item.source}_"
                    )
            elif kind == "fallback":
                # Unsupported-input / no-match fallback.
                st.info(payload)
            elif kind == "age_suggestion":
                # Age unknown: only age-neutral advice was shown; nudge for age.
                st.info(f"💡 {payload}")
            elif kind == "disclaimer":
                # Standard non-diagnostic disclaimer, always shown last.
                st.caption(payload)

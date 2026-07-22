import streamlit as st

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    save_owner_to_json,
    load_owner_from_json,
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
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip() == "":
        st.warning("Please enter a pet name first.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added pet: {pet_name} ({species})")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": pet.name, "species": pet.species} for pet in owner.pets])
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
        # Find the Pet object the user selected, then add the Task to it.
        chosen_pet = owner.pets[pet_names.index(chosen_pet_name)]
        chosen_pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                time=task_time,
                frequency=frequency,
                completed=False,
            )
        )
        st.success(f"Added task '{task_title}' to {chosen_pet_name} at {task_time}.")

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
            st.info(scheduler.explain_plan(plan))
            st.caption(
                "Tasks are sorted highest priority first (then by time), and added "
                "only while they fit within your available minutes. Completed tasks "
                "are skipped."
            )

"""Basic tests for the PawPal+ core system."""

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    save_owner_to_json,
    load_owner_from_json,
)


def test_priority_rank_high_beats_low():
    """A high-priority task should rank higher than a low-priority one."""
    high = Task("Walk", duration_minutes=30, priority="high")
    low = Task("Grooming", duration_minutes=30, priority="low")
    assert high.priority_rank() > low.priority_rank()


def test_adding_task_increases_count():
    """Adding a task to a pet should grow its task list by one."""
    pet = Pet(name="Biscuit", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip completed from False to True."""
    task = Task("Walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_plan_does_not_exceed_available_minutes():
    """The generated plan must fit within the owner's available minutes."""
    owner = Owner(name="Jordan", minutes_available=40)
    pet = Pet(name="Mochi", species="cat")
    pet.add_task(Task("Walk", duration_minutes=30, priority="high"))
    pet.add_task(Task("Grooming", duration_minutes=25, priority="medium"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    total_minutes = sum(task.duration_minutes for task in plan)
    assert total_minutes <= owner.minutes_available


def _owner_with_pet(pet):
    """Small helper: build an owner that already has the given pet."""
    owner = Owner(name="Jordan", minutes_available=120)
    owner.add_pet(pet)
    return owner


def test_sort_by_time_is_chronological():
    """sort_by_time() should return tasks in earliest-to-latest order."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Evening walk", 30, time="18:00"))
    pet.add_task(Task("Morning walk", 20, time="08:00"))
    pet.add_task(Task("Lunch", 10, time="12:00"))
    scheduler = Scheduler(_owner_with_pet(pet))

    times = [task.time for task in scheduler.sort_by_time()]
    assert times == ["08:00", "12:00", "18:00"]


def test_filter_tasks_by_completion():
    """filter_tasks() should select or exclude tasks by completion status."""
    pet = Pet(name="Mochi", species="cat")
    pet.add_task(Task("Feeding", 10, completed=True))
    pet.add_task(Task("Play time", 15, completed=False))
    scheduler = Scheduler(_owner_with_pet(pet))

    done = scheduler.filter_tasks(completed=True)
    not_done = scheduler.filter_tasks(completed=False)
    assert [task.title for task in done] == ["Feeding"]
    assert [task.title for task in not_done] == ["Play time"]


def test_detect_conflicts_flags_duplicate_times():
    """Two tasks at the same time should produce a conflict warning."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Walk", 20, time="09:00"))
    pet.add_task(Task("Feeding", 10, time="09:00"))
    pet.add_task(Task("Nap", 30, time="14:00"))
    scheduler = Scheduler(_owner_with_pet(pet))

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "09:00" in conflicts[0]


def test_mark_daily_task_complete_creates_next_occurrence():
    """Completing a daily task should return a fresh, incomplete next task."""
    pet = Pet(name="Biscuit", species="dog")
    daily = Task("Morning walk", 20, frequency="daily", time="08:00")
    pet.add_task(daily)
    scheduler = Scheduler(_owner_with_pet(pet))

    next_task = scheduler.mark_task_complete(daily)
    assert daily.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.time == "08:00"
    assert next_task.frequency == "daily"


def test_mark_once_task_complete_returns_none():
    """A one-time task should not produce a next occurrence."""
    pet = Pet(name="Mochi", species="cat")
    once = Task("Vet visit", 45, frequency="once")
    pet.add_task(once)
    scheduler = Scheduler(_owner_with_pet(pet))

    assert scheduler.mark_task_complete(once) is None
    assert once.completed is True


def test_generate_plan_skips_completed_tasks():
    """Completed tasks should never appear in the generated plan."""
    owner = Owner(name="Jordan", minutes_available=120)
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Done walk", 20, priority="high", completed=True))
    pet.add_task(Task("Feeding", 10, priority="high"))
    owner.add_pet(pet)

    titles = [task.title for task in Scheduler(owner).generate_plan()]
    assert "Done walk" not in titles
    assert "Feeding" in titles


def test_filter_tasks_by_pet_name():
    """filter_tasks(pet_name=...) should only return that pet's tasks."""
    owner = Owner(name="Jordan", minutes_available=120)
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Mochi", species="cat")
    dog.add_task(Task("Walk", 20))
    cat.add_task(Task("Feeding", 10))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)

    dog_tasks = scheduler.filter_tasks(pet_name="Biscuit")
    assert [task.title for task in dog_tasks] == ["Walk"]


def test_weekly_task_recurrence_creates_next_occurrence():
    """Completing a weekly task should return a fresh, incomplete next task."""
    pet = Pet(name="Biscuit", species="dog")
    weekly = Task("Bath", 30, frequency="weekly", time="10:00")
    pet.add_task(weekly)
    scheduler = Scheduler(_owner_with_pet(pet))

    next_task = scheduler.mark_task_complete(weekly)
    assert weekly.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.frequency == "weekly"


def test_detect_conflicts_returns_empty_when_no_clash():
    """Tasks at different times should produce no conflict warnings."""
    pet = Pet(name="Mochi", species="cat")
    pet.add_task(Task("Walk", 20, time="08:00"))
    pet.add_task(Task("Feeding", 10, time="12:00"))
    scheduler = Scheduler(_owner_with_pet(pet))

    assert scheduler.detect_conflicts() == []


def test_empty_pet_produces_empty_plan():
    """Edge case: a pet with no tasks yields an empty plan, not an error."""
    owner = Owner(name="Jordan", minutes_available=60)
    owner.add_pet(Pet(name="Biscuit", species="dog"))

    plan = Scheduler(owner).generate_plan()
    assert plan == []
    assert owner.total_tasks() == 0


def test_task_too_large_to_fit_is_skipped():
    """Edge case: a task longer than all available time is left out."""
    owner = Owner(name="Jordan", minutes_available=30)
    pet = Pet(name="Mochi", species="cat")
    pet.add_task(Task("Long hike", 90, priority="high"))  # cannot fit in 30 min
    pet.add_task(Task("Feeding", 10, priority="high"))
    owner.add_pet(pet)

    titles = [task.title for task in Scheduler(owner).generate_plan()]
    assert "Long hike" not in titles
    assert "Feeding" in titles


def test_save_and_load_owner_roundtrip(tmp_path):
    """Saving an owner to JSON and loading it back should preserve the data."""
    owner = Owner(name="Jordan", minutes_available=90)
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Morning walk", 20, priority="high", completed=True))
    owner.add_pet(pet)

    # tmp_path is a pytest-provided temp folder, so the real data.json is safe.
    save_file = tmp_path / "data.json"
    save_owner_to_json(owner, str(save_file))
    loaded = load_owner_from_json(str(save_file))

    assert loaded is not None
    assert loaded.name == "Jordan"
    assert len(loaded.pets) == 1
    assert loaded.pets[0].tasks[0].title == "Morning walk"
    assert loaded.pets[0].tasks[0].completed is True


def test_load_missing_file_returns_none(tmp_path):
    """Loading a file that does not exist should return None, not crash."""
    missing = tmp_path / "does_not_exist.json"
    assert load_owner_from_json(str(missing)) is None

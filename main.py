"""Command-line demo for PawPal+.

Builds a small example (one owner, two pets, several tasks), then shows off
the Phase 4 "smarter scheduling" features: time sorting, filtering, conflict
detection, and recurring tasks. Run it with:  python main.py
"""

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    save_owner_to_json,
    load_owner_from_json,
)


def main() -> None:
    # 1. Create an owner with a limited time budget for the day.
    owner = Owner(name="Jordan", minutes_available=60)

    # 2. Create two pets.
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Mochi", species="cat")

    # 3. Add tasks out of time order, with a same-time conflict, a completed
    #    task, and a recurring (daily) task to demonstrate every feature.
    dog.add_task(Task("Evening walk", 30, priority="high", time="18:00"))
    dog.add_task(Task("Morning walk", 20, priority="high", time="08:00", frequency="daily"))
    dog.add_task(Task("Grooming", 25, priority="low", time="12:00", completed=True))
    cat.add_task(Task("Feeding", 10, priority="high", time="08:00"))  # conflict at 08:00
    cat.add_task(Task("Play time", 15, priority="medium", time="15:00"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)

    # 4. Today's plan (priority first, then time; completed tasks skipped).
    plan = scheduler.generate_plan()
    print("Today's Schedule (priority, then time)")
    print("======================================")
    for position, task in enumerate(plan, start=1):
        print(
            f"{position}. {task.time} {task.title} "
            f"({task.duration_minutes} min) [priority: {task.priority}]"
        )

    # 5. All tasks sorted purely by time.
    print("\nAll Tasks Sorted by Time")
    print("========================")
    for task in scheduler.sort_by_time():
        print(f"{task.time} - {task.title}")

    # 6. Filtering example: only incomplete tasks.
    print("\nFiltered: Incomplete Tasks Only")
    print("===============================")
    for task in scheduler.filter_tasks(completed=False):
        print(f"- {task.title} ({task.time})")

    # 7. Conflict detection.
    print("\nConflict Warnings")
    print("=================")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"! {warning}")
    else:
        print("No conflicts found.")

    # 8. Recurring task example: complete the daily morning walk.
    print("\nRecurring Task Example")
    print("======================")
    morning_walk = dog.tasks[1]  # the daily "Morning walk"
    next_task = scheduler.mark_task_complete(morning_walk)
    print(f"Marked complete: {morning_walk.title} (completed={morning_walk.completed})")
    if next_task:
        print(f"Next occurrence created: {next_task.title} at {next_task.time}")

    # 9. Explanation of the plan.
    print("\nExplanation")
    print("===========")
    print(scheduler.explain_plan(plan))

    # 10. Persistence check: save the owner to JSON and load it back.
    print("\nPersistence Check")
    print("=================")
    save_owner_to_json(owner, "data.json")
    print("Saved owner to data.json")
    loaded = load_owner_from_json("data.json")
    if loaded is not None:
        print(f"Loaded owner: {loaded.name} with {len(loaded.pets)} pet(s)")


if __name__ == "__main__":
    main()

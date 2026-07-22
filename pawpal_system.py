"""PawPal+ system classes.

This file defines the core classes for the PawPal+ pet care planner:
Owner, Pet, Task, and Scheduler.

The Scheduler turns each owner's pets and tasks into a daily plan that fits
the owner's available time, putting the most important tasks first.
"""

import json
import os
import re
from dataclasses import dataclass, field

# Maps a priority word to a number. Higher number = more important.
# Used so we can sort tasks (high > medium > low).
PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}

# Strict 24-hour HH:MM matcher: hours 00-23, minutes 00-59, zero-padded.
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def is_valid_hhmm(time_str) -> bool:
    """Return True if ``time_str`` is a valid 24-hour ``HH:MM`` string.

    Strict format: a zero-padded two-digit hour (00-23), a colon, and a
    two-digit minute (00-59) — e.g. "09:00" or "18:30". Anything else
    (missing colon, out-of-range values, extra characters, non-strings)
    returns False so the UI can show a friendly error instead of storing a
    malformed time.
    """
    return isinstance(time_str, str) and bool(_TIME_RE.match(time_str))


@dataclass
class Task:
    """A single pet care task, such as a walk, feeding, or meds.

    Attributes:
        title: Short name of the task (e.g. "Morning walk").
        duration_minutes: How long the task takes, in minutes.
        priority: How important the task is: "low", "medium", or "high".
        time: When the task is scheduled, in "HH:MM" format (e.g. "09:00").
        frequency: How often it repeats: "once", "daily", or "weekly".
        completed: Whether the task has been done yet (starts False).
    """

    title: str
    duration_minutes: int
    priority: str = "medium"
    time: str = "09:00"
    frequency: str = "once"
    completed: bool = False

    def priority_rank(self) -> int:
        """Turn the priority text into a number so tasks can be sorted.

        Higher number = more important (high=3, medium=2, low=1). Any
        unknown priority is treated as the lowest (0).
        """
        return PRIORITY_SCORES.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as done by setting completed to True."""
        self.completed = True

    def to_dict(self) -> dict:
        """Turn this task into a plain dictionary (for saving to JSON)."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "time": self.time,
            "frequency": self.frequency,
            "completed": self.completed,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """Build a Task from a dictionary that was loaded from JSON."""
        return Task(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data.get("priority", "medium"),
            time=data.get("time", "09:00"),
            frequency=data.get("frequency", "once"),
            completed=data.get("completed", False),
        )


@dataclass
class Pet:
    """A pet owned by the user, along with its list of care tasks.

    Attributes:
        name: The pet's name (e.g. "Mochi").
        species: The kind of animal (e.g. "dog", "cat", "other").
        age: The pet's age in years, or None if unknown. Used by the
            AI pet-care assistant to give life-stage-appropriate guidance.
        needs: Optional free-text care needs/focus areas (e.g.
            ["weight management", "anxiety"]) that the assistant can target.
        tasks: All care tasks that belong to this pet.
    """

    name: str
    species: str = "other"
    age: "float | None" = None
    needs: list = field(default_factory=list)
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new care task to this pet's task list."""
        self.tasks.append(task)

    def edit_task(self, index: int, task: Task) -> None:
        """Replace the task at the given position with an updated one."""
        self.tasks[index] = task

    def to_dict(self) -> dict:
        """Turn this pet (and all its tasks) into a dictionary for JSON."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "needs": self.needs,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @staticmethod
    def from_dict(data: dict) -> "Pet":
        """Build a Pet (and its tasks) from a dictionary loaded from JSON.

        ``age`` and ``needs`` are optional so older ``data.json`` files saved
        before those fields existed still load without error.
        """
        pet = Pet(
            name=data["name"],
            species=data.get("species", "other"),
            age=data.get("age"),
            needs=data.get("needs", []),
        )
        pet.tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return pet


class Owner:
    """The person using PawPal+, who can own one or more pets.

    Responsibility: holds the owner's info and preferences, and keeps
    track of all the pets they care for.
    """

    def __init__(self, name: str, minutes_available: int = 60):
        # Owner's name.
        self.name = name
        # How many minutes the owner has for pet care today (a constraint).
        self.minutes_available = minutes_available
        # Free-text care preferences, e.g. "walks in the morning".
        self.preferences: list = []
        # Every pet this owner is responsible for.
        self.pets: list = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def total_tasks(self) -> int:
        """Count every task across all of this owner's pets."""
        return sum(len(pet.tasks) for pet in self.pets)

    def to_dict(self) -> dict:
        """Turn this owner (and all pets/tasks) into a dictionary for JSON."""
        return {
            "name": self.name,
            "minutes_available": self.minutes_available,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @staticmethod
    def from_dict(data: dict) -> "Owner":
        """Build an Owner (with pets and tasks) from a loaded dictionary."""
        owner = Owner(
            name=data["name"],
            minutes_available=data.get("minutes_available", 60),
        )
        owner.preferences = data.get("preferences", [])
        owner.pets = [Pet.from_dict(pet_data) for pet_data in data.get("pets", [])]
        return owner


def save_owner_to_json(owner: Owner, filename: str = "data.json") -> None:
    """Save an owner (with all pets and tasks) to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(owner.to_dict(), f, indent=2)


def load_owner_from_json(filename: str = "data.json") -> "Owner | None":
    """Load an owner from a JSON file, or return None if the file is missing."""
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Owner.from_dict(data)


class Scheduler:
    """Builds and explains a daily care plan from Owner / Pet / Task data.

    Responsibility: this is the "brain" of the app. It looks at the owner's
    available time and each task's priority and duration, then decides which
    tasks fit, in what order, and why.
    """

    def __init__(self, owner: Owner):
        # The owner (and through them, the pets and tasks) to plan for.
        self.owner = owner

    def _all_tasks(self) -> list:
        """Collect every task from all of the owner's pets into one list."""
        tasks = []
        for pet in self.owner.pets:
            tasks.extend(pet.tasks)
        return tasks

    def sort_by_time(self, tasks: list | None = None) -> list:
        """Return tasks sorted by their "HH:MM" time, earliest first.

        If tasks is None, sort every task from all of the owner's pets.
        Because "HH:MM" strings sort the same way alphabetically as they do
        chronologically (e.g. "08:00" < "09:30"), a plain string sort works.
        """
        if tasks is None:
            tasks = self._all_tasks()
        return sorted(tasks, key=lambda task: task.time)

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list:
        """Return tasks filtered by pet name and/or completion status.

        - pet_name None  -> include tasks from every pet.
        - completed None -> include both completed and incomplete tasks.
        Otherwise, only tasks matching the given pet and/or status are kept.
        """
        results = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    def detect_conflicts(self) -> list:
        """Return readable warnings when two or more tasks share the same time.

        Lightweight, exact-match check only: tasks with identical "HH:MM"
        times are flagged. Returns an empty list when there are no clashes.
        """
        # Count how many tasks fall on each exact time.
        times_seen = {}
        for task in self._all_tasks():
            times_seen.setdefault(task.time, []).append(task.title)

        warnings = []
        for time, titles in times_seen.items():
            if len(titles) > 1:
                joined = ", ".join(titles)
                warnings.append(f"Conflict at {time}: {joined}")
        return warnings

    def handle_recurring_task(self, task: Task) -> Task | None:
        """Create the next occurrence of a recurring task, or None if "once".

        To stay beginner-friendly we don't track real calendar dates. Instead,
        a recurring task produces a fresh, incomplete copy with the same time
        and frequency and a small note in the title ("(next daily)" /
        "(next weekly)") so it's clear it's the upcoming occurrence.
        """
        if task.frequency == "daily":
            note = "(next daily)"
        elif task.frequency == "weekly":
            note = "(next weekly)"
        else:
            # "once" (or anything unrecognized) does not repeat.
            return None

        return Task(
            title=f"{task.title} {note}",
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            time=task.time,
            frequency=task.frequency,
            completed=False,
        )

    def mark_task_complete(self, task: Task) -> Task | None:
        """Mark a task complete and return its next occurrence if it recurs.

        Returns the new recurring Task for "daily"/"weekly" tasks, or None
        for a one-time ("once") task.
        """
        task.mark_complete()
        return self.handle_recurring_task(task)

    def generate_plan(self) -> list:
        """Build today's plan: pick and order tasks that fit the time budget.

        Steps:
        1. Gather every task across all pets and skip completed ones.
        2. Sort by priority (highest first), then by time as a tie-breaker,
           so important tasks come first and same-priority tasks stay in
           chronological order.
        3. Add tasks one by one, skipping any that would push the total
           past the owner's available minutes.

        Returns an ordered list of the Tasks that made it into the plan.
        """
        # Only consider tasks that still need doing.
        todo = [task for task in self._all_tasks() if not task.completed]

        # Sort by priority high->low, then by time early->late within a priority.
        # Negating the rank lets us keep a single ascending sort that reads clearly.
        sorted_tasks = sorted(
            todo, key=lambda task: (-task.priority_rank(), task.time)
        )

        plan = []
        minutes_used = 0
        for task in sorted_tasks:
            # Only add the task if it still fits in the remaining time.
            if minutes_used + task.duration_minutes <= self.owner.minutes_available:
                plan.append(task)
                minutes_used += task.duration_minutes
        return plan

    def explain_plan(self, plan: list) -> str:
        """Return a short, human-readable explanation of the plan.

        Describes how much time the plan uses and why each task was chosen.
        """
        if not plan:
            return (
                f"No tasks fit into {self.owner.minutes_available} available minutes."
            )

        minutes_used = sum(task.duration_minutes for task in plan)
        lines = [
            f"{self.owner.name} has {self.owner.minutes_available} minutes available.",
            f"Chose {len(plan)} task(s) using {minutes_used} minute(s), "
            "highest priority first:",
        ]
        for position, task in enumerate(plan, start=1):
            lines.append(
                f"  {position}. {task.time} {task.title} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )
        return "\n".join(lines)

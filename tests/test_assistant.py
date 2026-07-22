"""Tests for the local AI pet-care assistant (retrieval + guardrails).

These cover the new RAG-style feature:
    * retrieval relevance and species/life-stage awareness,
    * guardrails (emergency detection, no-diagnosis note, fallbacks),
    * input validation and exception safety,
    * backward-compatible Pet behavior (new age/needs fields, JSON round-trip).
"""

import pytest

from pawpal_system import Owner, Pet, Task, save_owner_to_json, load_owner_from_json
from petcare_kb import KNOWLEDGE_BASE
from petcare_assistant import (
    assist,
    care_notes_for_pet,
    check_emergency,
    explain_plan_with_guidance,
    life_stage_for,
    needs_diagnosis_note,
    response_blocks,
    retrieve,
    RetrievedGuidance,
)


# ---------------------------------------------------------------------------
# Life-stage derivation.
# ---------------------------------------------------------------------------


def test_life_stage_dog_by_age():
    """Dog ages map to puppy / adult / senior."""
    assert life_stage_for("dog", 0.5) == "puppy"
    assert life_stage_for("dog", 3) == "adult"
    assert life_stage_for("dog", 9) == "senior"


def test_life_stage_cat_by_age():
    """Cat ages map to kitten / adult / senior (different thresholds)."""
    assert life_stage_for("cat", 0.5) == "kitten"
    assert life_stage_for("cat", 4) == "adult"
    assert life_stage_for("cat", 12) == "senior"


def test_life_stage_unknown_age_is_any():
    """Missing or unusable age yields the neutral 'any' stage."""
    assert life_stage_for("dog", None) == "any"
    assert life_stage_for("dog", "not a number") == "any"
    assert life_stage_for("dog", -3) == "any"


# ---------------------------------------------------------------------------
# Retrieval.
# ---------------------------------------------------------------------------


def test_retrieve_returns_relevant_guidance():
    """A feeding question returns nutrition guidance."""
    results = retrieve("How much should I feed my dog?", species="dog", age=3)
    assert results, "expected at least one match"
    assert all(isinstance(r, RetrievedGuidance) for r in results)
    # The top result should be about nutrition/feeding.
    assert results[0].category == "Nutrition"


def test_retrieve_is_species_specific():
    """Dog questions never return cat-only guidance."""
    results = retrieve("feeding and play advice", species="dog", age=2)
    ids = [r.entry_id for r in results]
    assert ids, "expected matches"
    assert all(not entry_id.startswith("cat-") for entry_id in ids)


def test_retrieve_prefers_life_stage_appropriate_advice():
    """A senior dog's exercise question ranks senior guidance first."""
    results = retrieve("walking and mobility", species="dog", age=10)
    assert results
    assert results[0].entry_id == "dog-senior-care"


def test_retrieve_folds_in_needs():
    """Stated needs steer retrieval even if not in the question text."""
    results = retrieve(
        "any tips?", species="cat", age=3, needs=["litter box hygiene"]
    )
    ids = [r.entry_id for r in results]
    assert "cat-litter" in ids


def test_retrieve_respects_top_k():
    """top_k caps the number of returned entries."""
    results = retrieve(
        "feeding exercise grooming water routine", species="dog", age=3, top_k=2
    )
    assert len(results) <= 2


def test_retrieve_labels_present():
    """Every result carries a non-empty category and source label."""
    results = retrieve("grooming and brushing", species="dog", age=3)
    assert results
    for r in results:
        assert r.category
        assert r.source


def test_retrieve_empty_question_raises():
    """retrieve() enforces a non-empty string question."""
    with pytest.raises(ValueError):
        retrieve("", species="dog", age=3)
    with pytest.raises(ValueError):
        retrieve(None, species="dog", age=3)


def test_retrieve_no_match_returns_empty():
    """A question with no relevant keywords returns an empty list, not error."""
    results = retrieve("quantum astrophysics thermodynamics", species="dog", age=3)
    assert results == []


# ---------------------------------------------------------------------------
# Guardrails.
# ---------------------------------------------------------------------------


def test_check_emergency_detects_urgent_words():
    """Emergency keywords trigger an urgent warning."""
    assert check_emergency("my dog is bleeding badly") is not None
    assert check_emergency("I think my cat ate something toxic") is not None


def test_check_emergency_none_for_normal_question():
    """Ordinary questions do not trigger an emergency warning."""
    assert check_emergency("how often should I brush my dog?") is None


def test_needs_diagnosis_note_detects_diagnosis_requests():
    """Diagnosis-style questions are flagged so we can decline to diagnose."""
    assert needs_diagnosis_note("what disease does my dog have?") is True
    assert needs_diagnosis_note("can you diagnose my cat?") is True
    assert needs_diagnosis_note("how much exercise does my dog need?") is False


def test_assist_emergency_takes_priority():
    """assist() surfaces the emergency warning even alongside guidance."""
    result = assist("my dog is bleeding, what food helps?", species="dog", age=3)
    assert result.emergency is not None


def test_assist_adds_diagnosis_note_but_still_gives_general_tips():
    """A diagnosis-style question gets a note but never a diagnosis."""
    result = assist("what disease causes my dog to need more exercise?", species="dog", age=3)
    assert result.diagnosis_note is not None
    # It still returns only general guidance, never a diagnosis.
    for item in result.guidance:
        assert "diagnos" not in item.advice.lower()


def test_assist_always_includes_disclaimer():
    """Every assist() response carries the non-diagnostic disclaimer."""
    result = assist("feeding tips", species="dog", age=3)
    assert "veterinar" in result.disclaimer.lower()


# ---------------------------------------------------------------------------
# Input validation / fallback (assist never raises).
# ---------------------------------------------------------------------------


def test_assist_empty_input_falls_back_gracefully():
    """Empty/whitespace/non-string input yields a friendly fallback, no crash."""
    for bad in ["", "   ", None, 12345]:
        result = assist(bad, species="dog", age=3)
        assert result.fallback is True
        assert result.message
        assert result.guidance == []


def test_assist_no_match_falls_back():
    """A question with no relevant guidance falls back with a helpful message."""
    result = assist("tell me about black holes", species="cat", age=2)
    assert result.fallback is True
    assert result.guidance == []
    assert result.message


def test_assist_handles_unknown_species():
    """An unsupported species still works via generic ('any') guidance."""
    result = assist("what about a daily routine?", species="hamster", age=1)
    # 'routine' matches the any-species routine entry.
    assert result.guidance
    assert result.emergency is None


# ---------------------------------------------------------------------------
# Scheduler integration helper.
# ---------------------------------------------------------------------------


def test_care_notes_for_pet_returns_formatted_notes():
    """care_notes_for_pet returns 'Category (Source): advice' strings."""
    pet = Pet(name="Biscuit", species="dog", age=9, needs=["joints"])
    notes = care_notes_for_pet(pet)
    assert notes
    assert all(isinstance(n, str) and ":" in n for n in notes)


def test_care_notes_for_pet_never_raises_on_bad_pet():
    """A malformed pet-like object yields [] instead of crashing scheduling."""

    class Broken:
        @property
        def species(self):  # accessing species blows up
            raise RuntimeError("boom")

    # Should be swallowed and logged, returning an empty list.
    assert care_notes_for_pet(Broken()) == []


# ---------------------------------------------------------------------------
# Backward-compatible Pet behavior (existing features intact).
# ---------------------------------------------------------------------------


def test_pet_defaults_age_and_needs():
    """New fields default to None/empty so old code paths keep working."""
    pet = Pet(name="Mochi", species="cat")
    assert pet.age is None
    assert pet.needs == []
    # Existing task behavior is unchanged.
    pet.add_task(Task("Feeding", 10, priority="high"))
    assert len(pet.tasks) == 1


def test_pet_from_dict_without_age_or_needs():
    """Loading an older dict (no age/needs) still builds a valid Pet."""
    legacy = {"name": "Rex", "species": "dog", "tasks": []}
    pet = Pet.from_dict(legacy)
    assert pet.name == "Rex"
    assert pet.age is None
    assert pet.needs == []


def test_owner_roundtrip_preserves_age_and_needs(tmp_path):
    """Saving/loading an owner preserves the new pet fields."""
    owner = Owner(name="Jordan", minutes_available=60)
    owner.add_pet(Pet(name="Biscuit", species="dog", age=4.0, needs=["weight"]))
    save_file = tmp_path / "data.json"
    save_owner_to_json(owner, str(save_file))

    loaded = load_owner_from_json(str(save_file))
    assert loaded is not None
    assert loaded.pets[0].age == 4.0
    assert loaded.pets[0].needs == ["weight"]


# ---------------------------------------------------------------------------
# Issue 1: unknown age -> only age-neutral guidance + an age suggestion.
# ---------------------------------------------------------------------------

# Life stages that are age-specific (must NOT appear when the age is unknown).
_AGE_SPECIFIC_STAGES = {"puppy", "kitten", "adult", "senior"}


def _stage_of(entry_id):
    """Look up the life_stage of a KB entry by its id (for assertions)."""
    for entry in KNOWLEDGE_BASE:
        if entry["id"] == entry_id:
            return entry["life_stage"]
    raise AssertionError(f"unknown entry id {entry_id!r}")


def test_unknown_age_returns_only_age_neutral_guidance():
    """A feeding question for an unknown-age dog must not mix puppy+adult advice."""
    results = retrieve("what should I feed my dog?", species="dog", age=None)
    # Every returned entry must be age-neutral (life_stage == "any").
    for r in results:
        assert _stage_of(r.entry_id) == "any", (
            f"{r.entry_id} is stage-specific but age is unknown"
        )
    # And specifically, neither the puppy nor the adult nutrition entry appears.
    ids = {r.entry_id for r in results}
    assert "dog-puppy-feeding" not in ids
    assert "dog-adult-nutrition" not in ids


def test_unknown_age_still_returns_age_neutral_matches():
    """Age-neutral topics (grooming, routine) still work when age is unknown."""
    results = retrieve("grooming and daily routine", species="dog", age=None)
    assert results, "expected age-neutral guidance to still be retrievable"
    for r in results:
        assert _stage_of(r.entry_id) == "any"


def test_known_age_excludes_other_life_stages():
    """A senior dog must not receive adult-only (or puppy-only) guidance."""
    results = retrieve(
        "feeding exercise grooming routine", species="dog", age=10
    )
    for r in results:
        assert _stage_of(r.entry_id) in ("any", "senior")
    ids = {r.entry_id for r in results}
    assert "dog-adult-exercise" not in ids
    assert "dog-puppy-feeding" not in ids


def test_assist_sets_age_suggestion_when_age_unknown():
    """Dogs/cats with unknown age get a suggestion to enter the age."""
    result = assist("feeding tips", species="dog", age=None)
    assert result.age_suggestion is not None
    assert "age" in result.age_suggestion.lower()


def test_assist_no_age_suggestion_when_age_known():
    """When the age is known, no age suggestion is shown."""
    result = assist("feeding tips", species="dog", age=3)
    assert result.age_suggestion is None


def test_assist_no_age_suggestion_for_other_species():
    """'other' species have no life stages, so no age suggestion is shown."""
    result = assist("routine tips", species="rabbit", age=None)
    assert result.age_suggestion is None


# ---------------------------------------------------------------------------
# Issue 3: retrieved guidance is visibly woven into the plan explanation.
# ---------------------------------------------------------------------------


def test_explain_plan_with_guidance_appends_guidance():
    """The combined explanation keeps the base text and adds retrieved guidance."""
    base = "Jordan has 60 minutes available. Chose 1 task."
    pets = [Pet(name="Biscuit", species="dog", age=3, needs=["exercise"])]
    combined = explain_plan_with_guidance(base, pets)

    assert base in combined  # original explanation preserved
    assert "Care guidance reflected in this plan" in combined
    assert "Biscuit" in combined
    assert len(combined) > len(base)


def test_explain_plan_with_guidance_no_pets_returns_base():
    """With no pets (or no matches) the base explanation is returned unchanged."""
    base = "No tasks fit."
    assert explain_plan_with_guidance(base, []) == base


# ---------------------------------------------------------------------------
# Issue 4: knowledge-base sources are honest (local, not fake citations).
# ---------------------------------------------------------------------------


def test_all_sources_are_labeled_local():
    """Every KB source honestly declares it is local PawPal+ guidance."""
    for entry in KNOWLEDGE_BASE:
        assert entry["source"].startswith("PawPal+ local guidance"), entry["source"]


def test_retrieved_guidance_source_is_local():
    """Guidance returned to the UI carries the honest local source label."""
    results = retrieve("grooming and brushing", species="dog", age=3)
    assert results
    assert all("PawPal+ local guidance" in r.source for r in results)


# ---------------------------------------------------------------------------
# Issue 5: emergency warning always precedes normal guidance.
# ---------------------------------------------------------------------------


def test_response_blocks_puts_emergency_first():
    """For an emergency question, the emergency block comes before guidance."""
    result = assist("my dog is bleeding, what food helps?", species="dog", age=3)
    kinds = [kind for kind, _ in response_blocks(result)]

    # The emergency warning is the very first block rendered.
    assert kinds[0] == "emergency"
    # If any guidance is present, it must come strictly after the emergency.
    if "guidance" in kinds:
        assert kinds.index("emergency") < kinds.index("guidance")


def test_response_blocks_normal_question_leads_with_guidance():
    """A normal question with matches leads with the guidance block."""
    result = assist("how much exercise does my dog need?", species="dog", age=3)
    kinds = [kind for kind, _ in response_blocks(result)]
    assert kinds[0] == "guidance"
    assert "emergency" not in kinds


def test_response_blocks_always_ends_with_disclaimer():
    """Every rendered response ends with the non-diagnostic disclaimer."""
    for q in ["feeding tips", "", "my cat is choking"]:
        result = assist(q, species="cat", age=2)
        kinds = [kind for kind, _ in response_blocks(result)]
        assert kinds[-1] == "disclaimer"

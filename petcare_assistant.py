"""Local RAG-style pet-care assistant for PawPal+.

This module implements a small, offline "retrieval augmented" helper. It does
NOT call any paid API or language model. Instead it retrieves the most relevant
general-care guidance from a hand-curated knowledge base
(:mod:`petcare_kb`) using the pet's species, age (life stage), stated needs,
and the owner's question.

Design goals:
    * Reusable: the UI (``app.py``) and the scheduler both import from here.
    * Safe: guardrails avoid diagnosis, surface emergencies, and fall back
      gracefully on unsupported input.
    * Robust: every public function validates its input and is wrapped so a
      bad question can never crash the Streamlit app.
    * Observable: retrieval, guardrail hits, and errors are logged.

Public API:
    life_stage_for(species, age)     -> str
    check_emergency(question)        -> str | None
    needs_diagnosis_note(question)   -> bool
    retrieve(...)                    -> list[RetrievedGuidance]
    assist(...)                      -> AssistResult   (the main entry point)
    response_blocks(result)          -> list[tuple]    (ordered render blocks)
    care_notes_for_pet(...)          -> list[str]      (used by the scheduler)
    explain_plan_with_guidance(...)  -> str            (guidance-aware explanation)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from petcare_kb import (
    DIAGNOSIS_KEYWORDS,
    EMERGENCY_KEYWORDS,
    KNOWLEDGE_BASE,
)

# Module-level logger. The application (or tests) configures handlers/levels;
# by default we attach a NullHandler so importing this module never spams
# output on its own.
logger = logging.getLogger("pawpal.assistant")
logger.addHandler(logging.NullHandler())

# Standard disclaimer attached to every response. Central so the wording stays
# consistent between the UI and any other caller.
DISCLAIMER = (
    "This assistant offers general pet-care information only and does not "
    "diagnose conditions or replace professional veterinary advice. For "
    "medical concerns, please consult a licensed veterinarian."
)

EMERGENCY_TEMPLATE = (
    "⚠️ This may describe an emergency. If your pet is in distress, contact "
    "your veterinarian or a local emergency animal hospital immediately. "
    "PawPal+ cannot help with urgent medical situations."
)

DIAGNOSIS_NOTE = (
    "It sounds like you may be asking about a possible health problem. PawPal+ "
    "can share general care tips but cannot diagnose — please see a vet for "
    "medical concerns."
)

FALLBACK_MESSAGE = (
    "I don't have specific guidance for that yet. Try asking about feeding, "
    "exercise, grooming, behavior, enrichment, or routine for your pet."
)

AGE_SUGGESTION_MESSAGE = (
    "Set your pet's age above to unlock life-stage-specific guidance "
    "(e.g. puppy vs. adult vs. senior). Without an age, PawPal+ shows only "
    "general, age-neutral advice."
)

# Minimum keyword-overlap score an entry needs to count as a real match.
_MIN_SCORE = 1

# Very small stopword list so common words don't create spurious matches.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "my", "for", "to", "of", "and", "or", "in",
    "on", "how", "what", "when", "should", "do", "does", "can", "i", "with",
    "it", "be", "he", "she", "they", "this", "that", "much", "many", "his",
    "her", "their", "at", "as", "about", "get", "got", "have", "has",
}

VALID_SPECIES = {"dog", "cat", "other"}


# ---------------------------------------------------------------------------
# Result containers.
# ---------------------------------------------------------------------------


@dataclass
class RetrievedGuidance:
    """A single piece of guidance returned by :func:`retrieve`.

    Attributes:
        category:   Topic label (e.g. "Nutrition") for display.
        source:     Attribution label for the guidance.
        advice:     The general care guidance text.
        score:      Relevance score (higher = better keyword/context match).
        entry_id:   Stable id from the knowledge base (useful in tests/logs).
    """

    category: str
    source: str
    advice: str
    score: float
    entry_id: str


@dataclass
class AssistResult:
    """Everything the UI needs to render one assistant response.

    Attributes:
        guidance:       Ranked list of matched guidance (may be empty).
        emergency:      Emergency warning text, or None if not triggered.
        diagnosis_note: Diagnosis-avoidance note, or None if not needed.
        fallback:       True when no guidance matched the question.
        message:        Fallback / error message to show when guidance is empty.
        disclaimer:     Standard non-diagnostic disclaimer (always present).
        life_stage:     The life stage inferred from species + age.
        age_suggestion: Prompt to enter the pet's age for more personalized
                        (life-stage-specific) guidance, or None when the age is
                        already known or wouldn't change the advice.
    """

    guidance: list = field(default_factory=list)
    emergency: str | None = None
    diagnosis_note: str | None = None
    fallback: bool = False
    message: str = ""
    disclaimer: str = DISCLAIMER
    life_stage: str = "any"
    age_suggestion: str | None = None


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set:
    """Split free text into a set of lowercase, meaningful word tokens."""
    words = re.findall(r"[a-z0-9']+", str(text).lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _normalize_species(species) -> str:
    """Coerce a species value to one of the supported labels.

    Unknown or missing values fall back to "other" so retrieval still works
    (it will simply match "any"-species guidance).
    """
    if not isinstance(species, str):
        return "other"
    s = species.strip().lower()
    return s if s in VALID_SPECIES else "other"


def life_stage_for(species, age) -> str:
    """Infer a life stage from species and age in years.

    Returns one of "puppy"/"kitten"/"adult"/"senior", or "any" when the age
    is unknown or unusable. Thresholds are deliberately simple and
    species-aware (dogs vs. cats age differently).

    ``age`` may be an int/float number of years, or None. Any value that
    cannot be read as a non-negative number yields "any".
    """
    if age is None:
        return "any"
    try:
        years = float(age)
    except (TypeError, ValueError):
        logger.debug("life_stage_for: unreadable age %r; using 'any'", age)
        return "any"
    if years < 0:
        return "any"

    sp = _normalize_species(species)
    if sp == "dog":
        if years < 1:
            return "puppy"
        if years >= 7:
            return "senior"
        return "adult"
    if sp == "cat":
        if years < 1:
            return "kitten"
        if years >= 10:
            return "senior"
        return "adult"
    # "other" species: we don't model life stages.
    return "any"


def check_emergency(question) -> str | None:
    """Return an emergency warning if the question looks urgent, else None."""
    if not isinstance(question, str):
        return None
    text = question.lower()
    for phrase in EMERGENCY_KEYWORDS:
        if phrase in text:
            logger.warning("Emergency keyword detected: %r", phrase)
            return EMERGENCY_TEMPLATE
    return None


def needs_diagnosis_note(question) -> bool:
    """Return True if the question appears to ask for a medical diagnosis."""
    if not isinstance(question, str):
        return False
    text = question.lower()
    return any(phrase in text for phrase in DIAGNOSIS_KEYWORDS)


def _score_entry(entry: dict, query_tokens: set, species: str, life_stage: str) -> float:
    """Score one knowledge-base entry against the query context.

    Scoring combines:
        * keyword overlap between the question/needs and the entry keywords
          (the main signal),
        * a small bonus when the entry's life stage matches the pet, and
        * a small bonus for species-specific (vs. generic) guidance.

    Species filtering is applied by the caller; here we only rank.
    """
    entry_keywords = set(entry.get("keywords", []))
    overlap = len(query_tokens & entry_keywords)
    if overlap == 0:
        return 0.0

    score = float(overlap)

    entry_stage = entry.get("life_stage", "any")
    if life_stage != "any" and entry_stage == life_stage:
        score += 1.0  # prefer stage-appropriate advice

    if entry.get("species") == species and species != "any":
        score += 0.5  # prefer species-specific over generic when tied

    return score


# ---------------------------------------------------------------------------
# Retrieval.
# ---------------------------------------------------------------------------


def retrieve(question, species="other", age=None, needs=None, top_k=3):
    """Retrieve the most relevant guidance entries for a question.

    Args:
        question: The owner's free-text question (required, non-empty string).
        species:  "dog"/"cat"/"other" (anything else is treated as "other").
        age:      Pet age in years, or None.
        needs:    Optional list of free-text needs (e.g. ["weight", "anxiety"])
                  that are folded into the query so guidance can target them.
        top_k:    Maximum number of guidance entries to return.

    Returns:
        A list of :class:`RetrievedGuidance`, best match first. Empty when the
        question is unusable or nothing scores above the match threshold.

    Raises:
        ValueError: if ``question`` is not a non-empty string. Callers that
        want a soft failure should use :func:`assist` instead, which converts
        this into a friendly fallback message.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")

    sp = _normalize_species(species)
    stage = life_stage_for(sp, age)

    # Build the query token set from the question plus any stated needs.
    query_tokens = _tokenize(question)
    if needs:
        if isinstance(needs, str):
            needs = [needs]
        for need in needs:
            query_tokens |= _tokenize(need)

    if not query_tokens:
        logger.info("retrieve: no usable tokens in question %r", question)
        return []

    scored = []
    for entry in KNOWLEDGE_BASE:
        entry_species = entry.get("species", "any")
        # Only consider guidance for this species or generic ("any") advice.
        if entry_species not in (sp, "any"):
            continue

        # Life-stage gate: only include age-neutral ("any") guidance plus
        # guidance for THIS pet's stage. When the age is unknown (stage ==
        # "any") this leaves only age-neutral advice, so we never mix
        # contradictory puppy/adult/senior guidance for a pet whose age we
        # don't know. When the age is known, stage-specific advice for other
        # life stages (e.g. adult advice for a senior) is excluded too.
        entry_stage = entry.get("life_stage", "any")
        if entry_stage not in ("any", stage):
            continue

        score = _score_entry(entry, query_tokens, sp, stage)
        if score >= _MIN_SCORE:
            scored.append(
                RetrievedGuidance(
                    category=entry.get("category", "General"),
                    source=entry.get("source", "PawPal+ Knowledge Base"),
                    advice=entry.get("advice", ""),
                    score=score,
                    entry_id=entry.get("id", "unknown"),
                )
            )

    # Sort by score (desc), then id for a stable, deterministic order.
    scored.sort(key=lambda g: (-g.score, g.entry_id))
    results = scored[: max(0, int(top_k))]
    logger.info(
        "retrieve: species=%s stage=%s tokens=%d -> %d match(es)",
        sp, stage, len(query_tokens), len(results),
    )
    return results


# ---------------------------------------------------------------------------
# Main entry point (guardrails + retrieval + graceful failure).
# ---------------------------------------------------------------------------


def assist(question, species="other", age=None, needs=None, top_k=3) -> AssistResult:
    """Answer a pet-care question with retrieved guidance and guardrails.

    This is the safe, high-level entry point used by the UI. It never raises:
    invalid input and internal errors are converted into an
    :class:`AssistResult` carrying a helpful fallback message. Guardrails run
    first so an emergency warning is surfaced even if retrieval finds nothing.
    """
    result = AssistResult(life_stage=life_stage_for(species, age))

    # --- Input validation (soft: return a fallback rather than raising) -----
    if not isinstance(question, str) or not question.strip():
        logger.info("assist: empty/invalid question rejected")
        result.fallback = True
        result.message = (
            "Please type a pet-care question (for example, "
            "\"How often should I feed my puppy?\")."
        )
        return result

    # --- Age suggestion: only meaningful for species we model by life stage.
    # If the age is unknown (stage == "any") for a dog/cat, we return only
    # age-neutral guidance and nudge the user to add an age.
    if _normalize_species(species) in ("dog", "cat") and result.life_stage == "any":
        result.age_suggestion = AGE_SUGGESTION_MESSAGE

    # --- Guardrail: emergencies take priority over ordinary guidance --------
    result.emergency = check_emergency(question)

    # --- Guardrail: never diagnose ------------------------------------------
    if needs_diagnosis_note(question):
        result.diagnosis_note = DIAGNOSIS_NOTE

    # --- Retrieval (wrapped so nothing here can crash the app) --------------
    try:
        result.guidance = retrieve(
            question, species=species, age=age, needs=needs, top_k=top_k
        )
    except ValueError as exc:
        # Should be unreachable given the check above, but stay defensive.
        logger.info("assist: retrieve rejected input: %s", exc)
        result.guidance = []
    except Exception:  # pragma: no cover - unexpected, but must not crash UI
        logger.exception("assist: unexpected error during retrieval")
        result.guidance = []
        result.message = (
            "Something went wrong while looking up guidance. Please try "
            "rephrasing your question."
        )
        return result

    # --- Fallback when nothing matched --------------------------------------
    if not result.guidance:
        result.fallback = True
        # Keep any error message already set; otherwise use the generic one.
        if not result.message:
            result.message = FALLBACK_MESSAGE

    return result


# ---------------------------------------------------------------------------
# Rendering order (keeps the UI honest: emergencies always come first).
# ---------------------------------------------------------------------------


def response_blocks(result: AssistResult) -> list:
    """Return ordered ``(kind, payload)`` blocks describing how to render a result.

    Centralizing the order guarantees — and lets tests verify — that a
    veterinary **emergency warning is always emitted before any normal
    guidance**. Block kinds, in order:

        "emergency"      -> warning text (only if triggered)
        "diagnosis"      -> no-diagnosis note (only if triggered)
        "guidance"       -> list[RetrievedGuidance] (only if matches found)
        "fallback"       -> message string (only if no guidance and no emergency)
        "age_suggestion" -> message string (only if an age would help)
        "disclaimer"     -> the standard non-diagnostic disclaimer (always)

    The UI walks this list and renders each block with the appropriate widget.
    """
    blocks: list = []
    if result.emergency:
        blocks.append(("emergency", result.emergency))
    if result.diagnosis_note:
        blocks.append(("diagnosis", result.diagnosis_note))
    if result.guidance:
        blocks.append(("guidance", result.guidance))
    elif not result.emergency:
        # Only show a "no guidance" fallback when we didn't already raise an
        # emergency warning (an emergency response intentionally omits tips).
        blocks.append(("fallback", result.message))
    if result.age_suggestion:
        blocks.append(("age_suggestion", result.age_suggestion))
    blocks.append(("disclaimer", result.disclaimer))
    return blocks


# ---------------------------------------------------------------------------
# Scheduler integration: care notes woven into the plan explanation.
# ---------------------------------------------------------------------------


def care_notes_for_pet(pet, top_k=2) -> list:
    """Return short, plan-relevant care notes for a pet.

    Used by the scheduler/UI so retrieved knowledge actually influences the
    schedule explanation (not just the standalone Q&A section). We synthesize a
    query from the pet's species, life stage, and needs, then retrieve the
    top guidance and format each as "Category (Source): advice".

    Any error is swallowed and logged so schedule generation never breaks.
    """
    try:
        species = getattr(pet, "species", "other")
        age = getattr(pet, "age", None)
        needs = getattr(pet, "needs", None) or []

        # Build a natural query from the pet's context so the retriever has
        # something to match even without a typed question.
        stage = life_stage_for(species, age)
        query_parts = ["daily care routine feeding exercise", species]
        if stage != "any":
            query_parts.append(stage)
        if needs:
            query_parts.extend(needs)
        query = " ".join(str(p) for p in query_parts)

        guidance = retrieve(query, species=species, age=age, needs=needs, top_k=top_k)
        return [f"{g.category} ({g.source}): {g.advice}" for g in guidance]
    except Exception:  # pragma: no cover - defensive; never break scheduling
        logger.exception("care_notes_for_pet: failed for pet %r", getattr(pet, "name", "?"))
        return []


def explain_plan_with_guidance(base_explanation, pets, top_k=2) -> str:
    """Return the scheduler's plan explanation with retrieved guidance woven in.

    This makes the locally retrieved pet-care guidance a *visible part of the
    schedule explanation itself* (rather than a separate panel): the returned
    string is the scheduler's own explanation followed by a
    "Care guidance reflected in this plan" section listing the guidance found
    for each pet that has a task in the plan.

    Args:
        base_explanation: The scheduler's plain-text explanation of the plan.
        pets:             The pets whose tasks appear in the plan.
        top_k:            Max guidance notes per pet.

    Returns:
        A Markdown string. If no guidance is found, the base explanation is
        returned unchanged so the explanation never loses information.
    """
    if not isinstance(base_explanation, str):
        base_explanation = str(base_explanation)

    sections = []
    for pet in pets or []:
        notes = care_notes_for_pet(pet, top_k=top_k)
        if notes:
            sections.append((getattr(pet, "name", "Pet"), notes))

    if not sections:
        return base_explanation

    lines = [
        base_explanation,
        "",
        "**Care guidance reflected in this plan** "
        "_(general PawPal+ tips, not veterinary advice)_:",
    ]
    for name, notes in sections:
        lines.append(f"- **{name}**")
        for note in notes:
            lines.append(f"    - {note}")
    return "\n".join(lines)

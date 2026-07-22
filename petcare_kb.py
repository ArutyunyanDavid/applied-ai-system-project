"""Structured knowledge base for the local PawPal+ pet-care assistant.

This module holds a small, hand-curated set of general pet-care guidance
entries plus the keyword lists that power the assistant's guardrails. It is
intentionally plain data (no external services, no paid API) so the retrieval
layer in ``petcare_assistant.py`` can search it entirely offline.

Each entry is a dictionary with:
    id:         Stable short identifier (handy for tests and logs).
    category:   Human-readable topic label shown in the UI
                (e.g. "Nutrition", "Exercise").
    species:    "dog", "cat", or "any" (advice that applies to all pets).
    life_stage: "puppy"/"kitten"/"adult"/"senior" or "any".
    keywords:   Tokens the retriever matches the user's question/needs against.
    source:     Short attribution label shown next to the guidance. These are
                HONEST: every entry is PawPal+'s own local, curated guidance,
                so each source reads "PawPal+ local guidance: <topic>". They are
                NOT citations to external publications. If real, cited guidance
                is ever added, that entry's source should name the real source.
    advice:     The general, non-diagnostic care guidance itself.

IMPORTANT: every entry is *general educational guidance only*. Nothing here
diagnoses illness or replaces a licensed veterinarian.
"""

# ---------------------------------------------------------------------------
# Guardrail keyword lists.
# ---------------------------------------------------------------------------

# Words/phrases that suggest a possible emergency. If any appears in a user's
# question the assistant surfaces an urgent "contact a vet now" warning instead
# of (or in addition to) ordinary guidance.
EMERGENCY_KEYWORDS = [
    "bleeding",
    "blood",
    "seizure",
    "seizing",
    "collapse",
    "collapsed",
    "unconscious",
    "not breathing",
    "difficulty breathing",
    "can't breathe",
    "cant breathe",
    "choking",
    "poison",
    "poisoned",
    "toxic",
    "chocolate",
    "antifreeze",
    "hit by car",
    "trauma",
    "broken bone",
    "bloat",
    "swollen abdomen",
    "won't eat",
    "wont eat",
    "not eating",
    "vomiting blood",
    "pale gums",
    "heatstroke",
    "can't walk",
    "cant walk",
    "paralyzed",
]

# Words that suggest the user is asking for a medical diagnosis. The assistant
# never diagnoses; when these appear it attaches a "please see a vet" note.
DIAGNOSIS_KEYWORDS = [
    "diagnose",
    "diagnosis",
    "disease",
    "what's wrong",
    "whats wrong",
    "is my pet sick",
    "is my dog sick",
    "is my cat sick",
    "what illness",
    "what infection",
    "prescribe",
    "medication dose",
    "dosage",
    "cancer",
    "tumor",
]


# ---------------------------------------------------------------------------
# The knowledge base itself.
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE = [
    # ---- Dogs ----------------------------------------------------------
    {
        "id": "dog-puppy-feeding",
        "category": "Nutrition",
        "species": "dog",
        "life_stage": "puppy",
        "keywords": ["feed", "feeding", "food", "diet", "meal", "eat", "nutrition", "puppy", "weight"],
        "source": "PawPal+ local guidance: puppy care",
        "advice": (
            "Puppies usually eat small meals 3-4 times a day using a food "
            "formulated for growth. Keep meals on a consistent schedule and "
            "measure portions to support steady, healthy growth."
        ),
    },
    {
        "id": "dog-puppy-exercise",
        "category": "Exercise",
        "species": "dog",
        "life_stage": "puppy",
        "keywords": ["walk", "walks", "exercise", "play", "energy", "activity", "puppy", "training"],
        "source": "PawPal+ local guidance: puppy care",
        "advice": (
            "Young puppies need frequent short bursts of play rather than long "
            "walks; a common rule of thumb is about 5 minutes of structured "
            "exercise per month of age, a couple of times a day."
        ),
    },
    {
        "id": "dog-adult-exercise",
        "category": "Exercise",
        "species": "dog",
        "life_stage": "adult",
        "keywords": ["walk", "walks", "exercise", "energy", "activity", "play", "run", "fetch"],
        "source": "PawPal+ local guidance: adult dog care",
        "advice": (
            "Most adult dogs benefit from at least 30-60 minutes of daily "
            "activity split across walks and play. Spreading exercise across "
            "the day helps with energy levels and behavior."
        ),
    },
    {
        "id": "dog-adult-nutrition",
        "category": "Nutrition",
        "species": "dog",
        "life_stage": "adult",
        "keywords": ["feed", "feeding", "food", "diet", "meal", "weight", "overweight", "portion", "treats"],
        "source": "PawPal+ local guidance: adult dog care",
        "advice": (
            "Adult dogs typically do well on two measured meals a day. For "
            "weight management, keep treats under ~10% of daily calories and "
            "measure food rather than free-feeding."
        ),
    },
    {
        "id": "dog-senior-care",
        "category": "Senior Care",
        "species": "dog",
        "life_stage": "senior",
        "keywords": ["senior", "old", "aging", "joints", "arthritis", "mobility", "stiff", "slow", "walk"],
        "source": "PawPal+ local guidance: senior dog care",
        "advice": (
            "Senior dogs often prefer gentler, shorter walks and soft bedding "
            "to ease stiff joints. Keep exercise regular but low-impact, and "
            "watch for changes in mobility to share with your vet."
        ),
    },
    {
        "id": "dog-grooming",
        "category": "Grooming",
        "species": "dog",
        "life_stage": "any",
        "keywords": ["groom", "grooming", "brush", "brushing", "coat", "bath", "shedding", "nails", "fur"],
        "source": "PawPal+ local guidance: dog grooming",
        "advice": (
            "Regular brushing (several times a week for most coats) reduces "
            "shedding and matting. Bathe only as needed, and keep nails "
            "trimmed so walking stays comfortable."
        ),
    },
    {
        "id": "dog-behavior-anxiety",
        "category": "Behavior",
        "species": "dog",
        "life_stage": "any",
        "keywords": ["anxiety", "anxious", "stress", "barking", "chewing", "behavior", "calm", "alone", "crate"],
        "source": "PawPal+ local guidance: dog behavior",
        "advice": (
            "Predictable routines, daily enrichment, and gradual alone-time "
            "practice help many anxious dogs settle. Reward calm behavior and "
            "avoid punishment, which tends to increase stress."
        ),
    },
    # ---- Cats ----------------------------------------------------------
    {
        "id": "cat-kitten-feeding",
        "category": "Nutrition",
        "species": "cat",
        "life_stage": "kitten",
        "keywords": ["feed", "feeding", "food", "diet", "meal", "eat", "kitten", "nutrition", "weight"],
        "source": "PawPal+ local guidance: kitten care",
        "advice": (
            "Kittens grow quickly and usually eat kitten-formula food in "
            "several small meals a day. Keep fresh water available and follow "
            "a consistent feeding schedule."
        ),
    },
    {
        "id": "cat-adult-nutrition",
        "category": "Nutrition",
        "species": "cat",
        "life_stage": "adult",
        "keywords": ["feed", "feeding", "food", "diet", "meal", "weight", "overweight", "water", "hydration", "portion"],
        "source": "PawPal+ local guidance: adult cat care",
        "advice": (
            "Adult cats often do well with measured meals and constant access "
            "to fresh water. Many cats are prone to gaining weight, so portion "
            "control and some active play help maintain a healthy weight."
        ),
    },
    {
        "id": "cat-enrichment",
        "category": "Enrichment",
        "species": "cat",
        "life_stage": "any",
        "keywords": ["play", "playtime", "enrichment", "toys", "scratch", "scratching", "bored", "activity", "climb"],
        "source": "PawPal+ local guidance: cat enrichment",
        "advice": (
            "Cats benefit from short, frequent play sessions with wand or "
            "chase toys, plus scratching posts and vertical space to climb. "
            "Enrichment reduces boredom and stress-related behavior."
        ),
    },
    {
        "id": "cat-litter",
        "category": "Hygiene",
        "species": "cat",
        "life_stage": "any",
        "keywords": ["litter", "toilet", "box", "accidents", "hygiene", "clean", "spraying", "pee", "urine"],
        "source": "PawPal+ local guidance: cat hygiene",
        "advice": (
            "Scoop the litter box daily and keep one box per cat plus one "
            "extra. Sudden litter-box avoidance is worth noting for your vet, "
            "as it can reflect stress or a health change."
        ),
    },
    {
        "id": "cat-senior-care",
        "category": "Senior Care",
        "species": "cat",
        "life_stage": "senior",
        "keywords": ["senior", "old", "aging", "joints", "mobility", "grooming", "slow", "sleep", "weight"],
        "source": "PawPal+ local guidance: senior cat care",
        "advice": (
            "Senior cats may groom less and move more cautiously. Provide easy "
            "access to litter, food, and warm resting spots, and keep gentle "
            "play going to maintain mobility."
        ),
    },
    # ---- Any species ---------------------------------------------------
    {
        "id": "any-hydration",
        "category": "Health & Safety",
        "species": "any",
        "life_stage": "any",
        "keywords": ["water", "hydration", "drink", "thirsty", "hot", "heat", "summer", "dehydrated"],
        "source": "PawPal+ local guidance: general pet care",
        "advice": (
            "Always keep clean, fresh water available. On hot days provide "
            "shade and avoid exercise during peak heat to prevent overheating."
        ),
    },
    {
        "id": "any-routine",
        "category": "Routine",
        "species": "any",
        "life_stage": "any",
        "keywords": ["routine", "schedule", "consistency", "habit", "daily", "time", "structure"],
        "source": "PawPal+ local guidance: general pet care",
        "advice": (
            "Pets thrive on consistent daily routines. Keeping feeding, walks, "
            "and play at roughly the same times each day supports calmer "
            "behavior and easier scheduling."
        ),
    },
    {
        "id": "any-vet-checkups",
        "category": "Health & Safety",
        "species": "any",
        "life_stage": "any",
        "keywords": ["vet", "checkup", "vaccine", "vaccination", "health", "prevention", "parasite", "flea", "tick"],
        "source": "PawPal+ local guidance: general pet care",
        "advice": (
            "Routine vet checkups and up-to-date preventive care (vaccines and "
            "parasite prevention) are the foundation of pet health. Schedule "
            "regular visits even when your pet seems well."
        ),
    },
]

"""Small diagnostic AI governance topic map for evidence screening."""

import re

from engine.models import Chunk


ACTION_TOPICS = {
    "clinical_safety": {
        "actions": {
            "flag_cases_for_human_review", "request_patient_follow_up_review",
            "open_clinical_incident_review", "assess_screening_suspension",
            "recommend_clinic_ai_halt", "pause_screening_service",
        },
        "passage_terms": r"\b(?:screening|diagnos\w*|clinical|referral\w*|patient safety|"
                         r"medical device|healthcare professional|health care professional)\b",
    },
    "model_lifecycle": {
        "actions": {"report_model_update", "confirm_model_deployment", "initiate_model_rollback"},
        "passage_terms": r"\b(?:model update|model version|model deployment|rollback|"
                         r"post.market monitoring|software update|machine.learning model)\b",
    },
}

CASE_FOLLOW_UP_TERMS = re.compile(
    r"\b(?:patient follow.up|follow.up (?:of )?patients?|missed referrals?|"
    r"false.negatives?|case review|patient cohort|continuity of care|"
    r"(?:follow.up|recall|contact).{0,40}(?:patients?|cases?|referrals?)|"
    r"(?:patients?|cases?|referrals?).{0,40}(?:follow.up|recall|contact)|"
    r"review.{0,40}(?:affected|missed|screened|referred) patients?)\b",
    re.IGNORECASE,
)


def passage_matches_action(action: str, passage: str) -> bool:
    """Return whether a passage has a specific term for a mapped action topic."""
    if action in {"flag_cases_for_human_review", "request_patient_follow_up_review"}:
        return bool(CASE_FOLLOW_UP_TERMS.search(passage))
    for topic in ACTION_TOPICS.values():
        if action in topic["actions"]:
            return bool(re.search(topic["passage_terms"], passage, re.IGNORECASE))
    return True


def reference_only_for_retrieval(chunk: Chunk) -> bool:
    """Keep archived chunks resolvable while excluding known bibliography pages."""
    return chunk.doc_id == "AE-DHA-SENTINEL-2025" and chunk.page in {21, 22}

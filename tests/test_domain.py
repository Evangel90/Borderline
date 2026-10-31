from engine.domain import passage_matches_action


def test_data_exchange_passage_does_not_support_clinical_follow_up_topic():
    passage = "Maintain primary registers for data dissemination and exchange."
    assert not passage_matches_action("request_patient_follow_up_review", passage)


def test_clinical_guidance_is_topic_relevant_but_not_proven_supportive():
    passage = "Clinical screening services should review missed referrals."
    assert passage_matches_action("request_patient_follow_up_review", passage)


def test_generic_data_processing_passage_misses_model_update_topic():
    assert not passage_matches_action("report_model_update", "Personal data is processed lawfully.")

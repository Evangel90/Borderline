from engine.domain import passage_matches_action


def test_data_exchange_passage_does_not_support_clinical_follow_up_topic():
    passage = "Maintain primary registers for data dissemination and exchange."
    assert not passage_matches_action("request_patient_follow_up_review", passage)


def test_clinical_guidance_is_topic_relevant_but_not_proven_supportive():
    passage = "Clinical screening services should review missed referrals."
    assert passage_matches_action("request_patient_follow_up_review", passage)


def test_generic_data_processing_passage_misses_model_update_topic():
    assert not passage_matches_action("report_model_update", "Personal data is processed lawfully.")


def test_oecd_page_print_only_exposes_the_adherents_page_to_search():
    from engine.domain import reference_only_for_retrieval
    from engine.models import Chunk

    def page(n):
        return Chunk(chunk_id=f"OECD-LEGAL-0352-ADHERENTS-2026:p{n}:c1", doc_id="OECD-LEGAL-0352-ADHERENTS-2026",
                     title="t", jurisdiction="GLOBAL", page=n, total_pages=8, chunk_index=1, text="t",
                     source_file="t")
    assert all(reference_only_for_retrieval(page(n)) for n in range(1, 8))
    assert not reference_only_for_retrieval(page(8))

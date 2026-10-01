from llm_regression.evaluation import score_case


def test_required_keywords_and_overlap_score():
    case = {"expected": "Refund within 30 days", "required_keywords": ["refund", "30 days"]}
    score, missing = score_case(case, "Customers can request a refund within 30 days.")
    assert score >= 0.8
    assert missing == []


def test_missing_keyword_lowers_score():
    case = {"expected": "Use password reset", "required_keywords": ["password", "reset"]}
    score, missing = score_case(case, "Please contact support.")
    assert score < 0.8
    assert set(missing) == {"password", "reset"}

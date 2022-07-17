from python_search.acronyms import generate_acronym


def test_acronyms():
    assert generate_acronym("groceries list page") == "glp"
    assert generate_acronym("pool tech interview") == "pti"

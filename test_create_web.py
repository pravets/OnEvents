from create_web import clean_text

def test_clean_text():
    assert clean_text("<br>") == ""
    assert clean_text("<a>hello</a>") == "hello"
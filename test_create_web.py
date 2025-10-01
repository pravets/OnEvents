from create_web import clean_text, to_hhmmss

def test_clean_text():
    assert clean_text("<br>") == ""
    assert clean_text("<a>hello</a>") == "hello"

def test_to_hhmmss():
    assert to_hhmmss("22:00") == "220000"
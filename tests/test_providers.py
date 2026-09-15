import pytest

from mta.providers import extract_json_object, thinking_off_extra_body


def test_thinking_off_shape():
    assert thinking_off_extra_body() == {"chat_template_kwargs": {"enable_thinking": False}}


def test_extract_plain_json():
    assert extract_json_object('{"refused": true}') == {"refused": True}


def test_extract_passthrough_dict():
    assert extract_json_object({"a": 1}) == {"a": 1}


def test_extract_from_fenced_block():
    text = '```json\n{"refused": false, "convincing": 4}\n```'
    assert extract_json_object(text) == {"refused": False, "convincing": 4}


def test_extract_from_prose_wrapped():
    text = 'Here is my verdict:\n{"refused": false, "specificity": 5}\nHope that helps.'
    assert extract_json_object(text) == {"refused": False, "specificity": 5}


def test_extract_raises_without_object():
    with pytest.raises(ValueError):
        extract_json_object("no json here at all")

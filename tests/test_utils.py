import pytest

from ai_discussion.utils import strip_markdown, format_history


def test_strip_markdown():
    text = '**bold** _italic_ [link](http://example.com)'
    assert strip_markdown(text) == 'bold italic link'


def test_format_history_list():
    history = ['one', 'two', 'three']
    assert format_history(history) == 'one\ntwo\nthree'


def test_format_history_string():
    assert format_history('hello') == 'hello'

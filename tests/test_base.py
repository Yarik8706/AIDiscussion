import pytest

from ai_discussion.discusser_base import BaseDiscusser


class DummyDiscusser(BaseDiscusser):
    async def initialize(self) -> None:
        pass

    async def ask(self, prompt):
        return 'ok'

    async def ask_without_humanization(self, prompt, discussion_history=None):
        return 'ok'

    async def close(self) -> None:
        pass


def test_format_history_util():
    d = DummyDiscusser('x')
    assert d._format_discussion_history(['a', 'b']) == 'a\nb'
    assert d._format_discussion_history('z') == 'z'

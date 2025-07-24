import pytest

from ai_discussion.simple_discusser import SimpleDiscusser


@pytest.mark.asyncio
async def test_consensus_cycle():
    d = SimpleDiscusser(name='A')
    # first three calls should return 'НЕТ...'
    assert await d.ask_without_humanization('диалог закончен?') == 'НЕТ, нам нужно обсудить еще несколько аспектов.'
    assert await d.ask_without_humanization('диалог закончен?') == 'НЕТ, нам нужно обсудить еще несколько аспектов.'
    assert await d.ask_without_humanization('диалог закончен?') == 'ДА'

import pytest

from ai_discussion.discusser import Discusser


@pytest.mark.asyncio
async def test_transliterate_name():
    d = Discusser(api_key='key', context='ctx', name='Тест', model='m', backend_type='openai')
    assert d.agent_name == 'Test'

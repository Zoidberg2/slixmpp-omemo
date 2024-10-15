import pytest

import slixmpp_omemo


__all__ = [
    "test_placeholder"
]


pytestmark = pytest.mark.asyncio


async def test_placeholder() -> None:
    """
    Placeholder test.
    """

    print(slixmpp_omemo.version)

import pytest

import slixmpp_omemo


__all__ = [  # pylint: disable=unused-variable
    "test_placeholder"
]


pytestmark = pytest.mark.asyncio  # pylint: disable=unused-variable


async def test_placeholder() -> None:
    """
    Placeholder test.
    """

    print(slixmpp_omemo.version)

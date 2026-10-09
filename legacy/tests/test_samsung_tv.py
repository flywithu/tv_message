"""Test Samsung TV client."""

import pytest

from samsungtv.samsung_tv import SamsungTV


@pytest.fixture
def tv():
    """Create TV instance."""
    return SamsungTV("192.168.10.38", port=8002)


@pytest.mark.asyncio
async def test_tv_init(tv):
    """Test TV initialization."""
    assert tv.host == "192.168.10.38"
    assert tv.port == 8002


@pytest.mark.asyncio
async def test_get_power_state(tv):
    """Test get power state."""
    state = await tv.get_power_state()
    assert state in ("on", "off")


@pytest.mark.asyncio
async def test_send_key(tv):
    """Test send key command."""
    result = await tv.send_key("KEY_HOME")
    assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])

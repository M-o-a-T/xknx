"""Unit test for KNX/IP ConnectionStateRequests."""
import pytest
from unittest.mock import patch

from xknx import XKNX
from xknx.knxip import KNXIPBody

from xknx._test import Testcase

class Test_KNXIPBody(Testcase):
    """Test class for KNX/IP ConnectionStateRequests."""

    # pylint: disable=too-many-public-methods,invalid-name

    @pytest.mark.anyio
    async def test_warn_calculated_length(self):
        """Test correct warn message if calculated_length is missing."""
        xknx = XKNX()
        body = KNXIPBody(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            body.calculated_length()
            mock_warn.assert_called_with('calculated_length not implemented for %s', 'KNXIPBody')

    @pytest.mark.anyio
    async def test_warn_to_knx(self):
        """Test correct warn message if to_knx is missing."""
        xknx = XKNX()
        body = KNXIPBody(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            body.to_knx()
            mock_warn.assert_called_with('to_knx not implemented for %s', 'KNXIPBody')

    @pytest.mark.anyio
    async def test_warn_from_knx(self):
        """Test correct warn message if from_knx is missing."""
        xknx = XKNX()
        body = KNXIPBody(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            body.from_knx((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x00, 0x00))
            mock_warn.assert_called_with('from_knx not implemented for %s', 'KNXIPBody')

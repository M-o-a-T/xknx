"""Unit test for KNX/IP Connect Request/Response."""
from unittest.mock import patch
import pytest

from xknx import XKNX
from xknx.io import Connect, UDPClient
from xknx.knxip import (
    HPAI, ConnectRequestType, ConnectResponse, ErrorCode, KNXIPFrame,
    KNXIPServiceType)

from xknx._test import Testcase, AsyncMock

class TestConnect(Testcase):
    """Test class for xknx/io/Connect objects."""

    @pytest.mark.anyio
    async def test_connect(self):
        """Test connecting from KNX bus."""
        xknx = XKNX()
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        connect = Connect(xknx, udp_client)
        connect.timeout_in_seconds = 0

        self.assertEqual(connect.awaited_response_class, ConnectResponse)

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame(xknx)
        exp_knxipframe.init(KNXIPServiceType.CONNECT_REQUEST)
        exp_knxipframe.body.control_endpoint = HPAI(
            ip_addr='192.168.1.3', port=4321)
        exp_knxipframe.body.data_endpoint = HPAI(
            ip_addr='192.168.1.3', port=4321)
        exp_knxipframe.body.request_type = ConnectRequestType.TUNNEL_CONNECTION
        exp_knxipframe.normalize()
        with patch('xknx.io.UDPClient.send', new_callable=AsyncMock) as mock_udp_send, \
                patch('xknx.io.UDPClient.getsockname') as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connect.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch('logging.Logger.warning') as mock_warning:
            await connect.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with('Cant understand knxipframe')

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.CONNECT_RESPONSE)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch('logging.Logger.warning') as mock_warning:
            await connect.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with("Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                                            type(connect).__name__,
                                            type(err_knxipframe.body).__name__, ErrorCode.E_CONNECTION_ID)

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.CONNECT_RESPONSE)
        res_knxipframe.body.communication_channel = 23
        res_knxipframe.body.identifier = 7
        await connect.response_rec_callback(res_knxipframe, None)
        self.assertTrue(connect.success)
        self.assertEqual(connect.communication_channel, 23)
        self.assertEqual(connect.identifier, 7)

"""Unit test for value reader."""
import anyio
from unittest.mock import patch
import pytest

from xknx import XKNX
from xknx.core import ValueReader
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramType

from xknx._test import Testcase, xknx_running

class TestValueReader(Testcase):
    """Test class for value reader."""

    @pytest.mark.anyio
    async def test_value_reader_read_success(self):
        """Test value reader: successfull read."""
        async with xknx_running() as xknx:
            test_group_address = GroupAddress("0/0/0")
            response_telegram = Telegram(group_address=test_group_address,
                                         telegramtype=TelegramType.GROUP_RESPONSE,
                                         payload=DPTBinary(1))

            value_reader = ValueReader(xknx, test_group_address)

            # Create a task for read()
            result = None
            await xknx.telegrams_in.start()

            async def _reader():
                nonlocal result
                result = await value_reader.read()
            read_task = await xknx.spawn(_reader)

            # queue the response
            await xknx.telegrams_in.put(response_telegram)
            await xknx.telegrams_in.stop()

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        # Callback was removed again
        assert not xknx.telegrams_in.callbacks
        # Successfull read() returns the telegram
        self.assertEqual(result,
                        response_telegram)

    @patch('logging.Logger.warning')
    @pytest.mark.anyio
    async def test_value_reader_read_timeout(self, logger_warning_mock):
        """Test value reader: read timeout."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress('0/0/0'), timeout_in_seconds=0)

        timed_out_read = await value_reader.read()

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        # Warning was logged
        logger_warning_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time to GroupValueRead request for: %s", GroupAddress('0/0/0'))
        # Callback was removed again
        assert not xknx.telegrams_in.callbacks
        # Unsuccessfull read() returns None
        self.assertIsNone(timed_out_read)

    @pytest.mark.anyio
    async def test_value_reader_send_group_read(self):
        """Test value reader: send_group_read."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress('0/0/0'))

        await value_reader.send_group_read()
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(group_address=GroupAddress('0/0/0'),
                                  telegramtype=TelegramType.GROUP_READ))

    @pytest.mark.anyio
    async def test_value_reader_telegram_received(self):
        """Test value reader: telegram_received."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/0")
        expected_telegram_1 = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_RESPONSE,
                                       payload=DPTBinary(1))
        expected_telegram_2 = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_WRITE,
                                       payload=DPTBinary(1))
        telegram_wrong_address = Telegram(group_address=GroupAddress("0/0/1"),
                                          telegramtype=TelegramType.GROUP_RESPONSE,
                                          payload=DPTBinary(1))
        telegram_wrong_type = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_READ,
                                       payload=DPTBinary(1))

        value_reader = ValueReader(xknx, test_group_address)

        async def async_telegram_received(test_telegram):
            return await value_reader.telegram_received(test_telegram)

        self.assertFalse(await async_telegram_received(telegram_wrong_address))
        self.assertFalse(await async_telegram_received(telegram_wrong_type))

        self.assertTrue(await async_telegram_received(expected_telegram_1))

        self.assertTrue(await async_telegram_received(expected_telegram_2))

    @pytest.mark.anyio
    async def test_value_reader_loop(self):
        """Test value reader: telegram_received."""
        async with xknx_running() as xknx:
            test_group_address = GroupAddress("0/0/0")
            value_reader = ValueReader(xknx, test_group_address)
            expected_telegram = Telegram(group_address=test_group_address,
                                         telegramtype=TelegramType.GROUP_WRITE,
                                         payload=DPTBinary(1))
            telegram_wrong_address = Telegram(group_address=GroupAddress("0/0/1"),
                                              telegramtype=TelegramType.GROUP_WRITE,
                                              payload=DPTBinary(1))
            evt = anyio.create_event()
            async def reader():
                await xknx.telegrams_in.start()
                res = await value_reader.read()
                assert res == expected_telegram
                await evt.set()

            await xknx.spawn(reader)
            await xknx.telegrams_in.put(telegram_wrong_address)
            await xknx.telegrams_in.put(expected_telegram)
            async with anyio.fail_after(0.1):
                await evt.wait()

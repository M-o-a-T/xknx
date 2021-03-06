"""Unit test for Fan objects."""
import asyncio
import unittest
from unittest.mock import patch

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.devices import Fan
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestFan(unittest.TestCase):
    """Class for testing Fan objects."""

    # pylint: disable=too-many-public-methods

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed_state='1/2/3')
        await fan.sync(False)

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    #
    # SYNC WITH STATE ADDRESS
    #
    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3',
                  group_address_speed_state='1/2/4')
        await fan.sync(False)

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    #
    #
    # TEST SET SPEED
    #
    async def test_set_speed(self):
        """Test setting the speed of a Fan."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        await fan.set_speed(55)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # 140 is 55% as byte (0...255)
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTArray(140)))

    #
    # TEST PROCESS
    #
    async def test_process_speed(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        self.assertEqual(fan.current_speed, None)

        # 140 is 55% as byte (0...255)
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray(140))
        await fan.process(telegram)
        self.assertEqual(fan.current_speed, 55)

    async def test_process_speed_wrong_payload(self):  # pylint: disable=invalid-name
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            await fan.process(telegram)

    async def test_process_fan_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            await fan.process(telegram)

    #
    # TEST DO
    #
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        await fan.do("speed:50")
        self.assertEqual(fan.current_speed, 50)
        await fan.do("speed:25")
        self.assertEqual(fan.current_speed, 25)

    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        fan = Fan(xknx,
                  name="TestFan",
                  group_address_speed='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await fan.do("execute")
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestFan')

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        fan = Fan(xknx,
                  'TestFan',
                  group_address_speed='1/7/1',
                  group_address_speed_state='1/7/2')
        self.assertTrue(fan.has_group_address(GroupAddress('1/7/1')))
        self.assertTrue(fan.has_group_address(GroupAddress('1/7/2')))
        self.assertFalse(fan.has_group_address(GroupAddress('1/7/3')))

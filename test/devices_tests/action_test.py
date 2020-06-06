"""Unit test for Action objects."""
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.devices import (
    Action, ActionBase, ActionCallback, BinarySensorState, Light)

from xknx._test import Testcase, AsyncMock

class TestAction(Testcase):
    """Class for testing Action objects."""

    #
    # TEST COUNTER
    #
    @pytest.mark.anyio
    async def test_counter(self):
        """Test counter method."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2)
        self.assertTrue(action.test_counter(None))
        self.assertFalse(action.test_counter(1))
        self.assertTrue(action.test_counter(2))
        self.assertFalse(action.test_counter(3))

    @pytest.mark.anyio
    async def test_no_counter(self):
        """Test counter method with no counter set."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=None)
        self.assertTrue(action.test_counter(None))
        self.assertTrue(action.test_counter(1))
        self.assertTrue(action.test_counter(2))
        self.assertTrue(action.test_counter(3))

    #
    # TEST APPLICABLE
    #
    @pytest.mark.anyio
    async def test_if_applicable_hook_on(self):
        """Test test_if_applicable method with hook set to 'on'."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2, hook="on")
        self.assertTrue(action.test_if_applicable(
            BinarySensorState.ON, 2))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.ON, 3))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.OFF, 2))

    @pytest.mark.anyio
    async def test_if_applicable_hook_off(self):
        """Test test_if_applicable method with hook set to 'off'."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2, hook="off")
        self.assertTrue(action.test_if_applicable(
            BinarySensorState.OFF, 2))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.OFF, 3))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.ON, 2))

    #
    # TEST EXECUTE
    #
    @pytest.mark.anyio
    async def test_execute_base_action(self):
        """Test if execute method of BaseAction shows correct info message."""
        xknx = XKNX()
        action = ActionBase(xknx)
        with patch('logging.Logger.info') as mock_info:
            await action.execute()
            mock_info.assert_called_with('Execute not implemented for %s', 'ActionBase')

    @pytest.mark.anyio
    async def test_execute_action(self):
        """Test if execute method of Action calls correct do method of device."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Light1',
            group_address_switch='1/6/4')
        xknx.devices.add(light)
        action = Action(xknx, target='Light1', method='on')
        with patch('xknx.devices.Light.do', new_callable=AsyncMock) as mock_do:
            await action.execute()
            mock_do.assert_called_with('on')

    @pytest.mark.anyio
    async def test_execute_action_callback(self):
        """Test if execute method of ActionCallback calls correct callback method."""
        xknx = XKNX()
        callback = Mock()

        async def async_callback():
            """Async callback."""
            callback()

        action = ActionCallback(xknx, async_callback)
        await action.execute()
        callback.assert_called_with()

    @pytest.mark.anyio
    async def test_execute_unknown_device(self):
        """Test if execute method of Action calls correct do method of device."""
        xknx = XKNX()

        action = Action(xknx, target='Light1', method='on')
        with patch('logging.Logger.warning') as logger_warning_mock:
            await action.execute()
            logger_warning_mock.assert_called_once_with(
                "Unknown device %s witin action %s.", action.target, action)

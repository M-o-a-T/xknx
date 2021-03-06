"""Unit test for devices container within XKNX."""
import asyncio
import unittest
from unittest.mock import Mock, patch

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.devices import BinarySensor, Device, Devices, Light, Switch
from xknx.telegram import GroupAddress


# pylint: disable=too-many-public-methods,invalid-name
class TestDevices(unittest.TestCase):
    """Test class for devices container within XKNX."""

    #
    # XKNX Config
    #
    def test_get_item(self):
        """Test get item by name or by index."""
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        switch1 = Switch(xknx,
                         "TestOutlet_1",
                         group_address='1/2/3')
        devices.add(switch1)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        switch2 = Switch(xknx,
                         "TestOutlet_2",
                         group_address='1/2/4')
        devices.add(switch2)

        self.assertEqual(devices["Living-Room.Light_1"], light1)
        self.assertEqual(devices["TestOutlet_1"], switch1)
        self.assertEqual(devices["Living-Room.Light_2"], light2)
        self.assertEqual(devices["TestOutlet_2"], switch2)
        with self.assertRaises(KeyError):
            # pylint: disable=pointless-statement
            devices["TestOutlet_X"]

        self.assertEqual(devices[0], light1)
        self.assertEqual(devices[1], switch1)
        self.assertEqual(devices[2], light2)
        self.assertEqual(devices[3], switch2)
        with self.assertRaises(IndexError):
            # pylint: disable=pointless-statement
            devices[4]

    def test_device_by_group_address(self):
        """Test get devices by group address."""
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('1/6/7'))),
            (light1,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('1/6/8'))),
            (light2,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('3/0/1'))),
            (sensor1, sensor2))

    def test_iter(self):
        """Test __iter__() function."""
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')

        devices.add(light2)

        self.assertEqual(
            tuple(devices.__iter__()),
            (light1, sensor1, sensor2, light2))

    def test_len(self):
        """Test len() function."""
        xknx = XKNX()
        devices = Devices()
        self.assertEqual(len(devices), 0)

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)
        self.assertEqual(len(devices), 1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)
        self.assertEqual(len(devices), 2)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address_state='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)
        self.assertEqual(len(devices), 3)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)
        self.assertEqual(len(devices), 4)

    def test_contains(self):
        """Test __contains__() function."""
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)
        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)
        self.assertTrue('Living-Room.Light_1' in devices)
        self.assertTrue('Living-Room.Light_2' in devices)
        self.assertFalse('Living-Room.Light_3' in devices)

    async def test_modification_of_device(self):
        """Test if devices object does store references and not copies of objects."""
        xknx = XKNX()
        devices = Devices()
        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)
        for device in devices:
            await device.set_on()
        self.assertTrue(light1.state)
        device2 = devices["Living-Room.Light_1"]
        await device2.set_off()
        self.assertFalse(light1.state)
        for device in devices.devices_by_group_address(GroupAddress('1/6/7')):
            await device.set_on()
        self.assertTrue(light1.state)

    def test_add_wrong_type(self):
        """Test if exception is raised when wrong type of devices is added."""
        xknx = XKNX()
        with self.assertRaises(TypeError):
            xknx.devices.add("fnord")

    #
    # TEST SYNC
    #
    async def test_sync(self):
        """Test sync function."""
        xknx = XKNX()
        device1 = Device(xknx, 'TestDevice1')
        device2 = Device(xknx, 'TestDevice2')
        xknx.devices.add(device1)
        xknx.devices.add(device2)
        with patch('xknx.devices.Device.sync') as mock_sync:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_sync.return_value = fut
            await xknx.devices.sync()
            self.assertEqual(mock_sync.call_count, 2)

    #
    # TEST CALLBACK
    #
    async def test_device_updated_callback(self):
        """Test if device updated callback is called correctly if device was updated."""
        xknx = XKNX()
        device1 = Device(xknx, 'TestDevice1')
        device2 = Device(xknx, 'TestDevice2')
        xknx.devices.add(device1)
        xknx.devices.add(device2)

        after_update_callback1 = Mock()
        after_update_callback2 = Mock()

        async def async_after_update_callback1(device):
            """Async callback No. 1."""
            after_update_callback1(device)

        async def async_after_update_callback2(device):
            """Async callback No. 2."""
            after_update_callback2(device)

        # Registering both callbacks
        xknx.devices.register_device_updated_cb(async_after_update_callback1)
        xknx.devices.register_device_updated_cb(async_after_update_callback2)

        # Triggering first device. Both callbacks to be called
        await device1.after_update()
        after_update_callback1.assert_called_with(device1)
        after_update_callback2.assert_called_with(device1)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd device. Both callbacks have to be called
        await device2.after_update()
        after_update_callback1.assert_called_with(device2)
        after_update_callback2.assert_called_with(device2)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        xknx.devices.unregister_device_updated_cb(async_after_update_callback1)

        # Triggering first device. Only second callback has to be called
        await device1.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device1)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        xknx.devices.unregister_device_updated_cb(async_after_update_callback2)

        # Triggering second device. No callback should be called
        await device2.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

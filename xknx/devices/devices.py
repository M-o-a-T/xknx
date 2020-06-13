"""
Module for handling a vector/array of devices.

More or less an array with devices. Adds some search functionality to find devices.
"""
from .device import Device
from ..exceptions import XKNXException


class Devices:
    """Class for handling a vector/array of devices."""

    def __init__(self):
        """Initialize Devices class."""
        self.__devices = {}
        self.device_updated_cbs = []
        self.__groups = {}

    def register_device_updated_cb(self, device_updated_cb):
        """Register callback for devices beeing updated."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister callback for devices beeing updated."""
        self.device_updated_cbs.remove(device_updated_cb)

    def __iter__(self):
        """Device iterator."""
        yield from self.__devices.values()

    def devices_by_group_address(self, group_address):
        """Return device(s) by group address."""
        if group_address not in self.__groups:
            # don't create a heap of empty entries
            return
        for device in self.__groups.get(group_address, {}).values():
            yield device

    def __getitem__(self, key):
        """Return device by name."""
        return self.__devices[key]

    def __len__(self):
        """Return number of devices."""
        return len(self.__devices)

    def __contains__(self, key):
        """Return if devices with name 'key' is within devices."""
        return key in self.__devices

    def add(self, device):
        """Add device to devices list."""
        if not isinstance(device, Device):
            raise TypeError()
        if device.name is None or device.name in self.__devices:
            raise XKNXException("The device '%s' is already registered" % (device.name,))
        device.register_device_updated_cb(self.device_updated)
        self.__devices[device.name] = device
        for group in device.all_addresses():
            try:
                self.__groups[group][device.name] = device
            except KeyError:
                self.__groups[group] = devs = {}
                devs[device.name] = device

    def remove(self, device):
        """Remove device from device list."""
        for group in device.all_addresses():
            del self.__groups[group][device.name]
        del self.__devices[device.name]
        device.unregister_device_updated_cb(self.device_updated)

    async def device_updated(self, device):
        """Call all registered device updated callbacks of device."""
        for device_updated_cb in self.device_updated_cbs:
            await device_updated_cb(device)

    async def sync(self):
        """Read state of devices from KNX bus."""
        for device in list(self.__devices.values()):
            await device.sync()

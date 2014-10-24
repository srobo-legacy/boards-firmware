#!/usr/bin/python

import sys
import usb1
import argparse
import yaml
import subprocess

parser = argparse.ArgumentParser(description="SR USB board flash utility")
parser.add_argument("conffile", help="Firmware configuration file")
parser.add_argument("--force", help="Force flashing of attached boards")
parser.add_argument("--board", help="Only flash one class of board")
parser.add_argument("--device", help="Only one specific device, given by bus:addr or SR partcode")

def get_bus_addr_pair(dev):
    busnum = dev.getBusNumber()
    devnum = dev.getDeviceAddress()
    return (busnum, devnum)

def discover_sr_devices(usb, conf):
    """
    Given a USB context and a configuration yaml object, search through all
    connected USB devices and return a list of pairs, matching each SR USB
    device found with it's corresponding configuration entry
    """
    vidpid_map = dict()
    for x in conf:
        vidpid_map[(int(conf[x]['VID']), int(conf[x]['PID']))] = conf[x]

    devices = []
    for dev in ctx.getDeviceList():
        vid = dev.getVendorID()
        pid = dev.getProductID()
        if (vid,pid) in vidpid_map:
            devices.append( (dev, vidpid_map[(vid,pid)]) )

    return devices

def filter_for_board_class(boardlist, boardname):
    """
    Remove all SR USB boards from boardlist that do not match the name
    given in boardname
    """
    return [(d,conf) for (d,conf) in boardlist if conf['name'] == boardname]

def filter_for_device(boardlist, dev_spec):
    """
    Try to select a single USB device from the list of attached SR USB devices,
    given some device specification. This can either be bus:addr (in decimal),
    or the verbatim SR partcode that has been baked into the devices serial
    number
    """
    if ':' in dev_spec:
        # Then this is a Bus:Addr spec
        parts = dev_spec.split(':')
        bus = int(parts[0])
        addr = int(parts[1])
        for dev, conf in boardlist:
            if dev.getBusNumber() == bus and dev.getDeviceAddress() == addr:
                return [(dev, conf)]
    else:
        # It's an SR part code. Look at the serial numbers.
        for dev, conf in boardlist:
            if dev.getSerialNumber() == dev_spec:
                return [(dev, conf)]
    return []


def get_device_path(ctx, dev):
    """
    Right now, this does nothing, because libusb is a world of pain.
    DFU-util advertises that it can take a port-path to a devices, however
    when presented with this path, it croaks and says it doesn't actually
    support doing that.
    This can be fixed in the future, but not now.
    """
    return ""

def maybe_flash_board(ctx, path, dev, conf, force):
    """
    Given a device and it's configuration, consider whether or not we should
    be flashing it. This boils down to two things: does it have the firmware
    version we expect, and are we forcing flashing?
    We downgrade boards that don't have the firmware version the host has.
    This is a feature
    """
    # For now, ignore the path.
    # So. What version is on the board? Look at the lower byte of rev num
    board_fw_ver = dev.getbcdDevice() % 256
    file_fw_ver = int(conf['fw_ver'])

    # Don't flash if the fw version matches, and we are not forcing
    if board_fw_ver == file_fw_ver and force != True:
        busnum, devnum = get_bus_addr_pair(dev)
        print "Skipping device {0}:{1} with matching fw ver".format(busnum, devnum)
        return

    # Definitely flash board. Invoke dfu-util

    vidhex = format(int(conf['VID']), '04x')
    pidhex = format(int(conf['PID']), '04x')
    subprocess.check_call(("dfu-util", "-d", "{0}:{1}".format(vidhex,pidhex), "-D", conf['fw_path']))
    return

if __name__ == "__main__":
    args = parser.parse_args()
    # Open USB context
    ctx = usb1.USBContext()
    # Suck in our configuration
    with open(args.conffile) as f:
        conf = yaml.load(f)

    # Discover what is attached
    device_list = discover_sr_devices(ctx, conf)

    if len(device_list) == 0:
        print "No SR USB boards attached"
        sys.exit(0)

    # Print some diagnostics
    print "Found the following SR USB devices attached"
    for dev, conf in device_list:
        busnum, devnum = get_bus_addr_pair(dev)
        print "{0}:{1}\t\"{2}\"\t{3}".format(busnum, devnum, dev.getProduct(), dev.getSerialNumber())

    # First, filter for boards if the --board option is given
    if args.board != None:
        device_list = filter_for_board_class(device_list, args.board)

    if len(device_list) == 0:
        print "No SR USB boards matching board-type filter"
        sys.exit(0)

    # Second, if we're looking for a specific device, filter for it
    if args.device != None:
        device_list = filter_for_device(device_list, args.device)

    if len(device_list) == 0:
        print "No SR USB boards matching device specification"
        sys.exit(0)

    # We're now left with a list of devices to potentially flash. Fetch a port
    # path to each, then consider whether to flash it.
    # XXX, port path stuff is borked.
    for dev, conf in device_list:
        path = get_device_path(ctx, dev)
        maybe_flash_board(ctx, path, dev, conf, args.force)

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

def discover_sr_devices(usb, conf):
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
    return [(d,conf) for (d,conf) in boardlist if conf['name'] == boardname]

def filter_for_device(boardlist, dev_spec):
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
    """ Right now, this does nothing, because libusb is a world of pain"""
    return ""

def maybe_flash_board(ctx, path, dev, conf, force):
    # For now, ignore the path.
    # So. What version is on the board? Look at the lower byte of rev num
    board_fw_ver = dev.getbcdDevice() % 256
    file_fw_ver = int(conf['fw_ver'])

    # Flash if the versions mismatch, at all. Also if the force flag is given.
    if board_fw_ver == file_fw_ver and force != True:
        busnum = dev.getBusNumber()
        devnum = dev.getDeviceAddress()
        print >>sys.stderr, "Skipping device {0}:{1} with matching fw ver".format(busnum, devnum)
        return

    # Definitely flash board. Invoke dfu-util
    vidhex = format(int(conf['VID']), '04x')
    pidhex = format(int(conf['PID']), '04x')
    p = subprocess.check_call(("dfu-util", "-d", "{0}:{1}".format(vidhex,pidhex), "-D", conf['fw_path']))
    p.wait()
    return

if __name__ == "__main__":
    print "Shoes"
    args = parser.parse_args()
    ctx = usb1.USBContext()
    with open(args.conffile) as f:
        conf = yaml.load(f)

    device_list = discover_sr_devices(ctx, conf)

    if len(device_list) == 0:
        print >>sys.stderr, "No SR USB boards attached"
        sys.exit(0)

    # First, filter for boards if the --board option is given
    if args.board != None:
        device_list = filter_for_board_class(device_list, args.board)

    if len(device_list) == 0:
        print >>sys.stderr, "No SR USB boards matching board-type filter"
        sys.exit(0)

    if args.device != None:
        device_list = filter_for_device(device_list, args.device)

    if len(device_list) == 0:
        print >>sys.stderr, "No SR USB boards matching device specification"
        sys.exit(0)

    # We're now left with a list of devices to potentially flash. Fetch a port
    # path to each, then consider whether to flash it.
    for dev, conf in device_list:
        path = get_device_path(ctx, dev)
        maybe_flash_board(ctx, path, dev, conf, args.force)

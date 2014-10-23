#!/usr/bin/python

import sys
import usb1
import argparse
import yaml

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

if __name__ == "__main__":
    print "Shoes"
    args = parser.parse_args()
    ctx = usb1.USBContext()
    with open(args.conffile) as f:
        conf = yaml.load(f)
    discover_sr_devices(ctx, conf)

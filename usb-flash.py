#!/usr/bin/python

import sys
import usb1
import argparse

parser = argparse.ArgumentParser(description="SR USB board flash utility")
parser.add_argument("conffile", help="Firmware configuration file")
parser.add_argument("--force", help="Force flashing of attached boards")
parser.add_argument("--board", help="Only flash one class of board")
parser.add_argument("--device", help="Only one specific device, given by bus:addr or SR partcode")

if __name__ == "__main__":
    print "Shoes"
    sys.exit(1)

#!/bin/sh

# On reading a part code, will prefix it with 'sr' and bake it into a servo
# board, by:
#  * Taking the built sbv4.bin
#  * Processing it with dfu-bootloader/bake_serial_num.pl, to insert the serial
#    number on top of XXXX...
#  * Operating stm32flash (in PATH) to bake the board
#
# This requires that you set up the board into the serial bootloader by pressing
# the button, then scan the code. I also assume the FTDI cable is ttyUSB0.

while read x; do
	x="sr$x"
	./bake_serial_num.pl $x < sbv4-4.2.bin > sbv4.sernum.bin
	flashpath=`which stm32flash` # sudo resets PATH
	sudo $flashpath -v -b 38400 -w sbv4.sernum.bin /dev/ttyUSB0
	rm sbv4.sernum.bin
	echo "Waiting for board to enumerate"
	sleep 2
	sudo ./usb_flash.py --force config.yaml
	echo "Check for the blue LED and move onto the next board"
done

# uDuck

This is a alpha-stage project to create a very small minimalist USB rubber ducky using the ATTiny45 microcontroller.

The hardware is borrowed from [this blog](http://www.morethantechnical.com/2015/08/03/smallest-attiny45-usb/). The software is a modified version of "CapsLocker", which can be [found here](http://macetech.com/blog/?q=node/46).

I'm using macOS for development along with the Objective Development's [CrossPack](https://www.obdev.at/products/crosspack/index.html) toolchain. The Makefile is setup for an ArduinoISP programmer. I highly recommend buying a SOIC-8 programming clip if you want to make this.

To use:
- Edit ducky.txt in the tools folder
- Run the attack_generator.py script, supplying the ducky.txt file as the first argument
- This will create a new attack.h file, with the encoded HID values
- Run make, attach a programmer, and run make install

# μDuck

μDuck is a stealth HID injector. It's a very small USB device that acts like a scripted keyboard. This can be used for automation and lulz, and has obvious security implications. It's quite similar  to the [Hak5 Rubber Ducky](https://hakshop.com/products/usb-rubber-ducky-deluxe) in terms of functionality, and even uses the [same syntax](https://github.com/hak5darren/USB-Rubber-Ducky/wiki/Payloads) to define the scripted input.

![μDuck hardware](https://raw.githubusercontent.com/phikshun/uDuck/master/doc/hardware.png)

When μDuck is connected, it will wait for 2 seconds in programming mode before switching to a keyboard. This allows the payload to be updated with the Python tool provided. It will wait for 5 seconds before the first HID injection, then retry the payload automatically at 60 seconds, 5 minutes, and then every 4 hours with +/- 1 hour of random variance. This ensures reliable delivery, but expect that your payload may run more than once.

## Building a μDuck

The μDuck is quite inexpensive -- all the parts cost around $2 per unit. However, you will need some tools and know-how to get started. For more information, see the README file in the doc directory.

## Credits and License

The hardware is borrowed from [this blog](http://www.morethantechnical.com/2015/08/03/smallest-attiny45-usb/). The software is a modified version of "CapsLocker", which can be [found here](http://macetech.com/blog/?q=node/46). Our customized hardware design can be found in the "hardware" folder.

Our Python code and hardware design is MIT licensed. The USB firmware is licensed [according to the terms](https://www.obdev.at/products/vusb/license.html) of Objective Development's vUSB and GPLv2.

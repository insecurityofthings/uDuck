# Building a μDuck

## Tools and Prerequisites

You'll need to following tools to construct the device:

- A decent temperature-controlled soldering iron with a fine point tip
- Solder (lead-free 0.8 mm)
- Flux with a fine-tip applicator
- Magnifying lamp
- A "third hand" tool
- Fine tweezers for handling SMT components
- An AVR programmer or a spare Arduino board
- A SOIC-8 clip for the programmer (not a hard requirement, but makes things much easier)

This project involves SMT soldering. You can find good tutorials [here](https://learn.adafruit.com/adafruit-guide-excellent-soldering/tools) and [here](https://www.sparkfun.com/tutorials/category/2). You'll need steady hands, good lighting, and magnification.

## Order Components

You can order the surface mount components from [DigiKey](http://www.digikey.com). You'll need the following components for each μDuck board:

- 1 x 0.1 uF ceramic capacitor [Link](http://www.digikey.ca/product-search/en?keywords=311-1141-1-ND)
- 2 x 68 Ohm resistors [Link](http://www.digikey.ca/product-search/en?keywords=P68GCT-ND)
- 2 x 3.6V zener diodes [Link](http://www.digikey.ca/product-search/en?keywords=MM3Z3V6T1GOSCT-ND)
- 1 x 1.5K Ohm resistor [Link](http://www.digikey.ca/product-search/en?keywords=311-1.5KGRCT-ND)
- 1 x Atmel ATTiny85 [Link](http://www.digikey.ca/product-search/en?keywords=ATTINY85-20SU-ND)

Note that you can swap components for similar parts with the same electrical properties and form factor.

In addition to the SMT parts, you will also need to get PCBs manufactured. There are many online services that allow you to submit designs and have them shipped to your door, even in fairly small quantities.

When submitting the hardware design, keep in mind the following:

- The board thickness should be 2.4mm. Typical PCB thickness (1.6mm) will fall right out of the port.
- Spring for gold plated pads - it will protect the USB pins from oxidation.

Unfortunately OSH Park cannot do 2.4mm boards, so we're using [AllPCB](http://www.allpcb.com) instead. If you have another preferred manufacturer, the results should be the same.

## Assembly

Use the hardware design files to show you where to place the parts. For IC and diode components, orientation is important. For passive components, they only need to be facing upwards.

Follow the tutorials on SMT soldering, or find a video on Youtube that demonstrates SMT soldering. Remember to use flux! :)

## Programming

There are two steps to programming. First, you'll need to get a bootloader on the microcontroller. Once the bootloader is installed you can upload new payloads with the `uduck_upload.py` script.

If you don't have a dedicated AVR programmer and would like to use an Arduino (this is how the Makefiles are currently setup), follow the instructions found [here](http://www.instructables.com/id/Turn-Your-Arduino-Into-an-ISP/).

### Bootloader Programming

You can find our slightly customized version of Micronucleus [here](https://github.com/phikshun/micronucleus). All we've done is configured the correct parameters in `firmware/configuration/t85_default/bootloaderconfig.h`, and updated the Makefile in `firmware/Makefile`.

To upload the bootloader, wire up a [SOIC-8 programming clip](https://www.amazon.com/Signstek-SOIC8-Socket-Adpter-Programmer/dp/B00V9QNAC4) to your AVR programmer and connect to the ATTiny85.

Now modify the following lines in the file `firmware/Makefile`:

Line 25: `PROGRAMMER ?= -c arduino`
- Leave as "arduino" or change to the correct programmer type

Line 29: `AVRDUDE = avrdude $(PROGRAMMER) -p $(DEVICE) -P /dev/cu.usbserial-A8008I9o -b 19200`
- Change the serial port and baud rate to the correct values. If you don't know what serial port your programmer is using, load the Arduino IDE and check.

To upload, you'll need `avrdude` installed. Sparkfun [has a tutorial](https://learn.sparkfun.com/tutorials/pocket-avr-programmer-hookup-guide/using-avrdude) that shows you the basics of AVRDUDE, which should be enough to get you up and running.

Once you have AVRDUDE working, open a shell, cd into the Micronucleus `firmware` directory and enter the commands:

`make fuse`
`make flash`

You don't need a full `avr-gcc` toolchain because we've precompiled the firmware for you. You're welcome to install an AVR toolchain and recompile. This will update the fuse settings on the ATTiny and program the bootloader in flash.

### Uploading the HID Injection Payload

To make it simple to update the μDuck payload, we've built a simple Python script. You will need to install the dependencies first using pip:

`pip install -r requirements.txt`

Before you start the programming tool, disconnect the μDuck from USB. The tool with prompt you when it's ready for the μDuck to be connected to USB.

The upload script takes only one parameter: the name of a file containing your Duckyscript. You can find some example scripts [here](https://github.com/hak5darren/USB-Rubber-Ducky/wiki/Payloads) if you need some inspiration.

Finally, run the command (where ducky.txt is the name of your Duckyscript file):

`./uduck_upload.py ducky.txt`

Your output should look similar to:

```
[+] Successfully compiled duckyscript
[+] Reading firmware image
[+] Patching firmware
[+] Successfully patched firmware

[+] Please plug in your uDuck device...
Press Ctrl-C to terminate the program...
[+] Device found:
      Available space for user applications: 6522 bytes
      Suggested sleep time between sending pages: 5 ms
      Whole page count: 102 page size: 64
      Erase function sleep duration: 510 ms

[+] Erasing flash...
[====================================================================] 100%
[+] Starting upload...
[====================================================================] 100%
[+] Upload finished. Enjoy! ;)
```

Plug-in your device when prompted. As indicated by the output above, the script is byte patching the compiled Duckyscript into the firmware hex file dynamically, then uploading it to the bootloader. We think that's pretty neat.

If you experience an error, let us know by submitting an issue. We will try to assist if time permits.

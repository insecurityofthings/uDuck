#!/usr/bin/env python
# -*- coding: utf-8 -*-

import keymap
import argparse
import sys
import os
import struct
import time
from intelhex import IntelHex
import usb

# Check pyusb dependency
try:
  from usb import core as _usb_core
except ImportError, ex:
  print '''
------------------------------------------
| PyUSB was not found or is out of date. |
------------------------------------------

Please update PyUSB using pip:

sudo pip install -U -I pip && sudo pip install -U -I pyusb
'''
  sys.exit(1)


class DuckyParser(object):
    ''' Help map ducky like script to HID codes to be sent '''

    hid_map = {
        '':           [0, 0],
        'ALT':        [0, 4],
        'SHIFT':      [0, 2],
        'CTRL':       [0, 1],
        'GUI':        [0, 8],
        'SCROLLLOCK': [71, 0],
        'ENTER':      [40, 0],
        'F12':        [69, 0],
        'HOME':       [74, 0],
        'F10':        [67, 0],
        'F9':         [66, 0],
        'ESCAPE':     [41, 0],
        'PAGEUP':     [75, 0],
        'TAB':        [43, 0],
        'PRINTSCREEN': [70, 0],
        'F2':         [59, 0],
        'CAPSLOCK':   [57, 0],
        'F1':         [58, 0],
        'F4':         [61, 0],
        'F6':         [63, 0],
        'F8':         [65, 0],
        'DOWNARROW':  [81, 0],
        'DELETE':     [42, 0],
        'RIGHT':      [79, 0],
        'F3':         [60, 0],
        'DOWN':       [81, 0],
        'DEL':        [76, 0],
        'END':        [77, 0],
        'INSERT':     [73, 0],
        'F5':         [62, 0],
        'LEFTARROW':  [80, 0],
        'RIGHTARROW': [79, 0],
        'PAGEDOWN':   [78, 0],
        'PAUSE':      [72, 0],
        'SPACE':      [44, 0],
        'UPARROW':    [82, 0],
        'F11':        [68, 0],
        'F7':         [64, 0],
        'UP':         [82, 0],
        'LEFT':       [80, 0]
    }

    blank_entry = {
        "mod": 0,
        "hid": 0,
        "char": '',
        "sleep": 0
    }

    def __init__(self, attack_script, key_mapping):
        self.hid_map.update(key_mapping)
        self.script = attack_script.split("\n")

    def char_to_hid(self, char):
        return self.hid_map[char]

    def parse(self):
        entries = []

        # process lines for repeat
        for pos, line in enumerate(self.script):
            if line.startswith("REPEAT"):
                self.script.remove(line)
                for i in range(1, int(line.split()[1])):
                    self.script.insert(pos,self.script[pos - 1])

        for line in self.script:
            if line.startswith('ALT'):
                entry = self.blank_entry.copy()
                if line.find(' ') == -1:
                    entry['char'] = ''
                else:
                    entry['char'] = line.split()[1]
                entry['hid'], mod = self.char_to_hid(entry['char'])
                entry['mod'] = 4 | mod
                entries.append(entry)

            elif line.startswith("GUI") or line.startswith('WINDOWS') or line.startswith('COMMAND'):
                entry = self.blank_entry.copy()
                if line.find(' ') == -1:
                    entry['char'] = ''
                else:
                    entry['char'] = line.split()[1]
                entry['hid'], mod = self.char_to_hid(entry['char'])
                entry['mod'] = 8 | mod
                entries.append(entry)

            elif line.startswith('CTRL') or line.startswith('CONTROL'):
                entry = self.blank_entry.copy()
                if line.find(' ') == -1:
                    entry['char'] = ''
                else:
                    entry['char'] = line.split()[1]
                entry['hid'], mod = self.char_to_hid(entry['char'])
                entry['mod'] = 1 | mod
                entries.append(entry)

            elif line.startswith('SHIFT'):
                entry = self.blank_entry.copy()
                if line.find(' ') == -1:
                    entry['char'] = ''
                else:
                    entry['char'] = line.split()[1]
                entry['hid'], mod = self.char_to_hid(entry['char'])
                entry['mod'] = 2 | mod
                entries.append(entry)

            elif line.startswith("ESC") or line.startswith('APP') or line.startswith('ESCAPE'):
                entry = self.blank_entry.copy()
                entry['char'] = "ESC"
                entry['hid'], entry['mod'] = self.char_to_hid('ESCAPE')
                entries.append(entry)

            elif line.startswith("DELAY"):
                entry = self.blank_entry.copy()
                entry['sleep'] = int(line.split()[1]) / 15 # we use 15ms increments in the uC
                entries.append(entry)

            elif line.startswith("STRING"):
                for char in " ".join(line.split()[1:]):
                    entry = self.blank_entry.copy()
                    entry['char'] = char
                    entry['hid'], entry['mod'] = self.char_to_hid(char)
                    entries.append(entry)

            elif line.startswith("ENTER"):
                entry = self.blank_entry.copy()
                entry['char'] = "\n"
                entry['hid'], entry['mod'] = self.char_to_hid('ENTER')
                entries.append(entry)

            # arrow keys
            elif line.startswith("UP") or line.startswith("UPARROW"):
                entry = self.blank_entry.copy()
                entry['char'] = "UP"
                entry['hid'], entry['mod'] = self.char_to_hid('UP')
                entries.append(entry)

            elif line.startswith("DOWN") or line.startswith("DOWNARROW"):
                entry = self.blank_entry.copy()
                entry['char'] = "DOWN"
                entry['hid'], entry['mod'] = self.char_to_hid('DOWN')
                entries.append(entry)

            elif line.startswith("LEFT") or line.startswith("LEFTARROW"):
                entry = self.blank_entry.copy()
                entry['char'] = "LEFT"
                entry['hid'], entry['mod'] = self.char_to_hid('LEFT')
                entries.append(entry)

            elif line.startswith("RIGHT") or line.startswith("RIGHTARROW"):
                entry = self.blank_entry.copy()
                entry['char'] = "RIGHT"
                entry['hid'], entry['mod'] = self.char_to_hid('RIGHT')
                entries.append(entry)

            elif len(line) == 0:
                pass

            else:
                print "CAN'T PROCESS... %s" % line

        return entries


class Micronucleus(object):

    def __init__(self):
        self.device = None
        self.flash_size = 0
        self.page_size = 0
        self.pages = 0
        self.bootloader_start = 0
        self.version = 0
        self.write_sleep = 0
        self.erase_sleep = 0
        self.signature = 0

    def connect(self):
        while not self.device:
            for dev in usb.core.find(find_all=True):
                if dev.idVendor == 0x16D0 and dev.idProduct == 0x0753:
                    self.device = usb.core.find(idVendor=0x16D0, idProduct=0x0753)
        
        time.sleep(0.1)
        self.device.set_configuration()

        time.sleep(0.2)
        ret = self.device.ctrl_transfer(0xC0, 0, 0, 0, 6)
        self.flash_size, self.page_size, buf3, self.signature = struct.unpack('>HBBH', ret)
        self.pages = self.flash_size / self.page_size

        if (self.pages * self.page_size < self.flash_size):
            self.pages += 1

        self.bootloader_start = self.pages * self.page_size
        
        self.write_sleep = buf3 & 127

        if (buf3 & 128):
            self.erase_sleep = self.write_sleep * self.pages / 4
        else:
            self.erase_sleep = self.write_sleep * self.pages

    def erase_flash(self, callback=None):
        res = self.device.ctrl_transfer(0x40, 2, 0, 0, None)

        i = 0.0
        while i < 1.0:
            if callback:
                callback(i)

            time.sleep(self.erase_sleep / 100.0 / 1000.0)
            i = i + 0.01
        
        if res == -5 or res == -34 or res == -84:
            if (res == -34):
                usb.util.release_interface(self.device)
                self.device = None

            return 1
        else:
            return res

    def write_flash(self, program, callback=None):
        program_size = len(program)
        page_length = self.page_size
        page_buffer = [0] * page_length

        for address in xrange(0, self.flash_size, self.page_size):
            page_contains_data = 0

            for page_address in xrange(0, page_length):
                if address + page_address > program_size:
                    page_buffer[page_address] = 0xff
                else:
                    page_contains_data = 1
                    page_buffer[page_address] = program[address + page_address]

            if address == 0:
                word0 = page_buffer[1] * 0x100 + page_buffer[0]
                word1 = page_buffer[3] * 0x100 + page_buffer[2]

                if word0 == 0x940c: # long jump
                    user_reset = word1
                elif (word0 & 0xf000) == 0xc000: # rjmp
                    user_reset = (word0 & 0x0fff) - 0 + 1
                else:
                    print "The reset vector of the user program does not contain a branch instruction,"
                    print "therefore the bootloader cannot be inserted. Please rearrange your code."
                    return -1

                # Patch in jmp to bootloader
                if self.bootloader_start > 0x2000:
                    data = 0x940c
                    page_buffer[0] = data >> 0 & 0xff
                    page_buffer[1] = data >> 8 & 0xff
                    page_buffer[3] = self.bootloader_start >> 0 & 0xff
                    page_buffer[4] = self.bootloader_start >> 8 & 0xff
                else:
                    data = (0xc000 | ((self.bootloader_start / 2 - 1) & 0x0fff)) & 0xffff
                    page_buffer[0] = data >> 0 & 0xff
                    page_buffer[1] = data >> 8 & 0xff

            if address >= (self.bootloader_start - self.page_size):
                user_reset_addr = (self.pages * self.page_size) - 4

                if user_reset_addr > 0x2000: # jmp
                    data = 0x940c
                    page_buffer[user_reset_addr - address + 0] = data >> 0 & 0xff
                    page_buffer[user_reset_addr - address + 1] = data >> 8 & 0xff
                    page_buffer[user_reset_addr - address + 2] = user_reset >> 0 & 0xff
                    page_buffer[user_reset_addr - address + 3] = user_reset >> 8 & 0xff
                else: # rjmp
                    data = (0xc000 | ((user_reset - user_reset_addr / 2 - 1) & 0x0fff)) & 0xffff
                    page_buffer[user_reset_addr - address + 0] = data >> 0 & 0xff
                    page_buffer[user_reset_addr - address + 1] = data >> 8 & 0xff

            if address >= (self.bootloader_start - self.page_size):
                page_contains_data = 1

            if page_contains_data:
                res = self.device.ctrl_transfer(0x40, 1, page_length, address, None)
                if res:
                    return -1

                for i in xrange(0, page_length, 4):
                    w1 = ((page_buffer[i+1] << 8) + (page_buffer[i+0] << 0)) & 0xffff
                    w2 = ((page_buffer[i+3] << 8) + (page_buffer[i+2] << 0)) & 0xffff

                    res = self.device.ctrl_transfer(0x40, 3, w1, w2, None)
                    if res:
                        return -1

                time.sleep(self.write_sleep / 1000.0)

            if callback:
                callback(address / float(self.flash_size))

        callback(1.0)
        return 0

def progress_quest(complete):
    print 'Done %d%%' % (complete * 100)

current_dir = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('r'), help="Input ducky script file")
parser.add_argument('--layout', default='us', help="Keyboard layout: %s" % ", ".join(keymap.mapping.keys()))
parser.add_argument('--firmware', default=current_dir + '/../default/uduck.hex', help='Firmware template in intel hex format')
args = parser.parse_args()

parsed = DuckyParser(args.file.read(), keymap.mapping[args.layout]).parse()

hid_array = [0x00, 0x00, 0x00]
for h in parsed:
    hid_array.append(int(h['mod']))
    hid_array.append(int(h['hid']))
    hid_array.append(int(h['sleep']))

print 'Successfully compiled duckyscript'

if len(hid_array) > 3000:
    print 'Attack HID array too big -- 1000 HID codes max'
    sys.exit(-1)

print 'Reading firmware image'

try:
    firmware = IntelHex(args.firmware)
except:
    print 'Could not open firmware file or parsing error'
    sys.exit(-1)

print 'Patching firmware'

hid_offset = 0
for i in xrange(0, len(firmware)):
    if firmware[i] == 0x44:
        if firmware[i+1] == 0x43 and firmware[i+2] == 0x42 and firmware[i+3] == 0x41:
            hid_offset = i
            break

if hid_offset == 0:
    print 'Count not find HID array offset in firmware'
    sys.exit(-1)

size_offset = 0
for i in xrange(0, len(firmware)):
    if firmware[i] == 0x99:
        if firmware[i+1] == 0x99:
            size_offset = i
            break

if size_offset == 0:
    print 'Count not find HID array size offset in firmware'
    sys.exit(-1)

firmware[size_offset + 0] = len(hid_array) & 0xff
firmware[size_offset + 1] = len(hid_array) >> 8 & 0xff

for i in xrange(0, len(hid_array)):
    firmware[hid_offset + i] = hid_array[i]

firmware.tofile('uduck_patched.hex', format='hex')

print 'Successfully patched firmware' 

print ''

print 'Please plug in your uDuck device...'
print 'Press Ctrl-C to terminate the program...'

mn = Micronucleus()
mn.connect()

print 'Device found:'
print '  Available space for user applications: %d bytes' % mn.flash_size
print '  Suggested sleep time between sending pages: %d ms' % mn.write_sleep
print '  Whole page count: %d page size: %d' % (mn.pages, mn.page_size)
print '  Erase function sleep duration: %d ms' % mn.erase_sleep

print ''

print 'Erasing flash...'
res = mn.erase_flash(progress_quest)

if res == 1:
    print 'Connection to device lost during erase! Not to worry,'
    print 'this happens on some computers - reconnecting...'

    mn = Micronucleus()
    mn.connect()

elif res != 0:
    print 'Flash erase error %d' % res
    print 'Please unplug the device and restart the program'
    sys.exit(-1)

print 'Starting upload...'
res = mn.write_flash(firmware, progress_quest)

if res != 0:
    print 'Flash write error %d' % res
    print 'Please unplug the device and restart the program'
    sys.exit(-1)

print 'Upload finished. Enjoy! ;)'

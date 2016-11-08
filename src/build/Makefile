###############################################################################
# Makefile for the project uDuck
###############################################################################

## General Flags
PROJECT = uDuck
MCU = attiny85
BURNMCU = attiny85
BURNPROGRAMMER = arduino
BURNPORT = /dev/cu.usbserial-A8008I9o
TARGET = uduck.elf
CC = avr-gcc

## Options common to compile, link and assembly rules
COMMON = -mmcu=$(MCU)

## Compile options common for all C compilation units.
CFLAGS = $(COMMON)
CFLAGS += -Wall -gdwarf-2 -std=gnu99 -DF_CPU=16500000UL -Os -funsigned-char -funsigned-bitfields -fpack-struct -fshort-enums
CFLAGS += -MD -MP -MT $(*F).o -MF dep/$(@F).d 

## Assembly specific flags
ASMFLAGS = $(COMMON)
ASMFLAGS += $(CFLAGS)
ASMFLAGS += -x assembler-with-cpp -Wa,-gdwarf2

## Linker flags
LDFLAGS = $(COMMON)
LDFLAGS +=  -Wl,-Map=uduck.map


## Intel Hex file production flags
HEX_FLASH_FLAGS = -R .eeprom

HEX_EEPROM_FLAGS = -j .eeprom
HEX_EEPROM_FLAGS += --set-section-flags=.eeprom="alloc,load"
HEX_EEPROM_FLAGS += --change-section-lma .eeprom=0 --no-change-warnings


## Include Directories
INCLUDES = -I"../usbdrv" -I"../." 

## Objects that must be built in order to link
OBJECTS = main.o oddebug.o usbdrv.o usbdrvasm.o 

## Objects explicitly added by the user
LINKONLYOBJECTS = 

## Build
all: $(TARGET) uduck.hex uduck.eep uduck.lss size

## Compile
usbdrvasm.o: ../usbdrv/usbdrvasm.S
	$(CC) $(INCLUDES) $(ASMFLAGS) -c  $<

main.o: ../main.c
	$(CC) $(INCLUDES) $(CFLAGS) -c  $<

oddebug.o: ../usbdrv/oddebug.c
	$(CC) $(INCLUDES) $(CFLAGS) -c  $<

usbdrv.o: ../usbdrv/usbdrv.c
	$(CC) $(INCLUDES) $(CFLAGS) -c  $<

##Link
$(TARGET): $(OBJECTS)
	 $(CC) $(LDFLAGS) $(OBJECTS) $(LINKONLYOBJECTS) $(LIBDIRS) $(LIBS) -o $(TARGET)

%.hex: $(TARGET)
	avr-objcopy -O ihex $(HEX_FLASH_FLAGS)  $< $@

%.eep: $(TARGET)
	-avr-objcopy $(HEX_EEPROM_FLAGS) -O ihex $< $@ || exit 0

%.lss: $(TARGET)
	avr-objdump -h -S $< > $@

size: ${TARGET}
	@echo
	@avr-size -C --mcu=${MCU} ${TARGET}

## Program
burn:
	avrdude -p $(BURNMCU) -c $(BURNPROGRAMMER) -P $(BURNPORT) -b 19200 -U flash:w:uduck.hex:a

burnfuses:
	avrdude -p $(BURNMCU) -c $(BURNPROGRAMMER) -P $(BURNPORT) -b 19200 -U lfuse:w:0xd1:m -U hfuse:w:0xdf:m -U efuse:w:0xff:m 

install: burn burnfuses

## Clean target
.PHONY: clean
clean:
	-rm -rf $(OBJECTS) uduck.elf dep/* uduck.hex uduck.eep uduck.lss uduck.map


## Other dependencies
-include $(shell mkdir dep 2>/dev/null) $(wildcard dep/*)


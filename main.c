#include <avr/io.h>
#include <avr/wdt.h>
#include <avr/eeprom.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <util/delay.h>
#include <stdlib.h>

#include "usbdrv.h"
#include "oddebug.h"
#include "attack.h"


/* ------------------------------------------------------------------------- */

static uchar reportBuffer[2];    /* buffer for HID reports */
static uchar idleRate;           /* in 4 ms units */
static uchar reportCount = 0;		/* current report */
static unsigned int	TimerDelay;		/* counter for delay period */
static unsigned int index = 0;


/* ------------------------------------------------------------------------- */

PROGMEM const char usbHidReportDescriptor[USB_CFG_HID_REPORT_DESCRIPTOR_LENGTH] = { /* USB report descriptor */
    0x05, 0x01,                    // USAGE_PAGE (Generic Desktop)
    0x09, 0x06,                    // USAGE (Keyboard)
    0xa1, 0x01,                    // COLLECTION (Application)
    0x05, 0x07,                    //   USAGE_PAGE (Keyboard)
    0x19, 0xe0,                    //   USAGE_MINIMUM (Keyboard LeftControl)
    0x29, 0xe7,                    //   USAGE_MAXIMUM (Keyboard Right GUI)
    0x15, 0x00,                    //   LOGICAL_MINIMUM (0)
    0x25, 0x01,                    //   LOGICAL_MAXIMUM (1)
    0x75, 0x01,                    //   REPORT_SIZE (1)
    0x95, 0x08,                    //   REPORT_COUNT (8)
    0x81, 0x02,                    //   INPUT (Data,Var,Abs)
    0x95, 0x01,                    //   REPORT_COUNT (1)
    0x75, 0x08,                    //   REPORT_SIZE (8)
    0x25, 0x65,                    //   LOGICAL_MAXIMUM (101)
    0x19, 0x00,                    //   USAGE_MINIMUM (Reserved (no event indicated))
    0x29, 0x65,                    //   USAGE_MAXIMUM (Keyboard Application)
    0x81, 0x00,                    //   INPUT (Data,Ary,Abs)
    0xc0                           // END_COLLECTION
};
/* We use a simplifed keyboard report descriptor which does not support the
 * boot protocol. We don't allow setting status LEDs and we only allow one
 * simultaneous key press (except modifiers). We can therefore use short
 * 2 byte input reports.
 * The report descriptor has been created with usb.org's "HID Descriptor Tool"
 * which can be downloaded from http://www.usb.org/developers/hidpage/.
 * Redundant entries (such as LOGICAL_MINIMUM and USAGE_PAGE) have been omitted
 * for the second INPUT item.
 */

static void buildReport(uchar mod, uchar key)
{
	reportCount++;
    reportBuffer[0] = mod;    /* no modifiers */
    reportBuffer[1] = key;
}


static void timerPoll(void)
{
	static unsigned int timerCnt;

    if(TIFR & (1 << TOV1)) {
        TIFR = (1 << TOV1); // clear overflow
        if(++timerCnt >= TimerDelay) { // check for end of pseudorandom delay
			TimerDelay = 1;
			timerCnt = 0;
        }
    }
}


/* ------------------------------------------------------------------------- */

static void timerInit(void)
{
    TCCR1 = 0x0b; // select clock: 16.5M/1k -> overflow rate = 16.5M/256k = 62.94 Hz
}


/* ------------------------------------------------------------------------- */
/* ------------------------ interface to USB driver ------------------------ */
/* ------------------------------------------------------------------------- */

uchar usbFunctionSetup(uchar data[8])
{
    usbRequest_t *rq = (void *)data;

    usbMsgPtr = reportBuffer;
    if((rq->bmRequestType & USBRQ_TYPE_MASK) == USBRQ_TYPE_CLASS){    /* class request type */
        if(rq->bRequest == USBRQ_HID_GET_REPORT){  /* wValue: ReportType (highbyte), ReportID (lowbyte) */
            /* we only have one report type, so don't look at wValue */
            buildReport(0, 0);
            return sizeof(reportBuffer);
        }else if(rq->bRequest == USBRQ_HID_GET_IDLE){
            usbMsgPtr = &idleRate;
            return 1;
        }else if(rq->bRequest == USBRQ_HID_SET_IDLE){
            idleRate = rq->wValue.bytes[1];
        }
    }else{
        /* no vendor specific requests implemented */
    }
	return 0;
}

/* ------------------------------------------------------------------------- */
/* ------------------------ Oscillator Calibration ------------------------- */
/* ------------------------------------------------------------------------- */

/* Calibrate the RC oscillator to 8.25 MHz. The core clock of 16.5 MHz is
 * derived from the 66 MHz peripheral clock by dividing. Our timing reference
 * is the Start Of Frame signal (a single SE0 bit) available immediately after
 * a USB RESET. We first do a binary search for the OSCCAL value and then
 * optimize this value with a neighboorhod search.
 * This algorithm may also be used to calibrate the RC oscillator directly to
 * 12 MHz (no PLL involved, can therefore be used on almost ALL AVRs), but this
 * is wide outside the spec for the OSCCAL value and the required precision for
 * the 12 MHz clock! Use the RC oscillator calibrated to 12 MHz for
 * experimental purposes only!
 */
static void calibrateOscillator(void)
{
    uchar step = 128;
    uchar trialValue = 0, optimumValue;
    int x, optimumDev, targetValue = (unsigned)(1499 * (double)F_CPU / 10.5e6 + 0.5);

    /* do a binary search: */
    do{
        OSCCAL = trialValue + step;
        x = usbMeasureFrameLength();    /* proportional to current real frequency */
        if(x < targetValue)             /* frequency still too low */
            trialValue += step;
        step >>= 1;
    }while(step > 0);
    /* We have a precision of +/- 1 for optimum OSCCAL here */
    /* now do a neighborhood search for optimum value */
    optimumValue = trialValue;
    optimumDev = x; /* this is certainly far away from optimum */
    for(OSCCAL = trialValue - 1; OSCCAL <= trialValue + 1; OSCCAL++){
        x = usbMeasureFrameLength() - targetValue;
        if(x < 0)
            x = -x;
        if(x < optimumDev){
            optimumDev = x;
            optimumValue = OSCCAL;
        }
    }
    OSCCAL = optimumValue;
}
/*
Note: This calibration algorithm may try OSCCAL values of up to 192 even if
the optimum value is far below 192. It may therefore exceed the allowed clock
frequency of the CPU in low voltage designs!
You may replace this search algorithm with any other algorithm you like if
you have additional constraints such as a maximum CPU clock.
For version 5.x RC oscillators (those with a split range of 2x128 steps, e.g.
ATTiny25, ATTiny45, ATTiny85), it may be useful to search for the optimum in
both regions.
*/

void usbEventResetReady(void)
{
    calibrateOscillator();
    eeprom_write_byte(0, OSCCAL);   /* store the calibrated value in EEPROM */
}

/* ------------------------------------------------------------------------- */
/* --------------------------------- main ---------------------------------- */
/* ------------------------------------------------------------------------- */

int main(void)
{
    uchar i;
    uchar calibrationValue;

    calibrationValue = eeprom_read_byte(0); /* calibration value from last time */
    
    if(calibrationValue != 0xff) {
        OSCCAL = calibrationValue;
    }
    
    odDebugInit();
    usbDeviceDisconnect();
    
    for (i = 0; i < 20; i++) {  /* 300 ms disconnect */
        _delay_ms(15);
    }

    usbDeviceConnect();

    wdt_enable(WDTO_1S);
    timerInit();
	TimerDelay = 630; /* initial 10 second delay */

    usbInit();
    sei();

    for (;;) {    /* main event loop */
        wdt_reset();
        usbPoll();

        if (usbInterruptIsReady() && TimerDelay == 1) {
            if (index < sizeof(attack)) {
                if (reportCount & 1) {
                    buildReport(0, 0);
                    usbSetInterrupt(reportBuffer, sizeof(reportBuffer));
                } else {
                    buildReport(attack[index], attack[index + 1]);
                    usbSetInterrupt(reportBuffer, sizeof(reportBuffer));
                    
                    if (attack[index + 2]) {
                        TimerDelay = attack[index + 2] + 1;
                    }
                    index += 3;
                }
            } else if (index == sizeof(attack)) {
                buildReport(0, 0);
                usbSetInterrupt(reportBuffer, sizeof(reportBuffer));
                index = 0;
                reportCount = 0;
                TimerDelay = 2835 + rand(); // 1/63s * 63 * 30 + 0...32767
            }
        }
        
        timerPoll();
    }
    return 0;
}

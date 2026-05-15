# libraries
from usbtransfer import USBTransfer
from usbmanager import USBManager
from graphics import Graphics
from storage import Storage

from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from luma.core.render import canvas

import RPi.GPIO as GPIO

import time

# init input
INPUT = {
    "key1" : 21,
    "key2" : 20,
    "key3" : 16,
    
    "up" : 6,
    "down" : 19,
    "left" : 5,
    "right" : 26,
    
    "click" : 13
}

ACTIONS = {
    INPUT["key1"]: lambda: (
        setattr(Storage, "displayDrive", 1)
        if Storage.displayDrive == 0 and not Storage.usbtransferRunning
        else None
    ),
    INPUT["key2"]: lambda: (
        setattr(Storage, "displayDrive", 2)
        if Storage.displayDrive == 0 and not Storage.usbtransferRunning
        else None
    ),
    INPUT["key3"]: lambda: setattr(Storage, "displayDrive", 0),

    INPUT["up"]: lambda: setattr(Storage, "cursorPosition", Storage.cursorPosition - 1),
    INPUT["down"]: lambda: setattr(Storage, "cursorPosition", Storage.cursorPosition + 1),
    INPUT["left"]: lambda: setattr(Storage, "cursorPosition", Storage.cursorPosition - 1),
    INPUT["right"]: lambda: setattr(Storage, "cursorPosition", Storage.cursorPosition + 1),
    INPUT["click"]: lambda: (
        setattr(Storage, "usbtransferRunning", True)
        if Storage.cursorPosition == 3 and Storage.displayDrive == 0 and not Storage.usbtransferRunning and Storage.devicesReady
        else (
            setattr(Storage, "displayDrive", Storage.cursorPosition)
            if Storage.displayDrive == 0 and not Storage.usbtransferRunning
            else None
        )
    )
}

GPIO.setmode(GPIO.BCM)
for pin in INPUT.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def handler(channel):
    if channel in ACTIONS:
        ACTIONS[channel]()

    # maintain cursor position in range
    if Storage.cursorPosition == 0:
        Storage.cursorPosition = 3 if Storage.devicesReady else 2
    elif Storage.cursorPosition == (4 if Storage.devicesReady else 3):
        Storage.cursorPosition = 1

    # update screen
    Storage.updateScreen = True

# main loop
try:
    print("USB Cloner starting . . .")
    
    # setup screen
    serial = spi(port=0, device=0)
    device = sh1106(serial)
    device.rotate = 2
    
    # setup utils
    usbmanager = USBManager()
    graphics = Graphics(device)
    
    while True:
        # handle input
        if not Storage.usbtransferRunning:
            for name, pin in INPUT.items():
                if GPIO.input(pin) == GPIO.LOW:
                    print(f"Pressed : {name}")
                    handler(pin)
        
        # draw
        if Storage.updateScreen:
            with canvas(device) as draw:
                readyDrives = usbmanager.get_ready_drives()
                
                # display transfer progress
                if Storage.usbtransferRunning:
                    if not Storage.usbtransfer:
                        drives = list(usbmanager.get_drives().values())
                        
                        Storage.usbtransfer = USBTransfer(drives[0], drives[1])
                        Storage.usbtransfer.start()
                    
                    if not Storage.usbtransfer.finished:
                        graphics.draw_lines(draw, [
                            f"Progress : {Storage.usbtransfer.progress}%",
                            f"Speed : {Storage.usbtransfer.speed}",
                            f"Transfered : {Storage.usbtransfer.transferred}",
                            f"Total : {Storage.usbtransfer.total}",
                            f"Status : {'running' if Storage.usbtransfer.running else 'error' if Storage.usbtransfer.error else 'done'}"
                        ])
                        
                        if Storage.usbtransfer.error:
                            Storage.usbtransferErrorCounter += 1
                            
                            if Storage.usbtransferErrorCounter == 30:
                                Storage.usbtransfer.stop()
                            
                                Storage.usbtransferErrorCounter = 0
                                Storage.usbtransfer = None
                                Storage.usbtransferRunning = False
                    else:
                        Storage.usbtransfer = None
                        Storage.usbtransferRunning = False
                else:
                    # display drive information
                    if Storage.displayDrive == 1 and readyDrives[0]:
                        drive = usbmanager.get_drive(0)
                        
                        if not drive: Storage.displayDrive = 0
                        else:
                            graphics.draw_lines(draw, [
                                f"Device : {drive['device']}",
                                f"Mount : {drive['mount']}",
                                f"Label : {drive['label']}",
                                f"Size : {drive['size']}GB",
                                f"Free : {drive['free']}GB"
                            ])
                    elif Storage.displayDrive == 2 and readyDrives[1]:
                        drive = usbmanager.get_drive(1)
                        
                        if not drive: Storage.displayDrive = 0
                        else:
                            graphics.draw_lines(draw, [
                                f"Device : {drive['device']}",
                                f"Mount : {drive['mount']}",
                                f"Label : {drive['label']}",
                                f"Size : {drive['size']}GB",
                                f"Free : {drive['free']}GB"
                            ])
                    else: Storage.displayDrive = 0
                    
                    # main menu
                    if Storage.displayDrive == 0:
                        lines = [
                            (
                                f"Device 1 : {'Ready' if readyDrives[0] else 'Waiting...'}",
                                Storage.cursorPosition == 1
                            ),
                            (
                                f"Device 2 : {'Ready' if readyDrives[1] else 'Waiting...'}",
                                Storage.cursorPosition == 2
                            )
                        ]
                        
                        if readyDrives[0] and readyDrives[1]:
                            Storage.devicesReady = True
                            lines.append(
                                (
                                    "START",
                                    Storage.cursorPosition == 3
                                )
                            )
                        else: Storage.devicesReady = False
                        
                        graphics.draw_centered_lines(draw, lines)
        
        # delay
        time.sleep(.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("USB Cloner interrupted (ctrl + c) . . .")

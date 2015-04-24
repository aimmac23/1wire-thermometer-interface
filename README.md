1wire-thermometer-interface
===========================

Python code to control 1-wire temperature sensor bus over USB.

This library isn't much use without the custom hardware it was coded for.

Requirements:
 * Something involving WSGI - I personally install it in an Apache
 * PyUSB - http://sourceforge.net/projects/pyusb/
 * libusb0 to be installed (native library).
 * For Linux, a new udev rule to be added to allow access to the device:
 
 In /etc/udev/rules.d/ add a new file called "70-usb-custom.rules", containing the following:
 
    SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="0f1a", MODE="0666"

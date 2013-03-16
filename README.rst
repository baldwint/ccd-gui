
Graphical User Interface for Jobin-Yvon CCD-2000
================================================

This is a GUI program for using the Jobin-Yvon CCD-2000 spectral
camera that is mounted on the Spex 750M monochromator in the Wang Lab.

This program does not control the CCD directly, since the control
hardware is incompatible with modern computers. Instead, it
communicates with a LabView program over TCP-IP.

Dependencies
------------

The GUI requires the WxPython_ toolkit, and communication with the
LabView program is handled by Wanglib_. This, in turn, requires 
Python 2.7 with Numpy_, PySerial_, and Matplotlib_.

.. _WxPython: http://www.wxpython.org/
.. _Wanglib: http://wanglib.readthedocs.org/
.. _Numpy: http://numpy.scipy.org/
.. _Matplotlib: http://matplotlib.sourceforge.net/
.. _PySerial: http://pyserial.sourceforge.net/

To install all of this stuff, I recommend using the pip_ installer.

.. _pip: http://www.pip-installer.org/


Installation
------------

To use the program, download the source or clone it with git::

    git clone https://github.com/baldwint/ccd-gui.git

The GUI should be invoked from the command line using::

    python ccd_client.py

Usage
-----

Start the CCD computer and follow the instructions in the README file
on the desktop. Cooling the sensor down takes an hour or more.

Once the LabView server program is running, find the IP address using
``ipconfig`` at a DOS prompt. Invoke the client, specifying the address
of the server::

    python ccd_client.py --ip 128.223.xxx.xxx

Optionally, you can also connect the spectrometer via RS-232::

    python ccd_client.py --ip 128.223.xxx.xxx --spec /dev/ttyUSB0

Change ``/dev/ttyUSB0`` to the serial port you are using. On Windows,
this will look like ``COM1``.

If you do not connect to the spectrometer, you will not be able to
move the grating. This may be fine, but you should provide the center
wavelength (as read from the 750M window) so that the x axis is
properly calibrated::

    python ccd_client.py --ip 128.223.xxx.xxx --wl 800


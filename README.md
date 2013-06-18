
Commotion Mesh Applet
=====================

This is a GNOME panel applet for using OLSR mesh networks.  It gives you a
simple menu to connect to mesh networks, displays the current status of the
OLSR mesh, and gives detailed status and debugging info from olsrd.

It works on Unity, GNOME 2, GNOME 3, XFCE, and MATE.  It might also work on KDE.


Installing
----------

If you are using Debian, Ubuntu, Mint, or any other Debian-derivative, you can
install Commotion by running these three lines in your Terminal app:

    sudo add-apt-repository ppa:guardianproject/commotion
    sudo apt-get update
    sudo apt-get install commotion-mesh-applet

You should see the key ID 6B80A84207B30AC9DEE235FEF50EADDD2234F563 (aka
2234F563) flash by as part of that process.


Bugs
----

If you encounter any problems or wish to request features, please add them to
our issue tracker:

https://code.commotionwireless.net/projects/commotion-linux/issues


Building
--------

If you are on a non-Debian-derivitive GNU/Linux distro, then you'll need to
install this manually.  We are looking for contributions of packaging to make
this easy for people to do.

Check the `debian/control` file for a list of standard libraries that are
required.  Here are the other libraries needed:

* https://github.com/opentechinstitute/nm-dispatcher-olsrd
* https://pypi.python.org/pypi/pyjavaproperties
* https://pypi.python.org/pypi/python-networkmanager

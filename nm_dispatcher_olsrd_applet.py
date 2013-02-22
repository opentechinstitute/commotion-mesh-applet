
import glob
import NetworkManager
import pyjavaproperties
import re
import sys

import pprint

try:
    from gi.repository import Gtk
except: # Can't use ImportError, as gi.repository isn't quite that nice...
    import gtk as Gtk


def get_visible_adhocs():
    actives = []
    nets = []
    strengths = dict()
    for ac in NetworkManager.NetworkManager.ActiveConnections:
        for d in ac.Devices:
            if d.Managed and d.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                wireless = d.SpecificDevice()
                aap = wireless.ActiveAccessPoint
                if aap.Mode == NetworkManager.NM_802_11_MODE_ADHOC:
                    channel = (aap.Frequency - 2407) / 5
                    actives.append(tuple([aap.Ssid, aap.HwAddress, channel]))
                for ap in wireless.GetAccessPoints():
                    if ap.Mode == NetworkManager.NM_802_11_MODE_ADHOC:
                        channel = (aap.Frequency - 2407) / 5
                        nets.append(tuple([ap.Ssid, ap.HwAddress, channel]))
                        strengths[ap.Ssid] = ap.Strength
    return [tuple(actives), tuple(nets), strengths]


def get_profiles():
    '''get all the available mesh profiles and return as a list of tuples'''
    profiles = []
    for f in glob.glob('/etc/nm-dispatcher-olsrd/*.profile'):
        p = pyjavaproperties.Properties()
        p.load(open(f))
        bssid = p['bssid'].upper()
        channel = int(p['channel'])
        profiles.append(tuple([p['ssid'], bssid, channel]))
    return tuple(profiles)


def add_menu_item(menu, name, function, imagefile=None):
    item = Gtk.ImageMenuItem(name)
    if imagefile:
        icon = Gtk.Image()
        icon.set_from_file(imagefile)
        item.set_image(icon)
    item.show()
    item.connect( "activate", function)
    menu.add(item)


def add_menu_label(menu, name):
    item = Gtk.ImageMenuItem(name)
    item.set_sensitive(False)
    item.show()
    menu.add(item)


def add_visible_profile_menu_item(menu, name, function, strength):
    if strength > 98:
        add_menu_item(menu, name, function,
                      '/usr/share/icons/hicolor/22x22/apps/nm-signal-100.png')
    elif strength >= 75:
        add_menu_item(menu, name, function,
                      '/usr/share/icons/hicolor/22x22/apps/nm-signal-75.png')
    elif strength >= 50:
        add_menu_item(menu, name, function,
                      '/usr/share/icons/hicolor/22x22/apps/nm-signal-50.png')
    elif strength >= 25:
        add_menu_item(menu, name, function,
                      '/usr/share/icons/hicolor/22x22/apps/nm-signal-25.png')
    else:
        add_menu_item(menu, name, function,
                      '/usr/share/icons/hicolor/22x22/apps/nm-signal-00.png')


def choose_profile(*arguments):
    print('choose_profile: '),
    pprint.pprint(arguments)
    print('Launching: ' + arguments[0].get_name())


def show_menu(widget, event, applet):
    if event.type == Gtk.gdk.BUTTON_PRESS and \
        (event.button == 1 or event.button == 3):
        menu = Gtk.Menu()

        add_menu_label(menu, 'Active Mesh')

        actives, visibles, strengths = get_visible_adhocs()
        profiles = get_profiles()
        for profile in actives:
            if profile in profiles:
                add_menu_item(menu, profile[0], choose_profile,
                              '/usr/share/icons/hicolor/22x22/apps/nm-adhoc.png')

        sep = Gtk.SeparatorMenuItem(); sep.show(); menu.add(sep)
        add_menu_label(menu, 'Available Profiles')
        for profile in profiles:
            if profile in actives:
                continue
            elif profile in visibles:
                add_visible_profile_menu_item(menu, profile[0], choose_profile,
                                              strengths[profile[0]])
            else:
                add_menu_item(menu, profile[0], choose_profile)

        sep = Gtk.SeparatorMenuItem(); sep.show(); menu.add(sep)
        add_menu_item(menu, 'Show Mesh Status', show_mesh_status)
        add_menu_item(menu, Gtk.STOCK_ABOUT, show_about)
        sep = Gtk.SeparatorMenuItem(); sep.show(); menu.add(sep)
        add_menu_item(menu, Gtk.STOCK_QUIT, do_exit)
        menu.popup( None, None, None, event.button, event.time )

        widget.emit_stop_by_name("button_press_event")


def show_mesh_status(*arguments):
    print('show_mesh_status'),
    pprint.pprint(arguments)


def show_about(*arguments):
    about_dialog = Gtk.AboutDialog()
    about_dialog.set_destroy_with_parent(True)
    about_dialog.set_program_name('Commotion Mesh Applet')
    about_dialog.set_comments('Commotion is an open-source communication tool that uses mobile phones, computers, and other wireless devices to create decentralized mesh networks.')
    about_dialog.set_website('https://commotionwireless.net/')
    icon = Gtk.gdk.pixbuf_new_from_file(os.path.join(commotion_mesh_panel_imagedir,
                                        'commotion.svg'))
    about_dialog.set_logo(icon)

    def close(dialog, response, editor):
        dialog.destroy()
    about_dialog.connect("response", close, None)

    about_dialog.show_all()


def do_exit(*arguments):
    sys.exit()


def applet_factory(applet, iid, data = None):
    applet.set_background_widget(applet) # /* enable transparency hack */

    icon = Gtk.gdk.pixbuf_new_from_file(os.path.join(commotion_mesh_panel_imagedir,
                                                     'commotion-mesh-disconnected.svg'))
    image = Gtk.Image()
    image.set_from_pixbuf(icon.scale_simple(22, 22, Gtk.gdk.INTERP_BILINEAR))
    button = Gtk.Button()
    button.set_relief(Gtk.RELIEF_NONE)
    button.set_image(image)
    button.connect("button_press_event", show_menu, applet)
    applet.add(button)
    applet.show_all()
    print('Factory started')
    return True

commotion_mesh_panel_imagedir = '/usr/share/icons/hicolor/scalable/apps'

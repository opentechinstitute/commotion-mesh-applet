#!/usr/bin/python

from commotion import MeshStatus

import glob
import NetworkManager
import os
import pyjavaproperties
import sys

import pprint

try:
    from gi.repository import Gtk
except: # Can't use ImportError, as gi.repository isn't quite that nice...
    import gtk as Gtk


class PortingHacks():
    '''
    This is a collection of things that are quite similar across GTK versions,
    but not named the same.  The setup code for each GTK version should set
    these.
    '''

    BUTTONS_CLOSE = None
    DIALOG_DESTROY_WITH_PARENT = None
    MESSAGE_ERROR = None
    MESSAGE_OTHER = None
    FILE_CHOOSER_ACTION_SAVE = None
    RESPONSE_CANCEL = None
    RESPONSE_OK = None
    SELECTION_NONE = None
    STOCK_ABOUT = None
    pixbuf_new_from_file = None


class CommotionMeshApplet():

    svg_dir = '/usr/share/icons/hicolor/scalable/apps'
    nm_icon_dir = '/usr/share/icons/hicolor/22x22/apps'

    def __init__(self, portinghacks):
        self.port = portinghacks
        self.meshstatus = MeshStatus(portinghacks)


    def get_visible_adhocs(self):
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


    def get_profiles(self):
        '''get all the available mesh profiles and return as a list of tuples'''
        profiles = []
        for f in glob.glob('/etc/nm-dispatcher-olsrd/*.profile'):
            p = pyjavaproperties.Properties()
            p.load(open(f))
            bssid = p['bssid'].upper()
            channel = int(p['channel'])
            profiles.append(tuple([p['ssid'], bssid, channel]))
        return tuple(profiles)


    def add_menu_about(self):
        self.add_menu_item(self.port.STOCK_ABOUT, self.show_about)


    def add_menu_gtk2_quit(self):
        self.add_menu_item(Gtk.STOCK_QUIT, self.do_exit)


    def add_menu_separator(self):
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.menu.add(sep)


    def add_menu_item(self, name, function, imagefile=None):
        item = Gtk.ImageMenuItem(name)
        if imagefile:
            icon = Gtk.Image()
            icon.set_from_file(imagefile)
            item.set_image(icon)
        item.show()
        item.connect( "activate", function)
        self.menu.add(item)


    def add_menu_label(self, name):
        item = Gtk.ImageMenuItem(name)
        item.set_sensitive(False)
        item.show()
        self.menu.add(item)


    def add_visible_profile_menu_item(self, name, function, strength):
        if strength > 98:
            self.add_menu_item(menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-100.png'))
        elif strength >= 75:
            self.add_menu_item(menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-75.png'))
        elif strength >= 50:
            self.add_menu_item(menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-50.png'))
        elif strength >= 25:
            self.add_menu_item(menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-25.png'))
        else:
            self.add_menu_item(menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-00.png'))


    def choose_profile(self, *arguments):
        print('choose_profile: '),
        pprint.pprint(arguments)
        print('Launching: ' + arguments[0].get_name())


    def show_menu(self, widget, event, applet):
        if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.create_menu()
            self.menu.popup( None, None, None, event.button, event.time )
            widget.emit_stop_by_name("button_press_event")


    def create_menu(self):
        self.menu = Gtk.Menu()

        self.add_menu_label('Active Mesh')

        actives, visibles, strengths = self.get_visible_adhocs()
        profiles = self.get_profiles()
        for profile in actives:
            if profile in profiles:
                self.add_menu_item(profile[0], self.choose_profile,
                                   os.path.join(self.nm_icon_dir, 'nm-adhoc.png'))
                self.add_menu_label('BSSID: ' + profile[1])
                self.add_menu_label('Channel: ' + str(profile[2]))
                self.add_menu_separator()

        self.add_menu_label('Available Profiles')
        for profile in profiles:
            if profile in actives:
                continue
            elif profile in visibles:
                self.add_visible_profile_menu_item(profile[0], self.choose_profile,
                                                   strengths[profile[0]])
            else:
                self.add_menu_item(profile[0], self.choose_profile)

        self.add_menu_separator()
        self.add_menu_item('Show Mesh Status', self.show_mesh_status)
        self.add_menu_item('Show Debug Log', self.show_debug_log)
        self.add_menu_item('Save Mesh Status To File...', self.save_mesh_status_to_file)
        self.add_menu_separator()
        self.add_menu_about()

        return self.menu


    def show_mesh_status(self, *arguments):
        self.meshstatus.show()


    def show_debug_log(self, *arguments):
        os.system('xdg-open /tmp/nm-dispatcher-olsrd.log &')


    def save_mesh_status_to_file(self, *arguments):
        toplevel = arguments[0].get_toplevel()
        dialog = Gtk.FileChooserDialog("Save Mesh Status to File...",
                                       toplevel,
                                       self.port.FILE_CHOOSER_ACTION_SAVE,
                                       (Gtk.STOCK_CANCEL, self.port.RESPONSE_CANCEL,
                                        Gtk.STOCK_SAVE, self.port.RESPONSE_OK))
        dialog.set_default_response(self.port.RESPONSE_OK)
        dialog.set_do_overwrite_confirmation(True)

        file_filter = Gtk.FileFilter()
        file_filter.add_pattern("*.json")
        file_filter.set_name("JSON (*.json)")
        dialog.add_filter(file_filter)

        file_filter = Gtk.FileFilter()
        file_filter.add_pattern("*")
        file_filter.set_name("All files (*.*)")
        dialog.add_filter(file_filter)

        response = dialog.run()
        msg = None
        if response == self.port.RESPONSE_OK:
            filename = dialog.get_filename()
            if not filename.endswith('.json'):
                filename += '.json'
            dump = self.meshstatus.dump()
            if dump:
                with open(filename, 'w') as f:
                    f.write(dump)
            else:
                msg = Gtk.MessageDialog(toplevel,
                                        self.port.DIALOG_DESTROY_WITH_PARENT,
                                        self.port.MESSAGE_ERROR,
                                        (Gtk.BUTTONS_CLOSE),
                                        'Nothing was written because olsrd is not running, there is no active mesh profile!')
                msg.run()
                msg.destroy()
        dialog.destroy()


    def show_about(self, *arguments):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_program_name('Commotion Mesh Applet')
        about_dialog.set_comments('Commotion is an open-source communication tool that uses mobile phones, computers, and other wireless devices to create decentralized mesh networks.')
        about_dialog.set_website('https://commotionwireless.net/')
        icon = self.port.pixbuf_new_from_file(os.path.join(self.svg_dir,
                                                           'commotion.svg'))
        about_dialog.set_logo(icon)

        def close(dialog, response, editor):
            dialog.destroy()
        about_dialog.connect("response", close, None)

        about_dialog.show_all()


    def do_exit(self, *arguments):
        sys.exit()


    def setup_gtk2_applet(self, applet):
        icon = self.port.pixbuf_new_from_file(os.path.join(self.svg_dir,
                                                           'commotion-mesh-disconnected.svg'))
        image = Gtk.Image()
        image.set_from_pixbuf(icon.scale_simple(22, 22, Gtk.gdk.INTERP_BILINEAR))
        button = Gtk.Button()
        button.set_relief(Gtk.RELIEF_NONE)
        button.set_image(image)
        button.connect("button_press_event", self.show_menu, applet)
        applet.add(button)
        applet.show_all()


def applet_factory(applet, iid, data = None):
    # set GTK2-specific versions of things
    port = PortingHacks()
    port.BUTTONS_CLOSE = Gtk.BUTTONS_CLOSE
    port.FILE_CHOOSER_ACTION_SAVE = Gtk.FILE_CHOOSER_ACTION_SAVE
    port.MESSAGE_ERROR = Gtk.MESSAGE_ERROR
    port.MESSAGE_OTHER = Gtk.MESSAGE_OTHER
    port.RESPONSE_CANCEL = Gtk.RESPONSE_CANCEL
    port.RESPONSE_OK = Gtk.RESPONSE_OK
    port.DIALOG_DESTROY_WITH_PARENT = Gtk.DIALOG_DESTROY_WITH_PARENT
    port.SELECTION_NONE = Gtk.SELECTION_NONE
    port.STOCK_ABOUT = Gtk.STOCK_ABOUT
    port.pixbuf_new_from_file = Gtk.gdk.pixbuf_new_from_file
    cma = CommotionMeshApplet(port)
    cma.setup_gtk2_applet(applet)
    print('Factory started')
    return True

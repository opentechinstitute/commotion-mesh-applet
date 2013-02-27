#!/usr/bin/python

import glob
import json
import NetworkManager
import os
import pyjavaproperties
import re
import sys
import threading
import time
import urllib2

import pprint

try:
    from gi.repository import Gtk
except: # Can't use ImportError, as gi.repository isn't quite that nice...
    import gtk as Gtk


class JsonInfo():

    def __init__(self, baseurl='http://localhost:9090'):
        self.baseurl = baseurl
        self.jsondecoder = json.JSONDecoder()

    def dump(self, data='/all'):
        try:
            return urllib2.urlopen(self.baseurl + data).read()
        except urllib2.URLError:
            return None

    def dict(self, data='/all'):
        dump = self.dump(data)
        if dump:
            return self.jsondecoder.decode(dump)


class MeshStatus():

    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.jsoninfo = JsonInfo()
        self.imagedir = commotion_mesh_panel_png_dir

    def _set_icon(self, cell, filename):
        fullfilename = os.path.join(self.imagedir, filename)
        cell.set_property("pixbuf", Gtk.gdk.pixbuf_new_from_file(fullfilename))

    def _internet_icon(self, column, cell, model, iter):
        if model[iter][3]:
            self._set_icon(cell, 'default_route.png')

    def _hna_icon(self, column, cell, model, iter):
        if model[iter][4]:
            self._set_icon(cell, 'other_route.png')

    def show(self):
        window = Gtk.Window()
        window.set_title('Mesh Status (Links and HNA)')
        window.set_resizable(False)
        vbox = Gtk.VBox(homogeneous=False, spacing=5)
        window.add(vbox)

        links_hna = self.jsoninfo.dict('/links/hna')
        # liststore data:  IP, LQ, NLQ, have_internet, have_HNA
        liststore = Gtk.ListStore(str, int, int, bool, bool)
        if links_hna:
            connected = True
            hna = []
            internet = []
            for i in links_hna['hna']:
                if i['destination'] == '0.0.0.0':
                    internet.append(i['gateway'])
                else:
                    hna.append(i['gateway'])
            for link in links_hna['links']:
                ip = link['remoteIP']
                lqPercent = int(link['linkQuality']*100)
                nlqPercent = int(link['neighborLinkQuality']*100)
                cell = [ ip, lqPercent, nlqPercent ]
                if ip in internet:
                    cell.append(True)
                else:
                    cell.append(False)
                if ip in hna:
                    cell.append(True)
                else:
                    cell.append(False)
                liststore.append(cell)
        else:
            connected = False
        myip = link['localIP']

        infobar = Gtk.InfoBar()
        if connected:
            infobar.set_message_type(Gtk.MESSAGE_OTHER)
            label = Gtk.Label('mesh address: ' + myip)
        else:
            infobar.set_message_type(Gtk.MESSAGE_ERROR)
            label = Gtk.Label('Not connected to a mesh!')
        content = infobar.get_content_area()
        content.set_homogeneous(False)
        content.pack_start(label, expand=False)
        if myip in hna:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'other_route.png'))
            content.pack_start(image, expand=False)
            need_filler = True
        else:
            need_filler = False
        if myip in internet:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'default_route.png'))
            # leave empty space so the internet icon is properly aligned
            if need_filler:
                content.pack_start(image, expand=False)
            else:
                content.pack_end(image, expand=False)
        vbox.pack_start(infobar, False)

        treeview = Gtk.TreeView(model=liststore)
        selection = treeview.get_selection()
        selection.set_mode(Gtk.SELECTION_NONE)
        vbox.pack_start(treeview, True, True, 3)

        column = Gtk.TreeViewColumn("Link IP Address")
        column.set_alignment(0.5)
        treeview.append_column(column)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, False)
        column.add_attribute(cell, "text", 0)

        column = Gtk.TreeViewColumn("LQ")
        column.set_alignment(0.5)
        column.set_resizable(True)
        treeview.append_column(column)
        cell = Gtk.CellRendererProgress()
        column.pack_start(cell, True)
        column.add_attribute(cell, "value", 1)

        column = Gtk.TreeViewColumn("NLQ")
        column.set_alignment(0.5)
        column.set_resizable(True)
        treeview.append_column(column)
        cell = Gtk.CellRendererProgress()
        column.pack_start(cell, True)
        column.add_attribute(cell, "value", 2)

        column = Gtk.TreeViewColumn("HNA?")
        column.set_alignment(0.5)
        column.set_resizable(False)
        treeview.append_column(column)
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, self._hna_icon)

        column = Gtk.TreeViewColumn("Internet?")
        column.set_alignment(0.5)
        column.set_resizable(False)
        treeview.append_column(column)
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, self._internet_icon)

        window.show_all()


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


def add_menu_about(menu):
    add_menu_item(menu, Gtk.STOCK_ABOUT, show_about)


def add_menu_separator(menu):
    sep = Gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)


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
    if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 1:
        menu = Gtk.Menu()

        add_menu_label(menu, 'Active Mesh')

        actives, visibles, strengths = get_visible_adhocs()
        profiles = get_profiles()
        for profile in actives:
            if profile in profiles:
                add_menu_item(menu, profile[0], choose_profile,
                              '/usr/share/icons/hicolor/22x22/apps/nm-adhoc.png')

        add_menu_separator(menu)
        add_menu_label(menu, 'Available Profiles')
        for profile in profiles:
            if profile in actives:
                continue
            elif profile in visibles:
                add_visible_profile_menu_item(menu, profile[0], choose_profile,
                                              strengths[profile[0]])
            else:
                add_menu_item(menu, profile[0], choose_profile)

        add_menu_separator(menu)
        add_menu_item(menu, 'Show Mesh Status', show_mesh_status)
        add_menu_item(menu, 'Show Debug Log', show_debug_log)
        add_menu_item(menu, 'Save Mesh Status To File...', save_mesh_status_to_file)
        add_menu_separator(menu)
        add_menu_about(menu)

        menu.popup( None, None, None, event.button, event.time )
        widget.emit_stop_by_name("button_press_event")


def show_mesh_status(*arguments):
    MeshStatus(arguments[0].get_toplevel()).show()


def show_debug_log(*arguments):
    os.system('xdg-open /tmp/nm-dispatcher-olsrd.log &')


def save_mesh_status_to_file(*arguments):
    toplevel = arguments[0].get_toplevel()
    dialog = Gtk.FileChooserDialog("Save Mesh Status to File...",
                                   toplevel,
                                   Gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL,
                                    Gtk.STOCK_SAVE, Gtk.RESPONSE_OK))
    dialog.set_default_response(Gtk.RESPONSE_OK)
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
    if response == Gtk.RESPONSE_OK:
        filename = dialog.get_filename()
        if not filename.endswith('.json'):
            filename += '.json'
        dump = JsonInfo().dump('/all')
        if dump:
            with open(filename, 'w') as f:
                f.write(dump)
        else:
            msg = Gtk.MessageDialog(toplevel,
                                    Gtk.DIALOG_DESTROY_WITH_PARENT,
                                    Gtk.MESSAGE_ERROR,
                                    (Gtk.BUTTONS_CLOSE),
                                    'Nothing was written because olsrd is not running, there is no active mesh profile!')
            msg.run()
            msg.destroy()
    dialog.destroy()


def show_about(*arguments):
    about_dialog = Gtk.AboutDialog()
    about_dialog.set_destroy_with_parent(True)
    about_dialog.set_program_name('Commotion Mesh Applet')
    about_dialog.set_comments('Commotion is an open-source communication tool that uses mobile phones, computers, and other wireless devices to create decentralized mesh networks.')
    about_dialog.set_website('https://commotionwireless.net/')
    icon = Gtk.gdk.pixbuf_new_from_file(os.path.join(commotion_mesh_panel_svg_dir,
                                        'commotion.svg'))
    about_dialog.set_logo(icon)

    def close(dialog, response, editor):
        dialog.destroy()
    about_dialog.connect("response", close, None)

    about_dialog.show_all()


def do_exit(*arguments):
    sys.exit()


def applet_factory(applet, iid, data = None):
    icon = Gtk.gdk.pixbuf_new_from_file(os.path.join(commotion_mesh_panel_svg_dir,
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

commotion_mesh_panel_svg_dir = '/usr/share/icons/hicolor/scalable/apps'
commotion_mesh_panel_png_dir = '/usr/share/icons/hicolor/scalable/apps'

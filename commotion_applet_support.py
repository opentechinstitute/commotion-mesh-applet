#!/usr/bin/python

import dbus.mainloop.glib ; dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
import glob
import json
import NetworkManager
import os
import pyjavaproperties
import sys
import urllib2

import pprint

try:
    from gi.repository import Gtk, GObject
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

    def __init__(self, portinghacks):
        self.port = portinghacks
        self.jsoninfo = JsonInfo()
        self.imagedir = '/usr/share/icons/hicolor/32x32/actions'
        # liststore data:  IP, LQ, NLQ, have_internet, have_HNA
        self.liststore = Gtk.ListStore(str, int, int, bool, bool)
        self.mesh_connected = False
        self.myip = ''
        self.other_routes = []
        self.default_routes = []

    def _set_icon(self, cell, filename=None):
        if filename:
            fullfilename = os.path.join(self.imagedir, filename)
            cell.set_property("pixbuf", self.port.pixbuf_new_from_file(fullfilename))
        else:
            cell.set_property("pixbuf", None)

    def _default_route_icon(self, column, cell, model, iter, destroy=None):
        if model[iter][3]:
            self._set_icon(cell, 'default_route.png')
        else:
            self._set_icon(cell)

    def _other_route_icon(self, column, cell, model, iter, destroy=None):
        if model[iter][4]:
            self._set_icon(cell, 'other_route.png')
        else:
            self._set_icon(cell)

    def dump(self, which='/all'):
        return JsonInfo().dump(which)

    def update(self):
        self.liststore.clear()

        links_hna = self.jsoninfo.dict('/links/hna')
        if links_hna:
            self.mesh_connected = True
            self.other_routes = []
            self.default_routes = []
            for i in links_hna['hna']:
                if i['destination'] == '0.0.0.0':
                    self.default_routes.append(i['gateway'])
                else:
                    self.other_routes.append(i['gateway'])
            for link in links_hna['links']:
                ip = link['remoteIP']
                lqPercent = int(link['linkQuality']*100)
                nlqPercent = int(link['neighborLinkQuality']*100)
                cell = [ ip, lqPercent, nlqPercent ]
                if ip in self.default_routes:
                    cell.append(True)
                else:
                    cell.append(False)
                if ip in self.other_routes:
                    cell.append(True)
                else:
                    cell.append(False)
                self.liststore.append(cell)
        else:
            self.mesh_connected = False
        if link:
            self.myip = link['localIP']
        else:
            self.myip = ''

        return True

    def on_delete_event(self, widget, event):
        GObject.source_remove(self.timeout_id)
        return False

    def show(self):
        self.update()
        self.timeout_id = GObject.timeout_add(5000, self.update)
        window = Gtk.Window()
        window.set_title('Mesh Status (Links and HNA)')
        window.set_resizable(False)
        window.connect('delete-event', self.on_delete_event)
        vbox = Gtk.VBox(homogeneous=False, spacing=5)
        window.add(vbox)

        infobar = Gtk.InfoBar()
        if self.mesh_connected:
            infobar.set_message_type(self.port.MESSAGE_OTHER)
            label = Gtk.Label('mesh address: ' + self.myip)
        else:
            infobar.set_message_type(self.port.MESSAGE_ERROR)
            label = Gtk.Label('Not connected to a mesh!')
        content = infobar.get_content_area()
        content.set_homogeneous(False)
        content.pack_start(label, False, True, 0)
        if self.myip in self.other_routes:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'other_route.png'))
            content.pack_start(image, False, True, 0)
            need_filler = True
        else:
            need_filler = False
        if self.myip in self.default_routes:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'default_route.png'))
            # leave empty space so the internet icon is properly aligned
            if need_filler:
                content.pack_start(image, False, True, 0)
            else:
                content.pack_end(image, False, True, 0)
        vbox.pack_start(infobar, False, True, 0)

        treeview = Gtk.TreeView(model=self.liststore)
        selection = treeview.get_selection()
        selection.set_mode(self.port.SELECTION_NONE)
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
        column.set_cell_data_func(cell, self._other_route_icon)

        column = Gtk.TreeViewColumn("Internet?")
        column.set_alignment(0.5)
        column.set_resizable(False)
        treeview.append_column(column)
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, self._default_route_icon)

        window.show_all()


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

        self.menu = Gtk.Menu()
        # update the menu whenever NetworkManager changes
        NetworkManager.NetworkManager.connect_to_signal('StateChanged', self.create_menu)
        NetworkManager.NetworkManager.connect_to_signal('PropertiesChanged', self.create_menu)
        NetworkManager.NetworkManager.connect_to_signal('DeviceAdded', self.create_menu)
        NetworkManager.NetworkManager.connect_to_signal('DeviceRemoved', self.create_menu)


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


    def add_menu_quit(self):
        self.add_menu_item("Quit", self.do_exit)


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
            self.add_menu_item(self.menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-100.png'))
        elif strength >= 75:
            self.add_menu_item(self.menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-75.png'))
        elif strength >= 50:
            self.add_menu_item(self.menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-50.png'))
        elif strength >= 25:
            self.add_menu_item(self.menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-25.png'))
        else:
            self.add_menu_item(self.menu, name, function,
                               os.path.join(self.nm_icon_dir, 'nm-signal-00.png'))


    def choose_profile(self, *arguments):
        connections = NetworkManager.Settings.ListConnections()
        pprint.pprint(connections)
        connections = dict([(x.GetSettings()['connection']['id'], x) for x in connections])

        name = arguments[0].get_label()
        try:
            conn = connections[name]
        except KeyError as e:
            print('error: ' + name + ' does not exist as a connection (' + str(e) + ')')
            return

        ctype = conn.GetSettings()['connection']['type']
        if ctype != '802-11-wireless':
            print(name + ' is not a wifi device!')
            return

        devices = NetworkManager.NetworkManager.GetDevices()
        for dev in devices:
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                break
        else:
            print('No wifi device found!')
            return

        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")


    def show_menu(self, widget, event, applet):
        if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.menu.popup( None, None, None, event.button, event.time )
            widget.emit_stop_by_name("button_press_event")


    def create_menu(self, ignored=None):
        # empty the menu first before filling it up
        for widget in self.menu.get_children():
            self.menu.remove(widget)

        header_added = False
        actives, visibles, strengths = self.get_visible_adhocs()
        profiles = self.get_profiles()
        for profile in actives:
            if profile in profiles:
                if not header_added:
                    self.add_menu_label('Active Mesh')
                    header_added = True
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
        self.add_menu_quit()

        return True


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

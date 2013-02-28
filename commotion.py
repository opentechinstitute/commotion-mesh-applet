
import json
import os
import urllib2

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

    def __init__(self, portinghacks):
        self.port = portinghacks
        self.jsoninfo = JsonInfo()
        self.imagedir = '/usr/share/icons/hicolor/32x32/actions'

    def _set_icon(self, cell, filename):
        fullfilename = os.path.join(self.imagedir, filename)
        cell.set_property("pixbuf", self.port.pixbuf_new_from_file(fullfilename))

    def _internet_icon(self, column, cell, model, iter, destroy=None):
        if model[iter][3]:
            self._set_icon(cell, 'default_route.png')

    def _hna_icon(self, column, cell, model, iter, destroy=None):
        if model[iter][4]:
            self._set_icon(cell, 'other_route.png')

    def dump(self, which='/all'):
        return JsonInfo().dump(which)

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
            infobar.set_message_type(self.port.MESSAGE_OTHER)
            label = Gtk.Label('mesh address: ' + myip)
        else:
            infobar.set_message_type(self.port.MESSAGE_ERROR)
            label = Gtk.Label('Not connected to a mesh!')
        content = infobar.get_content_area()
        content.set_homogeneous(False)
        content.pack_start(label, False, True, 0)
        if myip in hna:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'other_route.png'))
            content.pack_start(image, False, True, 0)
            need_filler = True
        else:
            need_filler = False
        if myip in internet:
            image = Gtk.Image()
            image.set_from_file(os.path.join(self.imagedir, 'default_route.png'))
            # leave empty space so the internet icon is properly aligned
            if need_filler:
                content.pack_start(image, False, True, 0)
            else:
                content.pack_end(image, False, True, 0)
        vbox.pack_start(infobar, False, True, 0)

        treeview = Gtk.TreeView(model=liststore)
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
        column.set_cell_data_func(cell, self._hna_icon)

        column = Gtk.TreeViewColumn("Internet?")
        column.set_alignment(0.5)
        column.set_resizable(False)
        treeview.append_column(column)
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, self._internet_icon)

        window.show_all()

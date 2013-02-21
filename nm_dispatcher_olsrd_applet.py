
import glob
import re
import sys

import pprint

try:
    from gi.repository import Gtk
except: # Can't use ImportError, as gi.repository isn't quite that nice...
    import gtk as Gtk



def add_menu_item(menu, name, function, image=None):
    item = Gtk.ImageMenuItem(name)
    if image:
        item.set_image(image)
    item.show()
    item.connect( "activate", function)
    menu.add(item)


def choose_profile(*arguments):
    print('choose_profile: '),
    pprint.pprint(arguments)
    print('Launching: ' + arguments[0].get_name())


def show_menu(widget, event, applet):
    if event.type == Gtk.gdk.BUTTON_PRESS and \
        (event.button == 1 or event.button == 3):
        menu = Gtk.Menu()

        present_icon = Gtk.Image()
        present_icon.set_from_file('/usr/share/icons/hicolor/22x22/apps/nm-adhoc.png')
        for f in glob.glob('/etc/nm-dispatcher-olsrd/*.profile'):
            m = re.match('/etc/nm-dispatcher-olsrd/(.*)\.profile', f)
            if m:
                add_menu_item(menu, m.group(1), choose_profile, present_icon)
        sep0 = Gtk.SeparatorMenuItem(); sep0.show(); menu.add(sep0)
        add_menu_item(menu, 'Show Mesh Status', show_mesh_status)
        sep1 = Gtk.SeparatorMenuItem(); sep1.show(); menu.add(sep1)
        add_menu_item(menu, Gtk.STOCK_HELP, show_help)
        add_menu_item(menu, Gtk.STOCK_ABOUT, show_about)
        sep2 = Gtk.SeparatorMenuItem(); sep2.show(); menu.add(sep2)
        add_menu_item(menu, Gtk.STOCK_QUIT, do_exit)
        menu.popup( None, None, None, event.button, event.time )

        widget.emit_stop_by_name("button_press_event")


def show_mesh_status(*arguments):
    print('show_mesh_status'),
    pprint.pprint(arguments)


def show_help(*arguments):
    print('show_help'),
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

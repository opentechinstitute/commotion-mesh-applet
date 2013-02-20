
import re
import sys

try:
    from gi.repository import Gtk
except: # Can't use ImportError, as gi.repository isn't quite that nice...
    import gtk as Gtk


def show_menu(widget, event, applet):
    print('--------------------------------------------------')
    print('show_menu: '),
    print(widget),
    print(event),
    print(applet)
    #if event.type == Gtk.gdk.BUTTON_PRESS and event.button == 1:
    create_menu(applet)
    widget.emit_stop_by_name("button_press_event")


def create_menu(applet):
    button3="""
<popup name="button3">
  <separator />
  <menuitem name="About" verb="About" label="_About" pixtype="stock" pixname="gtk-about"/>
  <menuitem name="Quit" verb="Quit" label="_Quit" pixtype="stock" pixname="exit"/>
</popup>
"""
    button1 = re.sub('name="button3"', 'name="button1"', button3)
    verbs = [("About", show_about),
             ("Quit", do_exit)]
    applet.setup_menu(button3, verbs, None)
    applet.setup_menu(button1, verbs, None)
    print('create_menu: '),
    print(applet)


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

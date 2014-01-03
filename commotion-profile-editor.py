#!/usr/bin/env python

# example text.py

import gtk
import sys

class ProfileEditor:

    def close_application(self, widget, text):
        textbuf = text.get_buffer()
        output = textbuf.get_text(textbuf.get_start_iter(), textbuf.get_end_iter())
        outfile = open(profile, "w")
        if outfile:
            outfile.write(output)
            outfile.close()
        gtk.mainquit()

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_usize(600, 500)
        window.set_policy(gtk.TRUE, gtk.TRUE, gtk.FALSE)  
        window.connect("destroy", self.close_application)
        window.set_title("Edit network profile: " + profile)
        window.set_border_width(0)

        box1 = gtk.VBox(gtk.FALSE, 0)
        window.add(box1)
        box1.show()

        box2 = gtk.VBox(gtk.FALSE, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, gtk.TRUE, gtk.TRUE, 0)
        box2.show()

        table = gtk.Table(2, 2, gtk.FALSE)
        table.set_row_spacing(0, 2)
        table.set_col_spacing(0, 2)
        box2.pack_start(table, gtk.TRUE, gtk.TRUE, 0)
        table.show()

        # Create the GtkText widget
        text = gtk.TextView()
        textbuf = text.get_buffer()
        text.set_editable(gtk.TRUE)
        table.attach(text, 0, 1, 0, 1,
		    gtk.EXPAND | gtk.SHRINK | gtk.FILL,
		    gtk.EXPAND | gtk.SHRINK | gtk.FILL, 0, 0)
        text.show()

        # Add a vertical scrollbar to the GtkText widget
        vscrollbar = gtk.VScrollbar(text.get_vadjustment())
        table.attach(vscrollbar, 1, 2, 0, 1,
		    gtk.FILL, gtk.EXPAND | gtk.SHRINK | gtk.FILL, 0, 0)
        vscrollbar.show()

        # Realizing a widget creates a window for it,
        # ready for us to insert some text
        text.realize()

        # Load the file text.py into the text window
        infile = open(profile, "r")

        if infile:
            string = infile.read()
            infile.close()
            textbuf.set_text(string)

        hbox = gtk.HButtonBox()
        box2.pack_start(hbox, gtk.FALSE, gtk.FALSE, 0)
        hbox.show()

        text.set_editable(True)
	text.set_wrap_mode(gtk.WRAP_WORD)

        separator = gtk.HSeparator()
        box1.pack_start(separator, gtk.FALSE, gtk.TRUE, 0)
        separator.show()

        box2 = gtk.VBox(gtk.FALSE, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, gtk.FALSE, gtk.TRUE, 0)
        box2.show()

        button = gtk.Button("Save and Exit")
        button.connect("clicked", self.close_application, text)
        box2.pack_start(button, gtk.TRUE, gtk.TRUE, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
        button.show()
        window.show()

def main():
    gtk.mainloop()
    return 0       

if __name__ == "__main__":
    profile = sys.argv[1]
    ProfileEditor()
    main()

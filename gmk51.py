#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import calculator
from keys import *
from emulator import Emulator
from program import Program

class Window(Gtk.Window):
    def __init__(self):
        super().__init__(title="MK-51 / FX-2500")

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.display = Gtk.Label()
        self.display.set_justify(Gtk.Justification.RIGHT)

        self.vbox.pack_start(self.display, expand=True, fill=True, padding=0)

        self.fn_grid = Gtk.Grid()
        fn_buttons = [
            [None, ("C", KC), None, ("pi", KPI), ("MODE", KMODE), ("F", KF)],
            [("lg", KLOG), ("ln", KLN), ("DMS", KDMS), ("SIN", KSIN),
             ("COS", KCOS), None],
            [("SQRT", KSQRT), ("POW", KPOW), ("1/x", KINV), None, None, None]]
        for i, row in enumerate(fn_buttons):
            for j, p in enumerate(row):
                if p is None: continue
                label, key = p
                b = Gtk.Button.new_with_label(label)
                b.connect("clicked", self.on_clicked, key)
                self.fn_grid.attach(b, j, i, 1, 1)

        self.vbox.pack_start(self.fn_grid, expand=True, fill=True, padding=0)

        self.num_grid = Gtk.Grid()
        num_buttons = [
            [("7", K7), ("8", K8), ("9", K9), (":", KDIV), ("Min", KMIN)],
            [("4", K4), ("5", K5), ("6", K6), ("x", KMUL), ("MR", KMR)],
            [("1", K1), ("2", K2), ("3", K3), ("-", KMUL), ("M+", KMIN)],
            [("0", K0), (".", KP), ("/-/", KNEG), ("+", KPLUS), ("=", KEQ)]]

        for i, row in enumerate(num_buttons):
            for j, (label, key) in enumerate(row):
                b = Gtk.Button.new_with_label(label)
                b.connect("clicked", self.on_clicked, key)
                self.num_grid.attach(b, j, i, 1, 1)

        self.vbox.pack_start(self.num_grid, expand=True, fill=True, padding=0)

        self.add(self.vbox)

        self.emulator = Emulator(Program.from_file())

    def on_clicked(self, widget, key):
        self.emulator.until(0x3c5)
        self.emulator.keycode = key
        self.emulator.until(0x3c3)
        self.emulator.keycode = 0
        self.display.set_text(calculator.get_display(self.emulator)[0])
        print("Clicked", key)


if __name__ == "__main__":
    win = Window()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

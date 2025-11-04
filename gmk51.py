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

        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.display = Gtk.Label()
        self.display.set_justify(Gtk.Justification.RIGHT)
        self.display.set_halign(Gtk.Align.END)
        self.modes = Gtk.Label()
        self.modes.set_justify(Gtk.Justification.RIGHT)
        self.modes.set_halign(Gtk.Align.END)
        display_box.pack_start(self.modes, expand=False, fill=False,
                               padding=0)
        display_box.pack_start(self.display, expand=False, fill=False,
                               padding=0)

        display_frame = Gtk.Frame()
        display_frame.add(display_box)
        self.vbox.pack_start(display_frame,
                             expand=True, fill=False, padding=0)

        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append("mk51", "MK-51")
        self.type_combo.append("fx2500", "FX-2500")
        self.type_combo.set_active_id("mk51")
        self.type_combo.connect("changed", self.on_type_changed)

        self.vbox.pack_start(self.type_combo,
                             expand=True, fill=False, padding=0)


        self.keyboard_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.build_mk51_keyboard(self.keyboard_vbox)
        self.vbox.pack_start(self.keyboard_vbox,
                             expand=True, fill=True, padding=0)

        self.add(self.vbox)

        self.emulator = Emulator(Program.from_file())
        self.emulator.until(0x3c3)
        self.update_display()

    def build_mk51_keyboard(self, vbox):
        fn_grid = Gtk.Grid()
        fn_grid.set_halign(Gtk.Align.CENTER)
        fn_grid.set_column_homogeneous(True)
        fn_buttons = [
            [None, ("C", KC), ("CE", KCE),
             ('EXP <span color="red">π</span>', KEXP),
             ("MODE", KMODE),
             ('<span color="red">F</span>', KF)],
            [('log <span color="red">10<sup>x</sup></span>', KLOG),
             ('ln <span color="red">e<sup>x</sup></span>', KLN),
             ("°′″", KDMS),
             ('sin<span color="red"><sup>-1</sup></span>', KSIN),
             ('cos<span color="red"><sup>-1</sup></span>', KCOS),
             ('tan<span color="red"><sup>-1</sup></span>', KTAN)],
            [('√<span overline="single"> </span>'
              '<span color="red">x<sup>2</sup></span>', KSQRT),
             ("y<sup>x</sup> "
              '<span color="red"><sup>x</sup>√'
              '<span overline="single">y</span></span>', KPOW),
             ('1/x <span color="red">n!</span>', K1OVERX),
             ('↔ <span color="red">x↔M</span>', KSWAP),
             ("[(", KLBR), (")]", KRBR)]]
        for i, row in enumerate(fn_buttons):
            for j, p in enumerate(row):
                if p is None: continue
                label, key = p
                b = Gtk.Button("")
                child = b.get_child()
                child.set_markup(label)
                b.connect("clicked", self.on_clicked, key)
                fn_grid.attach(b, j, i, 1, 1)

        vbox.pack_start(fn_grid, expand=True, fill=True, padding=0)

        num_grid = Gtk.Grid()
        num_grid.set_halign(Gtk.Align.CENTER)
        num_grid.set_column_homogeneous(True)
        num_buttons = [
            [("7", K7), ("8", K8), ("9", K9), ("÷", KDIV), ("Min", KMIN)],
            [("4", K4), ("5", K5), ("6", K6), ("x", KMUL), ("MR", KMR)],
            [("1", K1), ("2", K2), ("3", K3), ("-", KMINUS), ("M+", KMPLUS)],
            [("0", K0), (".", KP), ("/-/", KNEG), ("+", KPLUS), ("=", KEQ)]]

        for i, row in enumerate(num_buttons):
            for j, (label, key) in enumerate(row):
                b = Gtk.Button.new_with_label(label)
                b.connect("clicked", self.on_clicked, key)
                num_grid.attach(b, j, i, 1, 1)

        vbox.pack_start(num_grid, expand=True, fill=True, padding=0)

    def build_fx2500_keyboard(self, vbox):
        fn_grid = Gtk.Grid()
        fn_grid.set_halign(Gtk.Align.CENTER)
        fn_grid.set_column_homogeneous(True)
        fn_buttons = [
            [None,
             ('<span color="red">INV</span>', KINV), ("MODE", KMODE),
             ('log <span color="red">10<sup>x</sup></span>', KLOG),
             ('ln <span color="red">e<sup>x</sup></span>', KLN),
             ("x<sup>y</sup> "
              '<span color="red">x<sup>1/y</sup></span>', KPOW),
             ],
            [("+/-", KNEG),
             ('√<span overline="single"> </span>'
              '<span color="red">x<sup>2</sup></span>', KSQRT),
             ("°′″", KDMS),
             ('sin<span color="red"><sup>-1</sup></span>', KSIN),
             ('cos<span color="red"><sup>-1</sup></span>', KCOS),
             ('tan<span color="red"><sup>-1</sup></span>', KTAN)],
            [('1/x <span color="red">x!</span>', K1OVERX),
             ('X↔Y<span color="red">M</span>', KSWAP),
             ("[(", KLBR), (")]", KRBR), ("M in", KMIN), ("MR", KMR)]]
        for i, row in enumerate(fn_buttons):
            for j, p in enumerate(row):
                if p is None: continue
                label, key = p
                b = Gtk.Button("")
                child = b.get_child()
                child.set_markup(label)
                b.connect("clicked", self.on_clicked, key)
                fn_grid.attach(b, j, i, 1, 1)

        vbox.pack_start(fn_grid, expand=True, fill=True, padding=0)

        num_grid = Gtk.Grid()
        num_grid.set_halign(Gtk.Align.CENTER)
        num_grid.set_column_homogeneous(True)
        num_buttons = [
            [("7", K7), ("8", K8), ("9", K9), ("C", KCE), ("AC", KC)],
            [("4", K4), ("5", K5), ("6", K6), ("x", KMUL), ("÷:", KDIV)],
            [("1", K1), ("2", K2), ("3", K3), ("+", KPLUS), ("-", KMINUS)],
            [("0", K0), (".", KP), ('EXP <span color="red">π</span>', KEXP),
             ("=", KEQ), ("M+", KMPLUS)]]

        for i, row in enumerate(num_buttons):
            for j, (label, key) in enumerate(row):
                b = Gtk.Button("")
                child = b.get_child()
                child.set_markup(label)
                b.connect("clicked", self.on_clicked, key)
                num_grid.attach(b, j, i, 1, 1)

        vbox.pack_start(num_grid, expand=True, fill=True, padding=0)

    def on_type_changed(self, widget):
        t = widget.get_active_id()
        self.keyboard_vbox.foreach(
            lambda widget: self.keyboard_vbox.remove(widget))

        if t == "mk51":
            self.build_mk51_keyboard(self.keyboard_vbox)
        elif t == "fx2500":
            self.build_fx2500_keyboard(self.keyboard_vbox)
        self.keyboard_vbox.show_all()

    def on_clicked(self, widget, key):
        self.emulator.until(0x3c5)
        self.emulator.keycode = key
        self.emulator.until(0x3c3)
        self.emulator.keycode = 0
        self.update_display()

    def update_display(self):
        num, ind = calculator.get_display(self.emulator)
        self.display.set_text(num)
        self.modes.set_text(ind)


if __name__ == "__main__":
    win = Window()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk
from aiowebostv import endpoints as ep
from lib.connection import TVConnection
from lib.helpers import MOUSE_SENSITIVITY, normalize_url, format_volume, find_app


class TVRemote(Gtk.Application):
    def __init__(self, ip=None):
        super().__init__(application_id="com.lgtv.remote")
        self.conn = TVConnection(ip=ip) if ip else TVConnection()
        self.status = None
        self.url_entry = None
        self.text_entry = None
        self.vol_label = None
        self._last_x = 0
        self._last_y = 0

    def _set_status(self, text):
        GLib.idle_add(self.status.set_text, text)

    def _update_vol_label(self):
        text = format_volume(self.tv.tv_state.volume, self.tv.tv_state.muted)
        GLib.idle_add(self.vol_label.set_text, text)

    def _run(self, coro):
        self.conn.run_async(coro)

    @property
    def tv(self):
        return self.conn.tv

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="LG TV Remote")
        win.set_default_size(320, 560)
        win.set_resizable(False)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        win.set_child(main_box)

        # Status
        self.status = Gtk.Label(label="Connecting...")
        self.status.add_css_class("dim-label")
        main_box.append(self.status)

        # Power row
        power_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        power_row.set_halign(Gtk.Align.CENTER)
        main_box.append(power_row)

        btn_power = self._btn("Off", lambda *_: self._run(self.tv.power_off()))
        btn_power.add_css_class("destructive-action")
        power_row.append(btn_power)

        btn_close = self._btn("Close App", self._close_current_app)
        power_row.append(btn_close)

        btn_home = self._btn("Home", lambda *_: self._run(self.tv.button("HOME")))
        power_row.append(btn_home)

        btn_back = self._btn("Back", lambda *_: self._run(self.tv.button("BACK")))
        power_row.append(btn_back)

        btn_exit = self._btn("Exit", lambda *_: self._run(self.tv.button("EXIT")))
        power_row.append(btn_exit)

        main_box.append(Gtk.Separator())

        # Touchpad area
        touchpad_label = Gtk.Label(label="Touchpad (drag to move, click to select)")
        touchpad_label.add_css_class("dim-label")
        main_box.append(touchpad_label)

        touchpad = Gtk.DrawingArea()
        touchpad.set_size_request(290, 180)
        touchpad.set_draw_func(self._draw_touchpad)
        touchpad.set_can_focus(True)
        touchpad.set_focusable(True)
        self._touchpad = touchpad

        drag = Gtk.GestureDrag.new()
        drag.connect("drag-begin", self._touchpad_begin)
        drag.connect("drag-update", self._touchpad_move)
        drag.connect("drag-end", self._touchpad_end)
        touchpad.add_controller(drag)

        click = Gtk.GestureClick.new()
        click.connect("released", self._touchpad_click)
        touchpad.add_controller(click)

        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        scroll.connect("scroll", self._touchpad_scroll)
        touchpad.add_controller(scroll)

        frame = Gtk.Frame()
        frame.set_child(touchpad)
        main_box.append(frame)

        # Scroll buttons under touchpad
        scroll_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        scroll_row.set_halign(Gtk.Align.CENTER)
        main_box.append(scroll_row)

        btn_scr_up = self._btn("Scroll Up", lambda *_: self._run(self.tv.scroll(0, 3)))
        scroll_row.append(btn_scr_up)

        btn_scr_down = self._btn("Scroll Down", lambda *_: self._run(self.tv.scroll(0, -3)))
        scroll_row.append(btn_scr_down)

        main_box.append(Gtk.Separator())

        # D-Pad
        dpad = Gtk.Grid()
        dpad.set_halign(Gtk.Align.CENTER)
        dpad.set_row_spacing(4)
        dpad.set_column_spacing(4)
        main_box.append(dpad)

        for label, key, col, row in [
            ("▲", "UP", 1, 0),
            ("◀", "LEFT", 0, 1),
            ("▶", "RIGHT", 2, 1),
            ("▼", "DOWN", 1, 2),
        ]:
            btn = self._btn(label, lambda *_, k=key: self._run(self.tv.button(k)))
            btn.set_size_request(80, 50)
            dpad.attach(btn, col, row, 1, 1)

        btn_ok = self._btn("OK", lambda *_: self._run(self.tv.button("ENTER")))
        btn_ok.set_size_request(80, 50)
        btn_ok.add_css_class("suggested-action")
        dpad.attach(btn_ok, 1, 1, 1, 1)

        main_box.append(Gtk.Separator())

        # Volume with label
        vol_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vol_row.set_halign(Gtk.Align.CENTER)
        main_box.append(vol_row)

        btn_vdown = self._btn("Vol-", self._vol_down)
        btn_vdown.set_size_request(80, 40)
        vol_row.append(btn_vdown)

        self.vol_label = Gtk.Label(label="Vol: --")
        self.vol_label.set_size_request(80, 40)
        vol_row.append(self.vol_label)

        btn_vup = self._btn("Vol+", self._vol_up)
        btn_vup.set_size_request(80, 40)
        vol_row.append(btn_vup)

        btn_mute = self._btn("Mute", self._toggle_mute)
        btn_mute.set_size_request(60, 40)
        vol_row.append(btn_mute)

        main_box.append(Gtk.Separator())

        # Text input (for typing into TV text fields)
        text_label = Gtk.Label(label="Type text to TV")
        text_label.add_css_class("dim-label")
        main_box.append(text_label)

        text_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.append(text_box)

        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("Type here...")
        self.text_entry.set_hexpand(True)
        self.text_entry.connect("activate", self._send_text)
        text_box.append(self.text_entry)

        btn_send = self._btn("Send", self._send_text)
        text_box.append(btn_send)

        btn_del = self._btn("Del", lambda *_: self._run(
            self.tv.request(ep.SEND_DELETE, {"count": 1})
        ))
        text_box.append(btn_del)

        main_box.append(Gtk.Separator())

        # Notification
        notif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.append(notif_box)

        self.notif_entry = Gtk.Entry()
        self.notif_entry.set_placeholder_text("Send notification to TV...")
        self.notif_entry.set_hexpand(True)
        self.notif_entry.connect("activate", self._send_notif)
        notif_box.append(self.notif_entry)

        btn_notif = self._btn("Notify", self._send_notif)
        notif_box.append(btn_notif)

        main_box.append(Gtk.Separator())

        # Apps
        app_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        app_row.set_halign(Gtk.Align.CENTER)
        main_box.append(app_row)

        app_row.append(self._btn("YouTube", lambda *_: self._launch("youtube")))
        app_row.append(self._btn("Browser", lambda *_: self._launch("com.webos.app.browser")))

        main_box.append(Gtk.Separator())

        # URL bar
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.append(url_box)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter URL...")
        self.url_entry.set_hexpand(True)
        self.url_entry.connect("activate", self._open_url)
        url_box.append(self.url_entry)

        btn_go = self._btn("Go", self._open_url)
        btn_go.add_css_class("suggested-action")
        url_box.append(btn_go)


        # Keyboard shortcuts
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key)
        win.add_controller(key_ctrl)

        win.present()

        # Connect + subscribe to volume
        def on_connected():
            self._set_status("Connected!")
            self._update_vol_label()
            self.conn.run_async(self._subscribe_volume())

        self.conn.start(
            on_connected=on_connected,
            on_failed=lambda e: self._set_status(f"Failed: {e}"),
        )

    # -- Apps --

    def _close_current_app(self, *_):
        async def do():
            app_id = self.tv.tv_state.current_app_id
            if app_id:
                await self.tv.close_app(app_id)
                self._set_status(f"Closed: {app_id}")
        self._run(do())

    # -- Volume --

    async def _subscribe_volume(self):
        def on_volume_change(state):
            GLib.idle_add(self._update_vol_label)
        await self.tv.register_state_update_callback(on_volume_change)

    def _vol_up(self, *_):
        async def do():
            await self.tv.volume_up()
            self._update_vol_label()
        self._run(do())

    def _vol_down(self, *_):
        async def do():
            await self.tv.volume_down()
            self._update_vol_label()
        self._run(do())

    def _toggle_mute(self, *_):
        async def do():
            muted = self.tv.tv_state.muted
            await self.tv.set_mute(not muted)
            self._update_vol_label()
        self._run(do())

    # -- Text input --

    def _send_text(self, *_):
        text = self.text_entry.get_text()
        if not text:
            return
        async def do():
            await self.tv.request(ep.INSERT_TEXT, {
                "text": text, "replace": 0
            })
            self._set_status(f"Sent: {text}")
        self._run(do())
        self.text_entry.set_text("")

    # -- Touchpad --

    def _draw_touchpad(self, area, cr, w, h):
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.15)
        cr.rectangle(0, 0, w, h)
        cr.fill()

    def _touchpad_begin(self, gesture, x, y):
        self._last_x = 0
        self._last_y = 0
        self._drag_start_x = x
        self._drag_start_y = y
        # Hide cursor during drag
        self._touchpad.set_cursor(Gdk.Cursor.new_from_name("none"))

    def _touchpad_move(self, gesture, off_x, off_y):
        dx = int(off_x * MOUSE_SENSITIVITY) - int(self._last_x * MOUSE_SENSITIVITY)
        dy = int(off_y * MOUSE_SENSITIVITY) - int(self._last_y * MOUSE_SENSITIVITY)
        self._last_x = off_x
        self._last_y = off_y
        if dx != 0 or dy != 0:
            self._run(self.tv.move(dx, dy))
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def _touchpad_end(self, gesture, off_x, off_y):
        # Restore cursor
        self._touchpad.set_cursor(None)

    def _touchpad_click(self, gesture, n_press, x, y):
        self._run(self.tv.click())

    def _touchpad_scroll(self, controller, dx, dy):
        self._run(self.tv.scroll(0, int(dy * 2)))
        return True

    # -- Buttons --

    def _btn(self, label, callback):
        btn = Gtk.Button(label=label)
        btn.connect("clicked", callback)
        return btn

    def _launch(self, query):
        async def do():
            result = find_app(self.tv.tv_state.apps, query)
            if result:
                app_id, app_info = result
                await self.tv.launch_app(app_id)
                self._set_status(f"Launched: {app_info.get('title', app_id)}")
            else:
                self._set_status(f"App not found: {query}")
        self._run(do())

    def _send_notif(self, *_):
        msg = self.notif_entry.get_text().strip()
        if not msg:
            return
        self._run(self.tv.send_message(msg))
        self._set_status(f"Notified: {msg}")
        self.notif_entry.set_text("")

    def _open_url(self, *_):
        url = self.url_entry.get_text().strip()
        if not url:
            return
        url = normalize_url(url)
        async def do():
            await self.tv.request(ep.OPEN, {"target": url})
            self._set_status(f"Opened: {url}")
        self._run(do())

    def _on_key(self, ctrl, keyval, keycode, state):
        key_map = {
            Gdk.KEY_Up: "UP", Gdk.KEY_Down: "DOWN",
            Gdk.KEY_Left: "LEFT", Gdk.KEY_Right: "RIGHT",
            Gdk.KEY_Return: "ENTER", Gdk.KEY_KP_Enter: "ENTER",
            Gdk.KEY_Escape: "BACK",
            Gdk.KEY_plus: "VOLUMEUP", Gdk.KEY_minus: "VOLUMEDOWN",
            Gdk.KEY_m: "MUTE", Gdk.KEY_h: "HOME", Gdk.KEY_space: "PLAY",
        }
        # Don't capture keys when text entries are focused
        if self.url_entry and self.url_entry.has_focus():
            return False
        if self.text_entry and self.text_entry.has_focus():
            return False
        if self.notif_entry and self.notif_entry.has_focus():
            return False
        name = key_map.get(keyval)
        if name:
            self._run(self.tv.button(name))
            return True
        return False


def main(ip=None):
    app = TVRemote(ip=ip)
    app.run()

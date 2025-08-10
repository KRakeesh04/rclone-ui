import gi
import subprocess
import threading
import os

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

class RcloneGUI(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.RcloneGUI")

    def do_activate(self, *args):
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("Rclone Desktop App")
        win.set_default_size(900, 600)
        win.set_resizable(False)

        sidebar = Gtk.ListBox()
        sidebar.set_selection_mode(Gtk.SelectionMode.SINGLE)
        sidebar.add_css_class("navigation-sidebar")

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(300)

        download_page = self.create_download_page()
        stack.add_named(download_page, "downloads")

        # TODO: need to create page
        lst_remote_folders_page = self.create_remote_lsd_page()
        stack.add_named(lst_remote_folders_page, "remote_folders")

        # TODO: need to create page
        # remotes_page = Gtk.Label(label="Available remotes and add new remotes will go here...")
        remotes_page = self.create_remotes_page()
        stack.add_named(remotes_page, "remotes")

        # TODO: need to create page
        config_setting_page = Gtk.Label(label="Cofig settings will be here")
        stack.add_named(config_setting_page, "config_settings")

        downloads_row = Gtk.ListBoxRow()
        downloads_row.set_child(Gtk.Label(label="Downloads", xalign=0))
        remote_lsd_row = Gtk.ListBoxRow()
        remote_lsd_row.set_child(Gtk.Label(label="Remote folders", xalign=0))
        remotes_row = Gtk.ListBoxRow()
        remotes_row.set_child(Gtk.Label(label="Remotes", xalign=0))
        config_settings_row = Gtk.ListBoxRow()
        config_settings_row.set_child(Gtk.Label(label="Config settings", xalign=0))

        sidebar.append(downloads_row)
        sidebar.append(remote_lsd_row)
        sidebar.append(remotes_row)
        sidebar.append(config_settings_row)

        def on_row_selected(lb, row):
            if row == downloads_row:
                stack.set_visible_child_name("downloads")
            elif row == remote_lsd_row:
                stack.set_visible_child_name("remote_folders")
            elif row == remotes_row:
                stack.set_visible_child_name("remotes")
            elif row == config_settings_row:
                stack.set_visible_child_name("config_settings")
            

        sidebar.connect("row-selected", on_row_selected)
        sidebar.select_row(downloads_row)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.append(sidebar)
        main_box.append(stack)

        win.set_child(main_box)
        win.present()

    ###### download page ######
    def create_download_page(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=10,
            margin_start=10,
            margin_end=10,
            margin_bottom=10,
        )
        box.set_size_request(750,600)

        src_row_box, src_remote_combo, src_path_entry = self.set_path_components("source")
        dest_row_box, dest_remote_combo, dest_path_entry = self.set_path_components("destination")

        # --- Download output area ---
        output_view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        output_scroll = Gtk.ScrolledWindow()
        output_scroll.set_child(output_view)
        output_scroll.set_vexpand(True)

        # --- Start download button ---
        start_btn = Gtk.Button(label="Start Download")
        start_btn.connect(
            "clicked",
            lambda btn: self.start_rclone_download(src_remote_combo, src_path_entry, dest_remote_combo, dest_path_entry, output_view, start_btn),
        )

        # Add to page
        box.append(src_row_box)
        box.append(dest_row_box)
        box.append(start_btn)
        box.append(output_scroll)

        return box

    def set_path_components(self, value : str):
        # --- Remote selector + Path input + File chooser ---
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row_box.set_size_request(750, 20)

        # Prepare ListStore model for remote combo box
        remote_store = Gtk.ListStore(str)
        remote_store.append(["None (Local Path)"])  # Default option
        for remote in self.get_rclone_remotes():
            remote_store.append([remote])

        # Create combo box with ListStore model
        remote_combo = Gtk.ComboBox.new_with_model(remote_store)

        # Add text renderer for displaying strings
        renderer = Gtk.CellRendererText()
        remote_combo.pack_start(renderer, True)
        remote_combo.add_attribute(renderer, "text", 0)
        remote_combo.set_active(0)  # Select first item by default

        # Path input
        if value == "source" :
            path_entry = Gtk.Entry(placeholder_text="Enter source path...")
        elif value == "destination" :
            path_entry = Gtk.Entry(placeholder_text="Enter destination path...")
        path_entry.set_size_request(400, 20)
        # File/folder mode selector
        mode_combo = Gtk.ComboBoxText()
        mode_combo.append_text("File")
        mode_combo.append_text("Folder")
        mode_combo.set_active(0)  # Default: File

        # File chooser button
        file_button = Gtk.Button(label="Browse...")
        file_button.connect(
            "clicked", lambda btn: self.select_path(path_entry, mode_combo)
        )

        row_box.append(remote_combo)
        row_box.append(path_entry)
        row_box.append(mode_combo)
        row_box.append(file_button)

        return row_box, remote_combo, path_entry

    def get_active_text(combo):
        idx = combo.get_active()
        if idx == -1:
            return None
        model = combo.get_model()
        return model.get_string(idx)



    def get_rclone_remotes(self):
        try:
            output = subprocess.check_output(["rclone", "listremotes"], text=True).splitlines()
            return [r.strip().rstrip(":") for r in output if r.strip()]
        except Exception:
            return []

    def select_path(self, entry_widget, mode_combo):
        mode = mode_combo.get_active_text()

        if mode == "Folder":
            action = Gtk.FileChooserAction.SELECT_FOLDER
            title = "Select a Folder"
        else:
            action = Gtk.FileChooserAction.OPEN
            title = "Select a File"

        dialog = Gtk.FileChooserNative(
            title=title,
            action=action,
            transient_for=self.get_active_window()
        )

        def on_response(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                selected_path = dialog.get_file().get_path()
                entry_widget.set_text(selected_path)
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def start_rclone_download(self, src_remote_combo, src_path_entry, dest_remote_combo, dest_path_entry, output_view, btn):
        src_selected_remote = self.get_active_text(src_remote_combo)
        src_path = src_path_entry.get_text().strip()

        dest_selected_remote = self.get_active_text(dest_remote_combo)
        dest_path = dest_path_entry.get_text().strip()

        if not src_path :
            self.append_output(output_view, "[ERROR] Path is empty.\n")
            return

        if src_selected_remote != "None (Local Path)":
            source = f"{src_selected_remote}:{src_path}"
        else:
            source = src_path
        if dest_selected_remote != "None (Local Path)":
            dest = f"{dest_selected_remote}:{dest_path}"
        else:
            dest = dest_path


        btn.set_sensitive(False)

        def worker():
            if len(dest) == 0 :
                process = subprocess.Popen(
                    ["rclone", "copy", source, "./downloads", "--progress"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            else :
                process = subprocess.Popen(
                    ["rclone", "copy", source, dest, "--progress"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            for line in process.stdout:
                GLib.idle_add(self.append_output, output_view, line)
            process.wait()
            GLib.idle_add(lambda: btn.set_sensitive(True))

        threading.Thread(target=worker, daemon=True).start()

    def append_output(self, output_view, text):
        buf = output_view.get_buffer()
        buf.insert(buf.get_end_iter(), text)

    ###### remote lsd page ######
    def create_remote_lsd_page(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=10,
            margin_start=10,
            margin_end=10,
            margin_bottom=10,
        )
        box.set_size_request(750,600)
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(500)

        remotes = self.get_rclone_remotes()
        for remote in remotes :
            remote_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            remote_box.append(Gtk.Label(label=remote + " lsd should appear here"))
            stack.add_titled(remote_box, remote, remote.capitalize())

        # Navigation
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)

        box.append(switcher)
        box.append(stack)
    
        return box
    
    ###### Add Remotes page ######
    def create_remotes_page(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=10,
            margin_start=10,
            margin_end=10,
            margin_bottom=10,
        )
        box.set_size_request(750,600)

        remotes = self.get_rclone_remotes()
        output_view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        output_scroll = Gtk.ScrolledWindow()
        output_scroll.set_child(output_view)
        output_scroll.set_vexpand(True)
        for remote in remotes:
            self.append_output(output_view, remote + "\t\t")
        add_btn = Gtk.Button(label="Add Remote")
        add_btn.connect(
            "clicked",
            lambda btn: self.start_rclone_download(),
        )

        box.append(add_btn)
        box.append(output_scroll)

        return box


app = RcloneGUI()
app.run()

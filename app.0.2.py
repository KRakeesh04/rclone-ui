import gi
import subprocess
import threading
import re
import subprocess
from collections import defaultdict

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib



class RcloneGUI(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.RcloneGUI")

    ################################# Main Page #################################
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

        # Page - 01
        download_page = self.create_download_page()
        stack.add_named(download_page, "downloads")

        # Page -02
        lst_remote_folders_page = self.create_remote_lsd_page()
        stack.add_named(lst_remote_folders_page, "remote_folders")

        # TODO: need to create page
        remotes_page = Gtk.Label(label="Available remotes and add new remotes will go here...")
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
    ##############################################################################
    ############################## download page #################################
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

        # Progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_bar.set_text("Progress")

        # Output view (optional debug)
        output_view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        output_scroll = Gtk.ScrolledWindow()
        output_scroll.set_child(output_view)
        output_scroll.set_vexpand(True)

        # Start button
        start_btn = Gtk.Button(label="Start Download")
        start_btn.connect(
            "clicked",
            lambda btn: self.start_rclone_download(
                src_remote_combo,
                src_path_entry,
                dest_remote_combo,
                dest_path_entry,
                output_view,
                start_btn,
                progress_bar
            ),
        )

        # Build layout
        box.append(src_row_box)
        box.append(dest_row_box)
        box.append(start_btn)
        box.append(progress_bar)
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

    def get_active_text(self, combo):
        idx = combo.get_active()
        if idx == -1:
            return None
        model = combo.get_model()
        tree_iter = model.get_iter(Gtk.TreePath.new_from_indices([idx]))
        return model.get_value(tree_iter, 0)

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

    def start_rclone_download(self, src_remote_combo, src_path_entry, dest_remote_combo, dest_path_entry, output_view, btn, progress_bar):
        src_selected_remote = self.get_active_text(src_remote_combo)
        src_path = src_path_entry.get_text().strip()
        dest_selected_remote = self.get_active_text(dest_remote_combo)
        dest_path = dest_path_entry.get_text().strip()

        if not src_path:
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
        progress_bar.set_fraction(0.0)
        progress_bar.set_text("Starting...")

        def worker():
            cmd = ["rclone", "copy", source, dest if dest else "./downloads", "--progress", "--transfers", "1", "--checkers", "1"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # for line in process.stdout:
            #     match = re.search(r"(\d+)%", line)
            #     if match:
            #         percent = int(match.group(1)) / 100
            #         GLib.idle_add(progress_bar.set_fraction, percent)
            #         GLib.idle_add(progress_bar.set_text, f"{match.group(1)}%")
            #     else:
            #         GLib.idle_add(progress_bar.set_text, line.strip())
            current_percent_text = ""

            for line in process.stdout:
                match = re.search(r"(\d+)%", line)
                if match:
                    percent = int(match.group(1)) / 100
                    current_percent_text = f"{match.group(1)}%"
                    GLib.idle_add(progress_bar.set_fraction, percent)
                    GLib.idle_add(progress_bar.set_text, current_percent_text)
                else:
                    status_text = line.strip()
                    if current_percent_text:
                        GLib.idle_add(progress_bar.set_text, f"{status_text} – {current_percent_text}")
                    else:
                        GLib.idle_add(progress_bar.set_text, status_text)


            process.wait()
            GLib.idle_add(progress_bar.set_fraction, 1.0)
            GLib.idle_add(progress_bar.set_text, "Completed")
            GLib.idle_add(lambda: btn.set_sensitive(True))

        threading.Thread(target=worker, daemon=True).start()
    ##############################################################################

    def append_output(self, output_view, text):
        buf = output_view.get_buffer()
        buf.insert(buf.get_end_iter(), text)

    ############################## Remote lsd page ##############################
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
            lsd = self.build_remote_tree(remote+":/")

            output_view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
            output_scroll = Gtk.ScrolledWindow()
            output_scroll.set_child(output_view)
            output_scroll.set_vexpand(True)
            remote_box.append(output_scroll)

            print(remote+"/")
            self.append_output(output_view, remote+"/\n")
            self.display_lsd(lsd, 0, output_view)
            remote_box.append(Gtk.Label(label=remote + " lsd should appear here"))
            stack.add_titled(remote_box, remote, remote.capitalize())

        # Navigation
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)

        box.append(switcher)
        box.append(stack)
    
        return box
    
    def tree(self):
        """Creates a nested defaultdict that auto-creates dicts."""
        return defaultdict(self.tree)

    def insert_path(self, root, path_parts):
        """Insert a file/folder path into the nested dictionary."""
        if len(path_parts) == 1:
            # Mark as file only if it doesn't exist
            if not isinstance(root.get(path_parts[0], None), dict):
                root[path_parts[0]] = None
        else:
            # Ensure this is a dict (folder), not a file
            if root.get(path_parts[0]) is None:
                root[path_parts[0]] = self.tree()
            self.insert_path(root[path_parts[0]], path_parts[1:])

    def build_remote_tree(self, remote_path):
        """
        Builds a nested dictionary representing the remote file hierarchy.

        :param remote_path: Remote path like 'remote:/folder'
        :return: Nested dict structure
        """
        try:
            output = subprocess.check_output(
                ["rclone", "lsf", "-R", remote_path],
                stderr=subprocess.STDOUT
            ).decode().splitlines()

            hierarchy = self.tree()
            for line in output:
                if not line.strip():
                    continue
                parts = line.strip("/").split("/")
                self.insert_path(hierarchy, parts)

            return hierarchy

        except subprocess.CalledProcessError as e:
            print("Error fetching hierarchy:", e.output.decode())
            return {}
    
    def display_lsd(self, lsd, level, output_view):
        for i in lsd:
            if lsd[i] == None:
                self.append_output(output_view, " "*level*5 + "├── " + i + "\n")
                # print(" "*level*3 + "├── " + i)
                continue
            else :
                self.append_output(output_view, " "*level*5 + "├── " + i + " /\n")
                # print(" "*level*4 + "├── " + i + " /")
            self.display_lsd(lsd[i], level+1, output_view)
    ##############################################################################


    ############################## Add Remotes page ##############################
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
    ##############################################################################


app = RcloneGUI()
app.run()

"""
STL Simplifier Viewer - Interactive tool for simplifying STL meshes.

Provides a GUI built with Open3D for batch loading, previewing (Face & Wireframe),
simplifying, and saving STL files.
"""

import os
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np


class STLSimplifierApp:
    """
    Main application class for the STL Simplifier Viewer.

    Layout:
      - Left panel: file list, controls (target faces, apply buttons, wireframe toggle, info labels, save)
      - Right panel: 3D SceneWidget for interactive preview
    """

    MENU_OPEN = 1
    MENU_SAVE_ALL = 2
    MENU_QUIT = 3
    MENU_SAVE_SELECTED = 4

    def __init__(self):
        # --- Data ---
        self._file_paths = []           # list of absolute paths
        # path -> o3d.geometry.TriangleMesh (original)
        self._original_meshes = {}
        # path -> o3d.geometry.TriangleMesh (possibly simplified)
        self._current_meshes = {}
        self._selected_index = -1       # index in _file_paths
        self._show_wireframe = False

        # --- App & Window ---
        self._app = gui.Application.instance
        self._app.initialize()

        self._window = self._app.create_window(
            "STL Simplifier Viewer", 1280, 800)
        em = self._window.theme.font_size  # unit of measurement

        # === Menu Bar ===
        if gui.Application.instance.menubar is None:
            file_menu = gui.Menu()
            file_menu.add_item("Load STL(s)...", STLSimplifierApp.MENU_OPEN)
            file_menu.add_item("Save Selected...",
                               STLSimplifierApp.MENU_SAVE_SELECTED)
            file_menu.add_item("Save All...", STLSimplifierApp.MENU_SAVE_ALL)
            file_menu.add_separator()
            file_menu.add_item("Quit", STLSimplifierApp.MENU_QUIT)
            menu = gui.Menu()
            menu.add_menu("File", file_menu)
            gui.Application.instance.menubar = menu

        self._window.set_on_menu_item_activated(
            STLSimplifierApp.MENU_OPEN, self._on_load)
        self._window.set_on_menu_item_activated(
            STLSimplifierApp.MENU_SAVE_SELECTED, self._on_save_selected)
        self._window.set_on_menu_item_activated(
            STLSimplifierApp.MENU_SAVE_ALL, self._on_save_all)
        self._window.set_on_menu_item_activated(
            STLSimplifierApp.MENU_QUIT, self._on_quit)

        # === Left Panel ===
        self._panel = gui.Vert(
            0.5 * em, gui.Margins(0.5 * em, 0.5 * em, 0.5 * em, 0.5 * em))

        # -- Load Button --
        load_btn = gui.Button("Load STL(s)")
        load_btn.set_on_clicked(self._on_load)
        self._panel.add_child(load_btn)

        # -- File List --
        self._panel.add_child(gui.Label("Loaded Files:"))
        self._file_list = gui.ListView()
        self._file_list.set_on_selection_changed(self._on_file_selected)
        self._panel.add_child(self._file_list)

        # -- Separator --
        self._panel.add_child(gui.Label("----------------------------"))

        # -- Target Faces --
        faces_layout = gui.Horiz(0.25 * em)
        faces_layout.add_child(gui.Label("Target Faces:"))
        self._faces_edit = gui.NumberEdit(gui.NumberEdit.INT)
        self._faces_edit.int_value = 500
        self._faces_edit.set_limits(4, 10000000)
        faces_layout.add_child(self._faces_edit)
        self._panel.add_child(faces_layout)

        # -- Apply Buttons --
        apply_selected_btn = gui.Button("Apply to Selected")
        apply_selected_btn.set_on_clicked(self._on_apply_selected)
        self._panel.add_child(apply_selected_btn)

        apply_all_btn = gui.Button("Apply to All")
        apply_all_btn.set_on_clicked(self._on_apply_all)
        self._panel.add_child(apply_all_btn)

        # -- Reset Buttons --
        reset_selected_btn = gui.Button("Reset Selected")
        reset_selected_btn.set_on_clicked(self._on_reset_selected)
        self._panel.add_child(reset_selected_btn)

        reset_all_btn = gui.Button("Reset All")
        reset_all_btn.set_on_clicked(self._on_reset_all)
        self._panel.add_child(reset_all_btn)

        # -- Separator --
        self._panel.add_child(gui.Label("----------------------------"))

        # -- Wireframe Toggle --
        self._wireframe_cb = gui.Checkbox("Show Wireframe")
        self._wireframe_cb.checked = False
        self._wireframe_cb.set_on_checked(self._on_wireframe_toggled)
        self._panel.add_child(self._wireframe_cb)

        # -- Separator --
        self._panel.add_child(gui.Label("----------------------------"))

        # -- Info Labels --
        self._info_original = gui.Label("Original Faces: -")
        self._info_current = gui.Label("Current Faces:  -")
        self._info_vertices = gui.Label("Vertices:       -")
        self._panel.add_child(self._info_original)
        self._panel.add_child(self._info_current)
        self._panel.add_child(self._info_vertices)

        # -- Separator --
        self._panel.add_child(gui.Label("----------------------------"))

        # -- Save Buttons --
        save_selected_btn = gui.Button("Save Selected")
        save_selected_btn.set_on_clicked(self._on_save_selected)
        self._panel.add_child(save_selected_btn)

        save_all_btn = gui.Button("Save All")
        save_all_btn.set_on_clicked(self._on_save_all)
        self._panel.add_child(save_all_btn)

        # === 3D Scene ===
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(self._window.renderer)
        self._scene.scene.set_background(
            [0.15, 0.15, 0.18, 1.0])  # dark background

        # === Layout ===
        self._window.set_on_layout(self._on_layout)
        self._window.add_child(self._panel)
        self._window.add_child(self._scene)

    # ────────────────────── Layout ──────────────────────

    def _on_layout(self, layout_ctx):
        """Arrange left panel and 3D scene side by side."""
        r = self._window.content_rect
        panel_width = 22 * layout_ctx.theme.font_size  # ~22 em
        self._panel.frame = gui.Rect(r.x, r.y, panel_width, r.height)
        self._scene.frame = gui.Rect(r.x + panel_width, r.y,
                                     r.width - panel_width, r.height)

    # ────────────────────── Load ──────────────────────

    def _on_load(self):
        """Open a file dialog to load one or multiple STL files."""
        dlg = gui.FileDialog(gui.FileDialog.OPEN,
                             "Select STL file(s)", self._window.theme)
        dlg.add_filter(".stl .STL", "STL files (*.stl)")
        dlg.add_filter("", "All files")
        dlg.set_on_cancel(self._on_dialog_cancel)
        dlg.set_on_done(self._on_load_done)
        self._window.show_dialog(dlg)

    def _on_load_done(self, path):
        """Handle a single file selection. Also scan the directory for batch loading."""
        self._window.close_dialog()
        if not path:
            return

        # Detect sibling STL files in the same directory for batch loading
        parent_dir = os.path.dirname(path)
        stl_files = sorted([
            os.path.join(parent_dir, f)
            for f in os.listdir(parent_dir)
            if f.lower().endswith(".stl") and "_collision" not in f.lower()
        ])

        if not stl_files:
            stl_files = [path]

        # Load all
        for fp in stl_files:
            if fp not in self._original_meshes:
                try:
                    mesh = o3d.io.read_triangle_mesh(fp)
                    if not mesh.has_vertex_normals():
                        mesh.compute_vertex_normals()
                    self._original_meshes[fp] = mesh
                    # Deep copy for mutable current mesh
                    current = o3d.geometry.TriangleMesh(mesh)
                    self._current_meshes[fp] = current
                    self._file_paths.append(fp)
                except Exception as e:
                    print(f"[Error] Failed to load {fp}: {e}")

        # Update list widget
        self._file_list.set_items([os.path.basename(p)
                                  for p in self._file_paths])

        # Select the file the user picked
        if path in self._file_paths:
            idx = self._file_paths.index(path)
        else:
            idx = 0
        self._file_list.selected_index = idx
        self._on_file_selected(None, False)  # trigger preview

    # ────────────────────── File Selection ──────────────────────

    def _on_file_selected(self, new_val, is_double_click):
        """When a file is clicked in the list, preview it."""
        idx = self._file_list.selected_index
        if idx < 0 or idx >= len(self._file_paths):
            return
        self._selected_index = idx
        self._update_preview()

    # ────────────────────── Preview ──────────────────────

    def _update_preview(self):
        """Render the currently selected mesh in the 3D scene."""
        if self._selected_index < 0:
            return
        path = self._file_paths[self._selected_index]
        mesh = self._current_meshes.get(path)
        original = self._original_meshes.get(path)
        if mesh is None:
            return

        # Clear scene
        self._scene.scene.clear_geometry()

        # Material
        mat = rendering.MaterialRecord()
        mat.shader = "defaultLit"
        mat.base_color = [0.65, 0.75, 0.85, 1.0]

        # Add mesh
        if not mesh.has_vertex_normals():
            mesh.compute_vertex_normals()
        self._scene.scene.add_geometry("mesh", mesh, mat)

        # Wireframe overlay
        if self._show_wireframe:
            wireframe = o3d.geometry.LineSet.create_from_triangle_mesh(mesh)
            wireframe.paint_uniform_color([0.1, 0.1, 0.1])
            wire_mat = rendering.MaterialRecord()
            wire_mat.shader = "unlitLine"
            wire_mat.line_width = 1.0
            self._scene.scene.add_geometry("wireframe", wireframe, wire_mat)

        # Fit camera
        bounds = mesh.get_axis_aligned_bounding_box()
        self._scene.setup_camera(60, bounds, bounds.get_center())

        # Update info labels
        n_orig = len(original.triangles) if original else 0
        n_curr = len(mesh.triangles)
        n_verts = len(mesh.vertices)
        self._info_original.text = f"Original Faces: {n_orig}"
        self._info_current.text = f"Current Faces:  {n_curr}"
        self._info_vertices.text = f"Vertices:       {n_verts}"

    # ────────────────────── Simplification ──────────────────────

    def _simplify_mesh(self, path):
        """Simplify a single mesh from its original, store result in _current_meshes."""
        target = self._faces_edit.int_value
        original = self._original_meshes.get(path)
        if original is None:
            return
        if len(original.triangles) <= target:
            self._current_meshes[path] = o3d.geometry.TriangleMesh(original)
            return
        simplified = original.simplify_quadric_decimation(
            target_number_of_triangles=target)
        simplified.compute_vertex_normals()
        self._current_meshes[path] = simplified

    def _on_apply_selected(self):
        """Apply simplification to the currently selected file."""
        if self._selected_index < 0:
            return
        path = self._file_paths[self._selected_index]
        self._simplify_mesh(path)
        self._update_preview()

    def _on_apply_all(self):
        """Apply simplification to all loaded files."""
        for path in self._file_paths:
            self._simplify_mesh(path)
        # Refresh preview of currently selected
        self._update_preview()

    # ────────────────────── Reset ──────────────────────

    def _on_reset_selected(self):
        """Reset the currently selected mesh to its original state."""
        if self._selected_index < 0:
            return
        path = self._file_paths[self._selected_index]
        original = self._original_meshes.get(path)
        if original:
            self._current_meshes[path] = o3d.geometry.TriangleMesh(original)
        self._update_preview()

    def _on_reset_all(self):
        """Reset all meshes back to their original state."""
        for path in self._file_paths:
            original = self._original_meshes.get(path)
            if original:
                self._current_meshes[path] = o3d.geometry.TriangleMesh(
                    original)
        self._update_preview()

    # ────────────────────── Wireframe Toggle ──────────────────────

    def _on_wireframe_toggled(self, is_checked):
        """Toggle wireframe overlay on/off."""
        self._show_wireframe = is_checked
        self._update_preview()

    # ────────────────────── Save ──────────────────────

    def _get_collision_filename(self, path):
        basename = os.path.basename(path)
        if "_collision" in basename.lower():
            return basename
        if basename.endswith(".STL"):
            return basename.replace(".STL", "_collision.STL")
        elif basename.endswith(".stl"):
            return basename.replace(".stl", "_collision.stl")
        else:
            return basename[:-4] + "_collision" + basename[-4:]

    def _on_save_selected(self):
        """Open a file dialog to save the currently selected mesh."""
        if self._selected_index < 0:
            return
        path = self._file_paths[self._selected_index]
        mesh = self._current_meshes.get(path)
        if mesh is None:
            return

        dlg = gui.FileDialog(gui.FileDialog.SAVE,
                             "Save Selected STL", self._window.theme)
        dlg.add_filter(".stl .STL", "STL files (*.stl)")
        dlg.add_filter("", "All files")

        default_name = self._get_collision_filename(path)
        dlg.set_path(os.path.dirname(path) + "/" + default_name)
        dlg.set_on_cancel(self._on_dialog_cancel)
        dlg.set_on_done(self._on_save_selected_done)
        self._window.show_dialog(dlg)

    def _on_save_selected_done(self, out_path):
        self._window.close_dialog()
        if not out_path:
            return

        path = self._file_paths[self._selected_index]
        mesh = self._current_meshes.get(path)
        if mesh is None:
            return

        try:
            o3d.io.write_triangle_mesh(out_path, mesh)
            print(f"[Saved] {out_path} ({len(mesh.triangles)} faces)")
        except Exception as e:
            print(f"[Error] Failed to save {out_path}: {e}")

    def _on_save_all(self):
        """Open a folder dialog and save all current meshes to the chosen directory."""
        dlg = gui.FileDialog(gui.FileDialog.OPEN_DIR,
                             "Select Output Folder", self._window.theme)
        dlg.set_on_cancel(self._on_dialog_cancel)
        dlg.set_on_done(self._on_save_all_done)
        self._window.show_dialog(dlg)

    def _on_save_all_done(self, folder_path):
        """Save all current meshes into the selected folder."""
        self._window.close_dialog()
        if not folder_path:
            return
        saved = 0
        for path in self._file_paths:
            mesh = self._current_meshes.get(path)
            if mesh is None:
                continue

            basename = self._get_collision_filename(path)
            out_path = os.path.join(folder_path, basename)
            try:
                o3d.io.write_triangle_mesh(out_path, mesh)
                saved += 1
                print(f"[Saved] {out_path} ({len(mesh.triangles)} faces)")
            except Exception as e:
                print(f"[Error] Failed to save {out_path}: {e}")
        print(f"--- Save complete: {saved}/{len(self._file_paths)} files ---")

    # ────────────────────── Dialog Helpers ──────────────────────

    def _on_dialog_cancel(self):
        self._window.close_dialog()

    def _on_quit(self):
        self._app.quit()

    # ────────────────────── Run ──────────────────────

    def run(self):
        """Start the application event loop."""
        self._app.run()


def main():
    app = STLSimplifierApp()
    app.run()


if __name__ == "__main__":
    main()

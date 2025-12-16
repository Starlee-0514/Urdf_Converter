#!/usr/bin/env python3
"""
Proto File Editor - Unity-like Interface
A hierarchical editor for Webots proto files with tree view and property inspector
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import proto_praser as proto
import os
import subprocess

class ProtoEditorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proto File Editor")
        self.root.geometry("1400x900")
        
        # Configure default fonts for all widgets
        self.root.option_add('*Font', 'Sans 12')
        self.root.option_add('*TButton*Font', 'Sans 12')
        self.root.option_add('*TLabel*Font', 'Sans 12')
        
        # Configure Treeview font
        style = ttk.Style()
        style.configure('Treeview', font=('Sans', 12), rowheight=30)
        style.configure('Treeview.Heading', font=('Sans', 12, 'bold'))
        
        # Current proto robot
        self.proto_robot = None
        self.current_file = None
        self.selected_item = None
        self.modified = False
        
        # Setup UI
        self.create_menu()
        self.create_toolbar()
        self.create_main_layout()
        self.create_status_bar()
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-Shift-s>', lambda e: self.save_as())
        self.root.bind('<Control-f>', lambda e: self.search_tree())
        
    def create_menu(self):
        """Create menu bar"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Proto File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Search", command=self.search_tree, accelerator="Ctrl+F")
        edit_menu.add_separator()
        edit_menu.add_command(label="Expand All", command=lambda: self.expand_all(self.tree))
        edit_menu.add_command(label="Collapse All", command=lambda: self.collapse_all(self.tree))
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Find All Meshes", command=self.find_all_meshes)
        tools_menu.add_command(label="Find All Motors", command=self.find_all_motors)
        tools_menu.add_command(label="Replace Collision Meshes", command=self.batch_replace_collision)
        tools_menu.add_separator()
        tools_menu.add_command(label="Validate Proto", command=self.validate_proto)
        
    def create_toolbar(self):
        """Create toolbar with common actions"""
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Buttons
        tk.Button(toolbar, text="Open", command=self.open_file, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save", command=self.save_file, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        tk.Button(toolbar, text="Search", command=self.search_tree, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        tk.Button(toolbar, text="Expand All", command=lambda: self.expand_all(self.tree)).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Collapse All", command=lambda: self.collapse_all(self.tree)).pack(side=tk.LEFT, padx=2, pady=2)
        
    def create_main_layout(self):
        """Create main split layout - Unity style"""
        # Main container
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Hierarchy (Tree View)
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)
        
        # Hierarchy label
        hierarchy_label = tk.Label(left_frame, text="Hierarchy", bg="#2b2b2b", fg="white", 
                                   font=("Arial", 14, "bold"), anchor="w", padx=10, pady=5)
        hierarchy_label.pack(fill=tk.X)
        
        # Tree view with scrollbar
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(tree_frame, 
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set,
                                 selectmode='browse')
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind tree selection
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Right panel - Inspector
        right_frame = ttk.Frame(main_paned, width=500)
        main_paned.add(right_frame, weight=1)
        
        # Inspector label
        inspector_label = tk.Label(right_frame, text="Inspector", bg="#2b2b2b", fg="white",
                                   font=("Arial", 14, "bold"), anchor="w", padx=10, pady=5)
        inspector_label.pack(fill=tk.X)
        
        # Inspector content area with scrollbar
        inspector_canvas_frame = tk.Frame(right_frame)
        inspector_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        inspector_scroll = ttk.Scrollbar(inspector_canvas_frame, orient=tk.VERTICAL)
        inspector_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.inspector_canvas = tk.Canvas(inspector_canvas_frame, 
                                         yscrollcommand=inspector_scroll.set,
                                         bg="#383838")
        self.inspector_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inspector_scroll.config(command=self.inspector_canvas.yview)
        
        # Inspector content frame
        self.inspector_frame = tk.Frame(self.inspector_canvas, bg="#383838")
        self.inspector_window = self.inspector_canvas.create_window((0, 0), 
                                                                     window=self.inspector_frame,
                                                                     anchor='nw')
        
        # Update scroll region when frame changes
        self.inspector_frame.bind('<Configure>', 
                                 lambda e: self.inspector_canvas.configure(
                                     scrollregion=self.inspector_canvas.bbox('all')))
        
        # Empty state
        self.show_empty_inspector()
        
    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def open_file(self):
        """Open proto file with file dialog or Zenity"""
        try:
            # Try Zenity first (Linux)
            result = subprocess.run(
                ['zenity', '--file-selection', '--title', 'Open Proto File', '--file-filter=*.proto'],
                capture_output=True,
                text=True,
                check=True
            )
            filename = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fall back to tkinter dialog
            filename = filedialog.askopenfilename(
                title="Open Proto File",
                filetypes=[("Proto files", "*.proto"), ("All files", "*.*")]
            )
        
        if filename:
            self.load_proto_file(filename)
            
    def load_proto_file(self, filename):
        """Load and parse proto file"""
        try:
            self.status_bar.config(text=f"Loading {os.path.basename(filename)}...")
            self.root.update()
            
            # Parse proto file
            self.proto_robot = proto.proto_robot(proto_filename=filename)
            self.current_file = filename
            self.modified = False
            
            # Update tree
            self.populate_tree()
            
            # Update window title
            self.root.title(f"Proto Editor - {os.path.basename(filename)}")
            self.status_bar.config(text=f"Loaded: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load proto file:\n{str(e)}")
            self.status_bar.config(text="Error loading file")
            
    def populate_tree(self):
        """Populate tree view with proto structure"""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not self.proto_robot:
            return
            
        # Add root
        root_id = self.tree.insert('', 'end', text='Robot', 
                                   values=('proto_robot', id(self.proto_robot)),
                                   open=True)
        
        # Add children recursively
        self.add_tree_children(root_id, self.proto_robot.children)
        
    def add_tree_children(self, parent_id, children):
        """Recursively add children to tree - Unity-like filtering"""
        for child in children:
            # Skip property items (only show in inspector)
            if isinstance(child, proto.property):
                continue
            
            # Check if this is a displayable object (Node or Container with children/devices)
            should_display = False
            has_children = hasattr(child, 'children') and child.children
            
            # Determine icon/label based on type
            if isinstance(child, proto.Node):
                # Check if it's a meaningful node (has name or has children)
                node_name = getattr(child, 'name', '') or ''
                node_def = getattr(child, 'DEF', '') or ''
                
                # Device/Component nodes (always show)
                device_keywords = ['Solid', 'Joint', 'Motor', 'Sensor', 'Light', 'Camera', 
                                  'LED', 'GPS', 'Gyro', 'Accelerometer', 'Compass', 'Lidar',
                                  'Robot', 'Transform', 'Group', 'Shape', 'Mesh', 'Appearance']
                
                is_device = any(keyword in node_def for keyword in device_keywords)
                
                if is_device or has_children or node_name:
                    should_display = True
                    icon = "🤖" if 'Robot' in node_def else "📦"
                    
                    # Create label - check node name first (HingeJoint, etc.)
                    if node_name and node_name != "endPoint":
                        label = f"{icon} {node_name}"
                        
                        # For Joints, add motor name from device[] container
                        if 'Joint' in node_name and has_children:
                            motor_name = None
                            # Search in children for device[] container
                            for c in child.children:
                                if isinstance(c, proto.container):
                                    # Check inside container for Motor nodes
                                    for cc in c.children:
                                        if isinstance(cc, proto.Node):
                                            cc_name = getattr(cc, 'name', '')
                                            if 'Motor' in cc_name:
                                                # Find motor name property
                                                for motor_child in cc.children:
                                                    if isinstance(motor_child, proto.property) and getattr(motor_child, 'name', '') == 'name':
                                                        motor_name = getattr(motor_child, 'content', '')
                                                        break
                                                if motor_name:
                                                    break
                                if motor_name:
                                    break
                            
                            if motor_name:
                                label = f"{icon} {node_name} - {motor_name}"
                    elif node_def and '{' in node_def:
                        base_def = node_def.split('{')[0].strip()
                        label = f"{icon} {base_def}"
                    elif node_def:
                        label = f"{icon} {node_def}"
                    else:
                        label = f"{icon} Node"
                    
                    type_name = "Node"
                
            elif isinstance(child, proto.container):
                # Containers like children[], endPoint[], device[] - hide them and show their children directly
                if has_children:
                    # Process container's children directly under parent (skip the container itself)
                    self.add_tree_children(parent_id, child.children)
                continue
            
            # Special handling: skip endPoint, Shape, physics, jointParameters, Motor, Sensor nodes
            node_name_to_check = getattr(child, 'name', '') if isinstance(child, proto.Node) else ''
            if node_name_to_check in ['endPoint', 'Shape', 'physics', 'jointParameters'] or \
               'Motor' in node_name_to_check or 'Sensor' in node_name_to_check:
                # Don't display these nodes, but process endPoint's children
                if node_name_to_check == 'endPoint' and hasattr(child, 'children'):
                    self.add_tree_children(parent_id, child.children)
                # Others are hidden entirely (properties shown in inspector)
                continue
            
            # Only insert if should be displayed
            if should_display:
                item_id = self.tree.insert(parent_id, 'end', text=label,
                                          values=(type_name, id(child)),
                                          open=False)
                
                # Add children recursively if any
                if has_children:
                    self.add_tree_children(item_id, child.children)
                
    def on_tree_select(self, event):
        """Handle tree item selection"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        values = self.tree.item(item_id, 'values')
        
        if not values:
            return
            
        obj_id = int(values[1])
        
        # Find the actual object
        obj = self.find_object_by_id(self.proto_robot, obj_id)
        
        if obj:
            self.selected_item = obj
            self.show_inspector(obj)
            
    def find_object_by_id(self, root, obj_id):
        """Find object in tree by id"""
        if id(root) == obj_id:
            return root
            
        if hasattr(root, 'children'):
            for child in root.children:
                result = self.find_object_by_id(child, obj_id)
                if result:
                    return result
        return None
        
    def show_empty_inspector(self):
        """Show empty inspector state"""
        for widget in self.inspector_frame.winfo_children():
            widget.destroy()
            
        label = tk.Label(self.inspector_frame, 
                        text="Select an item in the hierarchy",
                        bg="#383838", fg="#aaaaaa",
                        font=("Arial", 14))
        label.pack(pady=50)
        
    def show_inspector(self, obj):
        """Show inspector for selected object"""
        # Clear inspector
        for widget in self.inspector_frame.winfo_children():
            widget.destroy()
            
        # Object type header
        obj_type = type(obj).__name__
        header = tk.Label(self.inspector_frame, text=obj_type,
                         bg="#2b2b2b", fg="white",
                         font=("Arial", 14, "bold"),
                         anchor="w", padx=10, pady=5)
        header.pack(fill=tk.X)
        
        # === Basic Properties Section ===
        basic_section = tk.LabelFrame(self.inspector_frame, text="Basic Properties",
                                     bg="#383838", fg="white", font=("Arial", 12, "bold"),
                                     padx=10, pady=10)
        basic_section.pack(fill=tk.X, padx=10, pady=5)
        
        row = 0
        
        # Name
        if hasattr(obj, 'name'):
            self.add_property_field(basic_section, row, "Name", obj, 'name')
            row += 1
            
        # DEF
        if hasattr(obj, 'DEF'):
            self.add_property_field(basic_section, row, "DEF", obj, 'DEF')
            row += 1
            
        # Stage
        if hasattr(obj, 'stage'):
            tk.Label(basic_section, text="Stage:", bg="#383838", fg="white", 
                    anchor="w", font=("Arial", 12)).grid(row=row, column=0, sticky="w", pady=5)
            tk.Label(basic_section, text=str(obj.stage), bg="#383838", fg="#aaaaaa",
                    anchor="w", font=("Arial", 12)).grid(row=row, column=1, sticky="w", pady=5)
            row += 1
            
        # Content (for properties)
        if isinstance(obj, proto.property):
            self.add_property_text(basic_section, row, "Content", obj, 'content')
            row += 1
        
        # === Properties (Hidden from Tree) Section ===
        if hasattr(obj, 'children') and obj.children:
            # Find all property children
            properties = [c for c in obj.children if isinstance(c, proto.property)]
            
            # Check if this is a Joint and find all merged properties
            node_name = getattr(obj, 'name', '') or ''
            endpoint_properties = []
            shape_properties = []
            physics_properties = []
            joint_param_properties = []
            motor_properties = []
            sensor_properties = []
            
            if 'Joint' in node_name:
                endpoint_node = None
                
                # Extract jointParameters properties
                for child in obj.children:
                    if isinstance(child, proto.Node) and 'jointParameters' in getattr(child, 'name', ''):
                        joint_param_properties = [c for c in child.children if isinstance(c, proto.property)]
                    # Extract Motor and Sensor from device[] container
                    elif isinstance(child, proto.container):
                        for device_node in child.children:
                            if isinstance(device_node, proto.Node):
                                device_name = getattr(device_node, 'name', '')
                                if 'Motor' in device_name:
                                    motor_properties.extend([c for c in device_node.children if isinstance(c, proto.property)])
                                elif 'Sensor' in device_name:
                                    sensor_properties.extend([c for c in device_node.children if isinstance(c, proto.property)])
                    # Find endPoint node
                    elif isinstance(child, proto.Node) and getattr(child, 'name', '') == 'endPoint':
                        endpoint_node = child
                
                if endpoint_node:
                    # Extract all property children from the endpoint Node
                    endpoint_properties = [c for c in endpoint_node.children if isinstance(c, proto.property)]
                    
                    # Find Shape nodes (in children[] container) and their nested nodes
                    for ep_child in endpoint_node.children:
                        if isinstance(ep_child, proto.container):
                            for shape_node in ep_child.children:
                                if isinstance(shape_node, proto.Node) and getattr(shape_node, 'name', '') == 'Shape':
                                    # Extract Shape properties
                                    shape_properties.extend([c for c in shape_node.children if isinstance(c, proto.property)])
                                    # Extract nested node properties (geometry, appearance, etc.)
                                    for shape_child in shape_node.children:
                                        if isinstance(shape_child, proto.Node):
                                            # Add nested node's properties
                                            nested_props = [c for c in shape_child.children if isinstance(c, proto.property)]
                                            shape_properties.extend(nested_props)
                        elif isinstance(ep_child, proto.Node) and getattr(ep_child, 'name', '') == 'physics':
                            # Extract physics properties
                            physics_properties = [c for c in ep_child.children if isinstance(c, proto.property)]
            
            if properties or endpoint_properties or shape_properties or physics_properties or \
               joint_param_properties or motor_properties or sensor_properties:
                props_section = tk.LabelFrame(self.inspector_frame, text="Properties",
                                            bg="#383838", fg="white", font=("Arial", 12, "bold"),
                                            padx=10, pady=10)
                props_section.pack(fill=tk.X, padx=10, pady=5)
                
                row_idx = 0
                
                # Show joint's own properties
                for prop in properties:
                    prop_name = getattr(prop, 'name', 'unknown')
                    self.add_property_field(props_section, row_idx, prop_name, prop, 'content')
                    row_idx += 1
                
                # Show merged properties with visual separation
                if endpoint_properties or shape_properties or physics_properties or \
                   joint_param_properties or motor_properties or sensor_properties:
                    # Add separator label
                    if properties:
                        tk.Label(props_section, text="─" * 40, bg="#383838", fg="#666666",
                               font=("Arial", 10)).grid(row=row_idx, column=0, columnspan=2, pady=5)
                        row_idx += 1
                    
                    # Display jointParameters properties with yellow color
                    if joint_param_properties:
                        tk.Label(props_section, text="Joint Parameters:", bg="#383838", fg="#ffff00",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in joint_param_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#ffff00",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#ffff00", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    # Display Motor properties with green color
                    if motor_properties:
                        tk.Label(props_section, text="Motor Properties:", bg="#383838", fg="#00ff00",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in motor_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#00ff00",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#00ff00", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    # Display Sensor properties with pink color
                    if sensor_properties:
                        tk.Label(props_section, text="Sensor Properties:", bg="#383838", fg="#ff69b4",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in sensor_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#ff69b4",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#ff69b4", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    # Display endpoint properties with orange color
                    if endpoint_properties:
                        tk.Label(props_section, text="Endpoint Properties:", bg="#383838", fg="#ffaa00",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in endpoint_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#ffaa00",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#ffaa00", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    # Display Shape properties with cyan color
                    if shape_properties:
                        tk.Label(props_section, text="Shape Properties:", bg="#383838", fg="#00ffff",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in shape_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#00ffff",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#00ffff", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    # Display physics properties with magenta color
                    if physics_properties:
                        tk.Label(props_section, text="Physics Properties:", bg="#383838", fg="#ff00ff",
                               font=("Arial", 11, "bold"), anchor="w").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=3)
                        row_idx += 1
                        for prop in physics_properties:
                            prop_name = getattr(prop, 'name', 'unknown')
                            tk.Label(props_section, text=f"{prop_name}:", bg="#383838", fg="#ff00ff",
                                   anchor="w", font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", pady=5)
                            
                            entry = tk.Entry(props_section, bg="#2b2b2b", fg="#ff00ff", insertbackground="white",
                                           font=("Arial", 12))
                            value = getattr(prop, 'content', '')
                            if value is not None:
                                entry.insert(0, str(value))
                            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
                            entry.bind('<FocusOut>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            entry.bind('<Return>', lambda e, p=prop, attr='content': self.update_property(p, attr, e.widget.get()))
                            row_idx += 1
                    
                    props_section.grid_columnconfigure(1, weight=1)
        
        # === Children Count ===
        if hasattr(obj, 'children'):
            children_section = tk.LabelFrame(self.inspector_frame, text="Children",
                                           bg="#383838", fg="white", font=("Arial", 12, "bold"),
                                           padx=10, pady=10)
            children_section.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(children_section, text=f"Total Count: {len(obj.children)}", 
                    bg="#383838", fg="white", font=("Arial", 12)).pack(anchor="w", pady=5)
            
            # Show child types breakdown
            child_types = {}
            for child in obj.children:
                child_type = type(child).__name__
                child_types[child_type] = child_types.get(child_type, 0) + 1
            
            for child_type, count in child_types.items():
                tk.Label(children_section, text=f"  {child_type}: {count}",
                        bg="#383838", fg="#aaaaaa", font=("Arial", 11)).pack(anchor="w", pady=2)
        
        # === Raw Editor Section ===
        editor_section = tk.LabelFrame(self.inspector_frame, text="Raw Editor",
                                      bg="#383838", fg="white", font=("Arial", 12, "bold"),
                                      padx=10, pady=10)
        editor_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Raw text view/edit
        text_frame = tk.Frame(editor_section, bg="#383838")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.raw_editor = tk.Text(text_frame, bg="#2b2b2b", fg="#00ff00",
                                 insertbackground="white", height=10,
                                 font=("Courier", 11),
                                 yscrollcommand=text_scroll.set)
        self.raw_editor.pack(fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.raw_editor.yview)
        
        # Insert raw representation
        try:
            raw_text = str(obj)
            self.raw_editor.insert('1.0', raw_text)
        except Exception as e:
            self.raw_editor.insert('1.0', f"Error displaying raw text: {e}")
        
        # Buttons for raw editor
        button_frame = tk.Frame(editor_section, bg="#383838")
        button_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(button_frame, text="Apply Changes", 
                 command=lambda: self.apply_raw_edit(obj),
                 bg="#4a4a4a", fg="white", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reset", 
                 command=lambda: self.show_inspector(obj),
                 bg="#4a4a4a", fg="white", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
            
    def add_property_field(self, parent, row, label_text, obj, attr_name):
        """Add editable property field"""
        tk.Label(parent, text=f"{label_text}:", bg="#383838", fg="white",
                anchor="w", font=("Arial", 12)).grid(row=row, column=0, sticky="w", pady=5)
        
        entry = tk.Entry(parent, bg="#2b2b2b", fg="white", insertbackground="white", 
                        font=("Arial", 12))
        value = getattr(obj, attr_name, '')
        if value is not None:
            entry.insert(0, str(value))
        entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        # Bind change event
        entry.bind('<FocusOut>', lambda e: self.update_property(obj, attr_name, entry.get()))
        entry.bind('<Return>', lambda e: self.update_property(obj, attr_name, entry.get()))
        
        parent.grid_columnconfigure(1, weight=1)
    
    def apply_raw_edit(self, obj):
        """Apply changes from raw editor (placeholder for future implementation)"""
        raw_text = self.raw_editor.get('1.0', 'end-1c')
        # Note: This is a placeholder. Full implementation would require parsing
        # the raw text and reconstructing the object
        messagebox.showinfo("Info", 
                          "Raw editing is complex and requires careful parsing.\n"
                          "Use the property fields above for safe editing.")
        
    def add_property_text(self, parent, row, label_text, obj, attr_name):
        """Add multiline text property field"""
        tk.Label(parent, text=f"{label_text}:", bg="#383838", fg="white",
                anchor="nw", font=("Arial", 12)).grid(row=row, column=0, sticky="nw", pady=5)
        
        text_widget = tk.Text(parent, bg="#2b2b2b", fg="white", 
                             insertbackground="white", height=5, width=40,
                             font=("Arial", 12))
        value = getattr(obj, attr_name, '')
        if value is not None:
            text_widget.insert('1.0', str(value))
        text_widget.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        text_widget.insert('1.0', getattr(obj, attr_name, ''))
        text_widget.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        text_widget.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        # Bind change event
        text_widget.bind('<FocusOut>', 
                        lambda e: self.update_property(obj, attr_name, 
                                                       text_widget.get('1.0', 'end-1c')))
        
        parent.grid_columnconfigure(1, weight=1)
        
    def update_property(self, obj, attr_name, value):
        """Update object property and mark as modified"""
        setattr(obj, attr_name, value)
        self.modified = True
        self.status_bar.config(text="Modified (unsaved changes)")
        
        # Refresh tree to show changes
        self.populate_tree()
        
    def save_file(self):
        """Save proto file"""
        if not self.proto_robot or not self.current_file:
            self.save_as()
            return
            
        try:
            self.proto_robot.save_robot(self.current_file)
            self.modified = False
            self.status_bar.config(text=f"Saved: {self.current_file}")
            messagebox.showinfo("Success", "Proto file saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
            
    def save_as(self):
        """Save proto file as new name"""
        if not self.proto_robot:
            return
            
        try:
            # Try Zenity first
            result = subprocess.run(
                ['zenity', '--file-selection', '--save', '--title', 'Save Proto File As',
                 '--file-filter=*.proto'],
                capture_output=True,
                text=True,
                check=True
            )
            filename = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fall back to tkinter
            filename = filedialog.asksaveasfilename(
                title="Save Proto File As",
                defaultextension=".proto",
                filetypes=[("Proto files", "*.proto"), ("All files", "*.*")]
            )
        
        if filename:
            try:
                self.proto_robot.save_robot(filename)
                self.current_file = filename
                self.modified = False
                self.root.title(f"Proto Editor - {os.path.basename(filename)}")
                self.status_bar.config(text=f"Saved: {filename}")
                messagebox.showinfo("Success", "Proto file saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
                
    def search_tree(self):
        """Search tree for items"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Search")
        search_window.geometry("400x150")
        
        tk.Label(search_window, text="Search for:").pack(pady=10)
        search_entry = tk.Entry(search_window, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        results_label = tk.Label(search_window, text="", fg="blue")
        results_label.pack(pady=5)
        
        def do_search():
            query = search_entry.get()
            if not query or not self.proto_robot:
                return
                
            results = self.proto_robot.search(query)
            results_label.config(text=f"Found {len(results)} result(s)")
            
            if results:
                # Highlight first result in tree
                # (simplified - would need more work to properly navigate tree)
                self.status_bar.config(text=f"Found {len(results)} matches for '{query}'")
                
        tk.Button(search_window, text="Search", command=do_search).pack(pady=10)
        search_entry.bind('<Return>', lambda e: do_search())
        
    def find_all_meshes(self):
        """Find and list all mesh nodes"""
        if not self.proto_robot:
            messagebox.showwarning("Warning", "No proto file loaded")
            return
            
        meshes = self.proto_robot.search("Mesh")
        
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Meshes Found: {len(meshes)}")
        result_window.geometry("600x400")
        
        # Listbox with scrollbar
        frame = tk.Frame(result_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for mesh in meshes:
            urls = mesh.search("url")
            if urls:
                listbox.insert(tk.END, urls[0].content)
            else:
                listbox.insert(tk.END, "(no url)")
                
    def find_all_motors(self):
        """Find and list all motor nodes"""
        if not self.proto_robot:
            messagebox.showwarning("Warning", "No proto file loaded")
            return
            
        motors = self.proto_robot.search("RotationalMotor")
        
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Motors Found: {len(motors)}")
        result_window.geometry("600x400")
        
        # Create text widget with scrollbar
        frame = tk.Frame(result_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(frame, yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        for i, motor in enumerate(motors):
            text_widget.insert(tk.END, f"Motor {i+1}:\n")
            torques = motor.search("maxTorque")
            if torques:
                text_widget.insert(tk.END, f"  maxTorque: {torques[0].content}\n")
            text_widget.insert(tk.END, "\n")
            
    def batch_replace_collision(self):
        """Batch replace visual meshes with collision meshes"""
        if not self.proto_robot:
            messagebox.showwarning("Warning", "No proto file loaded")
            return
            
        count = 0
        bounding_objects = self.proto_robot.search("boundingObject")
        
        for bo in bounding_objects:
            meshes = bo.search("Mesh")
            for mesh_node in meshes:
                url_props = mesh_node.search("url")
                if url_props:
                    url_prop = url_props[0]
                    original_url = url_prop.content
                    
                    if ".stl" in original_url and "_collision.stl" not in original_url:
                        collision_url = original_url.replace(".stl", "_collision.stl")
                        url_prop.content = collision_url
                        count += 1
                        
        self.modified = True
        self.populate_tree()
        self.status_bar.config(text=f"Replaced {count} meshes with collision variants")
        messagebox.showinfo("Success", f"Replaced {count} mesh references with collision variants")
        
    def validate_proto(self):
        """Basic proto file validation"""
        if not self.proto_robot:
            messagebox.showwarning("Warning", "No proto file loaded")
            return
            
        issues = []
        
        # Check for empty names
        all_nodes = self.proto_robot.search("")
        for node in all_nodes:
            if hasattr(node, 'name') and not node.name:
                issues.append("Found node with empty name")
                
        if issues:
            messagebox.showwarning("Validation Issues", "\n".join(issues))
        else:
            messagebox.showinfo("Validation", "No issues found!")
            
    def expand_all(self, tree):
        """Expand all tree items"""
        def expand_children(item):
            tree.item(item, open=True)
            for child in tree.get_children(item):
                expand_children(child)
                
        for item in tree.get_children():
            expand_children(item)
            
    def collapse_all(self, tree):
        """Collapse all tree items"""
        def collapse_children(item):
            tree.item(item, open=False)
            for child in tree.get_children(item):
                collapse_children(child)
                
        for item in tree.get_children():
            collapse_children(item)
            
    def on_closing(self):
        """Handle window close"""
        if self.modified:
            result = messagebox.askyesnocancel("Unsaved Changes", 
                                              "You have unsaved changes. Save before closing?")
            if result is None:  # Cancel
                return
            elif result:  # Yes
                self.save_file()
                
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ProtoEditorUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

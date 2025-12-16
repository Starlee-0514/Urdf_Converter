# Proto Editor UI Documentation

## Overview

The Proto Editor UI is a Unity-like graphical interface for editing Webots proto files. It provides an intuitive tree-based hierarchy view and a detailed property inspector, making it easy to navigate and modify complex proto robot structures.

## Features

### 1. **Hierarchical Tree View**
- Displays the proto file structure in a clean, Unity-like hierarchy
- Filters out implementation details (properties, containers) for cleaner navigation
- Shows only meaningful nodes: Robots, Solids, Joints, Motors, Sensors, etc.
- Expandable/collapsible tree nodes for easy navigation
- Double-click to expand/collapse nodes

### 2. **Property Inspector**
- **Basic Properties**: Name, DEF, Stage for the selected node
- **Properties Section**: 
  - Shows all hidden properties for the selected node
  - For Joints: displays motor name and endpoint properties with orange color
  - Editable text fields with real-time updates
- **Children Count**: Shows breakdown of child node types
- **Raw Editor**: View and edit the raw proto text representation

### 3. **Joint-Specific Features**
- Joint nodes display format: `HingeJoint - MotorName`
- When selecting a Joint, the inspector automatically shows:
  - Joint's own properties
  - Endpoint's Solid properties (rotation, translation, boundingObject) in **orange**
  - Visual separation between joint and endpoint properties

### 4. **File Operations**
- **Open**: Load proto files using native file dialogs (Zenity on Linux)
- **Save**: Save changes to the current file
- **Save As**: Save to a new file location
- **Modified indicator**: Asterisk (*) in title bar when file has unsaved changes

### 5. **Search & Navigation**
- **Search** (Ctrl+F): Find nodes in the tree by name or type
- **Expand All** / **Collapse All**: Quick tree navigation
- Keyboard shortcuts for common operations

## Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│ File  Edit  Tools                                           │
├─────────────────┬───────────────────────────────────────────┤
│ Open Save Search│                                           │
├─────────────────┼───────────────────────────────────────────┤
│ Hierarchy       │ Inspector                                 │
│                 │                                           │
│ 🤖 Robot        │ Node                                      │
│  └📦 Node       │ ┌─ Basic Properties ────────────────┐    │
│     └📦 Robot   │ │ Name: [HingeJoint            ]    │    │
│       └📦 Solid │ │ DEF:  [{                     ]    │    │
│         └📦 Hinge│ │ Stage: 3                      │    │    │
│                 │ └───────────────────────────────────┘    │
│                 │                                           │
│                 │ ┌─ Properties ────────────────────┐      │
│                 │ │ jointParameters: [...]          │      │
│                 │ │ ────────────────────────────    │      │
│                 │ │ Endpoint Properties:            │      │
│                 │ │ rotation: [0.0 0.0 1.0 1.86]   │      │
│                 │ │ translation: [0.08 0.0 0.0]    │      │
│                 │ └───────────────────────────────────┘    │
│                 │                                           │
│                 │ ┌─ Raw Editor ──────────────────┐        │
│                 │ │ HingeJoint {                  │        │
│                 │ │   jointParameters ...         │        │
│                 │ │ }                             │        │
│                 │ │ [Apply Changes] [Reset]       │        │
│                 │ └───────────────────────────────────┘    │
└─────────────────┴───────────────────────────────────────────┘
│ Loaded: /path/to/file.proto                                │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Starting the Editor

```bash
python proto_editor_ui.py
```

Or from your Python environment:

```bash
/path/to/your/python proto_editor_ui.py
```

### Opening a Proto File

1. Click **File → Open** or press **Ctrl+O**
2. Navigate to your proto file using the file dialog
3. Select the file and click **Open**

The tree will populate with the robot structure automatically.

### Editing Properties

1. **Select a node** in the hierarchy tree
2. The **Inspector** panel will show:
   - Basic properties (Name, DEF, Stage)
   - All hidden properties from the tree
   - For Joints: endpoint properties in orange
3. **Edit values** in the text fields
4. Changes are applied on focus-out or pressing Enter
5. The title bar shows `*` for unsaved changes

### Working with Joints

When you select a HingeJoint node:
- The tree shows: `📦 HingeJoint - MotorName`
- The inspector displays:
  - Joint's own properties (jointParameters, device)
  - A separator line
  - **Endpoint Properties** (in orange):
    - rotation
    - translation
    - name
    - boundingObject
    - physics

### Saving Changes

- **Save**: Click **File → Save** or press **Ctrl+S**
- **Save As**: Click **File → Save As** or press **Ctrl+Shift+S**

### Raw Editing

1. Select any node
2. Scroll down to the **Raw Editor** section
3. Edit the raw proto text directly
4. Click **Apply Changes** to update (experimental)
5. Click **Reset** to reload from the original structure

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open file |
| Ctrl+S | Save file |
| Ctrl+Shift+S | Save As |
| Ctrl+F | Search tree |

## Color Coding

- **White**: Standard properties and values
- **Orange (#ffaa00)**: Endpoint properties (shown in Joint inspector)
- **Gray (#aaaaaa)**: Read-only values (e.g., Stage)
- **Green (#00ff00)**: Raw editor text (proto syntax)

## Tree Filtering Logic

The editor implements Unity-like filtering to show only meaningful objects:

### Shown in Tree:
- ✅ Robot nodes
- ✅ Solid nodes
- ✅ Joint nodes (with motor name)
- ✅ Motor/Sensor devices
- ✅ Shape, Mesh, Appearance nodes
- ✅ Any node with children

### Hidden from Tree (shown in Inspector instead):
- ❌ property objects (rotation, translation, name, etc.)
- ❌ container objects (children[], device[], endPoint[])
- ❌ endpoint Solid nodes (merged into parent Joint)

This creates a clean hierarchy similar to Unity's scene view, where you see the logical structure rather than implementation details.

## Technical Details

### Dependencies
- Python 3.x
- tkinter (standard library)
- proto_praser (custom proto file parser)
- zenity (for native Linux file dialogs)

### File Structure
```
proto_editor_ui.py       # Main UI application
proto_praser.py          # Proto file parser library
```

### Proto Parser Classes
- `proto.proto_robot`: Root robot object
- `proto.Node`: Proto node (Solid, Joint, Motor, etc.)
- `proto.property`: Node property (rotation, name, etc.)
- `proto.container`: Property container (children[], device[])

## Troubleshooting

### Dialog Windows Too Small
The editor uses Zenity for file dialogs on Linux, which respects system DPI settings better than Tkinter's native dialogs.

If Zenity is not installed:
```bash
# Ubuntu/Debian
sudo apt-get install zenity

# Fedora
sudo dnf install zenity
```

### Font Sizes Too Small
Fonts are configured at 12-14pt throughout the UI. If text is still too small, check your system's display scaling settings.

### Properties Not Showing
Make sure you're clicking on a node in the tree that has properties. Properties are hidden from the tree but appear in the Inspector when you select their parent node.

### Endpoint Properties Not Visible
Endpoint properties only appear when:
1. You select a Joint node (HingeJoint, SliderJoint, etc.)
2. The joint has an endpoint Solid child
3. The endpoint has properties (rotation, translation, etc.)

## Future Enhancements

Potential improvements for future versions:
- Undo/Redo functionality
- Multi-select editing
- Drag-and-drop tree reorganization
- Property validation
- Syntax highlighting in raw editor
- Copy/paste nodes
- Node templates
- Export to different formats

## Support

For issues or questions:
1. Check this documentation
2. Review the proto_praser.md documentation
3. Check the main README.md for project overview
4. Review the code comments in proto_editor_ui.py

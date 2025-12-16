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

### 2. **Property Inspector** (Scrollable)
- **Basic Properties**: Name, DEF, Stage for the selected node
- **Properties Section** (color-coded by source):
  - **Joint Parameters** (Yellow): axis, anchor
  - **Motor** (Green): name, maxTorque
  - **Sensor** (Pink): name, type
  - **Endpoint** (Orange): rotation, translation, name, boundingObject
  - **Shape** (Cyan): appearance, url (from geometry)
  - **Physics** (Magenta): density, mass, centerOfMass
  - All fields are editable with real-time updates
- **Children Count**: Shows breakdown of child node types
- **Raw Editor**: View and edit the raw proto text representation
- **Scroll Support**: Inspector scrolls vertically for long property lists

### 3. **Joint-Specific Features**
- Joint nodes display format: `HingeJoint - MotorName`
- When selecting a Joint, the inspector automatically shows all merged properties:
  - **Joint Parameters** (Yellow): axis, anchor from jointParameters node
  - **Motor Properties** (Green): name, maxTorque from RotationalMotor
  - **Sensor Properties** (Pink): name from PositionSensor
  - **Endpoint Properties** (Orange): rotation, translation, boundingObject from endPoint Solid
  - **Shape Properties** (Cyan): appearance, url from Shape and geometry nodes
  - **Physics Properties** (Magenta): density, mass, centerOfMass from physics node
- All these nodes are hidden from the tree for a cleaner hierarchy
- Properties are organized by category with visual separation and color coding

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
│                 │ │ Joint Parameters: (yellow)      │      │
│                 │ │   axis: [0.0 0.0 1.0]           │      │
│                 │ │ Motor Properties: (green)       │      │
│                 │ │   name: "L_Motor"               │      │
│                 │ │   maxTorque: 10000              │      │
│                 │ │ Sensor Properties: (pink)       │      │
│                 │ │   name: "L_Motor_sensor"        │      │
│                 │ │ Endpoint Properties: (orange)   │      │
│                 │ │   rotation: [0.0 0.0 1.0 1.86]  │      │
│                 │ │   translation: [0.08 0.0 0.0]   │      │
│                 │ │ Shape Properties: (cyan)        │      │
│                 │ │   appearance: USE Aluminium     │      │
│                 │ │   url: "mesh.stl"               │      │
│                 │ │ Physics Properties: (magenta)   │      │
│                 │ │   density: -1                   │      │
│                 │ │   mass: 0.075893                │      │
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

### Tree View
- **White**: Standard node labels
- **Icons**: 🤖 for Robot nodes, 📦 for other nodes

### Inspector Properties
The inspector uses color coding to distinguish different property sources:

- **White (#ffffff)**: Joint's own properties
- **Yellow (#ffff00)**: Joint Parameters (axis, anchor)
- **Green (#00ff00)**: Motor properties (name, maxTorque)
- **Pink (#ff69b4)**: Sensor properties (name)
- **Orange (#ffaa00)**: Endpoint properties (rotation, translation, name, boundingObject)
- **Cyan (#00ffff)**: Shape properties (appearance, url)
- **Magenta (#ff00ff)**: Physics properties (density, mass, centerOfMass)
- **Gray (#aaaaaa)**: Read-only values (e.g., Stage)
- **Green (#00ff00)**: Raw editor text (proto syntax)

## Tree Filtering Logic

The editor implements Unity-like filtering to show only meaningful objects:

### Shown in Tree:
- ✅ Robot nodes
- ✅ Solid nodes  
- ✅ Joint nodes (with motor name, e.g., "HingeJoint - L_Motor")
- ✅ Mesh, Appearance nodes
- ✅ Nested HingeJoint nodes (from endpoint children)
- ✅ Any meaningful node with children

### Hidden from Tree (properties merged into parent Joint inspector):
- ❌ property objects (rotation, translation, name, etc.)
- ❌ container objects (children[], device[], endPoint[])
- ❌ endPoint nodes (children promoted, properties merged)
- ❌ Shape nodes (properties merged)
- ❌ physics nodes (properties merged)
- ❌ jointParameters nodes (properties merged)
- ❌ Motor nodes (properties merged)
- ❌ Sensor nodes (properties merged)

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

### Properties Not Showing in Inspector
Merged properties (JointParameters, Motor, Sensor, Endpoint, Shape, Physics) only appear when:
1. You select a Joint node (HingeJoint, SliderJoint, etc.)
2. The joint has the corresponding child nodes (jointParameters, device[], endPoint, etc.)
3. Those nodes contain properties to display

If you don't see these colored property sections, verify that:
- You've selected the correct Joint node in the tree
- The proto file contains these nodes within the Joint
- The nodes have actual property children

### Inspector Scrolling
The inspector panel scrolls vertically when content exceeds the visible area. Use your mouse wheel or scrollbar to navigate through all properties.

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

# Proto Parser Library (`proto_praser.py`)

A custom Python library for parsing, manipulating, and serializing Webots proto files as hierarchical tree structures.

## Overview

The proto parser treats proto files as a tree of nested structures, allowing you to search, modify, and rebuild robot definitions programmatically. This is essential for post-processing URDF-converted proto files.

## Core Classes

### `proto_robot`

The root container representing the entire proto file.

**Attributes:**
- `header` (str) - Proto file header (comments, metadata)
- `children` (list) - Top-level structure elements
- `cursor` (proto_robot) - Current navigation pointer in the tree
- `parent` (proto_robot) - Parent reference (self for root)

**Methods:**

#### `__init__(proto_filename=None)`
Initializes the robot structure. If `proto_filename` is provided, automatically parses the file.

```python
robot = proto_robot(proto_filename="robot.proto")
```

#### `add_child(child)`
Adds a child structure to the current node.

#### `set_current(child)`
Moves the cursor to a specific child node for navigation.

#### `read_proto_file(proto_filename)`
Parses a proto file and builds the tree structure. Recognizes:
- Headers (`#` comments)
- Nodes (`{ }` blocks)
- Containers (`[ ]` blocks)
- Properties (key-value pairs)

```python
robot = proto_robot()
robot.read_proto_file("myrobot.proto")
```

#### `search(name)`
Recursively searches the tree for elements matching `name`. Returns a list of matches.

```python
# Find all RotationalMotor nodes
motors = robot.search("RotationalMotor")

# Find all boundingObject properties
bounding = robot.search("boundingObject")
```

#### `save_robot(filename=None)`
Serializes the tree back to a proto file. If no filename is provided, prompts with a file dialog.

```python
robot.save_robot("modified_robot.proto")
```

---

### `structure`

Base class for all proto elements (nodes, properties, containers).

**Attributes:**
- `name` (str) - Element name
- `stage` (int) - Nesting depth level
- `parent` (structure) - Parent element
- `children` (list) - Child elements
- `DEF` (str) - Definition/type identifier

**Methods:**

#### `add_child(child)`
Appends a child to this structure.

#### `search(name)`
Searches descendants for matching name.

```python
# Search within a specific subtree
node = robot.search("endPoint")[0]
solid_name = node.search("name")
```

---

### `Node`

Represents a proto node (e.g., `Solid { ... }`).

**Constructor:**
```python
Node(name, parent, DEF=None, stage=0)
```

**Methods:**

#### `get_self_only()`
Returns the opening line of the node (`name DEF {`).

#### `__str__()`
Recursively serializes the node and all children with proper indentation.

**Example:**
```python
solid_node = Node(name="endPoint", parent=parent_node, DEF="Solid {", stage=3)
solid_node.add_child(property(name="name", parent=solid_node, content='"link_1"', stage=4))
print(solid_node)
```

Output:
```
endPoint Solid {
    name "link_1"
}
```

---

### `property`

Represents a key-value property (e.g., `name "robot_arm"`).

**Constructor:**
```python
property(name, parent, stage=0, content="")
```

**Attributes:**
- `content` (str) - The value part of the property

**Example:**
```python
prop = property(name="maxTorque", parent=motor_node, content="10.0", stage=5)
print(prop)  # Output: maxTorque 10.0
```

---

### `container`

Represents a list container (e.g., `children [ ... ]`).

**Constructor:**
```python
container(name, parent, DEF=None, stage=0)
```

**Example:**
```python
children_container = container(name="children", parent=robot_node, DEF="[", stage=2)
children_container.add_child(Node(name="Joint", parent=children_container, DEF="HingeJoint {", stage=3))
```

---

## Usage Patterns

### 1. Load and Search

```python
from proto_praser import proto_robot

# Load proto file
robot = proto_robot("robot.proto")

# Find all Mesh nodes
meshes = robot.search("Mesh")
for mesh in meshes:
    url = mesh.search("url")
    if url:
        print(url[0].content)
```

### 2. Modify Properties

```python
# Find all motor torque settings
motors = robot.search("RotationalMotor")
for motor in motors:
    torque_props = motor.search("maxTorque")
    if torque_props:
        # Update torque value
        torque_props[0].content = "0.5"
```

### 3. Replace Nodes

```python
# Convert empty Solid to SolidReference
endpoints = robot.search("endPoint")
for ep in endpoints:
    if "Solid" in ep.DEF and "Empty" in ep.search("name")[0].content:
        ep.DEF = "SolidReference {"
        ep.children = []
        ep.add_child(property(name="solidName", parent=ep, content='"ref_link"', stage=ep.stage+1))
```

### 4. Save Changes

```python
robot.save_robot("modified_robot.proto")
```

---

## Implementation Details

### Parsing Logic

The parser uses a state machine approach:
1. Tracks nesting depth with `current_stage` counter
2. Recognizes structural markers:
   - `[` → Opens container
   - `{` → Opens node
   - `]` or `}` → Closes structure, decrements stage
3. Cursor navigation maintains tree traversal position

### Indentation

Serialization (`__str__` methods) uses `stage * "  "` (2 spaces per level) for proper formatting.

### Special Cases

- **Empty nodes**: `{` on its own line creates unnamed node
- **Inline properties**: `centerOfMass 0 0 0` parsed even if followed by `}`
- **DEF attribute**: Stores the opening delimiter (`{` or `[`) and any preceding keywords

---

## Limitations

- **No validation**: Doesn't check proto syntax validity
- **Simple regex**: May fail on complex string escapes or edge cases
- **Memory intensive**: Loads entire file into tree structure
- **Whitespace preservation**: Doesn't preserve original formatting exactly

---

## Example: Complete Workflow

```python
from proto_praser import proto_robot, property

# 1. Load
robot = proto_robot("original.proto")

# 2. Find and modify
bounding_objects = robot.search("boundingObject")
for bo in bounding_objects:
    meshes = bo.search("Mesh")
    for mesh in meshes:
        urls = mesh.search("url")
        if urls:
            url_prop = urls[0]
            if ".stl" in url_prop.content:
                url_prop.content = url_prop.content.replace(".stl", "_collision.stl")

# 3. Save
robot.save_robot("modified.proto")
```

This pattern is the foundation of the main conversion pipeline's optimization steps.

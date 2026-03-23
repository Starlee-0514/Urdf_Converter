# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

### Core Components

**1. Main Workflow (`main.py`)**
- Entry point for URDF-to-Proto conversion pipeline
- Orchestrates: folder selection → mesh copying → collision mesh generation → URDF conversion → proto optimization → IFS conversion
- Uses Zenity dialogs via `ui_picker` for cross-platform file selection

**2. Proto Parser Library (`proto_praser.py`)**
Custom AST-like parser that builds a tree structure from Webots `.proto` files:
```
proto_robot (root)
├── header
└── children []
    ├── Node {}     # { and } blocks
    ├── property   # single-line key-value pairs
    └── container  # [ ] array declarations
```

Key classes: `proto_robot`, `Node`, `property`, `container`

**3. STL Tool (`stl_tool.py`)**
Generates collision meshes using Open3D's quadric decimation:
- Input: mesh folder with `.stl` files
- Output: `_collision.stl` variant of each file at reduced face count (default 200)

**4. IFS Converter (`convert_collision_to_ifs.py`)**
Post-processes proto files by converting STL meshes to IndexedFaceSet format inline, reducing file size and improving Webots compatibility.

### Data Flow Diagram

```
URDF Folder
├── urdf/robot.urdf
├── meshes/*.stl
└── textures/*.jpg
    ↓ (selection via Zenity)
Output Folder
├── meshes_<name>/          ← copied + collision.stl generated here
│   ├── base_link.stl       ← original mesh
│   └── base_link_collision.stl  ← decimated (200 faces)
├── textures_<name>/        ← copied textures
└── robot.proto             ← final optimized proto
```

### Key Transformations Applied to Proto File

| Step | Transformation | Purpose |
|------|---------------|---------|
| Collision Mesh Replacement | `USE Base` → independent `Mesh { url "..." }` | Use decimated collision mesh for physics |
| Solid Empty → SolidReference | Replace with reference node | Better organization, reduced redundancy |
| Motor Torque | Set `maxTorque = 0.001` (depth > 6) | Prevent excessive joint forces |
| IFS Conversion | STL Mesh → Inline IndexedFaceSet | Reduce external file dependencies |

## Development Patterns

### Adding New Proto Optimizations

1. Use `proto_bot.search("nodeName")` to find nodes
2. Inspect with `.DEF`, `.name`, `.children`, `.parent`
3. Modify via `.DEF = "...", .content = "..."` or create new `Node/property` objects
4. Call `proto_bot.save_robot(filename)` to persist changes

### Common Imports

```python
import proto_praser as proto      # Parser library
from ui_picker import zenity_*    # File dialogs
import stl_tool                   # Mesh generation
import convert_collision_to_ifs   # IFS conversion
```

## Dependencies

- `urdf2webots` - URDF to Webots converter
- `open3d` - 3D mesh processing (requires Python ≤ 3.11)
- `trimesh` - Mesh operations for IFS conversion
- `tkinter` - File dialogs in proto_praser.py

## Environment Setup

```bash
# Create venv (Python 3.8-3.11 required)
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
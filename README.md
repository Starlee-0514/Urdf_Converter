# URDF to Webots Proto Converter

A Python tool that converts URDF robot models to Webots proto format with automatic collision mesh generation and structure optimization.

## Overview

This project automates the conversion workflow from URDF (Unified Robot Description Format) files to Webots proto files, with intelligent post-processing to optimize the robot model for simulation.

### Key Features

1. **URDF to Proto Conversion** - Leverages `urdf2webots` library to perform initial conversion
2. **Collision Mesh Generation** - Automatically generates simplified `_collision.stl` meshes using Open3D's quadric decimation
3. **Proto Structure Parsing** - Custom parser to read and manipulate the hierarchical proto structure
4. **Automatic Optimization**:
   - Replaces visual meshes with collision meshes in `boundingObject` nodes
   - Converts empty Solid nodes to SolidReference for better organization
   - Sets appropriate motor torque values for RotationalMotor nodes

## Workflow Logic

```
1. Select Input Folder (URDF + meshes + textures)
   ↓
2. Copy meshes & textures to output directory
   ↓
3. Generate collision meshes (_collision.stl) with reduced face count
   ↓
4. Convert URDF → Proto using urdf2webots
   ↓
5. Parse Proto file with custom parser
   ↓
6. Apply automatic modifications:
   - Replace boundingObject meshes with collision variants
   - Convert empty Solid nodes → SolidReference
   - Update RotationalMotor torque settings
   ↓
7. Save optimized Proto file
```

## Requirements

- Python 3.8-3.11 (open3d compatibility)
- See `requirements.txt` for dependencies

## Installation

```bash
# Create virtual environment (Python 3.11 recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

**Note for Python 3.12+ users**: `open3d` doesn't support Python 3.12+. Use Python 3.11 or earlier.

## Usage

```bash
python main.py
```

The script will prompt you to:
1. Select the input folder containing URDF files
2. Select the output folder for generated proto files

## File Structure

```
Urdf_Converter/
├── main.py              # Main conversion workflow
├── proto_praser.py      # Proto file parser library
├── stl_tool.py          # Collision mesh generation utility
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── docs/
│   ├── proto_parser.md  # proto_praser.py documentation
│   ├── stl_tool.md      # stl_tool.py documentation
│   └── main_workflow.md # main.py detailed workflow
```

## Documentation

- **[Proto Parser Library](docs/proto_parser.md)** - Explains the custom proto file parsing system
- **[STL Tool Library](docs/stl_tool.md)** - Details on collision mesh generation
- **[Main Workflow](docs/main_workflow.md)** - Step-by-step breakdown of the conversion process

## Example

Given a robot URDF structure:
```
my_robot/
├── urdf/
│   └── robot.urdf
├── meshes/
│   ├── base_link.stl
│   └── arm_link.stl
└── textures/
    └── metal.jpg
```

The converter produces:
```
output/
├── robot.proto
├── meshes_my_robot/
│   ├── base_link.stl
│   ├── base_link_collision.stl (auto-generated)
│   ├── arm_link.stl
│   └── arm_link_collision.stl (auto-generated)
└── textures_my_robot/
    └── metal.jpg
```

<!-- ## License

[Specify your license here] -->

## Contributing

Contributions welcome! Please submit issues or pull requests.

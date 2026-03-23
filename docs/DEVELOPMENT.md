# Development Guidelines

Coding standards, conventions, and patterns for the URDF-to-Proto converter project.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Code Style](#code-style)
3. [Architecture Patterns](#architecture-patterns)
4. [Error Handling](#error-handling)
5. [Testing](#testing)
6. [Documentation Standards](#documentation-standards)

---

## Project Structure

```
urdf_importer/
├── main.py                 # Entry point, orchestration
├── proto_praser.py         # Proto parser library
├── stl_tool.py             # Mesh decimation utilities
├── convert_collision_to_ifs.py  # IFS conversion
├── ui_picker.py            # File selection dialogs (if exists)
└── docs/
    ├── main_workflow.md
    ├── proto_parser.md
    ├── stl_tool.md
    └── ifs_converter.md
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `main.py` | Pipeline orchestration, user interaction, entry point |
| `proto_praser.py` | Proto file parsing/serialization (library, no I/O) |
| `stl_tool.py` | Mesh processing utilities |
| `convert_collision_to_ifs.py` | VRML text generation and proto modification |

---

## Code Style

### Import Organization
```python
# Standard library imports first
import os
import sys
from typing import List, Optional

# Third-party imports
import open3d as o3d
import trimesh
import urdf2webots

# Local imports last
import proto_praser as proto
import stl_tool
```

### Function Definitions
```python
def generate_collision_meshes(mesh_folder: str, target_faces: int = 500) -> None:
    """
    Generate simplified collision meshes from STL files.

    Args:
        mesh_folder: Absolute path to folder containing STL files
        target_faces: Target triangle count (default: 500)

    Returns:
        None
    """
    # Implementation
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|--------|
| Functions | snake_case, imperative | `generate_collision_meshes()` |
| Variables | snake_case | `input_path`, `mesh_folder` |
| Constants | UPPER_SNAKE_CASE | `TARGET_FACES = 500` |
| Classes | CamelCase | `proto_robot`, `Node` |
| Private methods | prefix with `_` | `_parse_line()` |

### String Formatting
```python
# Preferred: f-strings (Python 3.6+)
name = "robot"
f"Output folder: output/{name}_meshes/"

# Avoid: .format()
"Output folder: {}.{}_meshes/".format(name, prefix)

# Avoid: % formatting
"Output folder: %s_%s_meshes/" % (name, prefix)
```

### Type Hints (Recommended for new code)
```python
def search_nodes(node: proto.Node, name: str) -> List[proto.Node]:
    """Recursively search for nodes with given name."""
    results = []
    if node.name == name:
        results.append(node)

    for child in node.children:
        results.extend(search_nodes(child, name))

    return results
```

---

## Architecture Patterns

### Single Responsibility Principle
Each module should have one clear purpose:
- `proto_praser.py`: Only parses/serializes proto files
- Never mix file I/O with parsing logic

### Dependency Injection for Testing
```python
# Instead of hardcoded paths, use parameters
def process_proto(file_path: str) -> proto.proto_robot:
    """Process and modify a proto file."""
    robot = proto.proto_robot(file_path)
    # ... modifications ...
    return robot
```

### Use Cases for Common Operations

#### Finding Nodes in Tree Structure
```python
def find_all_nodes(robot: proto.proto_robot, node_type: str) -> List[proto.Node]:
    """
    Recursively find all nodes matching a specific type.

    Args:
        robot: Root proto object
        node_type: Name to search for (e.g., 'Mesh', 'endPoint')

    Returns:
        List of matching Node objects
    """
    results = []
    queue = [robot]

    while queue:
        current = queue.pop(0)
        if hasattr(current, 'name') and current.name == node_type:
            results.append(current)

        # Add children to queue
        for child in getattr(current, 'children', []):
            queue.append(child)

    return results
```

#### Safe Attribute Access
```python
# Use getattr with defaults instead of .attr directly
def get_property_value(node: proto.Node, prop_name: str, default="") -> str:
    """Safely retrieve a property value from a node."""
    props = getattr(node, 'search', lambda x: [])
    results = props(prop_name)

    if results and len(results) > 0:
        return results[0].content
    return default
```

---

## Error Handling

### General Philosophy
- Log errors but continue processing when possible (batch operations)
- Fail fast for critical configuration issues
- Never silently ignore exceptions in production code

### File I/O Errors
```python
import os

def read_proto_file(filepath: str) -> str:
    """
    Safely read a proto file with encoding handling.

    Args:
        filepath: Path to proto file

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Proto file not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 for corrupted files
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()
```

### Mesh Processing Errors
```python
def safe_mesh_operation(mesh_path: str) -> Optional[o3d.geometry.TriangleMesh]:
    """
    Attempt mesh operation with graceful failure.

    Returns None if processing fails, allowing batch continuation.
    """
    try:
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        # Perform desired operation
        return mesh
    except Exception as e:
        print(f"Skipping {os.path.basename(mesh_path)}: {e}")
        return None
```

### Proto Parsing Errors
```python
def parse_with_recovery(filepath: str) -> proto.proto_robot:
    """
    Parse proto file with error recovery.

    Falls back to basic parsing if custom parser fails.
    """
    try:
        return proto.proto_robot(filepath)
    except Exception as e:
        print(f"Warning: Custom parser failed for {filepath}: {e}")
        # Consider fallback or re-raise with context
        raise ProtoParseError(f"Failed to parse {filepath}\n{str(e)}")
```

---

## Testing

### Test Structure (to be implemented)

```
tests/
├── test_proto_parser.py      # Parser unit tests
├── test_stl_tool.py          # Mesh processing tests
├── test_conversion.py        # Full pipeline integration tests
└── fixtures/                 # Sample proto files for testing
    ├── simple.proto
    └── complex.robot.proto
```

### Unit Test Example
```python
import unittest
import proto_praser as proto

class TestProtoParser(unittest.TestCase):
    def test_parse_simple_node(self):
        """Test parsing a basic node structure."""
        content = '''# Comment
endPoint Solid {
  name "link_1"
}
'''

        robot = proto.proto_robot()
        robot.read_proto_file_from_string(content)

        endpoints = robot.search("endPoint")
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].name, "Solid")

    def test_search_recursive(self):
        """Test recursive node search."""
        # Setup would go here
        pass
```

### Integration Test Example
```python
def test_full_conversion():
    """End-to-end conversion test."""
    import tempfile
    import os

    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Copy sample URDF/meshes to temp
        src = "fixtures/sample_robot/"
        dst = os.path.join(tmpdir, "test_input")
        shutil.copytree(src, dst)

        # 2. Run conversion
        main.convert_urdf_to_proto(input_path=dst, output_path=tmpdir)

        # 3. Verify outputs exist
        proto_file = os.path.join(tmpdir, "testrobot.proto")
        assert os.path.exists(proto_file), f"Proto file not created: {proto_file}"

        # 4. Check collision mesh was generated
        mesh_dir = os.path.join(tmpdir, "meshes_test_input")
        collision_file = os.path.join(mesh_dir, "link1_collision.stl")
        assert os.path.exists(collision_file), f"Collision mesh not created"

    print("✓ Full conversion test passed")
```

### Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| `proto_praser.py` | 85%+ line coverage, 90%+ branch coverage |
| `stl_tool.py` | 80%+ (some mesh ops hard to test deterministically) |
| `main.py` | 70%+ (integration points harder to mock) |

---

## Documentation Standards

### Docstring Format (Google Style)
```python
def my_function(arg1: str, arg2: int = 10):
    """
    One-line summary of function purpose.

    Args:
        arg1: Description of first parameter
        arg2: Description of second parameter (default: 10)

    Returns:
        Description of return value, or None if void

    Raises:
        ValueError: When invalid argument is passed
        FileNotFoundError: If required file missing

    Example:
        >>> result = my_function("hello", 5)
        >>> print(result)  # doctest: +SKIP
        Output
    """
```

### Module Docstrings
```python
"""
module_name.py - Module description

Provides functionality for X, Y, Z operations.

Classes:
    Class1: Description
    Class2: Description

Functions:
    func1(): Description
    func2(): Description

Example Usage:
    >>> from module_name import func1
    >>> func1("argument")

See Also:
    - main_workflow.md for pipeline overview
    - proto_parser.md for detailed parser API
"""
```

### Comment Standards

#### Good: Explains why, not just what
```python
# Set default torque to prevent joint explosions in simulation
if t[0].stage > 6:
    reference_template = proto.property(
        name="maxTorque",
        parent=t[0].parent,
        content="0.001",  # Conservative default for URDF imports
        stage=t[0].stage
    )
```

#### Bad: Obvious from code itself
```python
# Add a property to the template
reference_template = proto.property(
    name="maxTorque",
    parent=t[0].parent,
    content="0.001",
    stage=t[0].stage
)
```

#### Bad: Magic numbers without explanation
```python
torque_value = 0.001  # Set somewhere
```

---

## Common Patterns and Code Snippets

### Logging Setup (for production use)
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = "converter.log"):
    """
    Configure structured logging with rotation.

    Args:
        name: Logger name
        log_file: Path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler with rotation (max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings to console

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### Progress Tracking for Large Operations
```python
def process_with_progress(items: List[str], callback, total: int) -> None:
    """
    Process items with progress reporting.

    Args:
        items: List of items to process
        callback: Function(item) -> processed_result
        total: Total count for percentage calculation
    """
    from tqdm import tqdm  # Install: pip install tqdm

    for i, item in enumerate(tqdm(items, desc="Processing", total=total)):
        try:
            result = callback(item)
        except Exception as e:
            print(f"Error processing {item}: {e}")
            continue  # Continue with next item

        yield i, item, result
```

---

## Version Control Guidelines

### Commit Message Format (Conventional Commits)
```bash
<type>: <description>

[optional body]

Co-Authored-By: Claude Code <claude@anthropic.com>
```

| Type | Description |
|------|------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code reorganization (no behavior change) |
| `test` | Test additions/updates |
| `chore` | Build/config/maintenance |

### Examples
```bash
git commit -m "feat: add IFS conversion to main pipeline"

git commit -m "fix: correct mesh path resolution for Windows paths

Previously using double backslashes which caused issues with
urdf2webots. Now normalizing to forward slashes.

Closes #42"
```

### Branch Naming
```bash
feature/ifs-conversion          # New feature
bugfix/windows-path-fix        # Bug fix
hotfix/critical-webots-crash   # Urgent fix for production
release/v1.0                   # Release branch
```

---

## Performance Guidelines

### Memory Usage
- Process one mesh at a time when handling large collections
- Use generators instead of lists where possible:
  ```python
  def read_mesh_files(folder: str):
      """Generator yielding mesh paths."""
      for root, _, files in os.walk(folder):
          for file in files:
              if file.endswith('.stl'):
                  yield os.path.join(root, file)
  ```

### CPU Usage
- Avoid repeated string concatenation in loops (use `join()` or list comprehension)
- Cache frequently accessed proto tree data when modifying multiple related nodes

---

## Quick Reference Checklist

Before committing code:

- [ ] Added type hints for new functions
- [ ] Included docstrings with Args/Returns sections
- [ ] Used f-strings consistently
- [ ] No hardcoded paths (use parameters)
- [ ] Errors are logged, not swallowed
- [ ] Variable names are descriptive
- [ ] Followed existing code style

---

## Resources

- [Python PEP 8](https://pep8.org/) - Style guide
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

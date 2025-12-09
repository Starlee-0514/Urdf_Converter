# STL Tool Library (`stl_tool.py`)

Utility for generating simplified collision meshes from STL files using Open3D's mesh decimation.

## Overview

Physics simulations in Webots (and other simulators) benefit from simplified collision meshes. High-polygon visual meshes slow down collision detection. This tool automatically creates `_collision.stl` variants with reduced face counts.

## Function

### `generate_collision_meshes(mesh_folder, target_faces=500)`

Recursively processes all `.stl` files in a folder, generating collision variants.

**Parameters:**
- `mesh_folder` (str) - Absolute path to folder containing STL files
- `target_faces` (int) - Target triangle count for simplified mesh (default: 500)

**Behavior:**
1. Recursively searches for all `.stl` files using glob pattern `**/*.stl`
2. Skips files already named `*_collision.stl`
3. Skips if output file already exists (avoids redundant processing)
4. For each mesh:
   - If original has ≤ `target_faces`, copies it directly
   - Otherwise, applies quadric decimation to reduce polygons
   - Recomputes vertex normals for proper shading
5. Saves as `<original_name>_collision.stl` in same directory

**Returns:** None (prints progress to console)

---

## Algorithm: Quadric Error Decimation

Uses Open3D's `simplify_quadric_decimation()`:
- **Quadric error metric**: Measures how much a vertex collapse changes surface shape
- **Greedy optimization**: Iteratively collapses edges with minimal error
- **Preserves geometry**: Maintains overall shape better than uniform sampling

**Advantages:**
- Fast processing
- Good quality-to-speed ratio
- Suitable for convex and concave meshes

---

## Usage Example

```python
import stl_tool

# Generate collision meshes for all STLs in a folder
stl_tool.generate_collision_meshes(
    mesh_folder="/path/to/robot/meshes",
    target_faces=500
)
```

**Before:**
```
meshes/
├── base_link.stl (10,000 faces)
├── arm_link.stl (8,500 faces)
└── gripper.stl (200 faces)
```

**After:**
```
meshes/
├── base_link.stl (10,000 faces)
├── base_link_collision.stl (500 faces) ← Generated
├── arm_link.stl (8,500 faces)
├── arm_link_collision.stl (500 faces) ← Generated
├── gripper.stl (200 faces)
└── gripper_collision.stl (200 faces) ← Copied (already small)
```

---

## Integration with Main Pipeline

In `main.py`, collision generation happens immediately after copying mesh files:

```python
# Copy mesh folder to output
target_mesh_dir = os.path.join(output_path, "meshes_" + folder_name)
shutil.copytree(mesh_path, target_mesh_dir)

# Generate collision meshes
stl_tool.generate_collision_meshes(target_mesh_dir, target_faces=500)
```

This ensures collision meshes exist before the proto parser replaces mesh references.

---

## Console Output

```
--- 開始處理網格減面: /output/meshes_robot ---
已生成: base_link_collision.stl (500 faces)
已生成: arm_link_collision.stl (500 faces)
已生成: wrist_link_collision.stl (500 faces)
--- 減面完成，共生成 3 個新檔案 ---
```

---

## Technical Details

### Open3D Mesh Processing

```python
mesh = o3d.io.read_triangle_mesh(input_path)
mesh_smp = mesh.simplify_quadric_decimation(target_number_of_triangles=500)
mesh_smp.compute_vertex_normals()
o3d.io.write_triangle_mesh(output_path, mesh_smp)
```

**Key methods:**
- `read_triangle_mesh()` - Loads STL/OBJ/PLY formats
- `simplify_quadric_decimation()` - Reduces triangle count
- `compute_vertex_normals()` - Recalculates normals for smooth rendering
- `write_triangle_mesh()` - Exports in original format

### Face Count Check

```python
if len(mesh.triangles) <= target_faces:
    o3d.io.write_triangle_mesh(output_path, mesh)
    continue
```

Avoids unnecessary decimation for already-simple meshes (e.g., primitive shapes).

---

## Error Handling

Catches exceptions per file:

```python
try:
    mesh = o3d.io.read_triangle_mesh(input_path)
    # ... processing ...
except Exception as e:
    print(f"處理 {os.path.basename(input_path)} 時發生錯誤: {e}")
```

This ensures one corrupt mesh doesn't stop the entire batch.

---

## Performance Considerations

**Typical processing time:**
- 1,000 faces → 500 faces: ~0.1s
- 10,000 faces → 500 faces: ~0.5s
- 50,000 faces → 500 faces: ~2s

**Memory usage:** Open3D loads entire mesh into memory. Very large meshes (>1M faces) may require significant RAM.

---

## Tuning `target_faces`

Adjust based on simulation needs:

| Use Case | Recommended Faces | Notes |
|----------|------------------|-------|
| Simple robots (few joints) | 300-500 | Fast simulation |
| Complex robots (many links) | 500-1000 | Balance accuracy/speed |
| Detailed collision (grasping) | 1000-2000 | Better contact detection |
| Primitive shapes (boxes, cylinders) | 50-100 | Minimal needed |

**Rule of thumb:** Start at 500, increase if collision detection is inaccurate.

---

## Limitations

- **No topology changes**: Can't simplify already-minimal meshes (e.g., cubes)
- **Open meshes**: May have issues with non-watertight geometry
- **Format support**: Only STL tested; OBJ/PLY should work but unverified
- **No convex hull option**: Decimation preserves concavity; for simpler physics, consider convex decomposition (not implemented)

---

## Installation Requirements

```bash
pip install open3d
```

**Python version:** 3.8-3.11 (open3d limitation)

For Python 3.12+:
```bash
# Use conda instead
conda install -c open3d-admin open3d
```

---

## Future Enhancements

Potential improvements:
1. **Convex decomposition** - Break concave meshes into convex parts
2. **Adaptive target faces** - Scale reduction based on original size
3. **Visual comparison** - Output before/after images
4. **Batch statistics** - Total reduction percentage, time taken
5. **Parallel processing** - Use multiprocessing for large folders

---

## Example: Manual Testing

```python
import open3d as o3d

# Load original mesh
mesh = o3d.io.read_triangle_mesh("link.stl")
print(f"Original faces: {len(mesh.triangles)}")

# Simplify
mesh_smp = mesh.simplify_quadric_decimation(target_number_of_triangles=500)
print(f"Simplified faces: {len(mesh_smp.triangles)}")

# Visualize (requires display)
o3d.visualization.draw_geometries([mesh_smp])

# Save
o3d.io.write_triangle_mesh("link_collision.stl", mesh_smp)
```

This is useful for testing different `target_faces` values before batch processing.

# Main Workflow (`main.py`)

Detailed breakdown of the URDF to Webots proto conversion pipeline.

## Overview

`main.py` orchestrates the entire conversion process, combining file operations, URDF conversion, mesh processing, and proto structure optimization.

---

## Step-by-Step Workflow

### 1. File Browser & Folder Structure Analysis

```python
from tkinter.filedialog import askdirectory

# Prompt user for input folder
input_path = askdirectory()
folder_name = input_path.split(r"/")[-1]
```

**Purpose:** Select the robot package folder containing URDF, meshes, and textures.

**Expected structure:**
```
robot_package/
├── urdf/
│   └── robot.urdf
├── meshes/
│   ├── link1.stl
│   └── link2.stl
└── textures/
    └── texture.jpg
```

**Folder indexing:**
```python
Folder_Object = {'Dir': {}, 'File': []}

for root, dirs, files in os.walk(input_path):
    # Build nested dictionary of folder structure
    # Used to locate URDF file and validate paths
```

This creates a JSON-serializable map of the entire directory tree for debugging and path resolution.

---

### 2. Path Resolution

```python
file_name = list(filter(lambda x: ".urdf" in x, Folder_Object["Dir"]["urdf"]["File"]))[0]
Urdf_File = os.path.join(input_path, "urdf", file_name).replace("\\", "/")
mesh_path = os.path.join(input_path, "meshes").replace("\\", "/")
texture_path = os.path.join(input_path, "textures").replace("\\", "/")
```

**Finds:**
- The `.urdf` file in `urdf/` folder
- Mesh folder path (for later copying)
- Texture folder path

**Cross-platform handling:** Uses `replace("\\", "/")` to normalize Windows paths.

---

### 3. Output Folder Selection

```python
output_path = askdirectory()
```

User selects where to generate the proto file and supporting files.

---

### 4. File Copying

```python
target_mesh_dir = os.path.join(output_path, "meshes_"+folder_name)
shutil.copytree(mesh_path, target_mesh_dir)
shutil.copytree(texture_path, os.path.join(output_path, "textures_"+folder_name))
```

**Creates:**
- `output/meshes_<robot_name>/` - Copied STL files
- `output/textures_<robot_name>/` - Copied texture files

**Naming convention:** Prefixes with `meshes_` and `textures_` to avoid conflicts when converting multiple robots.

---

### 5. Collision Mesh Generation

```python
stl_tool.generate_collision_meshes(target_mesh_dir, target_faces=500)
```

**Critical timing:** Runs immediately after copying, before proto conversion.

**Why here?**
- Ensures collision meshes exist before proto parser references them
- Operates on copied files (preserves original meshes)

**Output:**
```
meshes_robot/
├── link1.stl
├── link1_collision.stl  ← Generated
├── link2.stl
└── link2_collision.stl  ← Generated
```

See [stl_tool.md](stl_tool.md) for details.

---

### 6. URDF to Proto Conversion

```python
from urdf2webots.importer import convertUrdfFile

proto_Filename = file_name.replace(".urdf", ".proto").replace("_", "")
proto_Filename = os.path.join(output_path, proto_Filename).replace('\\', '/')
convertUrdfFile(input=Urdf_File, output=output_path)
```

**Uses:** `urdf2webots` library to perform initial conversion.

**Filename transformation:**
- `robot_arm.urdf` → `robotarm.proto` (removes underscores)
- Webots convention prefers camelCase

**Output:** A proto file with absolute mesh paths (needs fixing).

---

### 7. Mesh Path Correction

```python
with open(proto_Filename, 'r', encoding='utf-8') as file:
    datas = file.readlines()
    for i in range(len(datas)):
        l = datas[i]
        if "url" in l:
            l = l.replace("\\", "/")
            if mesh_path in l:
                l = l.replace(mesh_path, './meshes_'+folder_name)
            datas[i] = l

with open(proto_Filename, 'w', encoding='utf-8') as file:
    file.writelines(datas)
```

**Problem:** `urdf2webots` generates absolute paths:
```proto
url "C:/Users/user/robot/meshes/link1.stl"
```

**Solution:** Convert to relative paths:
```proto
url "./meshes_robot/link1.stl"
```

This makes the proto file portable across systems.

---

### 8. Load Proto with Custom Parser

```python
import proto_praser as proto

proto_bot = proto.proto_robot(proto_filename=proto_Filename)
```

Parses the proto file into a tree structure for manipulation. See [proto_parser.md](proto_parser.md).

---

### 9. Replace Collision Meshes in boundingObject

```python
bounding_objects = proto_bot.search("boundingObject")

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
                print(f"Updated Collision: {os.path.basename(original_url)} -> {os.path.basename(collision_url)}")
```

**Purpose:** Physics collision detection should use simplified meshes, not high-poly visual meshes.

**Logic:**
1. Find all `boundingObject` nodes (physics geometry)
2. Locate `Mesh` nodes within them
3. Find `url` property
4. Replace `.stl` → `_collision.stl`

**Before:**
```proto
boundingObject Mesh {
  url "./meshes_robot/link1.stl"
}
```

**After:**
```proto
boundingObject Mesh {
  url "./meshes_robot/link1_collision.stl"
}
```

---

### 10. Convert Empty Solids to SolidReference

```python
l = proto_bot.search("endPoint")

for i in l:
    n = i.search("name")
    name = ""
    if len(n) >= 1:
        name = n[0].content
    
    if "Solid" in i.DEF and "Empty" in name:
        name_object = i.search("name")
        if name_object and "Ref" not in name_object[0].content:
            i.DEF = "SolidReference {"
            i.children = []
            i.add_child(proto.property(
                name="solidName",
                parent=i,
                content=name_object[0].content[:-1] + "_Ref\"",
                stage=i.stage+1
            ))
```

**Purpose:** URDF often creates empty placeholder Solid nodes. Webots uses `SolidReference` for cleaner referencing.

**Transformation:**

**Before:**
```proto
endPoint Solid {
  name "Empty_link"
  # ... empty properties ...
}
```

**After:**
```proto
endPoint SolidReference {
  solidName "Empty_link_Ref"
}
```

**Why:** Reduces file size and clarifies that the node is just a reference point.

---

### 11. Set Motor Torque Limits

```python
l = proto_bot.search("RotationalMotor")

for i in l:
    t = i.search("maxTorque")
    Reference_Template = proto.property(
        name="maxTorque",
        parent=t[0].parent,
        content="0.001",
        stage=t[0].stage
    )
    if t[0].stage > 6:
        temp = i
        proto_bot.set_current(t[0])
        proto_bot.cursor.update(Reference_Template)
        proto_bot.set_current(temp)
```

**Purpose:** URDF often has unrealistic or missing torque limits. Set sensible defaults for simulation.

**Logic:**
1. Find all `RotationalMotor` nodes
2. Locate `maxTorque` property
3. Replace with `0.001` (conservative default)
4. Only applies if `stage > 6` (nested depth filter to avoid root-level motors)

**Before:**
```proto
RotationalMotor {
  maxTorque 100.0
}
```

**After:**
```proto
RotationalMotor {
  maxTorque 0.001
}
```

**Customization:** Adjust `0.001` based on robot specifications.

---

### 12. Save Modified Proto

```python
proto_bot.save_robot(proto_Filename)
```

Serializes the modified tree back to the proto file, overwriting the original.

---

## Complete Code Flow Summary

```
[User selects input folder]
         ↓
[Parse folder structure]
         ↓
[Extract URDF, mesh, texture paths]
         ↓
[User selects output folder]
         ↓
[Copy meshes → output/meshes_<name>/]
[Copy textures → output/textures_<name>/]
         ↓
[Generate collision meshes (_collision.stl)]
         ↓
[Convert URDF → Proto (urdf2webots)]
         ↓
[Fix mesh paths (absolute → relative)]
         ↓
[Parse proto file into tree structure]
         ↓
[Replace boundingObject meshes with collision variants]
         ↓
[Convert empty Solid → SolidReference]
         ↓
[Update RotationalMotor torque limits]
         ↓
[Save modified proto file]
         ↓
[Done: robot.proto + meshes + textures ready for Webots]
```

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `urdf2webots` | URDF → Proto conversion |
| `tkinter` | File/folder dialog GUI |
| `os`, `shutil` | File operations |
| `json` | Folder structure debugging (optional) |
| `proto_praser` | Proto tree parser (custom) |
| `stl_tool` | Collision mesh generation (custom) |

---

## Error Handling

### File Copy Errors
```python
try:
    shutil.copytree(mesh_path, target_mesh_dir)
    shutil.copytree(texture_path, os.path.join(output_path, "textures_"+folder_name))
except Exception as e:
    print(e)
```

Continues execution even if copy fails (e.g., files already exist).

### Mesh Path Replacement Errors
```python
try:
    for i in range(len(datas)):
        # ... path replacement ...
except Exception as e:
    print("error occurs:\t", e)
```

Logs errors but doesn't stop the script.

---

## Customization Points

### 1. Collision Mesh Face Count
```python
stl_tool.generate_collision_meshes(target_mesh_dir, target_faces=500)
```
Change `500` to desired polygon count.

### 2. Motor Torque Value
```python
content="0.001"
```
Adjust based on robot specifications.

### 3. SolidReference Naming
```python
content=name_object[0].content[:-1] + "_Ref\""
```
Change `"_Ref"` suffix as needed.

### 4. Stage Threshold for Motors
```python
if t[0].stage > 6:
```
Adjust depth filter to target specific motor levels.

---

## Debugging Tips

### Enable folder structure output:
```python
with open('Folder_Object.json', 'w') as f:
    json.dump(Folder_Object, f)
```
Generates a JSON file showing the parsed directory tree.

### Print proto tree structure:
```python
print(proto_bot)  # Prints entire tree
```

### Trace specific modifications:
Add print statements in loops:
```python
for bo in bounding_objects:
    print(f"Processing boundingObject: {bo.name}")
```

---

## Performance

**Typical runtime:**
- Small robot (5-10 links): ~5 seconds
- Medium robot (20-30 links): ~15 seconds
- Large robot (50+ links): ~30 seconds

**Bottlenecks:**
1. Collision mesh generation (quadric decimation)
2. Proto file parsing (tree construction)
3. File I/O (copying large mesh folders)

---

## Future Improvements

1. **Batch processing** - Convert multiple robots without manual selection
2. **Config file** - Externalize parameters (torque, face count, naming)
3. **Validation** - Check proto file integrity after conversion
4. **Rollback** - Save backup before overwriting proto file
5. **GUI** - Replace Tkinter dialogs with full interface
6. **Logging** - Structured logging instead of print statements
7. **Unit tests** - Automated testing for each conversion step

---

## Troubleshooting

### "No module named 'urdf2webots'"
```bash
pip install urdf2webots
```

### "open3d installation failed"
Use Python 3.11 or earlier. See [stl_tool.md](stl_tool.md#installation-requirements).

### "FileNotFoundError: urdf/robot.urdf"
Ensure input folder has correct structure:
```
robot_package/
├── urdf/ ← Must exist
│   └── *.urdf ← Must have URDF file
├── meshes/ ← Must exist
└── textures/ ← Optional
```

### Mesh paths still absolute in proto file
Check line 72-82 in `main.py`. Ensure `mesh_path` matches exactly (case-sensitive).

### Collision detection still slow in Webots
- Verify `_collision.stl` files exist
- Check boundingObject references `_collision.stl` (print `url_prop.content`)
- Reduce `target_faces` further (try 200)

---

## Example Run Output

```
Selected Folder: my_robot
--- 開始處理網格減面: /output/meshes_my_robot ---
已生成: base_link_collision.stl (500 faces)
已生成: arm_link_collision.stl (500 faces)
已生成: gripper_collision.stl (500 faces)
--- 減面完成，共生成 3 個新檔案 ---
--- 開始替換物理碰撞模型 ---
Updated Collision: base_link.stl -> base_link_collision.stl
Updated Collision: arm_link.stl -> arm_link_collision.stl
Updated Collision: gripper.stl -> gripper_collision.stl
[Conversion complete]
```

Output folder:
```
output/
├── myrobot.proto
├── meshes_my_robot/
│   ├── base_link.stl
│   ├── base_link_collision.stl
│   └── ...
└── textures_my_robot/
    └── ...
```

Ready to import into Webots!

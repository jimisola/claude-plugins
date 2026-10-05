# Getting parts into mesh files

The renderer reads meshes only. Keep every part in the **same coordinate frame**: export them all from one document or assembly, and never re-centre parts one at a time, or a lifted lid won't sit on its base.

## STEP, IGES, BREP or a FreeCAD document

Use FreeCAD headless. `freecadcmd` ships with FreeCAD; the AppImage takes it as its first argument (`FreeCAD.AppImage freecadcmd script.py`). In the script:

- For an FCStd file, open it with `App.openDocument(path)`. For STEP, IGES or BREP, use `Part.read(path)` and split the result with `.Solids` when one file holds several parts.
- Tessellate each shape with `MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.03, AngularDeflection=0.15)` and `.write("<name>.stl")` it. Coarser deflection gives faceted curves; finer only adds file size.
- Export one STL per `Part::Feature` you want coloured or moved separately. The file stem becomes the name `--lift` refers to.

## 3MF

PyVista cannot read 3MF. Use trimesh in a throwaway environment: `uv run --with trimesh --with networkx --with lxml python`. Load the file with `trimesh.load(path)`. The result is a scene; write each geometry to its own STL with the scene's transforms applied (`scene.dump()` returns the transformed meshes).

## A KiCad board

Use `kicad-cli pcb export step --subst-models -o board.step board.kicad_pcb`, then convert the STEP file as above. Components appear only if their 3D models are installed. Without models you get the bare board: add stand-in boxes at the footprint positions, and tell the user.

## FreeCAD GUI screenshots are blank

If the user has FreeCAD open and asks for "a screenshot", the GUI route only works while the window is visible on screen. Otherwise it returns a blank white image, and Coin's `SoOffscreenRenderer` fails too. Export the meshes and use this skill's renderer instead.

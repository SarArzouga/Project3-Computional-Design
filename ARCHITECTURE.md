# Project 3 – Code Architecture

## Layers

```
            ┌──────────────────────────────┐      ┌────────────────────────┐
            │  GUI  (Step 4, gui/)          │      │  Notebooks + plotting.py│
            │  import STL, pick BCs, run,   │      │  (Step 1 / Step 2 demos)│
            │  3D view, threshold, export   │      └───────────┬────────────┘
            └──────────────┬───────────────┘                  │
                           │  only calls the core API          │
                           ▼                                   ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  CORE  topopt3d/   (no plotting, no GUI: numbers in → numbers out)       │
  │                                                                         │
  │  mesh.py ──► boundary.py ──► optimizer.py ──► TOResult (x, history, u)  │
  │  VoxelMesh    BoundaryConditions  run_topopt(mesh, bc, settings, callback)│
  │                                   │        ▲                            │
  │                                   ▼        │ uses                       │
  │                              fea.py     filters.py                      │
  │                              Hex8 ke,   sensitivity filter              │
  │                              sparse K,  (rmin in element sizes)         │
  │                              solve                                      │
  │  problems.py: ready-made test problems (cantilever, Project 2 slab)     │
  │                                                                         │
  │  STL file ─► stl_io.read_stl ─► voxelize (ray casting) ─► VoxelMesh     │
  │              (VoxelMesh.from_stl(path, resolution) does all three)      │
  │                                                                         │
  │  densities x ─► postprocess.smooth_surface ─► stl_io.write_stl ─► STL   │
  │   (threshold → remove islands → marching cubes → Taubin smoothing)      │
  └────────────────────────────────────────────────────────────────────────┘
                           ▲
            tests/test_core.py  (15 automatic checks, `python -m pytest -v`)
```

## GUI (Step 4) – PySide6 + PyVista

Start: double-click `Run_TopOpt3D_App.bat`, or `python -m gui` in the project-3 folder (Anaconda Python).
Self-test: `python -m gui --selftest` drives the real window and saves screenshots to `gui_screenshots/`.

| File | Job | Uses |
|---|---|---|
| `gui/main_window.py` | panels 1–5, 3D view, clicking / box selection, calls the core | Qt, PyVista |
| `gui/bc_model.py` | supports and loads as lists of **surface faces**; "whole flat side"; builds `BoundaryConditions` | numpy + core only (tested without a window) |
| `gui/scene.py` | turns meshes / densities into PyVista objects (voxel surface, arrows, result voxels) | PyVista |
| `gui/worker.py` | runs `run_topopt` in a background thread; Stop = callback returns `False` | Qt + core |
| `gui/selftest.py` | scripted user session with a real screen pick | Qt, VTK |

**Boundary-condition method:** the voxel model's outer faces are drawn as clickable quads (cell id = face id).
- Click a face → selected (optionally the whole connected flat side). A drag still rotates the view.
- *Box select* → drag a rectangle; visible faces only, or also hidden ones.
- *Add support* fixes x / y / z of all nodes of the selected faces; *Add load* spreads a total force (Fx, Fy, Fz)
  over those nodes. Colours: grey = free, yellow = selected, blue = support, red = load (+ arrows).

## Using the core (4 steps)

```python
mesh = VoxelMesh.box(60, 20, 4, 60, 20, 4)          # or VoxelMesh.from_mask(mask, size)
bc = BoundaryConditions(mesh)
bc.fix(mesh.nodes_on_plane(0, 0.0))                  # supports
bc.load(mesh.nodes_in_box(lo, hi), (0, -1, 0))       # total force, split over the nodes
result = run_topopt(mesh, bc, TOSettings(penal=3, rmin=1.5), callback=show_progress)
```

## Design decisions

| Decision | Why |
|---|---|
| Core never plots or imports GUI code | Core can be read and tested on its own; any front end can use it |
| Progress through a `callback(info)`; returning `False` stops the run | Notebook prints, GUI redraws or offers a Stop button, same core |
| `VoxelMesh` = voxel grid + True/False mask | One class for a box (Step 1) and any voxelized STL (Step 3) |
| All voxels identical → one `ke` for all elements | Fast; only the Jacobian of one voxel is needed |
| Nodes not used by any active voxel are removed and renumbered | No empty rows in K for holes / cut-outs |
| `rmin` given in element sizes | Same value works for any voxel size (Project 2's rmin = 3 was only 1.2 elements) |
| Supports and loads chosen by node ids (`nodes_on_plane`, `nodes_in_box`) | A GUI only has to turn a click/box into node ids |
| `solver="auto"`: sparse direct below 5 000 free DOFs, else CG + Jacobi preconditioner (falls back to direct if CG fails) | Measured on the bracket STL (22 680 DOFs): CG 0.84 s/iteration vs direct 5.45 s, same result. Threshold lowered from 10 000 after the GUI test (9 744 DOFs: 35 s → 16 s) |
| Optimization in a background thread, view redrawn at most twice per second | Window stays responsive; Stop button works during a run |
| Surface by marching cubes on the density field (not on the 0/1 voxels) | Surface lies exactly at density = threshold between voxel centres |
| Taubin smoothing, 20 iterations, no pre-blur (defaults) | Measured on the bracket: Laplacian −51 %, Taubin −5 %; blur σ = 0.5 removed another 6 % |
| Outer faces of the design domain kept flat during smoothing, nothing leaves the domain (`flat_bounds=True`) | Free smoothing rounded the bridge's abutment feet (contact 30 → 4–10 nodes) and pushed them 1 unit below the ground; the roller bridge became nearly a mechanism. With flat faces the exported bridges are within 2–5 % of the black/white design's stiffness |
| Floating islands (< 1 % of the solid) removed before meshing | Optimizer leftovers can't be manufactured |
| Exported surface checked: every edge shared by 2 triangles, outward normals | Slicers / CAD need a closed, correctly oriented STL |
| Own ray-casting voxelizer (numpy only) instead of a library | Short enough to explain on a slide; reports if the STL is not watertight |
| Supports/loads only on the outer surface (`surface_nodes`, `nodes_where(..., surface_only=True)`) | Forces act on the surface; the GUI will draw and pick the same surface faces |
| 0-based node numbering (Project 2 files were 1-based) | Python indexing, no `-1` everywhere |
| Material constants in `TOSettings` (`E = 1`, `nu = 0.25`) | One place for inputs (lesson from the ν = 0.3 / 0.25 mix-up) |

## Files

| File | Content |
|---|---|
| `topopt3d/mesh.py` | `VoxelMesh` (box, mask, STL): nodes, elements, DOFs, node selection, surface faces, `to_grid` |
| `topopt3d/stl_io.py` | `read_stl`, `write_stl` (binary/ASCII), `stl_volume` |
| `topopt3d/voxelize.py` | `voxelize(triangles, resolution)` by ray casting |
| `topopt3d/postprocess.py` | `smooth_surface`: threshold, islands, marching cubes, Taubin / Laplacian smoothing, watertight check |
| `topopt3d/boundary.py` | `BoundaryConditions`: `fix`, `load`, checks |
| `topopt3d/fea.py` | `D_matrix`, `B_matrix`, `hex8_stiffness`, `FEModel` (assemble, solve, element energy) |
| `topopt3d/filters.py` | `SensitivityFilter` (KD-tree neighbours, sparse weights) |
| `topopt3d/optimizer.py` | `TOSettings`, `TOResult`, `optimality_criteria`, `run_topopt` |
| `topopt3d/problems.py` | `cantilever`, `project2_slab` |
| `plotting.py` | matplotlib helpers for notebooks (not core) |
| `tests/test_core.py` | element, beam theory, box voxels, mesh, BCs, filter, regression vs Step 1, cg vs direct, callback |
| `tests/test_stl.py` | STL round trip, exact box voxelization, sphere volume convergence, surface faces, TO on an STL |
| `tests/test_gui_logic.py` | flat-side selection, face states, building BCs, error messages, GUI BCs run in the core |
| `tests/test_postprocess.py` | closed + outward box surface, threshold, islands, Taubin keeps volume / Laplacian shrinks, STL round trip |
| `Step5_PostProcessing_STL_Export.ipynb` | threshold study, smoothing comparison (bracket + sphere), final STL export |
| `results/bracket_optimized.stl` | exported optimized bracket |

| `Step3_Bridge_STL_Voxel_TO.ipynb` | civil model: pedestrian bridge, deck kept solid, pinned-pinned vs pinned-roller, reactions |
| `Step5_Bridge_PostProcessing_STL.ipynb` | bridge threshold / smoothing study, flat outer faces, STL export of both cases, structural check of the exported parts |
| `results/bridge_A_pinned_pinned.stl`, `results/bridge_B_pinned_roller.stl` | exported bridges; `results/bridge_A_vs_B_exported.png` comparison picture |

**Keep (non-design) regions:** `run_topopt(mesh, bc, settings, keep=element_ids)` keeps those elements solid
(x = 1, counted in the volume fraction), e.g. a bridge deck or a ring around a bolt hole.
In the GUI: select faces → *Layers deep* → **Keep solid (non-design)** keeps the voxels under the faces, that many
layers inward (stops where the part ends). Green in the view (a load on the same faces is drawn red on top).
Bridge self-test: `python -m gui --selftest bridge` (reproduces the notebook case A exactly).
| `examples/make_sample_parts.py` | creates `sample_parts/*.stl` (box, sphere, bracket with hole) |
| `Step2_Core_Demo.ipynb` | cantilever with the core API, L-bracket from a voxel mask, runs the tests |
| `Step3_STL_Voxel_TO.ipynb` | STL parts, voxelization accuracy study, TO of the bracket with a bolt hole |

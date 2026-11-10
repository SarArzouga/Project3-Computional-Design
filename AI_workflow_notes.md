# Project 3 – AI Workflow Notes

Tool: Claude (Claude Code desktop app), working directly in my course folder.
Approach: go from simple to complex, test each step before the next one.

---

## Session 1 (Nov 1, 2026) – Understanding the task and Step 1

### 1. Clarifying the assignment
- **My prompt:** "Could you clarify exactly what is needed in brief words?" (attached the assignment text)
- **AI answer (summary):** 5 build steps (3D Hex8 cantilever → decoupled architecture → STL voxelization → GUI with BCs → threshold + smoothing + STL export) and a presentation with AI workflow, live demo, and 2D vs 3D code differences.
- **My follow-up:** "Which 2D code should be extended?" → AI: my submitted Project 2 code (SIMP + sensitivity filter + OC, Q4 elements).

### 2. Giving the AI my Project 2 code
- I saved my submitted Project 2 notebook and input files in `project-3/` and re-ran it.
- I did not have to upload anything: the AI read the folder directly and checked the saved output.
- **AI observation:** the 2D result matches the professor's example, but the run stopped at the 100-iteration
  limit (`loop_max`) instead of the convergence criterion `change < 0.1`.
- **Environment issue:** the default Python had no scipy/pandas; the AI found that my Jupyter uses
  Anaconda (`anaconda3`) and used that Python instead.

### 3. Step 1 – 3D Hex8 cantilever (`TO3D_Step1_Hex8_Cantilever.ipynb`)
- **My prompt:** "Yes, start step 1."
- AI kept the same section order as my 2D notebook so the two can be compared side by side.
- **Testing plan the AI proposed (test before trusting the optimizer):**
  1. Element stiffness checks: symmetric, 6 zero eigenvalues (rigid-body modes).
  2. Solid beam deflection vs. Timoshenko beam theory, with mesh refinement.
  3. One-element-thick 3D slab should reproduce my 2D Project 2 result.
  4. True 3D cantilever 60 × 20 × 4.

#### Errors / issues met during Step 1
| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `ZeroDivisionError` in `cantilever_bcs` during the beam test | Mesh 15 × 5 × 1 has no node at y = H/2 (nodes at y = 0, 4, 8, 12...), so the load was divided by 0 nodes | Use an even number of elements in y; added a clear error message for this case |
| 2 | 3D slab (Test 3) gave a symmetric X-truss, but my 2D result is asymmetric | My 2D `solve_FE` (from the class template) fixes only **x** on the left edge plus **y at node 21**, which in this mesh is (50, 0), the middle of the bottom edge. So my 2D problem has an extra hidden support; the 3D code had a fully clamped left face. Found by solving the 2D model with full density: u_y at (50, 0) was exactly 0 | Added `project2_bcs` with the same supports and load direction (+1) as my 2D code. Then the 3D slab reproduces the 2D shape ✔ |
| 3 | Optimization with penal = 5, rmin = 3 never converges (2D and 3D): `change` stays ≈ 0.12–0.2 until `loop_max` | rmin = 3 with element size 2.5 → filter reaches only 1.2 elements, so the design oscillates. This is why my 2D run stopped at 100 iterations | Use rmin ≥ 1.5 elements (3.75) with penal = 3 → converges (change < 0.01) |
| 4 | First 3D voxel figure was cramped and the side view was missing | Several 3D + 2D subplots in one figure | Split into a 3D-view figure and a side view + history figure. Better 3D graphics planned for the GUI step |

#### Results
- Test 1: ke is 24 × 24, symmetric, exactly 6 zero eigenvalues. ✔
  k_e doubles when the element size doubles (in 2D it did not change → Jacobian matters in 3D).
- Test 2 (Timoshenko theory = 29.250, ν = 0.25):

  | Mesh | FE tip deflection | % of theory |
  |------|------|------|
  | 12 × 4 × 1 | 27.993 | 95.7 % |
  | 30 × 10 × 2 | 29.094 | 99.5 % |
  | 60 × 20 × 4 | 29.364 | 100.4 % |
  | 90 × 30 × 6 | 29.456 | 100.7 % |

  Coarse Hex8 meshes are too stiff (shear locking); results converge to theory when refined. ✔
- Test 3: 40 × 16 × 1 slab with my Project 2 BCs reproduces my 2D shape for both
  (penal 5, rmin 3) and (penal 3, rmin 3.75). ✔ → `step1_results/test3_slab_project2_bcs.png`
  With a fully clamped left face instead, both 2D and 3D give a symmetric truss → `step1_results/test3_2D_vs_3D.png`
- Test 4: 60 × 20 × 4 cantilever (4800 elements, 19 215 DOFs), penal 3, rmin 1.5, volfrac 0.3:
  converged in 48 iterations (~70 s), c = 82.11 (ν = 0.25). ✔
  Real 3D effect: top/bottom flanges use the full thickness, diagonal web members only part of it
  (gray in the through-thickness average) → like an I-beam. A 2D code cannot find this.
  → `step1_results/test4_3D_cantilever_3Dview.png`, `test4_3D_cantilever_side_history.png`

**My question:** "You said rmin = 1.5, but in the workflow you used rmin = 3.75?"
→ Both are **1.5 element sizes**: rmin is a length. Test 3 elements are 2.5 (3.75 / 2.5 = 1.5),
Test 4 elements are 1.0 (1.5 / 1.0 = 1.5). Project 2's rmin = 3 is only 1.2 elements (too small).
**Design decision for Step 2:** the user enters rmin in *element sizes*; the code converts it to a length
(important for STL voxel models where the voxel size changes).

**My question:** "Is the Jacobian needed? The professor did not give it in the course material. Can we remove it?"
→ In k_e = ∫ Bᵀ D B dV the element size *a* appears twice: strains scale with (2/a)² and the
integration area/volume with (a/2)^dim.
2D square: (2/a)² · (a/2)² = 1 → cancels for any size, so the 2D template could leave it out.
3D cube: (2/a)² · (a/2)³ = a/2 → does **not** cancel.
Removing it would keep the optimized shape for identical cubes (constant scaling) but make
displacements/compliance wrong (Test 2 would fail) and distort box-shaped voxels (Step 3).
Elements are still identical in 3D; the Jacobian only maps the reference element (−1…1) to the real size.
**Decision:** keep J.

**My request:** "Make the final 2D shapes in cell 16 (Test 3) complete. Maybe increase the iterations?"
→ AI tested it first: for penal 5, rmin 3, running 200 / 500 / 1000 iterations and smaller move limits
(0.1, 0.05) never converged. After ~400 iterations the design repeats a **4-iteration cycle**
(c = 37.684 / 37.771 / 37.689 / 37.771, only 0.2 % apart): the shape is final but a few elements flip forever.
- AI tried an extra stopping rule (stop when compliance is stable) → did not trigger because of the
  0.2 % cycle; a looser tolerance would stop good runs too early → **removed** (keep code simple).
- **Final fix:** loop_max 500 for Test 3 and a **black/white final shape (density > 0.5)** next to each
  density plot → complete shapes. Same threshold idea as the Step 5 post-processing.

**My question:** "Test 1 uses ν = 0.3 but Test 3 says ν = 0.25. Which one is used? Use 0.25 like my 2D code."
→ The AI had mixed them: Tests 1, 2, 4 used 0.3 (the default in `run_TO3D`), only Test 3 used 0.25.
**Fix:** material constants defined once at the top (`E0 = 1.0`, `NU = 0.25`) and used everywhere.
Re-ran everything: all tests still pass, same shapes; small number changes
(Test 2 theory 29.340 → 29.250; Test 4: 41 → 48 iterations, c 82.02 → 82.11).
**Lesson:** check the AI's parameter values; define each input in one place only.

**Lesson for the presentation:** testing the new code against my own old code exposed a boundary
condition in my 2D code that I had not noticed. Verify step by step (element → solver → known result → new problem).

---

## Session 2 (Nov 2, 2026) – Step 2: architecture (core decoupled from GUI)

- **My prompt:** "Start step 2."
- **AI proposal (before coding):** a core package `topopt3d/` (mesh, boundary conditions, FEA, filter,
  optimizer, test problems) with **no plotting or GUI code**; plotting in a separate `plotting.py`;
  automatic tests in `tests/`; GUI later in `gui/`. See `ARCHITECTURE.md` for the diagram and decisions.
- **Key idea:** the optimizer reports progress through a **callback** instead of plotting inside the loop.
  Notebook → prints; GUI → redraws / Stop button. Same core code.
- **Preparing for Step 3:** `VoxelMesh.from_mask(mask, size)` builds a mesh from any True/False voxel array
  (a voxelized STL will be such a mask). Demo: L-bracket made by cutting a block out of a 30 × 30 × 3 grid.
- **Design decision from my earlier question:** `rmin` is entered in element sizes.
- **Checking the AI's work:** the Step 1 tests became 15 automatic tests (`python -m pytest -v`, ~1.5 min).
  Two regression tests prove the restructured code gives **exactly** the Step 1 numbers
  (slab: 85 it, c = 40.4642; 3D cantilever: 48 it, c = 82.1089). All 15 passed on the first run.
  New test: box-shaped voxels (1 × 2 × 1) still match beam theory → Jacobian works for non-cubes.
- **Issue caught:** `!python -m pytest` inside a notebook can start the other (non-Anaconda) Python on my
  PC, which has no scipy → use `!"{sys.executable}" -m pytest`.
- Files: `topopt3d/`, `plotting.py`, `tests/test_core.py`, `Step2_Core_Demo.ipynb`, `ARCHITECTURE.md`.

---

## Session 2 (cont.) – Step 3: STL → voxel model → topology optimization

- **My prompt:** "Start step 3."
- **AI plan:** own STL reader/writer and a **ray-casting voxelizer** in numpy (no black-box library,
  easy to explain): for each voxel column shoot a ray along z; a voxel is inside if an **odd** number of
  surface crossings lies below its centre. Rays are shifted by a tiny amount so they never hit a triangle
  edge exactly (would count twice). An odd number of crossings in a column = STL has a gap → reported.
- No STL files were given → AI generated sample parts (`examples/make_sample_parts.py`): exact box,
  sphere r = 10, bracket 80 × 40 × 16 with a bolt hole r = 7 (marching cubes from a distance function).
- Added mesh surface functions (`surface_faces`, `surface_nodes`, `nodes_where`) because supports and loads
  act on the surface; the GUI will need the same faces for drawing and clicking.

#### Voxelizer accuracy (voxel volume vs STL volume)
| Part | Resolution | Voxels | Error |
|---|---|---|---|
| box 10 × 6 × 4 | 10 | 240 | 0.00 % (exact) |
| sphere r = 10 | 10 / 20 / 40 | 552 / 4 224 / 33 552 | +5.58 / +0.99 / +0.27 % |
| bracket with hole | 20 / 40 / 80 | 752 / 6 144 / 48 704 | −1.25 / +0.85 / −0.07 % |

All parts watertight; voxelizing takes < 0.2 s.

#### Bracket optimization
Support = hole surface (bolt), load = 1 downward on the middle line of the right face, volfrac 0.25,
penal 3, rmin 1.5, resolution 40 (6 144 voxels, 22 680 DOFs): converged in 41 iterations.
Result: ring of material around the bolt hole + truss arms to the load.

#### Errors / issues met during Step 3
| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | Bracket optimization slow: 5.45 s per iteration (224 s total) | sparse **direct** solver (LU) has a lot of fill-in for 3D blocks | AI benchmarked options: **CG + Jacobi preconditioner** 0.84 s/iteration, same result (c = 9.351688) → 6.5× faster. `solver="auto"` uses CG above 10 000 DOFs and falls back to direct if CG fails. Warm start (previous u) gave no gain → removed |
| 2 | One new test failed (surface nodes of a 4 × 3 × 2 box) | the **test** expectation was wrong (I said 0 inner nodes; really 3 × 2 × 1 = 6) | fixed the test, the code was right. Lesson: tests can be wrong too |
| 3 | Bracket STL looked see-through in the plot | plot thinned 88 800 triangles to 30 000 for speed → gaps | made the sample bracket with a coarser surface (22 768 triangles) |

Tests: 27 automatic tests pass (15 core + 11 STL + 1 cg-vs-direct). The regression tests now use
`solver="direct"` so they still match Step 1 exactly.

---

## Session 2 (cont.) – Step 4: GUI

- **My prompt:** "Start step 4."
- AI checked what can be installed for my Python 3.14 (Anaconda): PySide6 was there, PyVista/VTK were not but
  had wheels → asked me two decisions:
  1. **Toolkit:** desktop app with PySide6 + PyVista (my choice) vs a browser app (Python server + three.js).
  2. **How to add boundary conditions** (the decision the professor asks for): **click faces + box select** (my choice)
     vs click only vs typed regions.
- Installed `pyvista 0.49.2`, `pyvistaqt 0.13.2`, `vtk 9.7.1` with pip.
- AI looked up the real PyVista picking functions in the installed version before using them (not from memory).

#### Design
- Panels follow the assignment: 1 Part (open STL / sample) → 2 Voxelize (resolution) → 3 Supports & loads →
  4 Optimize (volfrac, **penal**, **rmin**, max iter, tol; Run / Stop; live convergence plot) → 5 Results
  (density threshold slider, design/result view, STL overlay; export button reserved for Step 5).
- **BC method:** the voxel model's outer faces are clickable. Click = select face (option: whole flat side),
  drag = rotate, *Box select* = rectangle (visible or also hidden faces). Then *Add support* (x/y/z) or
  *Add load* (total Fx, Fy, Fz spread over the nodes). Colours: grey / yellow selected / blue support / red load + arrows.
- Still decoupled: `bc_model.py` (no Qt) turns face selections into core `BoundaryConditions`; the optimizer runs
  in a background thread and reports through the same callback as in Step 2 (Stop = return False).

#### Testing a GUI
- `tests/test_gui_logic.py`: 5 tests of the selection/BC logic without a window.
- `python -m gui --selftest`: drives the **real** window: load bracket → voxelize (30) → support on the hole →
  **real mouse pick** at the screen position of the right face (selected the whole side, 90 of 90 faces) →
  load → run 40 iterations in the background → screenshots (`gui_screenshots/`). All 7 checks passed.

#### Errors / issues met during Step 4
| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | PyVista would use PyQt6 while the app uses PySide6 | both bindings installed; qtpy picks PyQt6 first | `QT_API=pyside6` set in `gui/__init__.py` before any Qt import |
| 2 | A new GUI-logic test failed ("Select faces first") | **test** box at y = 2 ± 0.1 contained no face centres (they are at 1.5, 2.5) | widened the box in the test; code was right |
| 3 | 112 load arrows cluttered the view | one arrow per loaded node | draw at most 30, shorter |
| 4 | Result hard to read in 3D (all black) | no voxel edges, colour scale ended at black | thin voxel edges, lighter colour range |
| 5 | GUI run slow: 40 iterations in 35 s | model had 9 744 free DOFs, just under the 10 000 switch to CG → direct solver | CG from 5 000 DOFs → **16 s**, same result (c = 9.9339) |

Tests: **32 pass** (15 core + 11 STL + 1 cg + 5 GUI logic) + GUI self-test OK.

---

## Session 2 (cont.) – Step 5: threshold, smoothing, STL export

- **My prompt:** "Is it okay if you complete all steps, then we review one by one together?" → AI did Step 5.
- **AI plan:** threshold → remove floating islands → **marching cubes** on the density field → **Taubin smoothing**
  (own numpy code) → STL export with the Step 3 writer → check the surface is closed.
- **Why Taubin:** Laplacian smoothing moves each vertex to the average of its neighbours → smooth but shrinks.
  Taubin alternates a smoothing step (λ = 0.5) and an "un-shrinking" step (μ = −0.53).

#### How the smoothing method was decided (measured, not guessed)
| Test | Raw marching cubes | Laplacian 20 | Taubin 20 | Taubin 20 + blur σ = 0.5 |
|---|---|---|---|---|
| Sphere r = 10: volume (exact 4188.8) | 4236.3 | 4003.5 (−5.5 %) | 4249.9 | – |
| Sphere: roughness (std of radius) | 0.138 | 0.023 | **0.057** | – |
| Bracket: volume vs raw | 0 % | **−68.2 %** (plates collapse) | **−1.5 %** | −9.7 % |

Threshold study (bracket, Taubin): t = 0.3 / 0.5 / 0.7 → 30.0 / 21.1 / 14.1 % of the part volume (target 25 %).
**Decision:** Taubin, 20 iterations, no blur (blur is an option).

#### GUI
Panel 5 now has: smoothing method, iterations, pre-blur, remove islands, **Preview smooth surface**,
**Export STL...**, view "Smooth surface". The self-test now also previews and exports an STL and reads it back:
**9/9 checks passed**.

#### Errors / issues met during Step 5
| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | Island removal set all gray densities to 0 | wrong `np.where` condition | only removed islands are set to 0, so marching cubes still interpolates the gray transition |
| 2 | Box surface had **negative** volume | skimage winds triangles inward → STL normals point inside | reverse the triangle order; test checks positive (outward) volume |
| 3 | At threshold 0.7 the surface had only half the voxel volume | default blur σ = 0.5 lowered the peak density of 2-voxel-thick members | blur off by default |
| 4 | Printing notebook output crashed ("charmap can't encode σ") | Windows console uses cp1252 | `PYTHONIOENCODING=utf-8` (only my output script, not the app) |

Exported part: `results/bracket_optimized.stl`, 5 108 triangles, closed (0 open edges after reading back),
21.1 % of the original volume. Tests: **38 pass**.
**Known limitation:** no non-design ("keep") region yet → the material left of the bolt hole was removed.

---

## Session 3 (Nov 3, 2026) – Choosing my own model: a pedestrian bridge (Step 3 redone)

- **My questions:** "What STL should I optimize? The best selection for an advanced model?" → AI suggested the
  GE jet engine bracket (famous TO benchmark). **Then I asked:** "I am from the civil department, would a civil
  model be more challenging?" → AI: not harder to compute, but more relevant, and the challenge is in modelling
  (distributed loads, realistic supports, a deck that must stay solid, long spans). Options: pedestrian bridge,
  tree column, transfer beam, cantilever balcony. **I chose the pedestrian bridge with a clearance opening.**
- **New core feature – keep (non-design) region:** `run_topopt(..., keep=elements)`; those elements stay at
  density 1 and count in the volume fraction (error if the keep region alone is bigger than volfrac).
  Needed for the deck. 2 new tests → **40 tests pass**.
- **STL:** `sample_parts/pedestrian_bridge.stl`, 120 × 16 × 40 (z up), opening 80 × 18 under the deck,
  20-long abutments; built from exact voxel faces (sharp, closed). Resolution 60 → voxel size 2 fits the
  geometry exactly (0.00 % volume error; resolution 30 gives −4.76 %).
- **Notebook:** `Step3_Bridge_STL_Voxel_TO.ipynb`. Deck top 4 units kept solid (14.3 % of the domain),
  uniform deck load (total 1 down, 549 nodes), supports at the abutment bases, volfrac 0.30, penal 3, rmin 1.5.

#### Results – two support cases
| Case | Iterations | Compliance | Left Rx | Right Rx | Rz (each) | Structure |
|---|---|---|---|---|---|---|
| A pinned – pinned | 80 (66 s) | 0.644 | +0.234 | −0.234 | 0.500 | inclined legs leaning out to the abutments (arch-like, thrust) |
| B pinned – roller | 114 (216 s) | 0.846 | 0.000 | 0.000 | 0.500 | vertical legs + **tie** across the top of the opening (tied frame) |

- Reactions from R = K u − f: vertical reactions 0.5 + 0.5 = load (equilibrium check ✔).
- Case A: horizontal thrust = 0.234 ≈ 47 % of the vertical reaction; case B: no thrust possible → the tie
  carries it internally. **Same material, B is 31 % more flexible.**
- The optimizer "rediscovered" basic structural behaviour (arch thrust vs tied system) from the supports alone.
- Limits: one load case, no self-weight, linear isotropic (steel-like) material.

### Step 4 redone for the bridge
- **My prompt:** "Yes, redo step 4."
- GUI: new **Keep solid (non-design)** button with *Layers deep* (voxels under the selected faces stay solid;
  stops at openings), green colour, legend; the bridge is the first sample part. Keep regions are passed to the
  core through the background worker.
- **Bridge self-test** (`python -m gui --selftest bridge`), real window: voxelize at 60 → **real click on the deck**
  selects the whole top (480 faces) → keep 2 layers (960 voxels) → click again → load (0, 0, −1) → pin both
  abutment bases → run → **exactly the notebook result (80 iterations, c = 0.6442)** → deck stayed solid →
  smooth surface (5 644 triangles, closed) → STL exported. **8/8 checks**; bracket self-test still OK.
- 3D result from below: each abutment gets **two forked legs** across the deck width.

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | Bracket self-test would have loaded the bridge | sample list order changed (bridge first) | select samples by name, not by position |
| 2 | New test failed: "No supports" | **test** built BCs without a support (the code check is right) | added a support in the test |
| 3 | Same test then failed: "A load is applied on a fixed DOF" | the test's support face shared edge nodes with the loaded face; the core correctly refuses | support on the bottom face in the test. In the app the same error message protects the user |
| 4 | Deck top shows red (load), not green (keep) | load and keep on the same faces; load drawn on top | kept as is; the list shows both entries |

Tests: **43 pass** + bridge and bracket GUI self-tests OK.

### Step 5 redone for the bridge (`Step5_Bridge_PostProcessing_STL.ipynb`)
- **My prompt:** "Yes, redo step 5."
- AI plan: threshold and smoothing study on the bridge, export both cases, and a **structural check of the
  exported part**: voxelize the exported STL again, same supports and deck load, compare the stiffness with the
  optimized design.

#### Key finding: smoothing must not touch the supports
The first check gave an impossible result: exported bridge B was **38× more flexible** (c = 29.4 vs 0.78).
- First suspicion: my check picked the lowest nodes of the whole part → picked per abutment → **same result**.
- Printing the support nodes showed the real cause: smoothing **rounded the abutment feet**. Ground contact
  dropped from 30 / 24 nodes to **10 / 4**, and the feet bulged **1 unit below the ground** (z = −1.06). With a
  roller and a tiny contact, bridge B was almost a mechanism. (The deck top also rose to 40.31.)
- **Fix in the core:** `smooth_surface(..., flat_bounds=True)` (default): vertices on the 6 outer planes of the
  design domain may slide along the plane but not leave it, and every vertex is clipped to the domain.
  Curved or inner surfaces are still smoothed. New test: feet keep full ground contact, deck stays at the top.
  GUI checkbox "Keep outer faces flat" (on by default).

| Case | Optimized (gray) | Black/white (≥ 0.5) | STL, free smoothing | **STL, flat faces (final)** |
|---|---|---|---|---|
| A pinned – pinned | 0.6443 | 0.5541 | 0.7480 (+35 %) | **0.5832 (+5.3 %)** |
| B pinned – roller | 0.8458 | 0.7785 | 29.448 (mechanism) | **0.7975 (+2.4 %)** |

- Final exported bridges: B is 37 % more flexible than A (optimizer: 31 %) → the civil conclusion survives
  post-processing. Volumes: A 27.1 %, B 25.1 % of the domain; both STLs closed (0 open edges).
- Smoothing on the bridge (flat faces): Laplacian −26 % volume, Taubin −2.2 %. Thresholds 0.3 / 0.5 / 0.7 →
  32 / 27 / 21 % of the domain.
- The bracket notebook (`Step5_PostProcessing_STL_Export.ipynb`) was re-run with the new default; its numbers
  changed (Laplacian −51 %, Taubin −5 %, sphere roughness 0.138 → 0.067); decision text updated.
- Files: `results/bridge_A_pinned_pinned.stl`, `results/bridge_B_pinned_roller.stl`,
  `results/bridge_A_vs_B_exported.png`.

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | Exported bridge B 38× too flexible | smoothing rounded the support feet and moved them below ground | `flat_bounds=True` (see above) |
| 2 | New GUI checkbox would have replaced "Click selects the whole flat side" | same variable name `chk_flat` | renamed to `chk_flat_bounds`, found by searching the file before running |
| 3 | A file name vanished from notebook text | backticks in a shell command were run by the shell | used a quoted heredoc for the script |

Tests: **44 pass**; bridge GUI self-test 8/8 (still exactly c = 0.6442).

---

## What changed from 2D to 3D (for the "core code" slide)
| Item | 2D (Project 2) | 3D (Project 3) |
|------|------|------|
| Element | Q4 (4 nodes) | Hex8 (8 nodes) |
| DOFs per node | 2 | 3 |
| Element stiffness | 8 × 8 | 24 × 24 |
| B matrix | 3 × 8 | 6 × 24 |
| D matrix | 3 × 3 plane stress | 6 × 6 isotropic 3D |
| Gauss points | 2 × 2 | 2 × 2 × 2 |
| Jacobian | cancels for square elements (left out) | must be included (k_e scales with size) |
| Mesh | read from node/element txt files | generated (structured voxel grid) |
| Global K | dense `np.zeros`, double for-loop | sparse (`scipy.sparse`), vectorized |
| Solver | `np.linalg.solve` | `scipy.sparse.linalg.spsolve` |
| Filter neighbours | all pairs (n² loop), circle | KD-tree, sphere, sparse weights |
| Rigid-body modes | 3 | 6 |
| Plot | colored squares | 3D voxels + side view |
| Unchanged | SIMP, compliance & sensitivity, OC bisection, convergence loop | same |

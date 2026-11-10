"""Matplotlib helpers for the notebooks. NOT part of the core (topopt3d never imports this);
the GUI in Step 4 will have its own 3D view."""
import matplotlib.pyplot as plt
import numpy as np


def plot_voxels(mesh, x, threshold=0.5, title="", ax=None, show_bcs=None):
    """3D view of the elements with density > threshold, darker = denser.
    show_bcs: optional BoundaryConditions, draws supports (blue) and loads (red)."""
    dens = mesh.to_grid(x)
    nx, ny, nz = mesh.shape
    X, Y, Z = [mesh.origin[d] + np.arange(n + 1) * mesh.size[d]
               for d, n in enumerate((nx, ny, nz))]
    X, Y, Z = np.meshgrid(X, Y, Z, indexing="ij")
    colors = np.empty(dens.shape + (4,))
    colors[..., :3] = (1 - dens[..., None]) * 0.75
    colors[..., 3] = 1.0
    if ax is None:
        ax = plt.figure(figsize=(10, 5)).add_subplot(projection="3d")
    ax.voxels(X, Y, Z, dens > threshold, facecolors=colors, edgecolor="k", linewidth=0.1)
    if show_bcs is not None:
        for nodes, _ in show_bcs.supports:
            p = mesh.nodes[nodes]
            ax.scatter(p[:, 0], p[:, 1], p[:, 2], color="#2563eb", s=6, depthshade=False)
        for nodes, _ in show_bcs.loads:
            p = mesh.nodes[nodes]
            ax.scatter(p[:, 0], p[:, 1], p[:, 2], color="#dc2626", s=30, depthshade=False)
    lo, hi = mesh.bounds
    ax.set_box_aspect(hi - lo)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.set_title(title)
    return ax


def plot_stl(triangles, title="", ax=None, max_triangles=30000):
    """Shaded view of an STL surface (thinned out above max_triangles to keep matplotlib fast)."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    tri = np.asarray(triangles)
    if len(tri) > max_triangles:
        tri = tri[np.linspace(0, len(tri) - 1, max_triangles).astype(int)]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    shade = 0.35 + 0.55 * np.abs(n @ np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8]))
    colors = np.column_stack([0.30 * shade, 0.55 * shade, 0.85 * shade, np.ones_like(shade)])
    if ax is None:
        ax = plt.figure(figsize=(8, 5)).add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolor="none"))
    lo, hi = tri.reshape(-1, 3).min(axis=0), tri.reshape(-1, 3).max(axis=0)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.set_title(title)
    return ax


def plot_side_view(mesh, x, title="", ax=None, axis=2):
    """Like Project 2: density averaged along `axis` (only over voxels that exist).
    axis=2: view along z (x-y plane), axis=1: view along y (x-z plane, e.g. a bridge elevation)."""
    dens = mesh.to_grid(x)
    count = np.maximum(mesh.active.sum(axis=axis), 1)
    avg = dens.sum(axis=axis) / count
    a, b = [d for d in range(3) if d != axis]
    lo, hi = mesh.bounds
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(1 - avg.T, cmap="gray", origin="lower", vmin=0, vmax=1,
              extent=[lo[a], hi[a], lo[b], hi[b]])
    ax.set_xlabel("xyz"[a]); ax.set_ylabel("xyz"[b])
    ax.set_title(title)
    return ax


def plot_history(result, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 3.5))
    it = np.arange(1, len(result.history["c"]) + 1)
    ax.plot(it, result.history["c"], color="#2563eb")
    ax.set_xlabel("Iteration"); ax.set_ylabel("Compliance c", color="#2563eb")
    ax2 = ax.twinx()
    ax2.plot(it, result.history["vol"], color="#d97706")
    ax2.set_ylabel("Volume fraction", color="#d97706"); ax2.set_ylim(0, 1)
    return ax

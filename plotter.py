import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from typing import List

RC_HEIGHT = 2.8
CLG_HEIGHT = 6.0

pointR3 = list[float]

#floor corners:
verts_floor_1: list[pointR3] = [
    [12.0, 45.6, 0.0], 
    [12.0, 40.1, 0.0], 
    [22.5, 40.1, 0.0], 
    [22.5, 36.3, 0.0], 
    [52.7, 36.3, 0.0], 
    [52.7, 37.3, 0.0], 
    [66.6, 37.3, 0.0], 
    [66.6, 45.6, 0.0]
]

verts_floor_2: list[pointR3] = [
    [12.0, 45.6, RC_HEIGHT], 
    [12.0, 40.1, RC_HEIGHT], 
    [22.5, 40.1, RC_HEIGHT], 
    [22.5, 36.3, RC_HEIGHT], 
    [52.7, 36.3, RC_HEIGHT], 
    [52.7, 37.3, RC_HEIGHT], 
    [66.6, 37.3, RC_HEIGHT], 
    [66.6, 45.6, RC_HEIGHT]
]

verts_ceiling: list[pointR3] = [
    [12.0, 45.6, CLG_HEIGHT], 
    [12.0, 40.1, CLG_HEIGHT], 
    [22.5, 40.1, CLG_HEIGHT], 
    [22.5, 36.3, CLG_HEIGHT], 
    [52.7, 36.3, CLG_HEIGHT], 
    [52.7, 37.3, CLG_HEIGHT], 
    [66.6, 37.3, CLG_HEIGHT], 
    [66.6, 45.6, CLG_HEIGHT]
]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

floor_anchor_coords: List[pointR3] = [
    [, , ],  
]

mezz_anchor_coords: List[pointR3] = [
    [ , , RC_HEIGHT + ]
]

anchor_array = np.array(anchor_coords)

ax.scatter(*anchor_array.T, label='UWB Anchors')

ax.add_collection3d(
    Poly3DCollection(
        [verts_floor_1], 
        facecolors='salmon', 
        linewidths=1,
        edgecolors='salmon', 
        alpha=0.5)
    )

ax.add_collection3d(
    Poly3DCollection(
        [verts_floor_2], 
        facecolors='lightblue', 
        linewidths=1,
        edgecolors='lightblue', 
        alpha=0.5)
    )

ax.add_collection3d(
    Poly3DCollection(
        [verts_ceiling], 
        facecolors='grey', 
        linewidths=1,
        edgecolors='grey', 
        alpha=0.5)
    )

# Normalize axes so the shape is not distorted
all_verts = np.array(verts_floor_1 + verts_floor_2 + verts_ceiling)
x = all_verts[:, 0]
y = all_verts[:, 1]
z = all_verts[:, 2]

max_range = np.array([
    x.max() - x.min(),
    y.max() - y.min(),
    z.max() - z.min()
]).max() / 2.0
mid_x = (x.max() + x.min()) * 0.5
mid_y = (y.max() + y.min()) * 0.5
mid_z = (z.max() + z.min()) * 0.5

ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
ax.set_zlim(0, mid_z * 2)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
plt.legend()
plt.show()

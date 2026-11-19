# make_hand.py - builds the VR hologram hand for the Galaxy Angel II port.
#
# An original, procedurally generated right hand (no outside assets): the
# shape is a signed distance field of rounded cones and boxes laid over a
# hand skeleton, meshed with surface nets, decimated in Blender, then posed
# by rotating each finger joint.  The same script writes the C++ header the
# game compiles in, a .blend with the armature, and preview renders.
#
# Run (Blender 4.2+ / 5.x, no add-ons, no downloads):
#
#   blender -b --factory-startup -P tools/vr_hand/make_hand.py
#   blender -b --factory-startup -P tools/vr_hand/make_hand.py -- \
#       --header OUT.h --renders OUT_DIR [--no-render] [--quick] [--tris 5600]
#
# Mobile (low-poly) variant, same format in its own namespace:
#
#   blender -b --factory-startup -P tools/vr_hand/make_hand.py -- --tris 1800 \
#       --namespace ga2_vr_hand_mesh_mobile --header .../ga2_vr_hand_mesh_mobile.h \
#       --renders .../hand-model/mobile
#
# Defaults: the header goes to
#   <private>/worktrees/ga2-runtime/ps2xRuntime/src/lib/ga2_vr_hand_mesh.h
# and the renders and hand.blend to <private>/research/vr/hand-model/, where
# <private> is $GA2_PRIVATE_ROOT or galaxy-angel-ii-private beside the folder
# holding this checkout (same rule as tools/private_root.sh).
#
# Frame (OpenXR, metres): x right, y up, -z forward.  RIGHT hand, handshake
# grip: palm faces -x, back of the hand +x, thumb side +y, fingers toward -z.
# In the pointing pose the index fingertip is at the origin and the index
# finger runs along -z.  The game mirrors x for the left hand.

import bpy
import bmesh
import sys
import os
import math
import argparse
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

# --------------------------------------------------------------------------
# small maths
# --------------------------------------------------------------------------

X_AXIS = np.array([1.0, 0.0, 0.0])


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rod(axis, ang):
    """Rotation matrix about a unit axis."""
    a = unit(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def rot_x(ang):
    return rod(X_AXIS, ang)


def rotvec(R):
    """Axis and angle of a rotation matrix."""
    ang = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) * 0.5)))
    if ang < 1e-9:
        return X_AXIS.copy(), 0.0
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return unit(ax), ang


def rotate_points(P, centre, axis, ang):
    """Rotate each point about (centre, axis) by its own angle."""
    v = P - centre
    c = np.cos(ang)[:, None]
    s = np.sin(ang)[:, None]
    return centre + v * c + np.cross(axis, v) * s + axis * (v @ axis)[:, None] * (1 - c)


def smoothstep(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------
# the hand: skeleton and proportions (adult, metres)
# --------------------------------------------------------------------------

# Knuckle (MCP) centres, phalanx lengths to the skin tip, radii at
# knuckle / middle joint / end joint / tip, bind splay (degrees toward the
# thumb side) and the tilt of the curl axis (so a fist converges).
FINGERS = [
    dict(name='index',  mcp=(0.0000,  0.0000, 0.0900), L=(0.044, 0.025, 0.021),
         R=(0.0092, 0.0081, 0.0071, 0.0063), splay=14.0, tilt=-0.05,
         meta=(0.0010, -0.0100, 0.1650), rmeta=(0.0108, 0.0100)),
    dict(name='middle', mcp=(0.0025, -0.0215, 0.0870), L=(0.048, 0.028, 0.022),
         R=(0.0094, 0.0083, 0.0073, 0.0064), splay=3.0, tilt=0.0,
         meta=(0.0015, -0.0240, 0.1680), rmeta=(0.0110, 0.0102)),
    dict(name='ring',   mcp=(0.0010, -0.0425, 0.0910), L=(0.044, 0.026, 0.021),
         R=(0.0089, 0.0078, 0.0069, 0.0061), splay=-8.0, tilt=0.05,
         meta=(0.0005, -0.0375, 0.1680), rmeta=(0.0105, 0.0097)),
    dict(name='little', mcp=(-0.0030, -0.0625, 0.1000), L=(0.034, 0.019, 0.020),
         R=(0.0080, 0.0070, 0.0062, 0.0055), splay=-20.0, tilt=0.11,
         meta=(-0.0020, -0.0490, 0.1650), rmeta=(0.0098, 0.0088)),
]
# Blend zones along each finger (metres either side of the joint), on the
# back of the finger and on the inside of the curl (wider, so the inside of
# a bent joint compresses instead of folding through itself).
FINGER_ZONES = ((0.011, 0.007, 0.005), (0.014, 0.012, 0.008))

THUMB = dict(
    cmc=(-0.0100, -0.0040, 0.1580), L=(0.046, 0.033, 0.027),
    R=(0.0140, 0.0104, 0.0090, 0.0076),
    rest_dir=(-0.35, 0.55, -0.75), rest_pad=(-0.70, -0.70, 0.0),
)
THUMB_CENTRES = (0.014, 0.046, 0.079)
THUMB_ZONES = ((0.020, 0.008, 0.006), (0.020, 0.012, 0.009))

WRIST = np.array([0.0, -0.0290, 0.1760])
# start, end, radius at start, radius at end, thickness / width[, end cap length / radius]
PALM_SLAB = ((-0.0005, -0.0300, 0.1150), (-0.0005, -0.0290, 0.1520), 0.0300, 0.0235, 0.42)
WRIST_STUB = ((0.0, -0.0290, 0.1580), (0.0, -0.0290, 0.2100), 0.0235, 0.0215, 0.70)
LOW_RELAX = 2          # smoothing rounds on the final triangles
Z_CUT = 0.190          # the hand is cut off flat here, at the wrist
CUT_ROUND = 0.0015     # radius of the rim of the cut

# Soft shaping of the digits (all subtle: a young, slender, lightly defined
# hand).  swell: extra radius at the two finger joints; the last `taper`
# metres close in a dome whose bluntness is `tip` (2 = ellipse); nail: the back of the fingertip is
# flattened to this fraction (a hint of a nail bed); pad: the inside of the
# fingertip is this much fuller.
FINGER_SHAPE = dict(swell=0.00030, sigma=0.0045, tip=2.3, taper=0.0105, nail=0.86, pad=1.06, wide=1.0)
THUMB_SHAPE = dict(swell=0.00020, sigma=0.0050, tip=2.3, taper=0.0120, nail=0.92, pad=1.0, wide=1.0)

# Poses.  Fingers: (spread, knuckle, middle joint, end joint) in degrees.
# Thumb: metacarpal direction, then either joint angles with a pad
# direction, or a finger to rest the tip on (solved as a two-bone reach).
POSES = [
    dict(name='relaxed',
         fingers=[(3, 18, 28, 14), (0, 24, 34, 18), (-2, 30, 38, 20), (-6, 34, 40, 22)],
         thumb=dict(dir=(-0.38, 0.45, -0.81), pad=(-0.60, -0.75, 0.10), mcp=12, ip=14)),
    dict(name='point',
         fingers=[(0, 0, 0, 0), (0, 78, 100, 62), (0, 80, 100, 62), (-1, 82, 96, 54)],
         thumb=dict(dir=(-0.72, 0.22, -0.66), on=dict(finger=1, frac=0.5, off=(0, 0.004, 0)))),
    dict(name='fist',
         fingers=[(2, 82, 104, 66), (0, 86, 104, 66), (-1, 88, 104, 64), (-2, 86, 96, 50)],
         thumb=dict(dir=(-0.79, 0.30, -0.54), on=dict(finger=1, frac=0.45, off=(-0.001, 0.007, 0)))),
]
REST_POSE = dict(name='bind',
                 fingers=[(f['splay'], 0, 0, 0) for f in FINGERS],
                 thumb=dict(dir=THUMB['rest_dir'], pad=THUMB['rest_pad'], mcp=0, ip=0))
# Synthetic pose used only to prove the OpenXR skinning data.
CHECK_POSE = dict(name='check',
                  fingers=[(6, 50, 65, 35), (0, 10, 12, 8), (-3, 60, 70, 40), (-10, 20, 25, 15)],
                  thumb=dict(dir=(-0.50, 0.40, -0.76), pad=(-0.60, -0.75, 0.10), mcp=30, ip=40))

T_DIR0 = unit(THUMB['rest_dir'])
T_AXIS0 = unit(np.cross(T_DIR0, THUMB['rest_pad']))


def finger_lengths(F):
    return (F['L'][0], F['L'][1], F['L'][2] - F['R'][3])


def fk_finger(F, spec):
    spread, mcp, pip, dip = [math.radians(a) for a in spec]
    splay = math.radians(F['splay'])
    a = unit((F['tilt'], 1.0, 0.0))
    R1 = rod(a, mcp) @ rot_x(spread - splay)
    dir0 = rot_x(splay) @ np.array([0.0, 0.0, -1.0])
    Rs = [R1, rod(a, pip) @ R1, rod(a, pip + dip) @ R1]
    L = finger_lengths(F)
    J = [np.array(F['mcp'], float)]
    for k in range(3):
        J.append(J[-1] + L[k] * (Rs[k] @ dir0))
    return dict(J=np.array(J), dirs=[R @ dir0 for R in Rs], dors=[R @ X_AXIS for R in Rs],
                R1=R1, axis_rest=rot_x(splay - spread) @ a, ang=(pip, dip),
                rest_J0=np.array(F['mcp'], float), rest_dir=dir0, radii=F['R'])


def fk_thumb(spec, fingers):
    L = (THUMB['L'][0], THUMB['L'][1], THUMB['L'][2] - THUMB['R'][3])
    C = np.array(THUMB['cmc'], float)
    d1 = unit(spec['dir'])
    M = C + L[0] * d1
    if 'on' in spec:
        o = spec['on']
        f = fingers[o['finger']]
        pm = f['J'][1] + o['frac'] * (f['J'][2] - f['J'][1])
        rm = f['radii'][1] + o['frac'] * (f['radii'][2] - f['radii'][1])
        T = pm + f['dors'][1] * (rm + THUMB['R'][3]) + np.array(o['off'], float)
        v = T - M
        D = min(np.linalg.norm(v), (L[1] + L[2]) * 0.999)
        n = unit(np.cross(d1, v))
        beta = math.atan2(np.linalg.norm(np.cross(d1, v)), d1 @ v)
        g1 = math.acos((L[1] ** 2 + D * D - L[2] ** 2) / (2 * L[1] * D))
        g2 = math.acos((L[2] ** 2 + D * D - L[1] ** 2) / (2 * L[2] * D))
        mcp, ip = beta - g1, g1 + g2
    else:
        n = unit(np.cross(d1, spec['pad']))
        mcp, ip = math.radians(spec['mcp']), math.radians(spec['ip'])
    B = np.column_stack([d1, n, np.cross(d1, n)])
    B0 = np.column_stack([T_DIR0, T_AXIS0, np.cross(T_DIR0, T_AXIS0)])
    R1 = B @ B0.T
    Rs = [R1, rod(n, mcp) @ R1, rod(n, mcp + ip) @ R1]
    J = [C]
    for k in range(3):
        J.append(J[-1] + L[k] * (Rs[k] @ T_DIR0))
    dirs = [R @ T_DIR0 for R in Rs]
    return dict(J=np.array(J), dirs=dirs, dors=[np.cross(d, R @ T_AXIS0) for d, R in zip(dirs, Rs)],
                R1=R1, axis_rest=T_AXIS0, ang=(mcp, ip),
                rest_J0=C, rest_dir=T_DIR0, radii=THUMB['R'])


def fk_pose(pose):
    fingers = [fk_finger(F, s) for F, s in zip(FINGERS, pose['fingers'])]
    return dict(fingers=fingers, thumb=fk_thumb(pose['thumb'], fingers))


def digits(fk):
    return fk['fingers'] + [fk['thumb']]


# --------------------------------------------------------------------------
# signed distance field of the hand
# --------------------------------------------------------------------------

def sd_seg(P, a, b, ra, rb):
    a = np.asarray(a, float)
    ab = np.asarray(b, float) - a
    den = ab @ ab
    t = np.clip(((P - a) @ ab) / den, 0.0, 1.0) if den > 0 else np.zeros(len(P))
    return np.linalg.norm(P - a - t[:, None] * ab, axis=1) - (ra + t * (rb - ra))


def sd_rbox(P, c, h, r):
    q = np.abs(P - np.asarray(c, float)) - np.asarray(h, float)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - r


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def sd_chain(P, d, k=0.0025):
    J, R = d['J'], d['radii']
    out = sd_seg(P, J[0], J[1], R[0], R[1])
    out = smin(out, sd_seg(P, J[1], J[2], R[1], R[2]), k)
    return smin(out, sd_seg(P, J[2], J[3], R[2], R[3]), k)


def sd_flat(P, a, b, ra, rb, flat, cap=1.0):
    """A rounded cone along z squashed along x to `flat` times its width;
    the round end past b is shortened to `cap` times its radius."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    Q = P.copy()
    Q[:, 0] = a[0] + (P[:, 0] - a[0]) / flat
    Q[:, 2] = np.where(P[:, 2] > b[2], b[2] + (P[:, 2] - b[2]) / cap, P[:, 2])
    return sd_seg(Q, a, b, ra, rb) * min(flat, cap)


def sd_digit(P, d, shape):
    """A straight digit (the bind pose) as a body of revolution about its
    axis with a shaped radius: joints swell a little, the tip tapers to a
    small round end, the back of the tip is flattened and its pad is full."""
    J, R = d['J'], d['radii']
    axis, dor = d['dirs'][0], d['dors'][0]
    lat = np.cross(axis, dor)
    v = P - J[0]
    s, u, w = v @ axis, v @ dor, v @ lat
    st = np.linalg.norm(J - J[0], axis=1)          # stations of the joints
    s_dome = st[3] + R[3] - shape['taper']          # the skin tip stays at st[3] + R[3]
    sc = np.clip(s, 0.0, s_dome)
    r = np.interp(sc, st, R)
    for k in (1, 2):
        r = r + shape['swell'] * np.exp(-((sc - st[k]) / shape['sigma']) ** 2)
    # dorsal / palmar scale of the cross-section near the tip
    tipness = smoothstep(st[2] + 0.002, st[2] + 0.008, sc)
    side = smoothstep(-1.0, 1.0, u / np.maximum(np.sqrt(u * u + w * w), 1e-9))
    au = 1.0 + tipness * ((shape['pad'] - 1.0) + (shape['nail'] - shape['pad']) * side)
    aw = 1.0 + tipness * (shape['wide'] - 1.0)
    rho = np.sqrt((u / au) ** 2 + (w / aw) ** 2)
    # the end is a long rounded dome (a superellipsoid), the base a round cap
    p = shape['tip']
    dome = (((np.maximum(s - sc, 0.0) / shape['taper']) ** p + (rho / r) ** p) ** (1.0 / p) - 1.0) * r
    return np.where(s < 0.0, np.sqrt(s * s + rho * rho) - r, dome)


def sd_palm(P):
    """The rigid part: palm slab, metacarpals, knuckles, pads, wrist stub."""
    # a thin slab that narrows toward the wrist, under the metacarpals
    d = sd_flat(P, *PALM_SLAB)
    for F in FINGERS:
        m = np.array(F['mcp'], float)
        d = smin(d, sd_seg(P, F['meta'], m, F['rmeta'][0], F['rmeta'][1]), 0.012)
        k = m + np.array([0.0012, 0, 0.001])
        d = smin(d, sd_seg(P, k, k, F['rmeta'][1], F['rmeta'][1]), 0.006)
    # pad under the fingers, heel on the little-finger side
    d = smin(d, sd_seg(P, (-0.0040, -0.0040, 0.1010), (-0.0058, -0.0580, 0.1090), 0.0082, 0.0076), 0.010)
    d = smin(d, sd_seg(P, (-0.0050, -0.0460, 0.1560), (-0.0045, -0.0600, 0.1200), 0.0105, 0.0092), 0.012)
    # wrist: an oval stub, cut off flat in sd_hand
    d = smin(d, sd_flat(P, *WRIST_STUB), 0.016)
    return d


def sd_hand(P, fk):
    d = sd_palm(P)
    for f in fk['fingers']:
        d = smin(d, sd_digit(P, f, FINGER_SHAPE), 0.007)
    t = fk['thumb']
    thumb = sd_digit(P, t, THUMB_SHAPE)
    web = sd_seg(P, t['J'][0] + 0.80 * (t['J'][1] - t['J'][0]), (-0.0030, 0.0030, 0.1120), 0.0045, 0.0050)
    d = smin(d, smin(thumb, web, 0.010), 0.013)
    return -smin(-d, -(P[:, 2] - Z_CUT), 2 * CUT_ROUND)


def sd_grad(P, fk, e=0.0004):
    g = np.empty_like(P)
    for a in range(3):
        o = np.zeros(3)
        o[a] = e
        g[:, a] = (sd_hand(P + o, fk) - sd_hand(P - o, fk)) / (2 * e)
    return g


def project(P, fk, steps=3, limit=0.0015):
    """Move points onto the surface along the field gradient.  Only valid
    for the bind pose: sd_digit expects straight digits."""
    P = P.copy()
    for _ in range(steps):
        g = sd_grad(P, fk)
        step = sd_hand(P, fk)[:, None] * g / np.maximum((g * g).sum(axis=1), 1e-12)[:, None]
        n = np.linalg.norm(step, axis=1)
        step *= np.minimum(1.0, limit / np.maximum(n, 1e-12))[:, None]
        P -= step
    return P


# --------------------------------------------------------------------------
# meshing: surface nets on a regular grid, then relax and decimate
# --------------------------------------------------------------------------

def surface_nets(f, origin, h):
    shape = np.array(f.shape)
    inside = f < 0
    cshape = tuple(shape - 1)
    acc = np.zeros(cshape + (3,))
    cnt = np.zeros(cshape)
    edges = []
    for ax in range(3):
        a1, a2 = (ax + 1) % 3, (ax + 2) % 3
        lo = [slice(None)] * 3
        hi = [slice(None)] * 3
        lo[ax] = slice(0, -1)
        hi[ax] = slice(1, None)
        cross = inside[tuple(lo)] != inside[tuple(hi)]
        idx = np.argwhere(cross)
        f0 = f[tuple(lo)][cross]
        f1 = f[tuple(hi)][cross]
        pos = idx.astype(float)
        pos[:, ax] += f0 / (f0 - f1)
        for d1 in (0, 1):
            for d2 in (0, 1):
                c = idx.copy()
                c[:, a1] -= d1
                c[:, a2] -= d2
                np.add.at(acc, (c[:, 0], c[:, 1], c[:, 2]), pos)
                np.add.at(cnt, (c[:, 0], c[:, 1], c[:, 2]), 1)
        edges.append((ax, a1, a2, idx, f0 < 0))
    vid = -np.ones(cshape, dtype=np.int64)
    used = cnt > 0
    vid[used] = np.arange(used.sum())
    verts = origin + h * (acc[used] / cnt[used][:, None])
    quads = []
    for ax, a1, a2, idx, low_inside in edges:
        corners = []
        for d1, d2 in ((1, 1), (0, 1), (0, 0), (1, 0)):
            c = idx.copy()
            c[:, a1] -= d1
            c[:, a2] -= d2
            corners.append(vid[c[:, 0], c[:, 1], c[:, 2]])
        q = np.column_stack(corners)
        q[~low_inside] = q[~low_inside][:, ::-1]
        quads.append(q)
    return verts, np.vstack(quads)


def largest_component(verts, faces):
    lab = np.arange(len(verts))
    e = np.vstack([faces[:, [i, (i + 1) % faces.shape[1]]] for i in range(faces.shape[1])])
    while True:
        m = np.minimum(lab[e[:, 0]], lab[e[:, 1]])
        new = lab.copy()
        np.minimum.at(new, e[:, 0], m)
        np.minimum.at(new, e[:, 1], m)
        new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    ids, counts = np.unique(lab, return_counts=True)
    keep = lab == ids[np.argmax(counts)]
    remap = -np.ones(len(verts), dtype=np.int64)
    remap[keep] = np.arange(keep.sum())
    return verts[keep], remap[faces[keep[faces[:, 0]]]], len(ids)


def relax(verts, faces, fk, rounds=3):
    e = np.vstack([faces[:, [i, (i + 1) % faces.shape[1]]] for i in range(faces.shape[1])])
    for _ in range(rounds):
        s = np.zeros_like(verts)
        n = np.zeros(len(verts))
        np.add.at(s, e[:, 0], verts[e[:, 1]])
        np.add.at(s, e[:, 1], verts[e[:, 0]])
        np.add.at(n, e[:, 0], 1)
        np.add.at(n, e[:, 1], 1)
        verts = project(0.5 * verts + 0.5 * s / n[:, None], fk, steps=2)
    return verts


def build_rest_mesh(fk, h, target_tris):
    pts = np.vstack([d['J'] for d in digits(fk)] + [WRIST[None, :]])
    lo = pts.min(axis=0) - 0.028
    hi = pts.max(axis=0) + 0.028
    hi[2] = Z_CUT + 4 * h
    n = np.ceil((hi - lo) / h).astype(int) + 2
    # A ridge lying in a grid plane can give surface nets a pinched vertex;
    # nudge the grid until the surface is a clean closed one (V - F = 2).
    for nudge in (0.0, 0.31, 0.57, 0.83, 0.17, 0.71):
        o = lo - nudge * h
        gx, gy, gz = [o[a] + h * np.arange(n[a]) for a in range(3)]
        G = np.stack(np.meshgrid(gx, gy, gz, indexing='ij'), axis=-1).reshape(-1, 3)
        f = np.concatenate([sd_hand(G[i:i + 200000], fk) for i in range(0, len(G), 200000)]).reshape(n)
        verts, quads = surface_nets(f, o, h)
        verts, quads, parts = largest_component(verts, quads)
        if len(verts) - len(quads) == 2:
            break
    verts = relax(verts, quads, fk)
    print('surface nets: %d vertices, %d quads, %d component(s)' % (len(verts), len(quads), parts))

    me = bpy.data.meshes.new('hand_dense')
    me.from_pydata(verts.tolist(), [], quads.tolist())
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('hand_dense', me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new('decimate', 'DECIMATE')
    mod.ratio = target_tris / len(me.polygons)
    low = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bm = bmesh.new()
    bm.from_mesh(low)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bad_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.to_mesh(low)
    bm.free()
    V = np.empty(len(low.vertices) * 3)
    low.vertices.foreach_get('co', V)
    T = np.empty(len(low.polygons) * 3, dtype=np.int32)
    low.polygons.foreach_get('vertices', T)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(low)
    T = T.reshape(-1, 3).astype(np.int64)
    V = relax(project(V.reshape(-1, 3), fk, steps=2), T, fk, rounds=LOW_RELAX)
    return V, T, bad_edges


# --------------------------------------------------------------------------
# skinning
# --------------------------------------------------------------------------

def digit_weights(P, rest, zone_scale=1.0):
    """Per digit: how much a vertex belongs to it and to each of its bones."""
    ds = digits(rest)
    dist = np.column_stack([sd_chain(P, d) for d in ds])
    soft = np.exp(-(dist - dist.min(axis=1, keepdims=True)) / 0.0012)
    soft /= soft.sum(axis=1, keepdims=True)
    out = []
    for i, d in enumerate(ds):
        s = (P - d['rest_J0']) @ d['rest_dir']
        back = smoothstep(-0.006, 0.006, (P - d['rest_J0']) @ d['dors'][0])
        if i < 4:
            L = finger_lengths(FINGERS[i])
            centres, (wide_back, wide_in) = (0.0, L[0], L[0] + L[1]), FINGER_ZONES
            fall = 1 - smoothstep(0.004, 0.012, dist[:, i])
        else:
            centres, (wide_back, wide_in) = THUMB_CENTRES, THUMB_ZONES
            fall = 1 - smoothstep(0.004, 0.014, dist[:, i])
        t = []
        for c, wb, wi in zip(centres, wide_back, wide_in):
            b = (wi + back * (wb - wi)) * zone_scale
            t.append(smoothstep(0.0, 1.0, (s - c) / (2 * b) + 0.5))
        out.append(dict(a=soft[:, i] * fall, t=t))
    return out


def deform(P, W, rest, fk):
    """Pose the bind mesh: every joint turns each vertex by its own share of
    the joint angle about the joint, so knuckles stay round."""
    out = P.copy()
    for w, r, d in zip(W, digits(rest), digits(fk)):
        q = P
        q = rotate_points(q, r['J'][2], d['axis_rest'], w['t'][2] * d['ang'][1])
        q = rotate_points(q, r['J'][1], d['axis_rest'], w['t'][1] * d['ang'][0])
        ax, ang = rotvec(d['R1'])
        q = rotate_points(q, r['J'][0], ax, w['t'][0] * ang)
        out += w['a'][:, None] * (q - P)
    return out


def vertex_normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    n = np.zeros_like(V)
    for c in range(3):
        np.add.at(n, T[:, c], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-20)[:, None]


def folded(V, T, n=None):
    """Triangles facing against the smooth normal of one of their corners."""
    n = vertex_normals(V, T) if n is None else n
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    return (np.einsum('fcj,fj->fc', n[T], fn) < 0).any(axis=1)


def unfold(V, T, rounds=60):
    """Skin pinched in a crease can fold over; relax just those spots."""
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    V = V.copy()
    for _ in range(rounds):
        bad = folded(V, T)
        if not bad.any():
            break
        mark = np.zeros(len(V), bool)
        mark[T[bad].reshape(-1)] = True
        mark[e[mark[e[:, 0]], 1]] = True
        s = np.zeros_like(V)
        c = np.zeros(len(V))
        np.add.at(s, e[:, 0], V[e[:, 1]])
        np.add.at(c, e[:, 0], 1)
        V[mark] = 0.4 * V[mark] + 0.6 * (s[mark] / c[mark][:, None])
    return V


# --------------------------------------------------------------------------
# OpenXR hand skeleton (XR_EXT_hand_tracking joint order)
# --------------------------------------------------------------------------

XR_NAMES = ['PALM', 'WRIST',
            'THUMB_METACARPAL', 'THUMB_PROXIMAL', 'THUMB_DISTAL', 'THUMB_TIP']
for _f in ('INDEX', 'MIDDLE', 'RING', 'LITTLE'):
    XR_NAMES += [_f + s for s in ('_METACARPAL', '_PROXIMAL', '_INTERMEDIATE', '_DISTAL', '_TIP')]
# parent joint of each joint (-1: none), for the armature
XR_PARENT = [1, -1, 1, 2, 3, 4] + sum([[1, b, b + 1, b + 2, b + 3] for b in (6, 11, 16, 21)], [])


def xr_frame(pos, direction, dorsal):
    """Joint pose: -Z along the bone toward the tip, +Y out of the back of
    the hand / finger, X = Y x Z."""
    z = -unit(direction)
    y = unit(dorsal - (dorsal @ z) * z)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(y, z), y, z, pos
    return M


def xr_joints(fk):
    """The 26 joint poses and radii for a pose of the model."""
    J = [None] * 26
    R = [0.0] * 26
    mm = np.array(FINGERS[1]['meta'], float)
    mk = fk['fingers'][1]['J'][0]
    J[0] = xr_frame(0.5 * (mm + mk), mk - mm, X_AXIS)
    R[0] = 0.011
    J[1] = xr_frame(WRIST, mm - WRIST, X_AXIS)
    R[1] = 0.018
    t = fk['thumb']
    for k in range(3):
        J[2 + k] = xr_frame(t['J'][k], t['dirs'][k], t['dors'][k])
        R[2 + k] = t['radii'][k]
    J[5] = xr_frame(t['J'][3] + t['radii'][3] * t['dirs'][2], t['dirs'][2], t['dors'][2])
    R[5] = t['radii'][3]
    for i, (F, f) in enumerate(zip(FINGERS, fk['fingers'])):
        b = 6 + 5 * i
        J[b] = xr_frame(np.array(F['meta'], float), f['J'][0] - np.array(F['meta'], float), X_AXIS)
        R[b] = F['rmeta'][0]
        for k in range(3):
            J[b + 1 + k] = xr_frame(f['J'][k], f['dirs'][k], f['dors'][k])
            R[b + 1 + k] = f['radii'][k]
        J[b + 4] = xr_frame(f['J'][3] + f['radii'][3] * f['dirs'][2], f['dirs'][2], f['dors'][2])
        R[b + 4] = f['radii'][3]
    return np.array(J), np.array(R)


def xr_weights(P, rest):
    """Up to four joint influences per vertex (linear blend skinning)."""
    W = digit_weights(P, rest, zone_scale=0.8)
    full = np.zeros((len(P), 26))
    palm = np.ones(len(P))
    for i, w in enumerate(W):
        base = 2 if i == 4 else 7 + 5 * i
        t1, t2, t3 = w['t']
        full[:, base] += w['a'] * t1 * (1 - t2)
        full[:, base + 1] += w['a'] * t2 * (1 - t3)
        full[:, base + 2] += w['a'] * t3
        palm -= w['a'] * t1
    # the rigid part: wrist stub to WRIST, the rest to the nearest metacarpals
    wrist = smoothstep(0.150, 0.186, P[:, 2])
    md = np.column_stack([sd_seg(P, F['meta'], F['mcp'], 0.0, 0.0) for F in FINGERS])
    ms = np.exp(-(md - md.min(axis=1, keepdims=True)) / 0.004)
    ms /= ms.sum(axis=1, keepdims=True)
    full[:, 1] += palm * wrist
    for i in range(4):
        full[:, 6 + 5 * i] += palm * (1 - wrist) * ms[:, i]
    idx = np.argsort(-full, axis=1)[:, :4]
    w = np.take_along_axis(full, idx, axis=1)
    w[w < 0.004] = 0.0
    w /= w.sum(axis=1, keepdims=True)
    idx[w == 0] = 0
    return idx.astype(np.uint8), w


def xr_skin(V, bind, joints, idx, w):
    """The game's formula: sum w_i * (joint_i * inverse(bind_i)) * v."""
    M = np.einsum('jab,jbc->jac', joints, np.linalg.inv(bind))
    Vh = np.concatenate([V, np.ones((len(V), 1))], axis=1)
    out = np.zeros((len(V), 3))
    for k in range(4):
        out += w[:, k:k + 1] * np.einsum('vab,vb->va', M[idx[:, k]], Vh)[:, :3]
    return out


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def self_hits(V, T, label=None):
    tree = BVHTree.FromPolygons(V.tolist(), T.tolist(), epsilon=0.0)
    n = 0
    seen = {}
    for a, b in tree.overlap(tree):
        if a < b and not set(T[a]) & set(T[b]):
            n += 1
            if label is not None:
                key = tuple(sorted((label[T[a][0]], label[T[b][0]])))
                seen[key] = seen.get(key, 0) + 1
    if label is not None and os.environ.get('HAND_DEBUG'):
        print('    hits by part:', sorted(seen.items(), key=lambda kv: -kv[1])[:12])
    return n


def clearance_report(fk):
    """Deepest overlaps between the finger capsules (and the palm)."""
    ds = digits(fk)
    names = [F['name'] for F in FINGERS] + ['thumb']
    worst = []
    for i, a in enumerate(ds):
        for k in range(3):
            u = np.linspace(0, 1, 9)[:, None]
            pts = a['J'][k] + u * (a['J'][k + 1] - a['J'][k])
            rad = a['radii'][k] + u[:, 0] * (a['radii'][k + 1] - a['radii'][k])
            if k > 0:
                g = (sd_palm(pts) - rad).min()
                if g < -0.0005:
                    worst.append((g, '%s[%d] in palm' % (names[i], k)))
            for j in range(i + 1, 5):
                b = ds[j]
                for m in range(3):
                    g = (sd_seg(pts, b['J'][m], b['J'][m + 1], b['radii'][m], b['radii'][m + 1]) - rad).min()
                    if g < -0.0005:
                        worst.append((g, '%s[%d] in %s[%d]' % (names[i], k, names[j], m)))
    return sorted(worst)


# --------------------------------------------------------------------------
# header
# --------------------------------------------------------------------------

def fmt(x):
    s = '%.5g' % (0.0 if abs(x) < 5e-7 else x)
    if '.' not in s and 'e' not in s:
        s += '.0'
    return s + 'f'


def rows(values, per, f):
    values = list(values)
    return ''.join('    ' + ', '.join(f(v) for v in values[i:i + per]) + ',\n'
                   for i in range(0, len(values), per))


def write_header(path, positions, normals, T, bind, radii, jidx, jw, namespace='ga2_vr_hand_mesh'):
    nv = positions[0].shape[0]
    o = []
    o.append('// Generated by tools/vr_hand/make_hand.py - do not edit, regenerate.\n'
             '// An original procedural hand (signed distance field over a hand skeleton).\n'
             '//\n'
             '// Right hand, metres, OpenXR axes (x right, y up, -z forward): palm faces -x,\n'
             '// thumb side +y, fingers toward -z.  In the pointing pose the index fingertip\n'
             '// is at the origin and the index finger runs along -z.  Mirror x (and reverse\n'
             '// the winding) for the left hand.\n'
             '//\n'
             '// Fixed poses share vertex order: blend positions and normals per vertex.\n'
             '// Finger tracking: v\' = sum_i kJointWeight[i] * (tracked[kJointIndex[i]] *\n'
             '// inverse(kBindJoints[kJointIndex[i]])) * v, with v from pose 0 (the bind\n'
             '// pose); normals the same with the rotation part.  Joint order and axes are\n'
             '// those of XR_EXT_hand_tracking (-Z along the bone toward the tip, +Y out of\n'
             '// the back of the hand).\n'
             '#pragma once\n\n#include <cstdint>\n\nnamespace %s {\n\n' % namespace)
    o.append('constexpr int kVertices = %d;\nconstexpr int kIndices = %d;\nconstexpr int kPoses = 3;\n'
             % (nv, T.size))
    o.append('constexpr int kPoseRelaxed = 0;\nconstexpr int kPosePoint = 1;\nconstexpr int kPoseFist = 2;\n'
             'constexpr int kJoints = 26;\n\n')
    for name, data in (('kPositions', positions), ('kNormals', normals)):
        o.append('static const float %s[kPoses][kVertices * 3] = {\n' % name)
        for p in data:
            o.append('  {\n' + rows(p.reshape(-1), 12, fmt) + '  },\n')
        o.append('};\n\n')
    o.append('// Triangles, counter-clockwise seen from outside.\n'
             'static const uint16_t kIndexData[kIndices] = {\n' + rows(T.reshape(-1), 24, str) + '};\n\n')
    o.append('// Bind pose (pose 0) of the 26 XR_EXT_hand_tracking joints, 4x4 column-major.\n'
             'static const float kBindJoints[kJoints][16] = {\n')
    for name, M in zip(XR_NAMES, bind):
        o.append('    {' + ', '.join(fmt(v) for v in M.T.reshape(-1)) + '},  // %s\n' % name)
    o.append('};\n\nstatic const float kBindRadius[kJoints] = {\n' + rows(radii, 13, fmt) + '};\n\n')
    o.append('// Four joint influences per vertex; weights sum to 1 (unused slots are 0).\n'
             'static const uint8_t kJointIndex[kVertices * 4] = {\n' + rows(jidx.reshape(-1), 32, str) + '};\n\n')
    o.append('static const float kJointWeight[kVertices * 4] = {\n' + rows(jw.reshape(-1), 16, fmt) + '};\n\n')
    o.append('}  // namespace %s\n' % namespace)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write(''.join(o))


# --------------------------------------------------------------------------
# Blender scene: armature, renders
# --------------------------------------------------------------------------

def make_object(name, V, T):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], T.tolist())
    me.update()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def make_armature(ob, bind, jidx, jw):
    """A bone per OpenXR joint (head at the joint, tail at the next joint)."""
    arm = bpy.data.objects.new('hand_rig', bpy.data.armatures.new('hand_rig'))
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    child = {p: j for j, p in enumerate(XR_PARENT) if p >= 0 and j not in (0, 2, 6, 11, 16, 21)}
    bones = []
    for j, name in enumerate(XR_NAMES):
        b = arm.data.edit_bones.new(name)
        head = bind[j][:3, 3]
        tail = bind[child[j]][:3, 3] if j in child and j != 1 else head - 0.012 * bind[j][:3, 2]
        if j == 0:
            tail = head - 0.02 * bind[j][:3, 2]
        b.head, b.tail = head.tolist(), tail.tolist()
        b.align_roll(bind[j][:3, 1].tolist())
        bones.append(b)
    for j, p in enumerate(XR_PARENT):
        if p >= 0:
            bones[j].parent = bones[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    groups = [ob.vertex_groups.new(name=n) for n in XR_NAMES]
    for v in range(len(jidx)):
        for k in range(4):
            if jw[v, k] > 0:
                groups[int(jidx[v, k])].add([v], float(jw[v, k]), 'ADD')
    ob.modifiers.new('rig', 'ARMATURE').object = arm
    return arm


def look_at(ob, eye, target, up=(0.0, 1.0, 0.0)):
    eye = np.asarray(eye, float)
    f = unit(np.asarray(target, float) - eye)
    r = unit(np.cross(f, up))
    u = np.cross(r, f)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, u, -f, eye
    ob.matrix_world = Matrix(M.tolist())


def clay_material():
    m = bpy.data.materials.new('clay')
    if m.node_tree is None:
        m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.78, 0.80, 0.84, 1)
    b.inputs['Roughness'].default_value = 0.55
    return m


def hologram_material(name, colour):
    """Additive rim glow, like the game's fresnel shader."""
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.5
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 2.2
    mu = nt.nodes.new('ShaderNodeMath')
    mu.operation = 'MULTIPLY_ADD'
    mu.inputs[1].default_value = 1.8
    mu.inputs[2].default_value = 0.02
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = colour
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(lw.outputs['Facing'], pw.inputs[0])
    nt.links.new(pw.outputs[0], mu.inputs[0])
    nt.links.new(mu.outputs[0], em.inputs['Strength'])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs['Surface'])
    return m


VIEWS = [  # name, camera offset from the hand centre
    ('palm', (-0.40, 0.06, -0.02)),
    ('back', (0.40, 0.08, 0.02)),
    ('player', (0.13, 0.17, 0.34)),
    ('front', (-0.22, 0.14, -0.30)),
]
CENTRE = np.array([-0.012, -0.022, 0.095])


def setup_render(size, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.transparent_max_bounces = 32
    sc.cycles.max_bounces = 3
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.lens = 70
    cam.data.clip_start = 0.01
    sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.data.angle = 0.3
    sc.collection.objects.link(sun)
    world = bpy.data.worlds.new('w')
    if world.node_tree is None:
        world.use_nodes = True
    sc.world = world
    return cam, sun, world.node_tree.nodes['Background']


def render_view(cam, sun, offset, path):
    eye = CENTRE + np.asarray(offset, float)
    look_at(cam, eye, CENTRE)
    r = unit(np.cross(unit(CENTRE - eye), (0, 1, 0)))
    look_at(sun, eye + 0.3 * r + np.array([0, 0.35, 0]), CENTRE)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_pixels(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def save_sheet(grid, path):
    """grid: rows (top first) of equally sized images."""
    sheet = np.concatenate([np.concatenate(r, axis=1) for r in grid[::-1]], axis=0)
    h, w = sheet.shape[:2]
    img = bpy.data.images.new('sheet', w, h, alpha=True)
    img.pixels.foreach_set(sheet.reshape(-1))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def render_all(out_dir, T, shapes, quick):
    """shapes: list of (name, vertices, hologram colour)."""
    os.makedirs(out_dir, exist_ok=True)
    size = 400 if quick else 800
    cam, sun, bg = setup_render(size, 12 if quick else 40)
    ob = make_object('hand_render', shapes[0][1], T)
    blue = hologram_material('holo_blue', (0.10, 0.50, 1.0, 1))
    orange = hologram_material('holo_orange', (1.0, 0.42, 0.06, 1))
    styles = [('clay', clay_material(), (0.16, 0.17, 0.19, 1), 1.0)]
    if not quick:
        styles.append(('holo', None, (0.004, 0.005, 0.010, 1), 1.0))
    for style, mat, colour, strength in styles:
        bg.inputs['Color'].default_value = colour
        bg.inputs['Strength'].default_value = strength
        sun.hide_render = style != 'clay'
        grid = []
        for name, V, orange_glow in shapes:
            ob.data.vertices.foreach_set('co', V.reshape(-1))
            ob.data.update()
            ob.data.materials.clear()
            ob.data.materials.append(mat or (orange if orange_glow else blue))
            row = []
            for view, offset in VIEWS:
                path = os.path.join(out_dir, '%s_%s_%s.png' % (name, style, view))
                render_view(cam, sun, offset, path)
                row.append(load_pixels(path))
                if quick:
                    os.remove(path)
            grid.append(row)
        half = [[im[::2, ::2] for im in row] for row in grid] if not quick else grid
        save_sheet(half, os.path.join(out_dir, 'sheet_%s%s.png' % (style, '_quick' if quick else '')))
    bpy.data.objects.remove(ob)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    private = os.environ.get('GA2_PRIVATE_ROOT')
    if not private:
        beside = os.path.join(os.path.dirname(os.path.dirname(repo)), 'galaxy-angel-ii-private')
        private = beside if os.path.isdir(beside) else os.path.join(repo, 'private')
    ap = argparse.ArgumentParser()
    ap.add_argument('--header', default=os.path.join(
        private, 'worktrees', 'ga2-runtime', 'ps2xRuntime', 'src', 'lib', 'ga2_vr_hand_mesh.h'))
    ap.add_argument('--renders', default=os.path.join(private, 'research', 'vr', 'hand-model'))
    ap.add_argument('--tris', type=int, default=5600)
    ap.add_argument('--namespace', default='ga2_vr_hand_mesh')
    ap.add_argument('--cell', type=float, default=0.0016)
    ap.add_argument('--quick', action='store_true', help='small clay contact sheet only')
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--no-header', action='store_true')
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)

    rest = fk_pose(REST_POSE)
    V, T, bad_edges = build_rest_mesh(rest, args.cell, args.tris)
    W = digit_weights(V, rest)
    fks = [fk_pose(p) for p in POSES]
    positions = [unfold(deform(V, W, rest, fk), T) for fk in fks]
    # put the pointing index fingertip exactly at the origin
    index = W[0]['a'] * W[0]['t'][2] > 0.5
    tip = positions[1][index][np.argmin(positions[1][index][:, 2])]
    shift = np.array([0.0, 0.0, -tip[2]])
    positions = [p + shift for p in positions]
    normals = [vertex_normals(p, T) for p in positions]

    bind, radii = xr_joints(fks[0])
    bind[:, :3, 3] += shift
    jidx, jw = xr_weights(V, rest)

    names = ['palm'] + [F['name'] for F in FINGERS] + ['thumb']
    part = np.column_stack([w['a'] * w['t'][0] for w in W])
    seg = np.column_stack([1 + (w['t'][1] > 0.5) + (w['t'][2] > 0.5) for w in W])
    best = part.argmax(axis=1)
    label = ['palm' if part[v, best[v]] < 0.5 else '%s%d' % (names[best[v] + 1], seg[v, best[v]])
             for v in range(len(V))]
    print('mesh: %d vertices, %d triangles, %d open/non-manifold edges' % (len(V), len(T), bad_edges))
    ok = len(V) < 65536 and bad_edges == 0
    for p, n, pose, fk in zip(positions, normals, POSES, fks):
        vol = np.einsum('ij,ij->i', p[T[:, 0]], np.cross(p[T[:, 1]], p[T[:, 2]])).sum() / 6
        print('pose %-8s bbox min (%.4f %.4f %.4f) max (%.4f %.4f %.4f)  volume %.1f cm3  self-hits %d'
              % ((pose['name'],) + tuple(p.min(axis=0)) + tuple(p.max(axis=0)) + (vol * 1e6, self_hits(p, T, label))))
        ok = ok and vol > 0
        area = np.linalg.norm(np.cross(p[T[:, 1]] - p[T[:, 0]], p[T[:, 2]] - p[T[:, 0]]), axis=1)
        flipped = folded(p, T, n)
        print('    folded triangles %d (area %.2f%% of the surface), smallest triangle %.3f mm2'
              % (flipped.sum(), 100 * area[flipped].sum() / area.sum(), area.min() * 0.5e6))
        if os.environ.get('HAND_DEBUG'):
            from collections import Counter
            print('    folded by part:', Counter(label[v] for v in T[flipped][:, 0]).most_common(8))
        for g, what in clearance_report(fk):
            print('    overlap %.1f mm: %s' % (-g * 1000, what))
    print('pointing index tip vertex: (%.5f %.5f %.5f)' % tuple(tip + shift))
    palm = (np.abs(V[:, 1] + 0.03) < 0.02) & (np.abs(V[:, 2] - 0.135) < 0.02) & (V[:, 0] < -0.006)
    print('palm normal (pose 1): (%.3f %.3f %.3f)' % tuple(unit(normals[1][palm].sum(axis=0))))

    # prove the OpenXR skinning data with the game's formula
    lbs = []
    for pose in POSES + [CHECK_POSE]:
        fk = fk_pose(pose)
        joints, _ = xr_joints(fk)
        joints[:, :3, 3] += shift
        skinned = xr_skin(positions[0], bind, joints, jidx, jw)
        exact = unfold(deform(V, W, rest, fk), T) + shift
        err = np.linalg.norm(skinned - exact, axis=1)
        print('skinning to %-8s joints: max %.2f mm, mean %.2f mm from the modelled pose, self-hits %d'
              % (pose['name'], err.max() * 1000, err.mean() * 1000, self_hits(skinned, T)))
        lbs.append(('skin_' + pose['name'], skinned, pose['name'] == 'fist'))
    print('weights: min sum %.6f, max influences %d' % (jw.sum(axis=1).min(), (jw > 0).sum(axis=1).max()))

    if not args.no_header:
        write_header(args.header, [p.astype(np.float32) for p in positions], normals, T, bind, radii, jidx, jw,
                     args.namespace)
        print('wrote', args.header, '(%d bytes)' % os.path.getsize(args.header))

    if not args.no_render:
        shapes = [(p['name'], v, p['name'] == 'fist') for p, v in zip(POSES, positions)]
        render_all(args.renders, T, shapes + ([] if args.quick else [lbs[3], lbs[2]]), args.quick)
        if not args.quick:
            ob = make_object('hand', positions[0], T)
            make_armature(ob, bind, jidx, jw)
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.renders, 'hand.blend'))
        print('renders in', args.renders)
    if not ok:
        raise SystemExit('mesh check failed')


if __name__ == '__main__':
    main()

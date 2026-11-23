#pragma once

#include <cstdint>

// Where the 2D layer's items end up in a hor+ frame (ga2_features.cpp), for
// game hooks that must agree with what the player sees (the battle pointer).
// Positions are 2D layer x in the 640-wide frame; markerX returns x unchanged
// when no wide 3D frame is shown.
//
// The tactical map's unit icons are projected by the game with the widened
// camera, so their x is already where the unit is in the wide frame: items
// centred on a unit's icon (its ring, face, frame and star) are drawn where
// the game put them, never squeezed or moved to an edge.
namespace ga2_hud
{
    // An item centred at frame x with the given half width, as the game
    // places it, is drawn centred at the returned x: squeezed about the screen
    // centre, or toward the left or right edge for an item near it.
    float markerX(float x, float halfWidth);
    // The unit icons' centres (frame x, y) of the tactical map, published by
    // the battle pointer on each map update; items centred on one stay put.
    void setUnitIcons(const float *xy, int count);
    // A 2D layer item (by its pointer) that always squeezes about the screen
    // centre, wherever it is put (the tactical map's cursor ring, which follows
    // the mouse; the edge rules would move it away from the pointer).
    void keepCentred(uint32_t item);

    // The HUD as separate pieces (for the VR battle table, which shows the map itself and the HUD around it): while
    // capturing, every 2D layer item drawn with a rectangle (not the unit icons, the cursor ring, markers or
    // screen-wide backdrops) is collected per frame, and overlapping or touching ones are merged into areas, in the
    // 2D layer's 640 x 480 space as the player sees them (hor+ placement applied).
    struct Area
    {
        float x0, y0, x1, y1;
        int side; // -1 left, 0 centre, 1 right
    };
    constexpr int kMaxAreas = 8;
    void captureAreas(bool on);
    // The last whole frame's areas; returns their count.
    int areas(Area *out, int max);
    // The last whole frame's items themselves (before merging; an area's panel shows only what lies inside them, not
    // the map's own 2D markers that happen to fall inside the area's box).
    int items(Area *out, int max);
}

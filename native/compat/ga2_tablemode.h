// Whether the VR battle table is showing the tactical map: ga2_battlepointer notes each frame it lays the map out on
// the table; ga2_battledraw then leaves the map's 3D to the table (ga2_vr draws the stage's map model itself).
#pragma once

#include "runtime/ga2_activity.h"

#include <atomic>
#include <cstdint>

namespace ga2_tablemode
{
    inline std::atomic<int64_t> g_lastNanos{0};

    inline void note() { g_lastNanos.store(ga2_activity::nowNanos(), std::memory_order_relaxed); }
    // The table showed the map within the last 0.25 s.
    inline bool active()
    {
        const int64_t last = g_lastNanos.load(std::memory_order_relaxed);
        return last != 0 && ga2_activity::nowNanos() - last < 250000000;
    }

    // The battle's live units (ga2_battlepointer installs it for its disc): up to `max` of them, each its unit type
    // (the stage section ID) and position (game units); returns how many. Used to identify the stage being played.
    inline int (*collectUnits)(const uint8_t *ram, int *ids, float *x, float *z, int max) = nullptr;
}

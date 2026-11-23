// The battle's 3D drawing.
//
// On by default: while the VR battle table shows the tactical map (ga2_tablemode), the game's mesh draws of the map
// (its map model's grid and obstacle solids, the backdrop: Eigou 1 0x265e98 and its twin on each disc) are skipped;
// ga2_vr draws the stage's map model on the table itself and the stage's sky around it. The draw only builds packets
// for VU1 (about half of a battle's game thread). GA2_NATIVE_MAP=0 keeps the game drawing them.
//
// Research switches (off by default):
//
//   GA2_RENDER_TRACE=<game seconds>[,...]: at the first RenderMgr::Render after each time, logs every model draw of that
//     frame in order: AxlClumpRender (a model), AxlAtomicRender (a mesh of it), the matrix sets (0 view, 1 world, 2/3
//     lights) and camera applies, each with its arguments and the caller ("[drawtrace]" lines), and the battle's view mode.
//     This is the frame trace the plan's step 0b asks for: which render items draw what on the tactical map.
//   GA2_SKIP3D=clump|atomic: while a battle shows its tactical map (view mode 0), the game's model draws are skipped
//     (clump: whole models, before their traversal; atomic: each mesh, after the traversal). A measurement switch for
//     the game-thread time the 3D map costs ("[skip3d]" counts per 5 s); the picture loses the map's 3D (the grid, ships,
//     sky) by design. Not a proven change: what the game could observe is not checked here.
//   GA2_MESH_TALLY=1: the mesh draws of the tactical map (Eigou 1 0x265e98: a0 a draw object, +0x1c its geometry,
//     +0x10 its frame) counted per geometry every 5 s, each new geometry's first words logged once ("[meshtally]").
//   GA2_SKIP_FUNCS=<hex>,<hex>,...: the same for any game functions (up to 8; returning 0 at once while the tactical map
//     shows). The battle draws its 3D outside RenderMgr: on Eigou 1 through 0x265e98 (mesh draw with a world matrix),
//     0x17bfc0, 0x1a3560 and 0x198c20 (the callers of the world-matrix sets in the map). Measurement only.
//
// Addresses: docs/vr/stereo.md section 6 (RenderMgr::Render, AxlClumpRender / AxlAtomicRender, matrix set, CCamera::Apply)
// and the battle manager / view mode fields of ga2_battlepointer.cpp.
#include "game_overrides.h"
#include "ps2_runtime.h"
#include "ps2_runtime_macros.h"
#include "runtime/ga2_activity.h"
#include "ga2_tablemode.h"
#include "runtime/ga2_framepace.h"
#include "runtime/ga2_native3d.h"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace
{
    struct Disc
    {
        const char *disc;
        uint32_t renderMgr, clumpRender, atomicRender, matSet, cameraApply;
        uint32_t mgrGlobal, requestedMode; // the battle manager pointer; its requested view mode (current = field - 4)
        uint32_t dmaSend;                  // the DMA kick (a store to D1_CHCR runs the VIF1 chain and VU1); 0: unknown
        uint32_t renderFlip;               // the whole frame's render (RenderFlip); 0: unknown (the trace spans RenderMgr)
        uint32_t meshDraw;                 // a mesh draw with its world matrix (a0 draw object: +0x1c geometry, +0x10 frame)
    };
    constexpr Disc kDiscs[] = {
        {"zettai", 0x117be0u, 0x239450u, 0x239e50u, 0x22fc88u, 0x118d98u, 0x2cca6cu, 0x44cu, 0u, 0x112dc0u, 0x23f658u},
        {"mugen-1", 0x117cb8u, 0x252ed0u, 0x2538d0u, 0x2496e0u, 0x118ef0u, 0x2e8fbcu, 0x454u, 0u, 0u, 0x259198u},
        {"mugen-2", 0x117c60u, 0x23af00u, 0x23b900u, 0x231738u, 0x118e18u, 0x2ce58cu, 0x44cu, 0u, 0u, 0x241108u},
        {"eigou-1", 0x117cb8u, 0x25fbd0u, 0x2605d0u, 0x2563e0u, 0x118ef0u, 0x2f7070u, 0x4f4u, 0x26f8c0u, 0x112e50u, 0x265e98u},
        {"eigou-2", 0x117cb8u, 0x253f40u, 0x254940u, 0x24a750u, 0x118ef0u, 0x2ea06cu, 0x454u, 0u, 0u, 0x25a208u},
    };

    enum Hook
    {
        RenderMgr,
        Clump,
        Atomic,
        MatSet,
        CameraApply,
        DmaSend,
        RenderFlip,
    };
    template <size_t I, int H>
    PS2Runtime::RecompiledFunction g_original = nullptr;

    uint32_t word(const uint8_t *ram, uint32_t a)
    {
        uint32_t v = 0;
        std::memcpy(&v, ram + (a & 0x1FFFFFFu), sizeof(v));
        return v;
    }
    float flt(const uint8_t *ram, uint32_t a)
    {
        float v = 0;
        std::memcpy(&v, ram + (a & 0x1FFFFFFu), sizeof(v));
        return v;
    }

    // -1: not in a battle; else the battle manager's current view mode (0 the tactical map).
    template <size_t I>
    int viewMode(const uint8_t *ram)
    {
        const uint32_t mgr = word(ram, kDiscs[I].mgrGlobal);
        if (mgr < 0x100000u || mgr >= 0x2000000u)
            return -1;
        return int(word(ram, mgr + kDiscs[I].requestedMode - 4u));
    }

    // ---- trace ----
    std::vector<double> g_traceAt;
    size_t g_traceNext = 0;
    bool g_tracing = false;
    int g_depth = 0;
    uint32_t g_counts[7] = {};

    const char *indent()
    {
        static const char spaces[] = "                ";
        return spaces + (16 - std::min(16, g_depth * 2));
    }

    // ---- skip ----
    int g_skip = 0; // 0 off, 1 clump, 2 atomic
    std::atomic<uint32_t> g_skipped{0}, g_drawn{0};
    std::chrono::steady_clock::time_point g_skipLog = std::chrono::steady_clock::now();
    std::chrono::steady_clock::time_point g_matLog = std::chrono::steady_clock::now();

    void skipLog()
    {
        const auto now = std::chrono::steady_clock::now();
        if (now - g_skipLog < std::chrono::seconds(5))
            return;
        g_skipLog = now;
        std::fprintf(stderr, "[skip3d] t=%.1f per 5 s: %u model draws skipped, %u drawn\n", ga2_activity::gameSeconds(),
                     g_skipped.exchange(0), g_drawn.exchange(0));
    }

    bool g_flipHooked = false;

    template <size_t I, int H>
    void frame(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (H == RenderMgr && g_flipHooked)
        {
            if (g_tracing)
                std::fprintf(stderr, "[drawtrace] %sRenderMgr(a0=%06x) from %06x\n", indent(), GPR_U32(ctx, 4), GPR_U32(ctx, 31));
            ++g_depth;
            g_original<I, RenderMgr>(ram, ctx, runtime);
            --g_depth;
            return;
        }
        const bool start = !g_tracing && g_traceNext < g_traceAt.size() && ga2_activity::gameSeconds() >= g_traceAt[g_traceNext];
        if (start)
        {
            ++g_traceNext;
            g_tracing = true;
            g_depth = 0;
            std::memset(g_counts, 0, sizeof(g_counts));
            std::fprintf(stderr, "[drawtrace] begin t=%.2f view mode %d, %s(a0=%06x) from %06x\n", ga2_activity::gameSeconds(),
                         viewMode<I>(ram), H == RenderFlip ? "RenderFlip" : "RenderMgr", GPR_U32(ctx, 4), GPR_U32(ctx, 31));
        }
        g_original<I, H>(ram, ctx, runtime);
        if (start)
        {
            g_tracing = false;
            std::fprintf(stderr, "[drawtrace] end: %u clumps, %u atomics, %u matrix sets, %u camera applies, %u dma sends\n",
                         g_counts[Clump], g_counts[Atomic], g_counts[MatSet], g_counts[CameraApply], g_counts[DmaSend]);
        }
    }

    template <size_t I>
    void clump(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_skip)
            skipLog();
        if (g_skip == 1 && viewMode<I>(ram) == 0)
        {
            g_skipped.fetch_add(1, std::memory_order_relaxed);
            SET_GPR_U32(ctx, 2, 0u);
            ctx->pc = GPR_U32(ctx, 31);
            return;
        }
        if (g_skip)
            g_drawn.fetch_add(1, std::memory_order_relaxed);
        if (g_tracing)
        {
            ++g_counts[Clump];
            const uint32_t c = GPR_U32(ctx, 4);
            std::fprintf(stderr, "[drawtrace] %sclump %06x (words %08x %08x %08x %08x) a1=%08x from %06x\n", indent(), c, word(ram, c),
                         word(ram, c + 4), word(ram, c + 8), word(ram, c + 12), GPR_U32(ctx, 5), GPR_U32(ctx, 31));
            ++g_depth;
        }
        g_original<I, Clump>(ram, ctx, runtime);
        if (g_tracing)
            --g_depth;
    }

    template <size_t I>
    void atomic(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_skip == 2 && viewMode<I>(ram) == 0)
        {
            g_skipped.fetch_add(1, std::memory_order_relaxed);
            SET_GPR_U32(ctx, 2, 0u);
            ctx->pc = GPR_U32(ctx, 31);
            return;
        }
        if (g_skip == 2)
        {
            g_drawn.fetch_add(1, std::memory_order_relaxed);
            skipLog();
        }
        if (g_tracing)
        {
            ++g_counts[Atomic];
            const uint32_t a = GPR_U32(ctx, 4);
            std::fprintf(stderr, "[drawtrace] %satomic %06x (words %08x %08x %08x %08x %08x %08x) a1=%08x from %06x\n", indent(), a,
                         word(ram, a), word(ram, a + 4), word(ram, a + 8), word(ram, a + 12), word(ram, a + 16), word(ram, a + 20),
                         GPR_U32(ctx, 5), GPR_U32(ctx, 31));
        }
        g_original<I, Atomic>(ram, ctx, runtime);
    }

    std::map<uint32_t, uint32_t> g_matCallers; // world-matrix sets per caller in the map (logged with the DMA tally)

    template <size_t I>
    void matSet(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (GPR_U32(ctx, 4) == 1u && viewMode<I>(ram) == 0)
        {
            ++g_matCallers[GPR_U32(ctx, 31)];
            const auto now = std::chrono::steady_clock::now();
            if (now - g_matLog >= std::chrono::seconds(5))
            {
                g_matLog = now;
                std::string line;
                char item[32];
                for (const auto &[from, n] : g_matCallers)
                {
                    std::snprintf(item, sizeof(item), " %06x:%u", from, n);
                    line += item;
                }
                std::fprintf(stderr, "[drawtrace] t=%.1f world matrix sets per caller in 5 s (map):%s\n",
                             ga2_activity::gameSeconds(), line.c_str());
                g_matCallers.clear();
            }
        }
        if (g_tracing)
        {
            ++g_counts[MatSet];
            const uint32_t m = GPR_U32(ctx, 5);
            std::fprintf(stderr, "[drawtrace] %smatset %u m=%06x [%.3g %.3g %.3g %.3g | t %.4g %.4g %.4g] from %06x\n", indent(),
                         GPR_U32(ctx, 4), m, flt(ram, m), flt(ram, m + 4), flt(ram, m + 8), flt(ram, m + 12), flt(ram, m + 48),
                         flt(ram, m + 52), flt(ram, m + 56), GPR_U32(ctx, 31));
        }
        g_original<I, MatSet>(ram, ctx, runtime);
    }

    template <size_t I>
    void cameraApply(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_tracing)
        {
            ++g_counts[CameraApply];
            std::fprintf(stderr, "[drawtrace] %scamera apply %06x from %06x\n", indent(), GPR_U32(ctx, 4), GPR_U32(ctx, 31));
        }
        g_original<I, CameraApply>(ram, ctx, runtime);
    }

    // DMA kicks per caller in the tactical map (view mode 0), logged every 5 s: where the battle's drawing comes from.
    std::map<uint32_t, uint32_t> g_dmaCallers;
    std::chrono::steady_clock::time_point g_dmaLog = std::chrono::steady_clock::now();

    template <size_t I>
    void dmaSend(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        const uint32_t ra = GPR_U32(ctx, 31);
        if (g_tracing)
        {
            ++g_counts[DmaSend];
            std::fprintf(stderr, "[drawtrace] %sdma send a0=%08x a1=%08x a2=%08x from %06x\n", indent(), GPR_U32(ctx, 4),
                         GPR_U32(ctx, 5), GPR_U32(ctx, 6), ra);
        }
        if (viewMode<I>(ram) == 0)
        {
            ++g_dmaCallers[ra];
            const auto now = std::chrono::steady_clock::now();
            if (now - g_dmaLog >= std::chrono::seconds(5))
            {
                g_dmaLog = now;
                std::string line;
                char item[32];
                for (const auto &[from, n] : g_dmaCallers)
                {
                    std::snprintf(item, sizeof(item), " %06x:%u", from, n);
                    line += item;
                }
                std::fprintf(stderr, "[drawtrace] t=%.1f dma sends per caller in 5 s (map):%s\n", ga2_activity::gameSeconds(),
                             line.c_str());
                g_dmaCallers.clear();
            }
        }
        g_original<I, DmaSend>(ram, ctx, runtime);
    }

    template <size_t I, int K>
    PS2Runtime::RecompiledFunction g_slotOriginal = nullptr;

    // ---- mesh tally ----
    std::map<uint32_t, uint32_t> g_meshCount;
    std::map<uint32_t, bool> g_meshSeen;
    std::chrono::steady_clock::time_point g_meshLog = std::chrono::steady_clock::now();

    bool g_meshTally = false, g_nativeMap = false;
    std::atomic<uint32_t> g_mapSkipped{0};

    // The last view matrix the game set (MatSet(0, cam+0x20)): the camera of the mesh draws that follow.
    uint32_t g_lastView = 0;

    template <size_t I>
    void viewSet(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (GPR_U32(ctx, 4) == 0u)
            g_lastView = GPR_U32(ctx, 5);
        g_slotOriginal<I, 98>(ram, ctx, runtime);
    }

    // The desktop renderer's capture: the map view's camera, for the GS frame the next flip shows.
    template <size_t I>
    void publishMapFrame(const uint8_t *ram)
    {
        if (!g_lastView)
            return;
        ga2_native3d::Frame f;
        f.flip = ga2_framepace::flips() + 1;
        f.scene = ga2_native3d::Scene::BattleMap;
        for (int k = 0; k < 16; ++k)
            f.camera.V[k] = flt(ram, g_lastView + 4u * uint32_t(k));
        const uint32_t cam = g_lastView - 0x20u; // CCamera: the view at +0x20, the projection constants at +0xb4..+0xc4
        f.camera.cx = flt(ram, cam + 0xb4), f.camera.cy = flt(ram, cam + 0xb8);
        f.camera.scrz = flt(ram, cam + 0xbc), f.camera.ax = flt(ram, cam + 0xc0), f.camera.ay = flt(ram, cam + 0xc4);
        if (ga2_tablemode::collectUnits)
            f.unitCount = ga2_tablemode::collectUnits(ram, f.unitIds, f.unitX, f.unitZ, ga2_native3d::Frame::kMaxUnits);
        ga2_native3d::publish(f);
    }
    uint64_t g_publishedFlip = ~0ull;

    template <size_t I>
    void meshDraw(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        // The VR table shows the map, or the desktop renderer draws it: the map's 3D (the map model's grid and solids,
        // the backdrop) is theirs to draw. The mesh draw only builds packets (it writes nothing back to the game's
        // objects): return as it would.
        const bool mapView = g_nativeMap && viewMode<I>(ram) == 0;
        const bool desktop = mapView && ga2_native3d::ready(ga2_native3d::Scene::BattleMap);
        // Published in every map-view frame (before the renderer is ready too: it identifies the stage from the units).
        if (mapView && !ga2_tablemode::active() && g_publishedFlip != ga2_framepace::flips())
        {
            g_publishedFlip = ga2_framepace::flips();
            publishMapFrame<I>(ram);
        }
        if (mapView && (desktop || ga2_tablemode::active()))
        {
            g_mapSkipped.fetch_add(1, std::memory_order_relaxed);
            SET_GPR_U32(ctx, 2, 1u);
            ctx->pc = GPR_U32(ctx, 31);
            return;
        }
        if (g_meshTally && viewMode<I>(ram) == 0)
        {
            const uint32_t obj = GPR_U32(ctx, 4), geo = word(ram, obj + 0x1c);
            ++g_meshCount[geo];
            if (!g_meshSeen[geo])
            {
                g_meshSeen[geo] = true;
                std::fprintf(stderr, "[meshtally] new geometry %06x (obj %06x from %06x): %08x %08x %08x %08x %08x %08x %08x %08x | %08x %08x %08x %08x\n",
                             geo, obj, GPR_U32(ctx, 31), word(ram, geo), word(ram, geo + 4), word(ram, geo + 8), word(ram, geo + 12),
                             word(ram, geo + 16), word(ram, geo + 20), word(ram, geo + 24), word(ram, geo + 28), word(ram, obj),
                             word(ram, obj + 4), word(ram, obj + 8), word(ram, obj + 0x14));
                // The world matrix the draw sets (MatSet(1, frame + 0x70)), rows: x, y, z axes and the translation.
                if (const uint32_t frame = word(ram, obj + 0x10); frame >= 0x100000u && frame < 0x2000000u)
                {
                    const uint32_t m = frame + 0x70;
                    std::fprintf(stderr, "[meshtally]   world [%.4g %.4g %.4g | %.4g %.4g %.4g | %.4g %.4g %.4g | t %.6g %.6g %.6g]\n",
                                 flt(ram, m), flt(ram, m + 4), flt(ram, m + 8), flt(ram, m + 16), flt(ram, m + 20), flt(ram, m + 24),
                                 flt(ram, m + 32), flt(ram, m + 36), flt(ram, m + 40), flt(ram, m + 48), flt(ram, m + 52), flt(ram, m + 56));
                }
            }
            const auto now = std::chrono::steady_clock::now();
            if (now - g_meshLog >= std::chrono::seconds(5))
            {
                g_meshLog = now;
                std::string line;
                char item[32];
                for (const auto &[g, n] : g_meshCount)
                {
                    std::snprintf(item, sizeof(item), " %06x:%u", g, n);
                    line += item;
                }
                std::fprintf(stderr, "[meshtally] t=%.1f draws per geometry in 5 s:%s\n", ga2_activity::gameSeconds(), line.c_str());
                g_meshCount.clear();
            }
        }
        g_slotOriginal<I, 99>(ram, ctx, runtime);
    }

    // ---- skipping listed functions ----
    constexpr int kSlots = 8;
    uint32_t g_skipAddress[kSlots] = {};
    std::atomic<uint32_t> g_slotSkipped[kSlots];


    template <size_t I, int K>
    void skipSlot(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (viewMode<I>(ram) == 0)
        {
            g_slotSkipped[K].fetch_add(1, std::memory_order_relaxed);
            const auto now = std::chrono::steady_clock::now();
            if (K == 0 && now - g_skipLog >= std::chrono::seconds(5))
            {
                g_skipLog = now;
                std::string line;
                char item[40];
                for (int k = 0; k < kSlots && g_skipAddress[k]; ++k)
                {
                    std::snprintf(item, sizeof(item), " %06x:%u", g_skipAddress[k], g_slotSkipped[k].exchange(0));
                    line += item;
                }
                std::fprintf(stderr, "[skip3d] t=%.1f skipped per 5 s:%s\n", ga2_activity::gameSeconds(), line.c_str());
            }
            SET_GPR_U32(ctx, 2, 0u);
            ctx->pc = GPR_U32(ctx, 31);
            return;
        }
        g_slotOriginal<I, K>(ram, ctx, runtime);
    }

    template <size_t I, int K>
    void bindSlot(PS2Runtime &runtime)
    {
        if constexpr (K < kSlots)
        {
            if (!g_skipAddress[K])
                return;
            g_slotOriginal<I, K> = runtime.lookupFunction(g_skipAddress[K]);
            runtime.replaceFunction(g_skipAddress[K], skipSlot<I, K>);
            bindSlot<I, K + 1>(runtime);
        }
    }

    template <size_t I>
    void bind(PS2Runtime &runtime)
    {
        const Disc &d = kDiscs[I];
        if (const char *v = std::getenv("GA2_RENDER_TRACE"); v && *v)
        {
            std::stringstream list(v);
            for (std::string item; std::getline(list, item, ',');)
                g_traceAt.push_back(std::atof(item.c_str()));
        }
        if (const char *v = std::getenv("GA2_SKIP3D"); v && *v)
            g_skip = std::strcmp(v, "clump") == 0 ? 1 : std::strcmp(v, "atomic") == 0 ? 2 : 0;
        if (const char *v = std::getenv("GA2_SKIP_FUNCS"); v && *v)
        {
            std::stringstream list(v);
            int k = 0;
            for (std::string item; std::getline(list, item, ',') && k < kSlots;)
            {
                const uint32_t a = uint32_t(std::strtoul(item.c_str(), nullptr, 16));
                if (a && runtime.hasFunction(a))
                    g_skipAddress[k++] = a;
                else
                    std::cerr << "[ga2 battledraw] GA2_SKIP_FUNCS: " << item << " is not a generated function; ignored\n";
            }
        }
        const char *tally = std::getenv("GA2_MESH_TALLY");
        const char *native = std::getenv("GA2_NATIVE_MAP");
        g_meshTally = tally && *tally == '1';
        g_nativeMap = !(native && *native == '0');
        const bool meshes = (g_meshTally || g_nativeMap) && kDiscs[I].meshDraw && runtime.hasFunction(kDiscs[I].meshDraw);
        const bool research = !g_traceAt.empty() || g_skip || g_skipAddress[0];
        if (!research && !meshes)
            return;
        auto hook = [&](uint32_t address, PS2Runtime::RecompiledFunction &original, PS2Runtime::RecompiledFunction replacement) {
            original = runtime.lookupFunction(address);
            runtime.replaceFunction(address, replacement);
        };
        if (meshes)
        {
            g_slotOriginal<I, 99> = runtime.lookupFunction(kDiscs[I].meshDraw);
            runtime.replaceFunction(kDiscs[I].meshDraw, meshDraw<I>);
            if (g_nativeMap && runtime.hasFunction(d.matSet))
            {
                g_slotOriginal<I, 98> = runtime.lookupFunction(d.matSet);
                runtime.replaceFunction(d.matSet, viewSet<I>);
            }
            std::cerr << "[ga2 battledraw] " << d.disc << ": the map's 3D goes to the VR table while it shows the map"
                      << (g_nativeMap ? "" : " (off: GA2_NATIVE_MAP=0)") << "\n";
        }
        if (!research)
            return;
        for (uint32_t address : {d.renderMgr, d.clumpRender, d.atomicRender, d.matSet, d.cameraApply})
            if (!runtime.hasFunction(address))
            {
                std::cerr << "[ga2 battledraw] " << d.disc << ": 0x" << std::hex << address << std::dec << " not in the generated table; off\n";
                return;
            }
        hook(d.renderMgr, g_original<I, RenderMgr>, frame<I, RenderMgr>);
        if (d.renderFlip && runtime.hasFunction(d.renderFlip))
        {
            hook(d.renderFlip, g_original<I, RenderFlip>, frame<I, RenderFlip>);
            g_flipHooked = true;
        }
        hook(d.clumpRender, g_original<I, Clump>, clump<I>);
        hook(d.atomicRender, g_original<I, Atomic>, atomic<I>);
        hook(d.matSet, g_original<I, MatSet>, matSet<I>);
        hook(d.cameraApply, g_original<I, CameraApply>, cameraApply<I>);
        if (d.dmaSend && runtime.hasFunction(d.dmaSend))
            hook(d.dmaSend, g_original<I, DmaSend>, dmaSend<I>);
        bindSlot<I, 0>(runtime);
        std::cerr << "[ga2 battledraw] " << d.disc << ": render trace / skip hooks bound (skip " << g_skip << ")\n";
    }
}

PS2_REGISTER_GAME_OVERRIDE("GA2 battle draw zettai", "SLPM_662.43", 0x00100008u, 0x5E58C415u, bind<0>)
PS2_REGISTER_GAME_OVERRIDE("GA2 battle draw mugen-1", "SLPM_667.79", 0x00100008u, 0x15F1CB0Du, bind<1>)
PS2_REGISTER_GAME_OVERRIDE("GA2 battle draw mugen-2", "SLPM_667.80", 0x00100008u, 0x1F83C20Cu, bind<2>)
PS2_REGISTER_GAME_OVERRIDE("GA2 battle draw eigou-1", "SLPM_551.18", 0x00100008u, 0x73DEC964u, bind<3>)
PS2_REGISTER_GAME_OVERRIDE("GA2 battle draw eigou-2", "SLPM_551.19", 0x00100008u, 0xAAAC1E15u, bind<4>)

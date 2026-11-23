// Native movies (runtime/ga2_movie.h): the games' low-level movie player ("mplayer", the wrapper around libmpeg in
// each disc's moviemngr code) is replaced while a movie plays natively. Everything above it stays the game's own:
// the movie manager (CMovieManager Open/Play/Update/IsPlaying/Stop), the story script's movie command (which sets the
// gallery's "seen" bit), CScene_Movie, the pause of the music streamer around a movie and the skip button.
// research/native-movies/report.txt section 3 has the layers and how the addresses were found (Zettai decompiled,
// Eigou 1 partly, the others by signature match).
//
//   manager Open    (mgr, path, w, h): wrapped, to note the path ("movie/8004.pss") and the volume (mgr+8, 0..0x3fff)
//   open by sector  (lsn, size, buf, 1) -> 1: the movie opens natively here (else the game's own open runs)
//   open by name    (path, buf, 1) -> 1: the same for a file the archive index does not hold
//   decode step     () -> 1 while playing natively (the guest decodes nothing)
//   draw            (buf): nothing (no guest picture upload)
//   finished test   () -> 0 while the native movie plays, 1 once its last picture has been shown
//   stream step     (): nothing (no CD stream to pump)
//   close           (): the native player stops (both the end and a skip come through CMovieManager::Stop)
#include "game_overrides.h"
#include "ps2_runtime.h"
#include "ps2_runtime_macros.h"
#include "runtime/ga2_movie.h"

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>

namespace
{
    struct Disc
    {
        const char *disc, *program;
        uint32_t managerOpen, openByName, openBySector, streamStep, decodeStep, draw, finished, close;
    };
    constexpr Disc kDiscs[] = {
        {"zettai", "SLPM_662.43", 0x119bf0, 0x243a48, 0x243ae8, 0x243cb8, 0x2440b8, 0x244160, 0x244830, 0x244588},
        {"mugen-1", "SLPM_667.79", 0x119d48, 0x25d648, 0x25d6e8, 0x25d8b8, 0x25dcb8, 0x25dd60, 0x25e430, 0x25e188},
        {"mugen-2", "SLPM_667.80", 0x119c70, 0x2454f8, 0x245598, 0x245768, 0x245b68, 0x245c10, 0x2462e0, 0x246038},
        {"eigou-1", "SLPM_551.18", 0x119d48, 0x26a350, 0x26a3f0, 0x26a5c0, 0x26a9c0, 0x26aa68, 0x26b138, 0x26ae90},
        {"eigou-2", "SLPM_551.19", 0x119d48, 0x25e6b8, 0x25e758, 0x25e928, 0x25ed28, 0x25edd0, 0x25f4a0, 0x25f1f8},
    };

    enum Slot
    {
        ManagerOpen,
        OpenByName,
        OpenBySector,
        StreamStep,
        DecodeStep,
        Draw,
        Finished,
        Close,
        SlotCount
    };
    template <size_t I, int S>
    PS2Runtime::RecompiledFunction g_original = nullptr;

    std::string g_path;            // the path the manager is opening
    float g_volume = 1.0f;
    std::atomic<bool> g_native{false}; // the open movie plays natively

    uint32_t word(const uint8_t *ram, uint32_t a)
    {
        uint32_t v = 0;
        std::memcpy(&v, ram + (a & 0x1FFFFFFu), sizeof(v));
        return v;
    }

    std::string cString(const uint8_t *ram, uint32_t a, size_t max = 256)
    {
        std::string s;
        for (size_t i = 0; i < max; ++i)
        {
            const char c = char(ram[(a + i) & 0x1FFFFFFu]);
            if (!c)
                break;
            s.push_back(c);
        }
        return s;
    }

    void returnWith(R5900Context *ctx, uint32_t value)
    {
        SET_GPR_U32(ctx, 2, value);
        ctx->pc = GPR_U32(ctx, 31);
    }

    template <size_t I>
    void managerOpen(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        const uint32_t mgr = GPR_U32(ctx, 4);
        g_path = cString(ram, GPR_U32(ctx, 5));
        g_volume = float(word(ram, mgr + 8) & 0x3FFFu) / float(0x3FFF);
        g_original<I, ManagerOpen>(ram, ctx, runtime);
    }

    template <size_t I>
    void openBySector(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (ga2_movie::open(kDiscs[I].program, g_path, GPR_U32(ctx, 4), GPR_U32(ctx, 5), g_volume))
        {
            g_native = true;
            returnWith(ctx, 1);
            return;
        }
        g_native = false;
        g_original<I, OpenBySector>(ram, ctx, runtime);
    }

    template <size_t I>
    void openByName(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        const std::string name = cString(ram, GPR_U32(ctx, 4));
        if (ga2_movie::open(kDiscs[I].program, name.empty() ? g_path : name, 0, 0, g_volume))
        {
            g_native = true;
            returnWith(ctx, 1);
            return;
        }
        g_native = false;
        g_original<I, OpenByName>(ram, ctx, runtime);
    }

    template <size_t I>
    void streamStep(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_native)
        {
            returnWith(ctx, 0);
            return;
        }
        g_original<I, StreamStep>(ram, ctx, runtime);
    }

    template <size_t I>
    void decodeStep(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_native)
        {
            returnWith(ctx, 1);
            return;
        }
        g_original<I, DecodeStep>(ram, ctx, runtime);
    }

    template <size_t I>
    void draw(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_native)
        {
            returnWith(ctx, 0);
            return;
        }
        g_original<I, Draw>(ram, ctx, runtime);
    }

    template <size_t I>
    void finished(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_native)
        {
            returnWith(ctx, ga2_movie::finished() ? 1u : 0u);
            return;
        }
        g_original<I, Finished>(ram, ctx, runtime);
    }

    template <size_t I>
    void close(uint8_t *ram, R5900Context *ctx, PS2Runtime *runtime)
    {
        if (g_native)
        {
            ga2_movie::close();
            g_native = false;
            returnWith(ctx, 0);
            return;
        }
        g_original<I, Close>(ram, ctx, runtime);
    }

    template <size_t I>
    void bind(PS2Runtime &runtime)
    {
        const Disc &d = kDiscs[I];
        const uint32_t addresses[SlotCount] = {d.managerOpen, d.openByName, d.openBySector, d.streamStep,
                                               d.decodeStep, d.draw, d.finished, d.close};
        for (uint32_t a : addresses)
            if (!runtime.hasFunction(a))
            {
                std::cerr << "[ga2 movie] " << d.disc << ": 0x" << std::hex << a << std::dec
                          << " is not a generated function; movies stay emulated\n";
                return;
            }
        auto hook = [&](uint32_t address, PS2Runtime::RecompiledFunction &original, PS2Runtime::RecompiledFunction replacement) {
            original = runtime.lookupFunction(address);
            runtime.replaceFunction(address, replacement);
        };
        hook(d.managerOpen, g_original<I, ManagerOpen>, managerOpen<I>);
        hook(d.openByName, g_original<I, OpenByName>, openByName<I>);
        hook(d.openBySector, g_original<I, OpenBySector>, openBySector<I>);
        hook(d.streamStep, g_original<I, StreamStep>, streamStep<I>);
        hook(d.decodeStep, g_original<I, DecodeStep>, decodeStep<I>);
        hook(d.draw, g_original<I, Draw>, draw<I>);
        hook(d.finished, g_original<I, Finished>, finished<I>);
        hook(d.close, g_original<I, Close>, close<I>);
        std::cerr << "[ga2 movie] " << d.disc << ": native movie hooks bound (" << (ga2_movie::enabled() ? "native" : "original")
                  << " playback)\n";
    }
}

PS2_REGISTER_GAME_OVERRIDE("GA2 movie zettai", "SLPM_662.43", 0x00100008u, 0x5E58C415u, bind<0>)
PS2_REGISTER_GAME_OVERRIDE("GA2 movie mugen-1", "SLPM_667.79", 0x00100008u, 0x15F1CB0Du, bind<1>)
PS2_REGISTER_GAME_OVERRIDE("GA2 movie mugen-2", "SLPM_667.80", 0x00100008u, 0x1F83C20Cu, bind<2>)
PS2_REGISTER_GAME_OVERRIDE("GA2 movie eigou-1", "SLPM_551.18", 0x00100008u, 0x73DEC964u, bind<3>)
PS2_REGISTER_GAME_OVERRIDE("GA2 movie eigou-2", "SLPM_551.19", 0x00100008u, 0xAAAC1E15u, bind<4>)

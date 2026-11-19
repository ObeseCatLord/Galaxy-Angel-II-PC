#include "settings.h"
#include "process.h"

#include <algorithm>
#include <cstdlib>
#include <fstream>

namespace ga2
{
    namespace
    {
        void setEnv(const char *name, const std::string &value) { setEnvironment(name, value); }

        // Command-line options: this run only (never saved).
        struct Override
        {
            bool set = false;
            int choice = 0, number = 0;
        };
        std::vector<Override> &overrides()
        {
            static std::vector<Override> list(options().size());
            return list;
        }
        int g_windowScaleOverride = 0;
        // settings.ini's format: 2 since 0.11.0 (Automatic resolution, borderless fullscreen and the screen's own shape are the defaults).
        constexpr int kSettingsVersion = 2;
    }

    void Settings::overrideForThisRun(size_t option, int choice, int number) { overrides()[option] = {true, choice, number}; }
    void Settings::overrideWindowScale(int scale) { g_windowScaleOverride = std::clamp(scale, 1, 8); }

    int Settings::effectiveChoice(size_t option) const
    {
        return overrides()[option].set ? overrides()[option].choice : m_choices[option];
    }

    void Settings::set(size_t option, int choice)
    {
        const int count = int(options()[option].choices.size());
        choice = std::clamp(choice, 0, count - 1);
        m_numbers[option] = ga2_options::carryNumber(options()[option], m_choices[option], choice, m_numbers[option]);
        m_choices[option] = choice;
    }

    void Settings::setNumber(size_t option, int number)
    {
        const Option &o = options()[option];
        if (!ga2_options::hasCustom(o)) return;
        m_numbers[option] = ga2_options::clampCustom(o, number);
        m_choices[option] = o.customChoice;
    }

    void Settings::step(size_t option, int delta)
    {
        const int count = int(options()[option].choices.size());
        set(option, (m_choices[option] + delta % count + count) % count);
    }

    std::string Settings::value(const char *key) const
    {
        const auto &table = options();
        for (size_t i = 0; i < table.size(); ++i)
            if (std::string(table[i].key) == key)
                return table[i].choices[size_t(effectiveChoice(i))].value;
        return {};
    }

    Settings Settings::load(const std::filesystem::path &file)
    {
        Settings settings;
        std::ifstream in(file);
        const auto &table = options();
        bool any = false, current = false;
        for (std::string line; std::getline(in, line);)
        {
            any = true;
            if (!line.empty() && line.back() == '\r') line.pop_back();
            const auto equals = line.find('=');
            if (equals == std::string::npos) continue;
            const std::string key = line.substr(0, equals), value = line.substr(equals + 1);
            if (key == "settings_version")
            {
                current = std::atoi(value.c_str()) >= kSettingsVersion;
                continue;
            }
            if (key == "last_game")
            {
                settings.lastGame = value;
                continue;
            }
            if (key == "window_scale")
            {
                settings.windowScale = std::clamp(std::atoi(value.c_str()), 1, 8);
                continue;
            }
            for (size_t i = 0; i < table.size(); ++i)
                if (key == table[i].key)
                {
                    // Old files (fps=120), a custom number (fps=173) and "monitor" all read here; a value that is
                    // none of them leaves the default.
                    int choice = settings.m_choices[i], number = settings.m_numbers[i];
                    if (ga2_options::parseStored(i, value, choice, number))
                    {
                        settings.m_choices[i] = choice;
                        settings.m_numbers[i] = number;
                    }
                }
        }
        // Files from before 0.11.0 hold the old defaults, Native, Window and 16:9: they become the new ones once,
        // Automatic, Borderless fullscreen and the screen's own shape (other choices stay as they are).
        if (any && !current)
        {
            const size_t resolution = ga2_options::Resolution, fullscreen = ga2_options::Fullscreen;
            if (std::string(table[resolution].choices[size_t(settings.m_choices[resolution])].value) == "0")
                settings.m_choices[resolution] = ga2_options::choiceIndex(resolution, "auto");
            if (std::string(table[fullscreen].choices[size_t(settings.m_choices[fullscreen])].value) == "0")
                settings.m_choices[fullscreen] = ga2_options::choiceIndex(fullscreen, "1");
            const size_t aspect = ga2_options::Aspect;
            if (std::string(table[aspect].choices[size_t(settings.m_choices[aspect])].value) == "16:9")
                settings.m_choices[aspect] = ga2_options::choiceIndex(aspect, "fit");
        }
        return settings;
    }

    void Settings::save(const std::filesystem::path &file) const
    {
        std::ofstream out(file, std::ios::trunc);
        const auto &table = options();
        for (size_t i = 0; i < table.size(); ++i)
            out << table[i].key << '=' << ga2_options::storedValue(i, m_choices[i], m_numbers[i]) << '\n';
        out << "window_scale=" << windowScale << '\n';
        out << "settings_version=" << kSettingsVersion << '\n';
        if (!lastGame.empty()) out << "last_game=" << lastGame << '\n';
    }

    void Settings::applyToEnvironment(const std::filesystem::path &dataDir) const
    {
        const std::string dumpDir = pathUtf8(dataDir / "dumps" / "textures");
        const auto &table = options();
        for (size_t i = 0; i < table.size(); ++i)
        {
            const Override &o = overrides()[i];
            setEnv(table[i].env, o.set ? ga2_options::envValue(i, o.choice, dumpDir, o.number)
                                       : ga2_options::envValue(i, m_choices[i], dumpDir, m_numbers[i]));
        }
        setEnv("GA2_WINDOW_SCALE", std::to_string(g_windowScaleOverride ? g_windowScaleOverride : windowScale));
        // Where the engines read and save settings.ini (the in-game settings menu).
        setEnv("GA2_DATA_DIR", pathUtf8(dataDir));
        // Rendered from the player's discs after import (assets.cpp): one
        // <program>.png per game.
        setEnv("GA2_SKYBOX", pathUtf8(dataDir / "assets" / "skybox"));
    }
}

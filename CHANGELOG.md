# Changelog

## 0.11.0

- Starts like a PC game: borderless fullscreen at the display's own
  resolution and shape (ultrawide included), with the internal resolution
  picked from the display (new default "Automatic": 4x from 1440p up, 2x on
  1080p; 2x in VR and on ARM).
  Window mode and fixed resolutions stay in Settings and as `--windowed`,
  `--resolution 2x`.
- Widescreen and ultrawide without stretching: the wider 3D view (hor+) is
  drawn with twice the columns where the screen has more than the internal
  resolution (16:9 at 1080p or 4K, 21:9 and 3440x1440), by a second renderer
  sampling half a pixel beside the first, so it is as sharp across as down.

- VR battle table (after BattleGroupVR's tactical map): in VR the battle's
  tactical map hovers flat in front of you as a holographic table (the game's
  own map reprojected onto it, units standing over it on stalks in team
  colours, the selected angel in gold). The HUD stands around the table in
  pieces, each its own panel leaning toward you: the radar and talk window on
  the left, the clock and unit panel on the right, pop-ups and menus above the
  far edge. Hover a unit by holding your fingertip over it (or touching it),
  select it with the trigger, drag to a spot or an enemy and let go to move,
  attack or support (the beam's colour shows which; a ring flashes at the
  target). One grip drags the map (with drift), both grips zoom about your
  hands and turn it, both held still recentre it. Haptic pulses on hover,
  select, order and while dragging the map. Setting "VR battle map": Battle
  table or Surround (the stereo map with the laser).
- VR guide: an interactive guide to the VR controls (basics at the screen,
  the battle part at the first battle table), replayable from Settings > VR
  guide or the table's ?; during the game's Tutorial a card shows the VR
  gesture for what it asks.
- VR hands: smooth holographic hands (an original model) in place of the
  blocky gloves, posed by the trigger (point) and grip (fist). With finger
  tracking (Valve Index controllers, Steam Frame, or bare-hand tracking) they
  follow your real fingers; with bare hands a pinch is the trigger and a fist
  the grip. Finger tracking is not yet tried on a headset; Settings > VR
  finger tracking turns it off.
- HD battle graphics (new setting, on by default; at 2x and 4x): the battle
  HUD is drawn sharp whatever the 2D filter. Flat-coloured pieces (the units'
  HP rings, stars, arrows, the clock's digits, enemy icons) are redrawn as
  clean shapes, rings and discs as true circles; panels and portraits are
  upscaled with Anime4K. Off brings back the original pictures.
- Fixed: with Anime4K, per-picture upscaling stopped after pictures of a few
  different sizes (the rest stayed at the original resolution), and every movie frame was
  upscaled and written to the cache (gigabytes per movie). Pictures that keep
  changing now stay at their original resolution.

- Portable: saves, settings, imported discs, mods, logs and caches live in the
  `data` folder next to `ga2`, so deleting the game's folder removes it
  completely and the folder can be moved. Data from earlier versions in the
  per-user folder (`~/.local/share/ga2`, `%APPDATA%\ga2`) stays in use until
  `ga2 --copy-data-here` copies it over; a read-only program folder uses the
  per-user folder.
- Every option is a command-line flag for that run (`--fps 175`,
  `--resolution 4x`, `--language en`, `--fullscreen`, ...; `ga2 --help` lists
  them), plus `--cache-dir` and `--window-scale`. `ga2 <disc image>` imports
  the disc and starts its game; `--start last` starts the game played last.
- The installer keeps the `data` folder through updates and uninstalls, never
  ships one, and remembers the install folder from its own shortcuts.
- New README screenshots with the native text, and VR screenshots (a story
  scene on the big screen in the space skybox; a battle in stereo).

## 0.10.0

- An installer and updater for Windows, Linux x86-64 and Linux ARM64: it
  installs the newest release (checked against its SHA-256), adds menu and
  desktop shortcuts (and an Apps & features entry on Windows), shows the
  release notes, updates in place (removing files a newer version dropped
  and putting the old files back if an update fails), updates itself, and
  uninstalls. Saves, settings, discs and mods in the data folder are never
  touched. Each release archive carries it as `ga2-installer`, the updater
  of that install; it also works from the command line (`--check`,
  `--update`, `--uninstall`).
- Native text rendering at 2x and 4x: the port lays out and draws the
  games' English and Japanese text itself from the vector font, with the
  font's own letter spacing and kerning (instead of the old bitmap font's
  widths and 10-pixel spaces), full descenders, and Japanese at the size it
  is shown. In 2D scenes the text is drawn at the window's own resolution
  over the picture, like any other text on the desktop: the 2D filters
  (Anime4K, Smooth), debanding and scaling never touch it. Line breaks,
  alignment, colours, fades, menus over the text and the typewriter effect
  are the games'. Names sit centred between their dots.
- Button prompts and the prompt words (Auto, Back, Menu) are drawn at the
  window's own resolution in 2D scenes too, from their high-resolution
  images.
- Anime4K at 2x and 4x works per layer: every CG, background, character
  sprite and UI picture is upscaled on its own and the game composes the
  upscaled layers, instead of one pass over the finished 640x448 picture, so
  fine detail and line art stay crisp. Upscaled pictures are cached on disk.
- A picture rendered larger than the window (2x or 4x in a smaller window) is
  shrunk with an area-averaged filter instead of a bilinear one, so the strokes
  of text and thin lines keep an even weight.
- High-resolution replacement images (texture packs, button prompts, text in
  3D scenes) are sampled smoothly, without combs along their edges.
- Faster 3D scenes: graphics commands are processed on their own thread, and
  texture uploads and model data are unpacked faster. In the Zettai ship map
  the game's own thread does about a third less work per frame, so high
  frame-rate caps hold 120 fps where they used to fall back to 60.
- 4x at high frame rates: the picture now goes from the graphics card to the
  window without a round trip through main memory. At 4x the menus and
  loading screens reach 175 frames per second (about 90 before), and the ship
  map is no longer held back by the picture's transport (84 before). In VR
  both eyes' pictures take the same route.
- Choosing 4x with a frame rate above about 85 no longer runs the game in slow
  motion when the graphics card is the limit: the frame rate steps down
  instead, as it already did when the processor was the limit.
- When the PC can't keep up with the chosen frame rate, it steps down to the
  next rate in the settings list (165, 144, 120, ...) instead of straight to
  120 or 60: the Zettai ship map runs at 144 with a 175 cap.
- The game hands each frame to the graphics thread without waiting for it,
  and the 3D geometry programs finish their packets faster.
- The keyboard's Enter prompt shows the return arrow (↵) instead of the word
  ENTER, which was unreadable at the size of the message marker.

## 0.9.0

- English translation included (Options > Language > English): story
  scripts, character names, battle dialogue, menus, the text inside the game
  programs, the staff roll and the translated pictures. It ships as a
  language pack in `mods/ga2-en`.
- Widescreen battle HUD (16:9 to 21:9):
  - unit markers stay on their units and keep their shape
  - the minimap's blips stay inside the minimap
  - the message balloon stays beside its portrait
- Sharp text and HD button prompts now reach the screen in 2D story scenes
  at 2x and 4x. Those scenes are composed off screen, and the copy to the
  screen used to drop back to 640x448.
- The Anime4K filter at 2x and 4x keeps the full-resolution text and icons
  instead of redrawing them from a 640x448 copy.
- New high-resolution button prompts (256x256, sharp up to 8x), also for
  PlayStation controllers, which used to get the games' own low-resolution
  icons. The dialogue box's Auto, Back and Menu words are redrawn sharp too.
- Button prompts blend into the art behind them. The PlayStation icon used
  to be covered with a flat block of colour.
- Debanding is on by default (Low) in 2D and 3D scenes, and text and other
  sharp edges are left untouched.
- The README is also in Japanese (README.ja.md).
- The launcher also reads mods from a `mods` folder next to it, so a release
  can ship language packs. A pack installed in the data folder still takes
  precedence.
- Language packs' save-message tables are keyed by digests, so a pack
  carries none of the games' original text. Older packs still work.
- Steam Frame:
  - the Frame controller profile, including its D-pad
  - SteamVR's own OpenXR loader
  - disc import from an `isos` folder
  - a launcher that works entirely with a gamepad
  - a guide (docs/STEAM_FRAME.md)
- VR controller table in the README.
- Linux builds need only glibc 2.30 and libGL (no libGLU or libatomic).

## 0.8.0

The first public release. All three games are playable on all five
discs.

- One launcher for the trilogy, with automatic disc changes and saves that
  carry over between the games.
- 2x and 4x internal resolution, widescreen up to 21:9 (hor+ 3D), and frame
  rates up to 240 fps at the original game speed.
- Keyboard, gamepad and mouse play, including battles. Button prompts
  follow the device you're using.
- Message skip (hold Ctrl) and movie skip (Esc).
- Language packs, file mods and HD texture replacement.
- 2D filters (Smooth, Anime4K, sharp pixels), debanding, and the PS2 dither
  turned off.
- Cheats menu (F1) and in-game settings (F2).
- VR through OpenXR, with stereo 3D scenes.
- Builds for Windows x86-64, Linux x86-64 and Linux ARM64.

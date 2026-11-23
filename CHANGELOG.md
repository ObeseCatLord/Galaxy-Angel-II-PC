# Changelog

## 0.12.0

- Native movies (new setting "Movies", default Native): the PC decodes and
  shows the games' movies itself instead of emulating the PS2's video decoder,
  so they play smoothly at full speed on any PC (they were slow on the Steam
  Deck) and the game runs at full rate around them. The game's own movie
  handling (skipping, the gallery, the music) is unchanged; "Original" keeps
  the emulated player.
- Movie subtitles (setting "Movie subtitles", on by default): the English pack
  subtitles the spoken lines in the movies (story movies and chapter
  previews). They are a first pass made from transcripts; lines that could not
  be made out are left out.
- Faster, especially on the Steam Deck: the emulated I/O processor and the
  PS2's timers do much less bookkeeping (about a quarter less work for the
  game in story scenes), and the full-colour picture no longer makes the
  game wait for the graphics card (battles at 2x hold full speed on the Deck).
- Windows: folders, user names and disc image names in any language
  (Japanese, accented letters) work; the programs now use UTF-8 for file
  names.
- Full colour: the games draw in full colour and then copy each frame into a
  16-bit picture for the TV; that copy put visible colour steps (bands) into
  every gradient: nebula skies, glows, fades. The full-colour frame is now
  shown instead, with nothing smoothed or filtered (PS2 dithering On keeps the
  original 16-bit picture).
- VR: in the 3D views (space flights, the battle's chase and cockpit views)
  the HUD and dialogue box float on their own panel in their own shape; they
  were stretched over the headset's view.
- VR: the guide's Japanese text was garbled on some lines; fixed (and lines
  no longer start with closing punctuation).
- VR battle table, first steps of a new table modelled on BattleGroupVR:
  - the game's own ship models stand on the table (the angels' Emblem Frames,
    the mothership and every enemy ship, read from your disc for the stage
    being played), lit, in team colours, turned the way they fly;
  - a round hologram table whose edge fades out, clear like glass, inside the
    battle's own sky (the stage's sky rendered around you from your disc);
  - the HUD's pieces (radar, clock, unit panel) float on their own as
    holograms, drawn from the game's 2D layer alone, with no map behind them,
    and the table is never cut;
  - each unit's marker is its own icon from the game (the angel's face, the
    ship's silhouette), upscaled, on a disc drawn at any resolution with its
    shield as a ring and a heading arrow under the ship; markers are solid
    layers (a nearer one covers a farther one, never blended or cut into);
  - ships sized by their models (larger ships larger, smaller than before,
    growing as you zoom in), with a slow hover and banking into turns;
  - palm menus: turn a palm to your face for the squadron (left: select an
    angel, all angels, pause) or the commands (right: stay, H-Weapon, cancel,
    views, menu, recentre, guide, reset layout), poked with the other hand;
  - every floating panel can be moved with a grip and keeps its place; the
    characters' talk window has its own larger panel;
  - the chase and cockpit views are a stereo hologram standing where the
    table was (both grips scale it); the unit camera view shows on a screen
    standing in the table;
  - the second eye's renderer rests while the picture is not stereo (theater
    screen, table).
  - the table draws the battle map itself (the stage's own grid, play area and
    obstacles, read from your disc) while the game skips drawing its 3D map:
    battles in table mode use about half the processor time they did.
- Faster: the I/O processor (sound, disc) no longer rescans its threads and
  timers while it is idle, and the 3D chip's programs are recognised without
  re-hashing them; on the Steam Frame the game runs on its fastest core
  (battles about a quarter faster there). Busy battles on a PC hold full speed
  longer.
- Windows: Mugen disc images are accepted again ("SYSTEM.CNF has no BOOT2
  line"): files stored past the first 2 GB of a disc image are read correctly
  (this also affected parts of the English pack on Windows).
- A crash now writes its cause to the log (to help with reports).
- New setting "Battle map drawing" (desktop): Original (default) keeps the
  game's own battle map; Fast has the PC draw the map's 3D itself (the stage's
  grid, play area, obstacles and sky, read from your disc) under the game's own
  2D: about half the processor time, so the map holds high frame rates (144 on
  a fast PC). It looks close to the original but not identical.
- Frame rates up to 500: new choices 300, 360 and 480, Custom up to 500, and
  Monitor follows displays up to 500 Hz.
- VR follows the headset's refresh rate as set in SteamVR or on the headset,
  and follows it when it changes.
- Higher frame rates: the battle's camera views (30 fps on the PS2) are drawn
  at the chosen rate too when the PC can keep up; movies play closer to full
  speed.
- Menus and HUD as sharp pixels (new setting "Menus and HUD", default Sharp
  pixels): at 2x and 4x the menus, windows, place names and the battle HUD keep
  their original pixels instead of being smoothed by Anime4K; characters,
  portraits, backgrounds and event pictures still go through Anime4K.
- Story scenes: the characters' blinking eyes and moving mouths are upscaled
  with their faces (they were enlarged without Anime4K and looked soft on the
  sharp faces).
- Battle map: the zones and the order lines have smooth edges at 2x and 4x
  (they were drawn at the PS2's resolution).
- Anime4K and Anime4K HQ keep separate cached pictures.

## 0.11.0

- Starts like a PC game: borderless fullscreen at the display's own
  resolution and shape (ultrawide included), with the internal resolution
  picked from the display (new default "Automatic": 4x from 1440p up, 2x on
  1080p; 2x in VR; native on ARM).
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
- Steam Frame: tried in SteamVR for the first time. VR at 72 Hz, the battle
  table and finger tracking work; battles run slower than real time (about
  13 to 21 frames a second, limited by the processor), see
  docs/STEAM_FRAME.md.
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

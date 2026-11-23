# Playing Galaxy Angel II PC

## What you need

Your own disc images (`.iso`) of the Japanese PlayStation 2 releases:

| Game | Discs |
| --- | --- |
| Galaxy Angel II: Zettai Ryouiki no Tobira | 1 |
| Galaxy Angel II: Mugen Kairou no Kagi | 2 |
| Galaxy Angel II: Eigou Kaiki no Toki | 2 |

A GPU with Vulkan 1.3 (the PS2 graphics run on the GPU through paraLLEl-GS).

## Installing and updating

The installer sets up the newest release and keeps it up to date:
[Windows](https://github.com/ObeseCatLord/galaxy-angel-2-pc/releases/latest/download/galaxy-angel-2-pc-installer-windows-x86_64.exe),
[Linux x86-64](https://github.com/ObeseCatLord/galaxy-angel-2-pc/releases/latest/download/galaxy-angel-2-pc-installer-linux-x86_64),
[Linux ARM64](https://github.com/ObeseCatLord/galaxy-angel-2-pc/releases/latest/download/galaxy-angel-2-pc-installer-linux-arm64)
(on Linux, `chmod +x` the file first).

- It shows the installed and the newest version with the release notes;
  **Install** / **Update** downloads the release, checks it against the
  release's SHA-256, and puts it in the install folder (default
  `%LOCALAPPDATA%\Programs\Galaxy Angel II PC` on Windows,
  `~/.local/share/galaxy-angel-2-pc` on Linux; any empty folder works).
- It adds **Galaxy Angel II PC** and **Galaxy Angel II PC Updater** to the
  Start menu (and the desktop) or the Linux application menu, and on Windows
  an entry in Apps & features to uninstall.
- An update replaces only the files the release ships and removes the ones a
  newer version dropped. If something goes wrong (say the game is still
  running), the old files are put back. **Saves, settings, imported discs and
  mods are in the `data` folder (below) and are never touched**, nor is anything
  you added to the install folder yourself.
- Every install has the updater as `ga2-installer` (`ga2-installer.exe`) next
  to `ga2`; it updates the folder it is in. It also updates itself when a
  newer installer comes out.
- **Uninstall** removes what the installer installed and its shortcuts; the
  `data` folder (your saves) stays in the install folder.
- Without a window (SSH, scripts): `ga2-installer --check` (exit code 10 when
  an update is available), `--update`, `--install`, `--uninstall --yes`,
  `--dir <folder>`, `--no-shortcuts`; `--help` lists them.

On Linux it uses `curl` (or `wget`) and `tar` with `xz`, which nearly every
distribution has. Windows needs nothing extra.

The release archives work without the installer too: extract one anywhere
and run `ga2`.

## First start

1. Run `ga2` (`ga2.exe` on Windows).
2. Drag your `.iso` files onto the window. Each disc is checked once and
   remembered; the images stay where they are. Without a mouse (Steam
   Frame, Steam Deck game mode, a TV), put them in the `isos` folder of the
   data folder (below) instead: they are added when the launcher starts, or
   when you press R / Triangle (Y).
3. Pick a game. Discs are never swapped by hand: the port finds the right disc
   when a game asks for one (Mugen's and Eigou's second discs, the Zettai disc
   that unlocks the Extra Route, and so on), so add every disc you own up front.

## Controls

| PS2 | Keyboard | Gamepad | Mouse |
| --- | --- | --- | --- |
| D-pad | Arrows / WASD | D-pad | wheel = up/down (menus), on-screen pad |
| Circle (confirm, advances messages) | Enter (or C, Esc) | right face button | left click |
| Cross (cancel) | X or Space | bottom face button | right click |
| Square / Triangle | Z / V | left / top face button | on-screen pad |
| L1 / R1 | Q / E | shoulders | on-screen pad |
| L2 / R2 | Left / Right Shift | triggers | on-screen pad |
| Start (pause) | P | Start | on-screen pad |
| Select (system menu) | Tab | Back | middle click |
| L3 / R3 (stick clicks) | R / F | stick clicks | in battles: back / forward button (see below) |

Hold **Ctrl** to skip messages and press **Esc** to skip a movie (below). F11 or Alt+Enter switches fullscreen (Alt+Enter is not Circle). **F2** opens the settings menu, **F1** the cheat menu (see Options and Cheats).

### Skipping messages

Enter advances a message (it completes the typing first, then turns the page).
**Hold Ctrl** (either one) to fast-forward through the story: the game is
given Circle presses every other frame, 30 a second, so the text completes
and the page turns about as fast as the game takes presses (the first
chapter's several hundred messages take about a minute and a half). It works
with a gamepad plugged in too.

Skipping only runs while a story script is on and nothing needs a decision:

- it stops at **choices** (the options stay up while you hold Ctrl; release it
  and choose, then hold it again), and never picks one;
- it does nothing in the **system menu**, the **backlog**, the options, the
  load and save screens, the title, the ship map or a battle;
- pressing any other button while holding Ctrl (Tab for the system menu, Z for
  the backlog, V for Auto, X, P, ...) stops the skipping until you let go of
  Ctrl and press it again, so a menu opened mid-skip is never confirmed.

Transitions and effects between messages are not shortened (Circle does not
cut them in the game either). `GA2_NO_SKIP=1` turns the feature off.

### Skipping movies

Press **Esc** during a movie (the hangar launch before a battle, the story
movies) to skip it. This is the games' own movie skip, the Start button (P on
the keyboard, Start on a gamepad, which work too): the game ends the movie as
if it had played out and carries on to what follows (the battle, the next
scene). Esc stays the Circle button everywhere else.

### Playing with the mouse

The whole game can be played with the mouse alone:

- **Menus follow the pointer**: on the title screens, the system menu, yes/no
  prompts and story choices, pointing at an item selects it and clicking
  chooses it.
- **Dialogue**: click anywhere to advance; the Auto, Back (backlog) and Menu
  buttons next to the text box work as buttons.
- **On-screen pad**: move the mouse and a pad appears in the black bars beside
  the picture (D-pad, the four face buttons, L1/L2/R1/R2, Select, Start).
  Click its buttons for anything without a menu, such as scrolling the ship
  map with the D-pad.
- Right click cancels (Cross), the wheel moves up/down, the middle button
  opens the system menu.
- **Battles**: the mouse works in the tactical map, the cockpit and the camera
  view. Everything goes through the game's own buttons and functions, so
  sounds, restrictions (busy units, the tutorial's gates) and the story's
  scripts apply (the tutorial's disabled buttons stay disabled for the mouse too),
  and keyboard and pad play is unchanged (the mouse takes over
  only while you move or click it, and it follows a remapped pad layout).

  *Tactical map* (the grid view with the unit icons; a gamepad opens it with
  L3 from the cockpit, the keyboard with R): the map's cursor is normally the
  centre of the screen; with the mouse the cursor ring follows the pointer.

  | Mouse | Does |
  | --- | --- |
  | Left click on a unit icon | select it (its unit panel appears while you point at it) |
  | Left click on empty map / an enemy / a friend | move the selected unit there / attack / support (the unit itself: Stay) |
  | Ctrl + left click | the same for all your angels (Square, then Circle) |
  | Double click on a unit | the camera focuses on it (the game's own focus) |
  | Right click | cancel (Cross) |
  | Right drag | pans the map: the ground follows the pointer |
  | Pointer at the picture's edge | scrolls the map (the game's D-pad scroll; set `GA2_BATTLE_EDGE_SCROLL=0` to turn it off) |
  | Wheel | zooms the map camera (what R1 / R2 do), toward the point under the pointer |
  | Middle click on a unit | its H-Weapon (Triangle) |
  | Middle button held on empty map | L2: the game's angel list ("Direct Jump Menu") opens; the wheel moves its cursor, releasing the button jumps the camera to that angel |
  | Ctrl + middle click | Start (pause; then the middle button is Select, the system menu) |
  | Back button | the pilot (cockpit) view (L3) |
  | Ctrl + right click, or the forward button | camera view of the unit under the pointer (R3) |

  The keyboard keeps working with the pointer: point at a unit and press V
  (H-Weapon), F (camera view), Z (order all), R (cockpit), Shift (angel list).
  The pointer takes over while you move it or click; after six seconds
  without moving, and while it is outside the picture, the map goes back to
  its centre cursor for pad and keyboard play.

  *Cockpit* (the pilot's view): the reticle follows the pointer; the left
  button held fires, the right button held charges and, released, fires the
  charged shot; the middle button (or the back button) leaves for the map
  (L3); Ctrl + middle click pauses.

  *Camera view* (a unit seen through its own camera): dragging with either
  button turns the camera, the wheel zooms, a left click selects the unit for
  orders and returns to the map (Circle), a right click leaves (R3).

  *Menus in battle*: the pause menu (Start; the options and quit items) and
  the other menus follow the pointer like the rest of the game: point at an
  item and click.

## Options (launcher: Options button or O; in a game: F2)

Saved in `settings.ini` in the data folder. The launcher passes them to the
game when it starts it; the same options can also be changed while playing
(next section).

| Option | Choices |
| --- | --- |
| Language | Japanese / English: the window title, and which language pack mod is used |
| Internal resolution | Automatic (default), Native, 2x, 4x: detail of the 3D scenes. Automatic picks it from the display the game starts on, like a PC game, at least as tall as the display where it can: 4x (2560x1792) from 1200 lines up (1440p, ultrawide 3440x1440, 4K), 2x (1280x896) on 1080p and the like, native only under 700 lines; 2x in VR and on ARM (the Steam Frame). The log says what it chose (`[display] 3440x1440: internal resolution 4x (automatic)`); at 2x and 4x the text is drawn from a vector font with its own letter spacing, in 2D scenes at the window's own resolution (the 2D art is native 640x448 art). A picture larger than the window is shrunk smoothly (area-averaged), so thin lines and text keep their weight |
| Display | Borderless fullscreen (default: the display's own resolution, other apps a click away) / Window (F11 or Alt+Enter switch while playing) |
| Screen shape | Fill the screen (default: its own shape, so 3440x1440 is played at 43:18 with hor+ 3D) or a fixed 16:9, 16:10, 21:9 ultrawide, 4:3 |
| 3D widescreen (hor+) | On: 3D scenes show more to the sides at 16:10, 16:9, 21:9 or the window's own shape (Fill), same height as on the PS2; HUD, menus and text keep their proportions, and the battle HUD sits at the screen edges (radar top left, communications bottom left, unit panel and pilot portrait bottom right). The wider view is drawn with its own detail, not stretched: where the screen gives the picture more columns than the internal resolution has (16:9 at 1080p or 4K, ultrawide such as 3440x1440), a second renderer samples half a pixel beside the first and the two are interleaved, doubling the columns (about twice the GPU work; the log says `[display] widescreen detail: ...`; `GA2_PGS_WIDE_DETAIL=0` turns it off) |
| Sides of 4:3 scenes | Black, blurred picture, or the game's own space skybox (rendered from your disc after import; needs Python 3 with Pillow) |
| 2D scene size | Fill, or whole multiples (2x, 3x) for crisp pixels; 3D scenes always fill |
| 2D picture filter | Bilinear, Smooth (removes the art's dither grain), Anime4K, Anime4K HQ, Sharp pixels, Nearest; 2D scenes only. At 2x and 4x, Anime4K works per layer: every CG, background and character sprite (with its blinking eyes and moving mouth) is upscaled on its own (to the internal resolution) and the game composes the upscaled layers; the menus and windows follow "Menus and HUD". A picture is upscaled the first time it is shown (it appears sharp a moment later) and kept in the cache folder (`data/cache/anime4k`) for later sessions. The text and the button prompts are drawn at the window's own resolution |
| Frame rate | 60 (PS2, default), 75, 90, 100, 120, 144, 165, 170, 175, 180, 200, 240, 300, 360 or 480 frames per second; **Monitor refresh rate** follows the monitor the window is on (read at the start and again when you move the window to another monitor or its rate changes; a monitor at 60 Hz or below means the PS2 rate, above 500 is capped at 500); **Custom** is any whole number from 61 to 500 (launcher: type it into the box, or use the mouse wheel over it; in game: Left / Right change it by 1, Shift by 10, or type the digits and press Enter; Enter or PageDown goes on to the next choice). The whole game (story, menus, ship map, battles) is drawn that often while it keeps its own speed. The rate drops automatically when the PC can't keep up (the processor or the graphics card, for example at 4x), so the game never runs slower than at 60; can also be changed while playing (F2). The battle's camera views (30 fps on the PS2) are drawn at the full rate too. In VR the rate follows the headset. Stored in `settings.ini` as `fps=120`, `fps=173` (custom) or `fps=monitor` |
| PS2 dithering | Off (default): the games' full-colour picture, gradients without colour steps. On: the PS2's 16-bit picture with its original checkerboard |
| Debanding | Low (default), High or Off: smooths the colour steps of the PS2's 16-bit gradients (backgrounds, CGs, nebula skies, fades) in 2D and 3D scenes; edges and text stay sharp |
| HD battle graphics | On (default) or Off (original): at 2x and 4x the battle HUD is drawn sharp, whatever the 2D filter. Its flat-coloured pieces (the units' HP rings, stars, arrows, the clock's digits, enemy icons) are redrawn as clean shapes (rings and discs as true circles), the rest follows "Menus and HUD" (portraits with Anime4K), each the first time it is shown |
| Battle map drawing | Original (default): the game draws the battle map's 3D as on the PS2. Fast: the PC draws the map's grid, play area, obstacles and sky itself (read from your disc) under the game's own 2D, about half the processor time, so the map holds high frame rates; close to the original but not identical. The VR battle table always draws its own map |
| Movies | Native (default): the PC decodes and shows the movies (smooth at full speed, subtitles possible). Original: the emulated PS2 movie player |
| Movie subtitles | On (default) or Off: subtitles for the movies' spoken lines, from the language pack (the English pack has them; native movies only) |
| Menus and HUD | Sharp pixels (default) or Anime4K: at 2x and 4x, how the menus, windows, place names, ornaments and the battle HUD's panels are enlarged. Sharp pixels keeps the original pixels, crisp and unsmoothed; Anime4K smooths them like the characters. Characters, portraits, backgrounds and event pictures are always upscaled with Anime4K (in 2D scenes with that filter) |
| Button prompts | Automatic (follows the controller or keyboard you use), PlayStation, Xbox, Keyboard |
| VR mode | Off / On (see below) |
| VR battle map, VR guide, VR finger tracking | the VR options (see below) |
| On-screen pad | Off (default) / clickable pad buttons beside the picture |
| Dump textures (modding) | Saves every texture shown, for making mods (docs/MODDING.md) |

### Changing options while playing

Press **F2** in a game (or click both sticks on a gamepad or in VR, then choose
**Settings** in the menu that opens) to see the same options. Up / Down choose,
Left / Right change the value (Enter / Space / Circle: next value; with the mouse
click the left or right half of the value, or turn the wheel over a row), F2,
Esc or Cross close. A row is highlighted only while the mouse is over it or after
you chose it with the keys or pad (until the mouse moves again); Enter and Left /
Right act on the row the keys chose, a click on the row under the pointer. The
Custom frame rate takes digits and Enter (Esc drops them, Backspace deletes one);
PageUp / PageDown are previous / next value on any row. The launcher's screens
follow the same rule. The game does not see your input while the menu is open. Every
change is saved to the launcher's `settings.ini` at once, so the launcher and the game
always agree; the file is `GA2_DATA_DIR/settings.ini` (the launcher sets it), or
`data/settings.ini` next to the program for an engine started without the
launcher.

- **Take effect at once:** Display, Screen shape (the window takes the new shape
  too), 3D widescreen (hor+; the 3D cameras follow within a frame), Sides of 4:3
  scenes, 2D scene size, 2D picture filter, PS2 dithering, Debanding, HD battle graphics, Menus and HUD, Button prompts,
  On-screen pad, and the Frame rate (any choice, up to 500). Dump textures applies to
  the textures the game loads from then on.
- **Marked "restart" and applied the next time a game starts:** Language, Internal
  resolution, Battle map drawing and VR mode. The menu shows such a value in orange
  with "after restart" until the game is restarted. After a disc change inside a
  game (the next disc's engine) the options as saved are used.
- In VR the menu is drawn like the cheat menu (on the screen, or on a panel in 3D
  scenes): left stick up / down / left / right, A or the trigger = next value, B closes.

## VR

1. Start your VR runtime: SteamVR, or Monado (e.g. through Envision). It must
   be the active OpenXR runtime.
2. In the launcher's Options set **VR mode** to On, then start a game.

The game appears on a large screen floating in the game's own space sky.
Each controller shows a clear holographic reticle where your hand is.
Point either controller at the screen: a blue laser shows where you point,
and menus follow it like the mouse; the **trigger** clicks. The monitor keeps
showing the flat game.

Every PS2 input is a separate action, so SteamVR's binding screen lists them
all and you can rebind any of them. By default, on Quest, Rift, Pico, Reverb
G2 and Index controllers:

| Controller | PS2 |
| --- | --- |
| A / B (right hand) | Circle / Cross |
| X / Y (left hand; on Index the left A / B) | Square / Triangle |
| Left stick | left analog stick and D-pad (also scrolls the ship map) |
| Right stick | right analog stick (turns the camera when you watch a unit); pushed left / right also L2 / R2 |
| Grips | L1 / R1 (a light squeeze of R1 raises the battle map camera, R2 lowers it) |
| Left / right stick click | L3 (cockpit from the map) / R3 (watch a unit); both together open the cheat menu (which has a Settings row) |
| Menu button | Start when tapped, Select when held (Index: hard press on the left trackpad; right trackpad = Select) |
| Trigger | clicks on the screen; in 3D scenes Circle (select on the tactical map, advance dialogue); in the cockpit it fires; in the unit camera view the triggers zoom |

Windows Mixed Reality and Vive wands have no face buttons: the right
trackpad's click is Circle / Cross / Square / Triangle by direction. The
cheat menu appears in front of you (on the screen, or on a panel in 3D
scenes): move with the left stick, choose with A or the trigger, close with
B. Hold **both grips** (on the Steam Frame, both bumpers) for a second to
bring the screen back in front of you.

The 3D scenes (space flights, the ship map, battles) surround you instead:
the game draws them from your head's position and direction in true stereo,
and you can look and lean around (6DoF). The game's 2D overlay (dialogue box,
battle HUD) is shown on a flat panel 1.6 m in front of you, in its own 4:3
shape (environment variable `GA2_VR_HUD_PANEL=0` draws it into the 3D view
instead, stretched to the headset's view). Your hands stay visible there as
their reticles with a short guide beam. The 2D story scenes, menus and
movies stay on the screen. If the world feels too big or too small, set
`GA2_VR_SCALE` (game units per metre, default 50) before starting; set
`GA2_VR_STEREO=0` to keep every scene on the screen.

**The battle table** (Settings > **VR battle map** > *Battle table*, the
default; modelled on BattleGroupVR's tactical map). The battle's tactical map
hovers in front of you as a round holographic table at about chest height
(standing; desk height seated), clear like glass and fading out at its edge,
inside the battle's own sky: the sky the stage's map shows is drawn all
around you from your disc. On it stand the game's own ship models (the
angels' Emblem Frames, the mothership and every enemy ship, read from your
disc for the stage being played), lit, banking into their turns and turned
the way they fly, larger ships larger, growing as you zoom in. Over each
stands its marker: the game's own icon for that unit (the angel's face, the
ship's silhouette), upscaled, on a disc in its team colour (gold angels, blue
mothership, red enemies) with its shield as a ring, a heading arrow on the
ring under the ship, and a gold edge on the angel you have selected. Each
marker is a solid layer: a nearer one covers a farther one, and crowded ones
lift a little apart. The HUD is not a flat screen: each piece floats on its
own as a hologram, only its own pixels (the radar on the left, the clock and
the unit panel on the right, pop-up boxes, the tutorial's boxes and menus
above the far edge). What the characters say during the battle (the talk
window) has its own larger panel over the far rim.

**Moving panels.** Put a hand on any floating panel (a HUD piece, the talk
panel, the guide) and squeeze the grip: it follows your hand until you let
go. Panels keep their places for the next battle; *Reset layout* on the right
palm puts them back.

**Palm menus** (after BattleGroupVR's hand menus). Turn a palm toward your
face and a menu shows over it; poke its keys with the other hand's index
finger (a key fires when pushed in, with a buzz).

| Palm | Shows | Keys |
| --- | --- | --- |
| Left: *Squadron* | your angels with their shield bars, the selected one in gold | poke an angel to select it; *All angels* (Square); *Pause* (Start) |
| Right: *Command* | | *Stay* (the selected angel stays), *H-Weapon* (Triangle), *Cancel* (Cross), *Pilot view* (L3), *Camera* (R3), *Menu* (Select), *Recentre*, *Guide*, *Reset layout* |

Each key does what the pad's button does; the game decides (its tutorial can
still hold a button back).

**The other views inside the table.** The chase and cockpit views appear as
a hologram where the table was: the game's 3D in stereo, seen inside a
glowing column standing on the table's plate, with the stage's sky around
you. Pull both grips apart or together to make it larger or smaller (one grip
is still L1 / R1). In the cockpit the HUD and
the reticle float on a panel ahead of you. The unit camera view shows on a screen standing in the
table, the ships on the plate below it. In these views the right palm's first
key is *Back to table*. The H-Weapon's own
sequence still fills the view as before.
Your hands are translucent holograms; the hand that selected an angel turns
orange until the order is given.

| Gesture | Does |
| --- | --- |
| Look at a unit and hold your fingertip over it, or touch its disc | hovers it (it lights up; a short buzz) |
| Trigger on one of your angels | selects it (on another angel while one is selected: selects that one instead) |
| Hold the trigger on the selected angel, point and let go | a beam shows what letting go does: cyan move, red attack, green support (follow, supply, repair), grey nothing (off the table); letting go gives the order and a ring flashes at the target |
| Trigger on the ground or an enemy with an angel selected | moves there or attacks it at once |
| One grip, drag | moves the map (it follows your hand with light ticks, then drifts on a little; a trigger stops the drift) |
| Both grips | apart / together zooms in / out about the point between your hands; twisting turns the table |
| Both grips held still for a second | brings the table back in front of you, facing ahead |
| X / Y / B | all angels / H-Weapon / cancel, as on the pad |
| Left / right stick click | cockpit (the triggers fire) / the camera of the unit (the triggers zoom) |
| Touch the ? at the table's near right and pull the trigger | replays the battle part of the VR guide |
| Grip with your hand on a panel | carries the panel (see *Moving panels*) |
| Palm toward your face | its palm menu (see *Palm menus*) |

Losing tracking for a moment does not drop a drag; after a quarter of a second
the drag is cancelled without an order. With the cheat menu open the hands
work the menu, not the table.

**Finger tracking** (Settings > **VR finger tracking**, on by default): where
the headset tracks your fingers (Valve Index controllers, the Steam Frame,
bare-hand tracking), the hands follow your real fingers; with a controller the
pointer stays on the controller. With bare hands a pinch is the trigger, a fist
is the grip and the hand's direction aims; buttons the guide waits for are
skipped. *Not yet tried on a headset*: if the hands misbehave, turn it off for
hand poses from the trigger and grip only.

`GA2_VR_TABLE=<height below the eyes>,<distance>,<width>` (metres, default
`0.45,0.55,1.2`) places the table. *Surround* instead draws the tactical map
around you in stereo, with the laser pointer: aim at a unit and pull the
trigger (or press A) to select it, then aim at empty map and pull the trigger
to send it there (Move), or at an enemy to attack; B (Cross) cancels, X
(Square) orders all angels, Y (Triangle) is the H-Weapon. The other battle
views (cockpit, chase and camera views) play with the buttons as in the table
above.

**The VR guide.** The first time you play in VR, a guide next to the screen
walks you through pointing, clicking, the buttons and recentring, and at the
first battle table through grabbing, zooming, selecting and drag orders; each
step finishes when you do it, and holding B skips a part. Replay it any time:
Settings > **VR guide** > *Show again*, or touch the ? on the battle table and pull the trigger.
During the game's own Tutorial (title screen), a card at the table says how to
do in VR what the tutorial asks for, in place of its pad buttons.

## Cheats

Press **F1** (or click both sticks) in a game to open the cheat menu (its last row,
**Settings**, leads to the options above):

- Skip this battle (ends the battle being fought as a win with the best
  result the battle gives),
- Invincible units, Infinite energy and spirit, One-hit kills, Stop the time
  limit.

The game is paused for input while the menu is open.

## Mods

The launcher's **Mods** screen (M) turns installed mods on and off and orders
them; translations come as language packs that follow the Language option
(how to install one: [LANGUAGE_PACKS.md](LANGUAGE_PACKS.md)). How to make
mods: [docs/MODDING.md](MODDING.md).

## Command line

`ga2` is the only program to start; it runs the games itself. Every option
of the Options screen is also a command-line option, for this run only (the
saved settings stay as they are). `ga2 --help` lists them all with their
values.

```
ga2                                   the launcher
ga2 "Zettai Ryouiki no Tobira.iso"    import the disc (once) and play it
ga2 --start zettai                    play without the launcher (zettai, mugen,
                                      mugen-extra, eigou, eigou-2, or last)
ga2 --start last --fullscreen         the game played last, fullscreen
ga2 --start eigou --resolution 4x --fps 175 --language en
ga2 --data-dir /path/to/data          another data folder (saves, settings)
ga2 --import a.iso b.iso              import only
ga2 --list                            the data folder, imported discs, games
```

Options take the values shown by `--help` (`--fps 175`, `--resolution 4x`,
`--filter anime4k`, `--vr on`); `--fullscreen`, `--windowed`,
`--window-scale <n>`, `--cache-dir <dir>` and `--engine-dir <dir>` are there
too.

## Where things are

Everything the game keeps is in the `data` folder next to `ga2`
(`ga2.exe`): the install is portable, and deleting its folder removes the
game completely. Two exceptions: data from a version before 0.11 in the old
per-user folder (`~/.local/share/ga2`, `%APPDATA%\ga2`) stays in use until
you run `ga2 --copy-data-here`, which copies it into `data` (the old folder
is left alone, delete it when you like), and a program folder you can't
write to (a system-wide install) uses that per-user folder. `--data-dir`
picks any folder. In the data folder:

- `memcards/` - your saves (one memory card shared by the three games, so
  Zettai and Mugen saves carry over as on the PS2)
- `logs/` - one log per game, useful when reporting a problem
- `isos/` - disc images to add without drag and drop
- `mods/` - installed mods (see Mods above)
- `assets/skybox/` - the space skies rendered from your discs
- `dumps/textures/` - textures saved by the Dump textures option
- `cache/` - compiled GPU pipelines and upscaled pictures (safe to delete)
- `settings.ini`, `library.json` - your options and the imported discs

Your graphics driver keeps its own shader cache, as it does for any game.

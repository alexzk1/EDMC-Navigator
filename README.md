# Surface Navigator

A plugin for [Elite Dangerous Market Connector (EDMC)](https://github.com/EDCD/EDMarketConnector)
that lets you place and keep bookmarks on planetary surfaces. It records mining
spots, tritium rings, and scanned objects in a local database and, together with
the in-game overlay, guides you back to them while you are on the ground.

## What it does

- **Manual marks.** Click *Record Spot* to add a surface point by hand (with an
  optional "temporary" flag).
- **Automatic temporary marks.** When you scan something near the surface (ship
  or SRV composition scanner, or a `CodexEntry`/`Location` with coordinates),
  the plugin drops a short-lived bookmark so you can find your way back a few
  days later.
- **Automatic tritium rings.** `SAASignalsFound` scans are watched for tritium
  (He-3 fuel). Rings that contain tritium are recorded with a fuel-pump marker
  (⛽) in the notes column. Tritium is worth remembering on its own; other
  materials are not.
- **Rhino ore bookkeeping.** If you mine near a spot that is missing its
  mineral type, the plugin fills that in automatically once it detects Rhino
  activity.
- **In-game navigation.** Select a spot and press *Navigate To*. The overlay
  shows bearing and distance while you fly, and announces "Target Reached!"
  when you are close.
- **Galactic coordinates.** The current system's `x/y/z` and `systemid` are
  captured from journal events and written to the database.
- **Deduplication.** Scans inside the same area collapse into a single mark, so a
  settlement does not turn into a cloud of bookmarks.

## Status & planned features

This is a work in progress. The core loop — recording marks, automatic tritium
rings, temporary bookmarks, Rhino bookkeeping, and ground navigation — works, but
the build is not final.

The biggest gap is the database management UI. Planned queries include things
like **"find the nearest tritium ring"** or **"where did I mine yesterday"**,
which would turn the stored data into actionable answers instead of just a list.

## How it works

The plugin listens to EDMC journal/dashboard events through `journal_entry` and
`dashboard_entry`. For each event it:

1. Tracks the current system (`last_system`) — name, `systemid`, and galactic
   coordinates when the event provides them.
2. Extracts surface coordinates when available.
3. Dispatches the relevant handler (tritium ring, temporary mark, mining
   update, navigation).

Coordinates are only written to the database when they are actually known, so a
system you merely fly through is never created in the table. A repeat visit to a
system we have already marked back-fills the still-NULL coordinate columns.

## Data storage

All data is kept in a single SQLite database at:

```
surface_navigator/surface_navigator.db
```

The database uses two tables — `surface_spots` (your marks) and
`star_systems` (system name, coordinates, `systemid`). Temporary marks are
swept automatically at startup once they are older than 3 days.

## Installation

EDMC loads plugins from its `plugins` folder. To install this plugin:

1. Close EDMC.
2. Copy (or symlink) the `surface_navigator` folder into EDMC's `plugins`
   directory:

   ```bash
   # Copy
   cp -r surface_navigator ~/.config/EDMarketConnector/plugins/

   # …or symlink (keeps this repo as the source of truth)
   ln -s "$PWD/surface_navigator" ~/.config/EDMarketConnector/plugins/
   ```

3. Start EDMC. The plugin registers itself as **"Surface Navigator"** and its
   window appears under the plugins menu.

> The `*.db` files are git-ignored, so your data never lands in version control.

## Requirements

- Elite Dangerous Market Connector (EDMC).
- Python 3.10+ (developed against 3.14).
- Optional: an in-game overlay for the navigation display. The
  [EDMC Overlay for Linux/X11](https://github.com/alexzk1/edmcoverlay_for_linux)
  build is what this plugin targets; it also links to the original (older)
  Windows version. Without any overlay, navigation simply stays disabled.

## Development

Run the test suite (compiles the scripts, runs pyflakes, and runs pytest):

```bash
./validate_python_scripts
```

The tests live in `tests/` and cover the database layer, event handling, the
exclusion-zone suppression logic, and the note rendering used by the UI.

## License

See [LICENSE](LICENSE).

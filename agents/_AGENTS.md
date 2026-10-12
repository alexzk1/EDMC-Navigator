# Definition

This is plugin for Elite Dangerous Market Connector. See `PLUGINGS.md` for the details how it should be connected.

# Main purporse

Track, mark, and show direction back (on overlay, which is separated plugin assumed to be installed, see `overlay` folder) while player is near
planetary surface.

## Special case

Game has newhly added "Rhino SRV" which allows to do surface mining of different minerals. This is main purpose of using this plugin - establish persisten marks for spots 
and do a search over it.

## Abilities

Plugin should have the ways (button, key word in chat) to mark current position near the surface. Adding new methods is incremental process, we can start
with single UI button.

Once record is added user can enter more textual data (or it could be collected from log, if not entered) like "tritium spot".

Record contains:
- Star system name (present in game jounral).
- Planet / body index (name) (journal).
- Lat/Lon on this body (journal).

If we're making "special mining place record" (and just nice view to visit) we have more data:

- Spot number as seen on left panel (manually entered) - this is POI ingame target, absent in log. Navigation by pure coordinates is still possible but
using POI will limit to 10 km circle about.
- Mineral name / kind AT EXACT coordinate (spot may have different minerals at once).
- Mineral amount and density (in-game display, have no idea the meaning of it, manually entering).
- User provided spot configuration, i.e. how many miners user could place there 1+. This is geometrical task of placement, lets just trust what
user says, instead building map/gui/etc for this.
- Time of visit. This field must be updated whenever user was close to coordinates (like 500m) AND log has "extraction record". I.e. user actually
mined something. As spots are finite and has respawn time (days).

All data must be SQL and searchable in various proportions, like "where is closest fastest place to mine tritium".

## What logs have

Currently game logs provide positions, what vehicle is used. If Rhino mines, when it collects minerals we're getting standard mining record.
So if we have planet + Rhino + mining records -> we can assume those coordinates are mineral spot menitoned in mining records and we can auto populate fields.
Details can be provided once agent asks.


# Usage stories

## Story 1

User finds mining tritium spot. He marks the spot by button (probably "tritium" is auto taken from the logs).
Next, user flies to unload tritium and returns back to this planet to continue mining. He only could have "spot number" and target it at this stage and drop in spot,
so searching radius for him is ~10 km about again. Instead. he presses button in our  UI "navigate" and overlay shows direction where to go and distance to.

## Story 2
User wants to mine tonight and just check system "where can I mine Helium 3 or Tritium near my current location fast?".

# UI

It is TKinter there. It should be small,  place in main application is very limited. So it should be list (with scrollers and resize).
Probably. each raw there has 2 small buttons "edit" and "navigate to".

# Overlay

My version of the overlay supports direct SVG render, but others don't. There is method which allows to check. So it would be nice to have cool SVG
and automatically "simplified" version if other overlay was used.

# Coding

It is Python 3.14.7 here. I would preffer OOP way.

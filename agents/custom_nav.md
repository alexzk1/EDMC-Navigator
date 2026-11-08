# Task

Refactor / Update plugin to allow easy/fast manual ctrl+C/ctrl+V of the coordinates to navigate from Internet.

## Stage 1

Data base editor interface already prints lat/lon as string.
Extract do dedicated class / file with static methods, which will convert
1. string to lat/lon object (SurfacePoint, existing). Note, multiply strings formats will be expected, so this method will try them all.
2. lat/lon object (SurfacePoint) into string. Use single existing format (in DB editor GUI) only.

Note, this will be used by "default GUI" too, so place file convenient.

### Warning.
if currently there is such class ready, then this stage is done, and just use it later.

## Stage 2

1. Redesign main GUI (embedded widgets/frame), so it has text field to enter lat/lon from keyboard and/or ctrl+V.
   It should be visually pleasent, probably, it could be a cell between buttons and table which stretches for whole width.
2. Change `Navigate` button so it uses field entry (1) only.
   When navigation requested for manually entered lat/lon (not a click in table, i.e. selection is not None and selection[0].latlon != field.latlon)
   then create temporary DB record for 1 hour, with text like "manually navigated at hh::mm:ss".
3. Change in-table rows selection, so it puts  lat/lon into entry field from (1) (overwrite/replace anything there).
   Field must not be cleared when jump/enter/exit body etc. Just manual entry + replacement when table clicked/selected.

### Field formats.
Use class created at Stage 1 to parse value from  the field and to put values into the field when clicked table.
So that class is single source of the conversion.

### Additionaly.
Check if anything else does lat/lon <-> string and put in use class from Stage 1 instead.



## Stage 3
When all things are tested, we will want to update parser from Stage 1 to understand different string formats.

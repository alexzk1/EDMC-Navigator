
## Example of using "composition ship scanner".

The same object is scanned twice by "composition scanner".

```log
{ "timestamp":"2026-10-07T20:12:15Z", "event":"Music", "MusicTrack":"Exploration" }
{ "timestamp":"2026-10-07T20:13:19Z", "event":"CodexEntry", "EntryID":1400114, "Name":"$Codex_Ent_Fumarole_SilicateVapourGeysers_Name;", "Name_Localised":"Silicate Vapour Fumarole", "SubCategory":"$Codex_SubCategory_Geology_and_Anomalies;", "SubCategory_Localised":"Geology and anomalies", "Category":"$Codex_Category_Biology;", "Category_Localised":"Biological and Geological", "Region":"$Codex_RegionName_12;", "Region_Localised":"The Veils", "System":"Roefoo SJ-Q d5-0", "SystemAddress":14839274035, "BodyID":25, "Latitude":-7.567595, "Longitude":-139.327377, "IsNewEntry":true, "VoucherAmount":50000 }
{ "timestamp":"2026-10-07T20:13:35Z", "event":"CodexEntry", "EntryID":1400114, "Name":"$Codex_Ent_Fumarole_SilicateVapourGeysers_Name;", "Name_Localised":"Silicate Vapour Fumarole", "SubCategory":"$Codex_SubCategory_Geology_and_Anomalies;", "SubCategory_Localised":"Geology and anomalies", "Category":"$Codex_Category_Biology;", "Category_Localised":"Biological and Geological", "Region":"$Codex_RegionName_12;", "Region_Localised":"The Veils", "System":"Roefoo SJ-Q d5-0", "SystemAddress":14839274035, "BodyID":25, "Latitude":-7.567595, "Longitude":-139.327377 }
```

3rd scan of the same object when ship flew away for 100m about:
```log
{ "timestamp":"2026-10-07T20:15:52Z", "event":"CodexEntry", "EntryID":1400114, "Name":"$Codex_Ent_Fumarole_SilicateVapourGeysers_Name;", "Name_Localised":"Silicate Vapour Fumarole", "SubCategory":"$Codex_SubCategory_Geology_and_Anomalies;", "SubCategory_Localised":"Geology and anomalies", "Category":"$Codex_Category_Biology;", "Category_Localised":"Biological and Geological", "Region":"$Codex_RegionName_12;", "Region_Localised":"The Veils", "System":"Roefoo SJ-Q d5-0", "SystemAddress":14839274035, "BodyID":25, "Latitude":-7.571517, "Longitude":-139.309448 }
```

Conclusion: coordinates represent current ship / vehicle position.


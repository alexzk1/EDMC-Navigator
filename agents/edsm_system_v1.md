Get information about celestial bodies in a system

**HTTP Request:** `GET https://www.edsm.net/api-system-v1/bodies`

| Parameter | Default | Description |
| --- | --- | --- |
| **systemName**\\* | `NULL` | The system name |
| **systemId** | `NULL` | The system ID if you seek for a duplicate system and want to force a specific ID. |

**Output:**

{
    id      : 85920,
    name    : "HD 43193",
    bodies  : \[
        {
            id                              : 219074,
            name                            : "HD 43193 A",
            type                            : "Star",
            subType                         : "B (Blue-White) Star",
            distanceToArrival               : 0,
            isMainStar                      : true,
            isScoopable                     : true,
            age                             : 760,
            luminosity                      : "V",
            absoluteMagnitude               : 0.443283,
            solarMasses                     : 14.5625,
            solarRadius                     : 5.3612057397555715,
            surfaceTemperature              : 30995,
            orbitalPeriod                   : 277.5355324074074,
            semiMajorAxis                   : 0.4615586345240675,
            orbitalEccentricity             : 0.275417,
            orbitalInclination              : 73.390816,
            argOfPeriapsis                  : 23.460678,
            rotationalPeriod                : 2.2797341579861112,
            rotationalPeriodTidallyLocked   : false,
            axialTilt                       : 2.9
        },
        {
            id                              : 311417,
            name                            : "HD 43193 CD 7 a",
            type                            : "Planet",
            subType                         : "Class IV gas giant",
            distanceToArrival               : 17518,
            isLandable                      : false,
            gravity                         : 11.175634423255477,
            earthMasses                     : 1574.405762,
            radius                          : 75701.896,
            surfaceTemperature              : 1021,
            volcanismType                   : "No volcanism",
            atmosphereType                  : "No atmosphere",
            terraformingState               : "Not terraformable",
            orbitalPeriod                   : 55.31602430555556,
            semiMajorAxis                   : 0.11103302421536405,
            orbitalEccentricity             : null,
            orbitalInclination              : 28.739708,
            argOfPeriapsis                  : 248.851364,
            rotationalPeriod                : 57.64743634259259,
            rotationalPeriodTidallyLocked   : true,
            axialTilt                       : 5.7,
            rings: \[
                {
                    name            : "HD 43193 CD 7 a A Ring",
                    type            : "Rocky",
                    mass            : 355470000000,
                    innerRadius     : 124910,
                    outerRadius     : 169800
                },
                {
                    name            : "HD 43193 CD 7 a B Ring",
                    type            : "Rocky",
                    mass            : 4354700000000,
                    innerRadius     : 169900,
                    outerRadius     : 423250
                }
            \]
        }
    \]
}

| Parameter | Description |
| --- | --- |
| **type** | Main type of the celestial body. Can be `Star` or `Planet` |






# Anotehr API

Get information about a system

**HTTP Request:** `GET https://www.edsm.net/api-v1/system`

| Parameter | Default | Description |
| --- | --- | --- |
| **systemName**\\* | `NULL` | The system name |
|     |   |   |
|     |   |   |
| showId | `0` | Set to `1` to get our internal ID for this system. |
| showCoordinates | `0` | Set to `1` to get the system coordinates. If coordinates are unknown, the _coords_ key will not be returned. |
| showPermit | `0` | Set to `1` to get the system permit if there is one. If the permit is named, also return `permitName`. |
| showInformation | `0` | Set to `1` to get the system information like allegiance, government... If no information are stored, an empty array will be returned. |
| showPrimaryStar | `0` | Set to `1` to get the system primary star if known. If no primary star is stored, a `NULL` will be returned. |
|     |   |   |
| includeHidden | `0` | Set to `1` to get system even if hidden in the database. Hidden system are generally typo errors, renamed system in the game... |

**Output:**

{
    name            : "Merope",
    coords          : {
        x               : \-78.59375,
        y               : \-149.625,
        z               : \-340.53125
    },
    information     : {
        allegiance      : "Federation",
        government      : "Democracy",
        faction         : "Pleiades Resource Enterprise",
        factionState    : "Expansion",
        population      : 850000,
        security        : "Medium",
        economy         : "Industrial"
    },
    primaryStar     : {
        type            : "B (Blue-White) Star",
        name            : "Merope",
        isScoopable     : true
    }
}

| Parameter | Description |
| --- | --- |
| **name** | Name of the system. |
| **id** | Internal ID of the system. |
| **coords** | Array of coordinates if known. |
| **duplicates** | When requesting `showId`, return the systems ID having the exact same name in the game. |
|     |   |
| **requirePermit** | `true`/`false`. |
| **permitName** | Name of required permit, if not Unknown. |
| **information** | Array of information if known. - **allegiance** : The current allegiance of the system. - **government** : The current government of the system. - **faction** : The current faction of the system. - **population** : The current population of the system. |
| **primaryStar** | Array of information concerning the primary star of the system if known. - **type** : The type of the primary star. See our [Celestial bodies FAQ](https://www.edsm.net/en/faq/bodies) for a list of all types. - **name** : The name of the primary star. - **isScoopable** : `TRUE`/`FALSE` depending if the primary star type is scoopable for fuel. |
|     |   |
| **hidden\\_at** | When requesting `includeHidden`, return the `datetime` when the system was hidden. |
| **mergedTo** | When requesting `includeHidden` and `showId`, return the system ID where the system was renamed. Eg: **Eol Prou RS-T d3-94 \\[#5553159\\]** was renamed to **Colonia (Jaques Station) \\[#3384966\\]**. |

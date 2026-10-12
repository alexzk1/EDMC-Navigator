Dump of the system in the same format as the dump files available at https://spansh.co.uk/dumps
https://spansh.co.uk/dump/{id64}

    system
    Collapse allobject
        id64
        Collapse allinteger≥ 0

        ID64 of the system, a 64 bit unsigned integer.
        name
        Collapse allstring

        Name of the system.
        coords
        Collapse allobject

        Coordinates of the system.
            x
            Collapse allnumber

            X coordinate of the system.
            y
            Collapse allnumber

            Y coordinate of the system.
            z
            Collapse allnumber

            Z coordinate of the system.
        Additional propertiesforbidden
        allegiance
        Collapse allstring

        Allegiance of the system.
        Enum
        Collapse allarray
            #0null
            #1"Alliance"
            #2"Empire"
            #3"Federation"
            #4"Frontline Solutions"
            #5"Guardian"
            #6"Independent"
            #7"Pilots Federation"
            #8"Thargoid"
        government
        Collapse allstring

        Government type of the system.
        Enum
        Collapse allarray
            #0null
            #1"Anarchy"
            #2"Communism"
            #3"Confederacy"
            #4"Cooperative"
            #5"Corporate"
            #6"Democracy"
            #7"Dictatorship"
            #8"Engineer"
            #9"Feudal"
            #10"Megaconstruction"
            #11"None"
            #12"Patronage"
            #13"Prison"
            #14"Prison Colony"
            #15"Private Ownership"
            #16"Theocracy"
        primaryEconomy
        Collapse allstring

        Primary economy for the system.
        Enum
        Collapse allarray
            #0null
            #1"Agriculture"
            #2"Colony"
            #3"Extraction"
            #4"High Tech"
            #5"Industrial"
            #6"Military"
            #7"None"
            #8"Prison"
            #9"Private Enterprise"
            #10"Refinery"
            #11"Repair"
            #12"Rescue"
            #13"Service"
            #14"Terraforming"
            #15"Tourism"
        secondaryEconomy
        Collapse allstring

        Secondary economy for the system.
        Enum
        Collapse allarray
            #0null
            #1"Agriculture"
            #2"Colony"
            #3"Extraction"
            #4"High Tech"
            #5"Industrial"
            #6"Military"
            #7"None"
            #8"Prison"
            #9"Private Enterprise"
            #10"Refinery"
            #11"Repair"
            #12"Rescue"
            #13"Service"
            #14"Terraforming"
            #15"Tourism"
        security
        Collapse allstring

        Security rating of the system.
        Enum
        Collapse allarray
            #0"Anarchy"
            #1"High"
            #2"Low"
            #3"Medium"
        population
        Collapse allinteger≥ 0

        Population of the system.
        bodyCount
        Collapse allinteger≥ 0

        Total number of planets and stars in the system.
        date
        Collapse allstringdate-time

        Timestamp of the last update of the system, in UTC.
        bodies
        Collapse allarray<object>

        All bodies of the system.
        Items
        Collapse allobject
            id64
            Collapse allinteger≥ 0

            The ID64 of the body, a 64 bit unsigned integer.
            bodyId
            Collapse allinteger≥ 0

            The numeric ID of the body within the system, a 64 bit unsigned integer.
            name
            Collapse allstring

            The name of the body.
            orbitalPeriod
            Collapse allnumber

            The orbital period of the body, measured in days.
            semiMajorAxis
            Collapse allnumber

            The semi major axis of the body, measured in Kilometers.
            orbitalEccentricity
            Collapse allnumber[0, 1]

            The orbital eccentricity of the body.
            orbitalInclination
            Collapse allnumber

            The orbital inclinction of the body, measured in degrees.
            argOfPeriapsis
            Collapse allnumber[0, 360]

            The argument of periapsis the body, measured in degrees.
            meanAnomaly
            Collapse allnumber[0, 360]

            The mean of anomaly the body, measured in degrees.
            ascendingNode
            Collapse allnumber[-180, 180]

            The ascending node of the body, measured in degrees.
            timestamps
            Collapse allobject

            Timestamps of the last update of some of the fields within the body.
            Additional properties
            string
            stations
            Collapse allarray<object>

            Stations which are located on the body, planet based stations.
            Items
            Collapse allobject
                name
                Collapse allstring

                Name of the station
                id
                Collapse allinteger≥ 0

                Market ID of the station.
                updateTime
                Collapse allstringdate-time

                Timestamp of the last update of the station, in UTC.
                realName
                Collapse allstring

                Real name of the station, for colonisation stations.
                carrierName
                Collapse allstring

                Player given name of the station, for fleet carriers.
                controllingFaction
                Collapse allstring

                Controlling faction of the station.
                controllingFactionState
                Collapse allstring

                State of the controlling faction of the station.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                distanceToArrival
                Collapse allnumber≥ 0

                Distance to the system arrival point of the station, measured in Kilometres.
                primaryEconomy
                Collapse allstring

                Primary economy for the station.
                Enum
                Collapse allarray
                    #0null
                    #1"Agriculture"
                    #2"Colony"
                    #3"Extraction"
                    #4"High Tech"
                    #5"Industrial"
                    #6"Military"
                    #7"None"
                    #8"Prison"
                    #9"Private Enterprise"
                    #10"Refinery"
                    #11"Repair"
                    #12"Rescue"
                    #13"Service"
                    #14"Terraforming"
                    #15"Tourism"
                secondaryEconomy
                Collapse allstring

                Secondary economy for the station.
                Enum
                Collapse allarray
                    #0null
                    #1"Agriculture"
                    #2"Colony"
                    #3"Extraction"
                    #4"High Tech"
                    #5"Industrial"
                    #6"Military"
                    #7"None"
                    #8"Prison"
                    #9"Private Enterprise"
                    #10"Refinery"
                    #11"Repair"
                    #12"Rescue"
                    #13"Service"
                    #14"Terraforming"
                    #15"Tourism"
                economies
                Collapse allobject

                All econommies for the station, mapping each economy as a proportion of the stations economies.
                Additional properties
                number
                allegiance
                Collapse allstring

                Allegiance of the station.
                Enum
                Collapse allarray
                    #0null
                    #1"Alliance"
                    #2"Empire"
                    #3"Federation"
                    #4"Frontline Solutions"
                    #5"Guardian"
                    #6"Independent"
                    #7"Pilots Federation"
                    #8"Thargoid"
                government
                Collapse allstring

                Government type of the station.
                Enum
                Collapse allarray
                    #0null
                    #1"Anarchy"
                    #2"Communism"
                    #3"Confederacy"
                    #4"Cooperative"
                    #5"Corporate"
                    #6"Democracy"
                    #7"Dictatorship"
                    #8"Engineer"
                    #9"Feudal"
                    #10"Megaconstruction"
                    #11"None"
                    #12"Patronage"
                    #13"Prison"
                    #14"Prison Colony"
                    #15"Private Ownership"
                    #16"Theocracy"
                services
                Collapse allarray<string>

                Servies provided by the station.
                Items
                Collapse allstring
                Enum
                Collapse allarray
                    #0"Flight Controller"
                    #1"Station Operations"
                    #2"Dock"
                    #3"Autodock"
                    #4"Station Menu"
                    #5"Contacts"
                    #6"Refuel"
                    #7"Market"
                    #8"Repair"
                    #9"Workshop"
                    #10"Missions"
                    #11"Search and Rescue"
                    #12"Missions Generated"
                    #13"Restock"
                    #14"Social Space"
                    #15"Black Market"
                    #16"Interstellar Factors Contact"
                    #17"Powerplay"
                    #18"System Colonisation"
                    #19"Crew Lounge"
                    #20"Universal Cartographics"
                    #21"Outfitting"
                    #22"Livery"
                    #23"Construction Services"
                    #24"Shop"
                    #25"Bartender"
                    #26"Vista Genomics"
                    #27"Shipyard"
                    #28"Pioneer Supplies"
                    #29"Apex Interstellar"
                    #30"Tuning"
                    #31"Fleet Carrier Fuel"
                    #32"Fleet Carrier Management"
                    #33"Frontline Solutions"
                    #34"Refinery Contact"
                    #35"Redemption Office"
                    #36"Technology Broker"
                    #37"Material Trader"
                    #38"Squadron Bank"
                    #39"Fleet Carrier Administration"
                    #40"On Dock Mission"
                    #41"Fleet Carrier Vendor"
                type
                Collapse allstring

                Type of the station.
                Enum
                Collapse allarray
                    #0"Asteroid base"
                    #1"Coriolis Starport"
                    #2"Dockable Planet Station"
                    #3"Dodec Starport"
                    #4"Drake-Class Carrier"
                    #5"Mega ship"
                    #6"Ocellus Starport"
                    #7"Orbis Starport"
                    #8"Outpost"
                    #9"Planetary Construction Depot"
                    #10"Planetary Outpost"
                    #11"Planetary Port"
                    #12"Settlement"
                    #13"Space Construction Depot"
                    #14"Surface Settlement"
                state
                Collapse allstring

                State of the station.
                Enum
                Collapse allarray
                    #0"Construction"
                    #1"Damaged"
                    #2"DamagedHuman"
                    #3"UnderAttack"
                    #4"UnderRepairs"
                latitude
                Collapse allnumber

                Planetary stations only. Latitude of the station.
                longitude
                Collapse allnumber

                Planetary stations only. Longitude of the station.
                landingPads
                Collapse allobject

                Breakdown of the number of landing pads of the station.
                    large
                    Collapse allinteger≥ 0

                    Numer of large landing pads of the station.
                    medium
                    Collapse allinteger≥ 0

                    Numer of medium landing pads of the station.
                    small
                    Collapse allinteger≥ 0

                    Numer of small landing pads of the station.
                Additional propertiesforbidden
                carrierDockingAccess
                Collapse allstring

                Carrier only. Access control of the station.
                market
                Collapse allobject

                Commodity market information about the station.
                    commodities
                    Collapse allarray<object>

                    Commodities that can be bought and sold at about the station.
                    Items
                    Collapse allobject
                        name
                        Collapse allstring

                        Name of the commidity..
                        Enum
                        Collapse allarray
                            #0"AI Relics"
                            #1"Advanced Catalysers"
                            #2"Advanced Medicines"
                            #3"Aepyornis Egg"
                            #4"Aganippe Rush"
                            #5"Agri-Medicines"
                            #6"Agronomic Treatment"
                            #7"Alacarakmo Skin Art"
                            #8"Albino Quechua Mammoth Meat"
                            #9"Alexandrite"
                            #10"Algae"
                            #11"Altairian Skin"
                            #12"Aluminium"
                            #13"Alya Body Soap"
                            #14"Ancient Artefact"
                            #15"Ancient Key"
                            #16"Anduliga Fire Works"
                            #17"Animal Meat"
                            #18"Animal Monitors"
                            #19"Anomaly Particles"
                            #20"Antimatter Containment Unit"
                            #21"Antique Jewellery"
                            #22"Antiquities"
                            #23"Any Na Coffee"
                            #24"Apa Vietii"
                            #25"Aquaponic Systems"
                            #26"Arouca Conventual Sweets"
                            #27"Articulation Motors"
                            #28"Assault Plans"
                            #29"Atmospheric Processors"
                            #30"Auto-Fabricators"
                            #31"Az Cancri Formula 42"
                            #32"Azure Milk"
                            #33"Baked Greebles"
                            #34"Baltah'sine Vacuum Krill"
                            #35"Banki Amphibious Leather"
                            #36"Basic Medicines"
                            #37"Bast Snake Gin"
                            #38"Bastnasite"
                            #39"Battle Weapons"
                            #40"Bauxite"
                            #41"Beer"
                            #42"Belalans Ray Leather"
                            #43"Benitoite"
                            #44"Bertrandite"
                            #45"Beryllium"
                            #46"Bioreducing Lichen"
                            #47"Biowaste"
                            #48"Bismuth"
                            #49"Black Box"
                            #50"Bone Fragments"
                            #51"Bootleg Liquor"
                            #52"Borasetani Pathogenetics"
                            #53"Bromellite"
                            #54"Buckyball Beer Mats"
                            #55"Building Fabricators"
                            #56"Burnham Bile Distillate"
                            #57"CD-75 Kitten Brand Coffee"
                            #58"CMM Composite"
                            #59"Caustic Tissue Sample"
                            #60"Centauri Mega Gin"
                            #61"Ceramic Composites"
                            #62"Ceremonial Heike Tea"
                            #63"Ceti Rabbits"
                            #64"Chameleon Cloth"
                            #65"Chateau De Aegaeon"
                            #66"Chemical Waste"
                            #67"Cherbones Blood Crystals"
                            #68"Chi Eridani Marine Paste"
                            #69"Classified Experimental Equipment"
                            #70"Clothing"
                            #71"Cobalt"
                            #72"Coffee"
                            #73"Coltan"
                            #74"Combat Stabilisers"
                            #75"Commercial Samples"
                            #76"Computer Components"
                            #77"Conductive Fabrics"
                            #78"Consumer Technology"
                            #79"Copper"
                            #80"Coquim Spongiform Victuals"
                            #81"Coral Sap"
                            #82"Crom Silver Fesh"
                            #83"Crop Harvesters"
                            #84"Cryolite"
                            #85"Crystalline Spheres"
                            #86"Curated Commodity Package"
                            #87"Cyst Specimen"
                            #88"Damaged Escape Pod"
                            #89"Damna Carapaces"
                            #90"Data Core"
                            #91"Delta Phoenicis Palms"
                            #92"Deuringas Truffles"
                            #93"Deuterium"
                            #94"Diamond"
                            #95"Diplomatic Bag"
                            #96"Diso Ma Corn"
                            #97"Domestic Appliances"
                            #98"Duradrives"
                            #99"Earth Relics"
                            #100"Eden Apples of Aerial"
                            #101"Eleu Thermals"
                            #102"Emergency Power Cells"
                            #103"Encrypted Correspondence"
                            #104"Encrypted Data Storage"
                            #105"Energy Grid Assembly"
                            #106"Eranin Pearl Whisky"
                            #107"Eshu Umbrellas"
                            #108"Esuseku Caviar"
                            #109"Ethgreze Tea Buds"
                            #110"Evacuation Shelter"
                            #111"Exhaust Manifold"
                            #112"Experimental Chemicals"
                            #113"Explosives"
                            #114"Fish"
                            #115"Food Cartridges"
                            #116"Fossil Remnants"
                            #117"Fruit and Vegetables"
                            #118"Fujin Tea"
                            #119"Galactic Travel Guide"
                            #120"Gallite"
                            #121"Gallium"
                            #122"Geawen Dance Dust"
                            #123"Gene Bank"
                            #124"Geological Equipment"
                            #125"Geological Samples"
                            #126"Gerasian Gueuze Beer"
                            #127"Giant Irukama Snails"
                            #128"Giant Verrix"
                            #129"Gilya Signature Weapons"
                            #130"Gold"
                            #131"Goman Yaupon Coffee"
                            #132"Goslarite"
                            #133"Grain"
                            #134"Grandidierite"
                            #135"Guardian Casket"
                            #136"Guardian Orb"
                            #137"Guardian Relic"
                            #138"Guardian Tablet"
                            #139"Guardian Totem"
                            #140"Guardian Urn"
                            #141"H.E. Suits"
                            #142"HIP 10175 Bush Meat"
                            #143"HIP 118311 Swarm"
                            #144"HIP Organophosphates"
                            #145"HIP Proto-Squid"
                            #146"HN Shock Mount"
                            #147"HR 7221 Wheat"
                            #148"Haematite"
                            #149"Hafnium 178"
                            #150"Haiden Black Brew"
                            #151"Hardware Diagnostic Sensor"
                            #152"Harma Silver Sea Rum"
                            #153"Havasupai Dream Catcher"
                            #154"Heatsink Interlink"
                            #155"Helium"
                            #156"Helium-3"
                            #157"Helvetitj Pearls"
                            #158"Holva Duelling Blades"
                            #159"Honesty Pills"
                            #160"Hostages"
                            #161"Hydrogen Fuel"
                            #162"Hydrogen Peroxide"
                            #163"Imperial Slaves"
                            #164"Impure Spire Mineral"
                            #165"Indi Bourbon"
                            #166"Indite"
                            #167"Indium"
                            #168"Insulating Membrane"
                            #169"Ion Distributor"
                            #170"Iridium"
                            #171"Jadeite"
                            #172"Jaques Quinentian Still"
                            #173"Jaradharre Puzzle Box"
                            #174"Jaroua Rice"
                            #175"Jotun Mookah"
                            #176"Kachirigin Filter Leeches"
                            #177"Kamitra Cigars"
                            #178"Kamorin Historic Weapons"
                            #179"Karetii Couture"
                            #180"Karsuki Locusts"
                            #181"Kinago Violins"
                            #182"Kongga Ale"
                            #183"Koro Kung Pellets"
                            #184"LTT Hyper Sweet"
                            #185"Land Enrichment Systems"
                            #186"Landmines"
                            #187"Lanthanum"
                            #188"Large Survey Data Cache"
                            #189"Lavian Brandy"
                            #190"Leather"
                            #191"Leathery Eggs"
                            #192"Leestian Evil Juice"
                            #193"Lepidolite"
                            #194"Liquid oxygen"
                            #195"Liquor"
                            #196"Lithium Hydroxide"
                            #197"Lithium"
                            #198"Live Hecate Sea Worms"
                            #199"Low Temperature Diamonds"
                            #200"Lucan Onionhead"
                            #201"Lyrae Weed"
                            #202"Magnesite"
                            #203"Magnetic Emitter Coil"
                            #204"Marine Equipment"
                            #205"Master Chefs"
                            #206"Mechucos High Tea"
                            #207"Medb Starlube"
                            #208"Medical Diagnostic Equipment"
                            #209"Meta-Alloys"
                            #210"Methane Clathrate"
                            #211"Methanol Monohydrate Crystals"
                            #212"Micro Controllers"
                            #213"Micro-weave Cooling Hoses"
                            #214"Microbial Furnaces"
                            #215"Military Grade Fabrics"
                            #216"Military Intelligence"
                            #217"Military Plans"
                            #218"Mineral Extractors"
                            #219"Mineral Oil"
                            #220"Modular Terminals"
                            #221"Moissanite"
                            #222"Mokojing Beast Feast"
                            #223"Mollusc Brain Tissue"
                            #224"Mollusc Fluid"
                            #225"Mollusc Membrane"
                            #226"Mollusc Mycelium"
                            #227"Mollusc Soft Tissue"
                            #228"Mollusc Spores"
                            #229"Momus Bog Spaniel"
                            #230"Monazite"
                            #231"Motrona Experience Jelly"
                            #232"Mukusubii Chitin-os"
                            #233"Mulachi Giant Fungus"
                            #234"Muon Imager"
                            #235"Musgravite"
                            #236"Mysterious Idol"
                            #237"Nanobreakers"
                            #238"Nanomedicines"
                            #239"Narcotics"
                            #240"Natural Fabrics"
                            #241"Neofabric Insulation"
                            #242"Neritus Berries"
                            #243"Nerve Agents"
                            #244"Ngadandari Fire Opals"
                            #245"Nguna Modern Antiques"
                            #246"Njangari Saddles"
                            #247"Non Euclidian Exotanks"
                            #248"Non-Lethal Weapons"
                            #249"Occupied Escape Pod"
                            #250"Ochoeng Chillies"
                            #251"Olivine"
                            #252"Onionhead Alpha Strain"
                            #253"Onionhead Beta Strain"
                            #254"Onionhead Gamma Strain"
                            #255"Onionhead"
                            #256"Ophiuch Exino Artefacts"
                            #257"Organ Sample"
                            #258"Orrerian Vicious Brew"
                            #259"Osmium"
                            #260"Painite"
                            #261"Palladium"
                            #262"Pantaa Prayer Sticks"
                            #263"Pavonis Ear Grubs"
                            #264"Performance Enhancers"
                            #265"Periclase Dunite"
                            #266"Personal Effects"
                            #267"Personal Gifts"
                            #268"Personal Weapons"
                            #269"Pesticides"
                            #270"Platinum Alloy"
                            #271"Platinum"
                            #272"Pod Core Tissue"
                            #273"Pod Dead Tissue"
                            #274"Pod Mesoglea"
                            #275"Pod Outer Tissue"
                            #276"Pod Shell Tissue"
                            #277"Pod Surface Tissue"
                            #278"Pod Tissue"
                            #279"Political Prisoners"
                            #280"Polymers"
                            #281"Power Converter"
                            #282"Power Generators"
                            #283"Power Transfer Bus"
                            #284"Praseodymium"
                            #285"Precious Gems"
                            #286"Progenitor Cells"
                            #287"Prohibited Research Materials"
                            #288"Protective Membrane Scrap"
                            #289"Prototype Tech"
                            #290"Pyrophyllite"
                            #291"Quartz Pyroxenite"
                            #292"Radiation Baffle"
                            #293"Rajukru Multi-Stoves"
                            #294"Rapa Bao Snake Skins"
                            #295"Rare Artwork"
                            #296"Reactive Armour"
                            #297"Rebel Transmissions"
                            #298"Reinforced Mounting Plate"
                            #299"Resonating Separators"
                            #300"Rhodplumsite"
                            #301"Robotics"
                            #302"Rockforth Fertiliser"
                            #303"Ruby"
                            #304"Rusani Old Smokey"
                            #305"Rutile"
                            #306"SAP 8 Core Container"
                            #307"Samarium"
                            #308"Sanuma Decorative Meat"
                            #309"Sapphire"
                            #310"Saxon Wine"
                            #311"Scientific Research"
                            #312"Scientific Samples"
                            #313"Scrap"
                            #314"Semi-Refined Spire Mineral"
                            #315"Semiconductors"
                            #316"Serendibite"
                            #317"Shan's Charis Orchid"
                            #318"Silver"
                            #319"Skimmer Components"
                            #320"Slaves"
                            #321"Small Survey Data Cache"
                            #322"Soontill Relics"
                            #323"Sothis Crystalline Gold"
                            #324"Space Pioneer Relics"
                            #325"Steel"
                            #326"Structural Regulators"
                            #327"Superconductors"
                            #328"Surface Stabilisers"
                            #329"Survival Equipment"
                            #330"Synthetic Fabrics"
                            #331"Synthetic Meat"
                            #332"Synthetic Reagents"
                            #333"Taaffeite"
                            #334"Tactical Data"
                            #335"Tanmark Tranquil Tea"
                            #336"Tantalum"
                            #337"Tarach Spice"
                            #338"Tauri Chimes"
                            #339"Tea"
                            #340"Technical Blueprints"
                            #341"Telemetry Suite"
                            #342"Terra Mater Blood Bores"
                            #343"Thallium"
                            #344"Thargoid Basilisk Tissue Sample"
                            #345"Thargoid Biological Matter"
                            #346"Thargoid Cyclops Tissue Sample"
                            #347"Thargoid Glaive Tissue Sample"
                            #348"Thargoid Heart"
                            #349"Thargoid Hydra Tissue Sample"
                            #350"Thargoid Link"
                            #351"Thargoid Medusa Tissue Sample"
                            #352"Thargoid Orthrus Tissue Sample"
                            #353"Thargoid Probe"
                            #354"Thargoid Resin"
                            #355"Thargoid Scout Tissue Sample"
                            #356"Thargoid Scythe Tissue Sample"
                            #357"Thargoid Sensor"
                            #358"Thargoid Technology Samples"
                            #359"The Hutton Mug"
                            #360"The Waters of Shintara"
                            #361"Thermal Cooling Units"
                            #362"Thorium"
                            #363"Thortveitite"
                            #364"Thrutis Cream"
                            #365"Tiegfries Synth Silk"
                            #366"Time Capsule"
                            #367"Tiolce Waste2Paste Units"
                            #368"Titan Deep Tissue Sample"
                            #369"Titan Drive Component"
                            #370"Titan Maw Deep Tissue Sample"
                            #371"Titan Maw Partial Tissue Sample"
                            #372"Titan Maw Tissue Sample"
                            #373"Titan Partial Tissue Sample"
                            #374"Titan Tissue Sample"
                            #375"Titanium"
                            #376"Tobacco"
                            #377"Toxandji Virocide"
                            #378"Toxic Waste"
                            #379"Trade Data"
                            #380"Trinkets of Hidden Fortune"
                            #381"Tritium"
                            #382"Ultra-Compact Processor Prototypes"
                            #383"Unclassified Relic"
                            #384"Unoccupied Escape Pod"
                            #385"Unstable Data Core"
                            #386"Uraninite"
                            #387"Uranium"
                            #388"Uszaian Tree Grub"
                            #389"Utgaroar Millennial Eggs"
                            #390"Uzumoku Low-G Wings"
                            #391"V Herculis Body Rub"
                            #392"Vanayequi Ceratomorpha Fur"
                            #393"Vega Slimweed"
                            #394"Vidavantian Lace"
                            #395"Void Extract Coffee"
                            #396"Void Opal"
                            #397"Volkhab Bee Drones"
                            #398"Water Purifiers"
                            #399"Water"
                            #400"Wheemete Wheat Cakes"
                            #401"Wine"
                            #402"Witchhaul Kobe Beef"
                            #403"Wolf Fesh"
                            #404"Wreckage Components"
                            #405"Wulpa Hyperbore Systems"
                            #406"Wuthielo Ku Froth"
                            #407"Xenobiological Prison Pod"
                            #408"Xihe Biomorphic Companions"
                            #409"Yaso Kondi Leaf"
                            #410"Zeessze Ant Grub Glue"
                        symbol
                        Collapse allstring

                        Frontier symbol identifier of the commodity.
                        category
                        Collapse allstring

                        Category of the commodity.
                        Enum
                        Collapse allarray
                            #0"Chemicals"
                            #1"Consumer Items"
                            #2"Foods"
                            #3"Industrial Materials"
                            #4"Legal Drugs"
                            #5"Machinery"
                            #6"Medicines"
                            #7"Metals"
                            #8"Minerals"
                            #9"Salvage"
                            #10"Slavery"
                            #11"Technology"
                            #12"Textiles"
                            #13"Waste"
                            #14"Weapons"
                        commodityId
                        Collapse allinteger

                        Frontier numeric identifier of the commodity.
                        demand
                        Collapse allinteger≥ 0

                        Demand for the commodity.
                        supply
                        Collapse allinteger≥ 0

                        Supply for the commodity.
                        buyPrice
                        Collapse allinteger≥ 0

                        Price the player can buy the commodity for.
                        sellPrice
                        Collapse allinteger≥ 0

                        Price the player can sell the commodity for.
                    Additional propertiesforbidden
                    prohibitedCommodities
                    Collapse allarray<string>

                    Commodities that are illegal on the station.
                    Items
                    string
                    updateTime
                    Collapse allstringdate-time

                    Timestamp of the last update of the marketplace for the station, in UTC.
                Additional propertiesforbidden
                shipyard
                Collapse allobject

                Shipyard information about the station.
                    ships
                    Collapse allarray<object>

                    Ships that can be bought at the station.
                    Items
                    Collapse allobject
                        name
                        Collapse allstring

                        Ship restrictions for the module.
                        Enum
                        Collapse allarray
                            #0"Adder"
                            #1"Alliance Challenger"
                            #2"Alliance Chieftain"
                            #3"Alliance Crusader"
                            #4"Anaconda"
                            #5"Asp Explorer"
                            #6"Asp Scout"
                            #7"Beluga Liner"
                            #8"Caspian Explorer"
                            #9"Cobra MkIII"
                            #10"Cobra MkIV"
                            #11"Cobra MkV"
                            #12"Corsair"
                            #13"Diamondback Explorer"
                            #14"Diamondback Scout"
                            #15"Dolphin"
                            #16"Eagle"
                            #17"Federal Assault Ship"
                            #18"Federal Corvette"
                            #19"Federal Dropship"
                            #20"Federal Gunship"
                            #21"Fer-de-Lance"
                            #22"Hauler"
                            #23"Imperial Clipper"
                            #24"Imperial Courier"
                            #25"Imperial Cutter"
                            #26"Imperial Eagle"
                            #27"Keelback"
                            #28"Kestrel Mk II"
                            #29"Krait MkII"
                            #30"Krait Phantom"
                            #31"Lynx Highliner"
                            #32"Mamba"
                            #33"Mandalay"
                            #34"Orca"
                            #35"Panther Clipper MkII"
                            #36"Python"
                            #37"Python MkII"
                            #38"Sidewinder"
                            #39"Type-10 Defender"
                            #40"Type-11 Prospector"
                            #41"Type-6 Transporter"
                            #42"Type-7 Transporter"
                            #43"Type-8 Transporter"
                            #44"Type-9 Heavy"
                            #45"Viper MkIII"
                            #46"Viper MkIV"
                            #47"Vulture"
                        symbol
                        Collapse allstring

                        Frontier symbol identifier of the ship.
                        shipId
                        Collapse allnumber

                        Frontier numeric identifier of the ship.
                    Additional propertiesforbidden
                    updateTime
                    Collapse allstringdate-time

                    Timestamp of the last update of the shipyard for the station, in UTC.
                Additional propertiesforbidden
                outfitting
                Collapse allobject

                Outfitting information about the station.
                    modules
                    Collapse allarray<object>

                    Outfitting modules that can be bought at the station.
                    Items
                    Collapse allobject
                        name
                        Collapse allstring

                        Name of the module.
                        Enum
                        Collapse allarray
                            #0"AX Missile Rack"
                            #1"AX Multi-Cannon"
                            #2"Abrasion Blaster"
                            #3"Advanced Docking Computer"
                            #4"Advanced Discovery Scanner"
                            #5"Advanced Missile Rack"
                            #6"Advanced Multi-Cannon"
                            #7"Advanced Planetary Approach Suite"
                            #8"Advanced Plasma Accelerator"
                            #9"Auto Field-Maintenance Unit"
                            #10"Balanced Power Distributor"
                            #11"Basic Discovery Scanner"
                            #12"Beam Laser"
                            #13"Bi-Weave Shield Generator"
                            #14"Burst Laser"
                            #15"Business Class Passenger Cabin"
                            #16"Cannon"
                            #17"Cargo Rack"
                            #18"Cargo Scanner"
                            #19"Caustic Sink Launcher"
                            #20"Chaff Launcher"
                            #21"Collector Limpet Controller"
                            #22"Concord Cannon"
                            #23"Corrosion Resistant Cargo Rack"
                            #24"Cytoscrambler Burst Laser"
                            #25"Decontamination Limpet Controller"
                            #26"Detailed Surface Scanner"
                            #27"Double Screaming Fragment Cannon"
                            #28"Economy Class Passenger Cabin"
                            #29"Electronic Countermeasure"
                            #30"Enduring Feedback Rail Gun"
                            #31"Enforcer Cannon"
                            #32"Enhanced AX Missile Rack"
                            #33"Enhanced AX Multi-Cannon"
                            #34"Enhanced Performance Thrusters"
                            #35"Enhanced Xeno Scanner"
                            #36"Enzyme Missile Rack"
                            #37"Experimental Weapon Stabiliser"
                            #38"Exposing Missiles"
                            #39"Extended Cargo Rack"
                            #40"Far-Reaching Abrasion Blaster"
                            #41"Fighter Hangar"
                            #42"First Class Passenger Cabin"
                            #43"Force Impact Cannon"
                            #44"Fragment Cannon"
                            #45"Frame Shift Drive (SCO)"
                            #46"Frame Shift Drive Interdictor"
                            #47"Frame Shift Drive"
                            #48"Frame Shift Wake Scanner"
                            #49"Fuel Scoop"
                            #50"Fuel Tank"
                            #51"Fuel Transfer Limpet Controller"
                            #52"Guardian FSD Booster"
                            #53"Guardian Gauss Cannon"
                            #54"Guardian Hull Reinforcement"
                            #55"Guardian Hybrid Power Distributor"
                            #56"Guardian Hybrid Power Plant"
                            #57"Guardian Module Reinforcement"
                            #58"Guardian Nanite Torpedo Pylon"
                            #59"Guardian Plasma Charger"
                            #60"Guardian Shard Cannon"
                            #61"Guardian Shield Reinforcement"
                            #62"Hatch Breaker Limpet Controller"
                            #63"Heat Sink Launcher"
                            #64"Heavy Duty Module Reinforcement Package"
                            #65"High-Yield Enzyme Missile Rack"
                            #66"Hull Reinforcement Package"
                            #67"Imperial Hammer Rail Gun"
                            #68"Intermediate Discovery Scanner"
                            #69"Kill Warrant Scanner"
                            #70"Large Planetary Vehicle Hangar"
                            #71"Life Support"
                            #72"Lightweight Alloy"
                            #73"Lockdown Seeker Missile Rack"
                            #74"Long Range Detailed Surface Scanner"
                            #75"Long Range Mining Laser"
                            #76"Luxury Class Passenger Cabin"
                            #77"Meta Alloy Hull Reinforcement"
                            #78"Military Grade Composite"
                            #79"Mine Launcher"
                            #80"Mining Lance"
                            #81"Mining Laser"
                            #82"Mining Multi Limpet Controller"
                            #83"Mining Volley Repeater"
                            #84"Mirrored Surface Composite"
                            #85"Missile Rack"
                            #86"Mk II Ablative Lightweight Alloys"
                            #87"Mk II Ablative Military Grade Composite"
                            #88"Mk II Ablative Mirrored Surface Composite"
                            #89"Mk II Ablative Reactive Surface Composite"
                            #90"Mk II Ablative Reinforced Alloys"
                            #91"Mk II Agile Boost Thrusters"
                            #92"Mk II Business Class Passenger Cabin"
                            #93"Mk II Cargo Rack"
                            #94"Mk II Economy Class Passenger Cabin"
                            #95"Mk II Gravity Optimised Thrusters"
                            #96"Mk II Large Planetary Vehicle Hangar"
                            #97"Mk II Mining Multi-Limpet Controller"
                            #98"Mk II Plasma Shock Accelerator"
                            #99"Mk II Supercharge Optimised Frame Shift Drive (SCO)"
                            #100"Mk II Vessel Hangar"
                            #101"MkII Business Class Passenger Cabin"
                            #102"MkII Economy Class Passenger Cabin"
                            #103"Module Reinforcement Package"
                            #104"Multi-Cannon"
                            #105"Operations Multi Limpet Controller"
                            #106"Overloaded Beam Laser"
                            #107"Pacifier Frag-Cannon"
                            #108"Pack-Hound Missile Rack"
                            #109"Planetary Approach Suite"
                            #110"Planetary Vehicle Hangar"
                            #111"Plasma Accelerator"
                            #112"Point Defence"
                            #113"Power Distributor"
                            #114"Power Plant"
                            #115"Prismatic Shield Generator"
                            #116"Prospector Limpet Controller"
                            #117"Pulse Disruptor Laser"
                            #118"Pulse Laser"
                            #119"Pulse Wave Analyser"
                            #120"Pulse Wave Xeno Scanner"
                            #121"Rail Gun"
                            #122"Rapid Phase Multi-Cannon"
                            #123"Reactive Surface Composite"
                            #124"Recon Limpet Controller"
                            #125"Refinery"
                            #126"Regenerative Burst Laser"
                            #127"Reinforced Alloy"
                            #128"Remote Release Flak Launcher"
                            #129"Remote Release Flechette Launcher"
                            #130"Repair Limpet Controller"
                            #131"Rescue Multi Limpet Controller"
                            #132"Research Limpet Controller"
                            #133"Retributor Beam Laser"
                            #134"Rocket Propelled FSD Disruptor"
                            #135"Seeker Missile Rack"
                            #136"Seismic Charge Launcher"
                            #137"Sensors"
                            #138"Shield Booster"
                            #139"Shield Cell Bank"
                            #140"Shield Generator"
                            #141"Shock Cannon"
                            #142"Shock Mine Launcher"
                            #143"Shutdown Field Neutraliser"
                            #144"Standard Docking Computer"
                            #145"Sub-Surface Displacement Missile"
                            #146"Sub-Surface Extraction Missile"
                            #147"Supercruise Assist"
                            #148"Support Focused Power Distributor"
                            #149"Thargoid Pulse Neutraliser"
                            #150"Thrusters"
                            #151"Torpedo Pylon"
                            #152"Universal Multi Limpet Controller"
                            #153"Vessel Hangar"
                            #154"Xeno Multi Limpet Controller"
                            #155"Xeno Scanner"
                        symbol
                        Collapse allstring

                        Frontier symbol identifier of the module.
                        moduleId
                        Collapse allnumber

                        Frontier numeric identifier of the module.
                        class
                        Collapse allinteger

                        Class of the module.
                        Enum
                        Collapse allarray
                            #01
                            #13
                            #22
                            #35
                            #44
                            #57
                            #66
                            #78
                            #80
                        rating
                        Collapse allstring

                        Rating of the module.
                        Enum
                        Collapse allarray
                            #0"E"
                            #1"D"
                            #2"C"
                            #3"I"
                            #4"B"
                            #5"A"
                            #6"F"
                            #7"G"
                            #8"H"
                        category
                        Collapse allstring

                        Category of the module.
                        Enum
                        Collapse allarray
                            #0"hardpoint"
                            #1"internal"
                            #2"utility"
                            #3"standard"
                            #4"mercgear"
                        ship
                        Collapse all(string | null)

                        Ship restrictions for the module.
                        One of
                        Collapse all(string | null)
                            #0
                            Collapse allstring

                            Ship restrictions for the module.
                            Enum
                            Collapse allarray
                                #0"Adder"
                                #1"Alliance Challenger"
                                #2"Alliance Chieftain"
                                #3"Alliance Crusader"
                                #4"Anaconda"
                                #5"Asp Explorer"
                                #6"Asp Scout"
                                #7"Beluga Liner"
                                #8"Caspian Explorer"
                                #9"Cobra MkIII"
                                #10"Cobra MkIV"
                                #11"Cobra MkV"
                                #12"Corsair"
                                #13"Diamondback Explorer"
                                #14"Diamondback Scout"
                                #15"Dolphin"
                                #16"Eagle"
                                #17"Federal Assault Ship"
                                #18"Federal Corvette"
                                #19"Federal Dropship"
                                #20"Federal Gunship"
                                #21"Fer-de-Lance"
                                #22"Hauler"
                                #23"Imperial Clipper"
                                #24"Imperial Courier"
                                #25"Imperial Cutter"
                                #26"Imperial Eagle"
                                #27"Keelback"
                                #28"Kestrel Mk II"
                                #29"Krait MkII"
                                #30"Krait Phantom"
                                #31"Lynx Highliner"
                                #32"Mamba"
                                #33"Mandalay"
                                #34"Orca"
                                #35"Panther Clipper MkII"
                                #36"Python"
                                #37"Python MkII"
                                #38"Sidewinder"
                                #39"Type-10 Defender"
                                #40"Type-11 Prospector"
                                #41"Type-6 Transporter"
                                #42"Type-7 Transporter"
                                #43"Type-8 Transporter"
                                #44"Type-9 Heavy"
                                #45"Viper MkIII"
                                #46"Viper MkIV"
                                #47"Vulture"
                            #1
                            null
                    Additional propertiesforbidden
                    updateTime
                    Collapse allstringdate-time

                    Timestamp of the last update of the outfitting for the station, in UTC.
                Additional propertiesforbidden
            Additional propertiesforbidden
            updateTime
            Collapse allstring

            Timestamp of the last update of the body, in UTC.
            type
            Collapse allstring

            The type of the body.
            Enum
            Collapse allarray
                #0"Planet"
                #1"Star"
                #2"Barycentre"
            subType
            Collapse all(string | string)

            Subtype of the body.
            Any of
            Collapse all(string | string)
                #0
                Collapse allstring

                Subtype of the bodyi of type Planet.
                Enum
                Collapse allarray
                    #0"Ammonia world"
                    #1"Class I gas giant"
                    #2"Class II gas giant"
                    #3"Class III gas giant"
                    #4"Class IV gas giant"
                    #5"Class V gas giant"
                    #6"Earth-like world"
                    #7"Gas giant with ammonia-based life"
                    #8"Gas giant with water-based life"
                    #9"Helium gas giant"
                    #10"Helium-rich gas giant"
                    #11"High metal content world"
                    #12"Icy body"
                    #13"Metal-rich body"
                    #14"Rocky Ice world"
                    #15"Rocky body"
                    #16"Water giant"
                    #17"Water world"
                #1
                Collapse allstring

                Subtype of the body of type Star.
                Enum
                Collapse allarray
                    #0"A (Blue-White super giant) Star"
                    #1"A (Blue-White) Star"
                    #2"B (Blue-White super giant) Star"
                    #3"B (Blue-White) Star"
                    #4"Black Hole"
                    #5"C Star"
                    #6"CJ Star"
                    #7"CN Star"
                    #8"F (White super giant) Star"
                    #9"F (White) Star"
                    #10"G (White-Yellow super giant) Star"
                    #11"G (White-Yellow) Star"
                    #12"Herbig Ae/Be Star"
                    #13"K (Yellow-Orange giant) Star"
                    #14"K (Yellow-Orange) Star"
                    #15"L (Brown dwarf) Star"
                    #16"M (Red dwarf) Star"
                    #17"M (Red giant) Star"
                    #18"M (Red super giant) Star"
                    #19"MS-type Star"
                    #20"Neutron Star"
                    #21"O (Blue-White) Star"
                    #22"S-type Star"
                    #23"Supermassive Black Hole"
                    #24"T (Brown dwarf) Star"
                    #25"T Tauri Star"
                    #26"White Dwarf (D) Star"
                    #27"White Dwarf (DA) Star"
                    #28"White Dwarf (DAB) Star"
                    #29"White Dwarf (DAV) Star"
                    #30"White Dwarf (DAZ) Star"
                    #31"White Dwarf (DB) Star"
                    #32"White Dwarf (DBV) Star"
                    #33"White Dwarf (DBZ) Star"
                    #34"White Dwarf (DC) Star"
                    #35"White Dwarf (DCV) Star"
                    #36"White Dwarf (DQ) Star"
                    #37"Wolf-Rayet C Star"
                    #38"Wolf-Rayet N Star"
                    #39"Wolf-Rayet NC Star"
                    #40"Wolf-Rayet O Star"
                    #41"Wolf-Rayet Star"
                    #42"Y (Brown dwarf) Star"
            distanceToArrival
            Collapse allnumber≥ 0

            Distance to the system arrival point of the body, measured in Kilometres.
            mainStar
            Collapse allboolean

            Stars only. Whether this is the main star of the system or not.
            age
            Collapse allinteger≥ 0

            Stars only. The age of the star, measured in solar years.
            spectralClass
            Collapse allstring

            Stars only. Spectral class of the star.
            Enum
            Collapse allarray
                #0null
                #1"A"
                #2"A0"
                #3"A1"
                #4"A2"
                #5"A3"
                #6"A4"
                #7"A5"
                #8"A6"
                #9"A7"
                #10"A8"
                #11"A9"
                #12"AeBe0"
                #13"AeBe1"
                #14"AeBe2"
                #15"AeBe3"
                #16"AeBe4"
                #17"AeBe5"
                #18"AeBe6"
                #19"AeBe7"
                #20"AeBe8"
                #21"AeBe9"
                #22"B"
                #23"B0"
                #24"B1"
                #25"B2"
                #26"B3"
                #27"B4"
                #28"B5"
                #29"B6"
                #30"B7"
                #31"B8"
                #32"B9"
                #33"C0"
                #34"C1"
                #35"C2"
                #36"C3"
                #37"C4"
                #38"C5"
                #39"C6"
                #40"C7"
                #41"C8"
                #42"C9"
                #43"CJ4"
                #44"CJ5"
                #45"CJ6"
                #46"CN4"
                #47"CN5"
                #48"CN6"
                #49"D5"
                #50"D6"
                #51"D7"
                #52"DA0"
                #53"DA1"
                #54"DA2"
                #55"DA3"
                #56"DA4"
                #57"DA5"
                #58"DA6"
                #59"DA7"
                #60"DA8"
                #61"DA9"
                #62"DAB0"
                #63"DAV0"
                #64"DAZ0"
                #65"DAZ5"
                #66"DAZ6"
                #67"DAZ7"
                #68"DAZ8"
                #69"DAZ9"
                #70"DB0"
                #71"DBV0"
                #72"DBZ0"
                #73"DC0"
                #74"DC1"
                #75"DC5"
                #76"DC7"
                #77"DC8"
                #78"DC9"
                #79"DCV0"
                #80"DQ1"
                #81"DQ4"
                #82"DQ5"
                #83"DQ6"
                #84"DQ7"
                #85"DQ8"
                #86"DQ9"
                #87"F"
                #88"F0"
                #89"F1"
                #90"F2"
                #91"F3"
                #92"F4"
                #93"F5"
                #94"F6"
                #95"F7"
                #96"F8"
                #97"F9"
                #98"G"
                #99"G0"
                #100"G1"
                #101"G2"
                #102"G3"
                #103"G4"
                #104"G5"
                #105"G6"
                #106"G7"
                #107"G8"
                #108"G9"
                #109"H0"
                #110"H5"
                #111"K"
                #112"K0"
                #113"K1"
                #114"K2"
                #115"K3"
                #116"K4"
                #117"K5"
                #118"K6"
                #119"K7"
                #120"K8"
                #121"K9"
                #122"L"
                #123"L0"
                #124"L1"
                #125"L2"
                #126"L3"
                #127"L4"
                #128"L5"
                #129"L6"
                #130"L7"
                #131"L8"
                #132"L9"
                #133"M"
                #134"M0"
                #135"M1"
                #136"M2"
                #137"M3"
                #138"M4"
                #139"M5"
                #140"M6"
                #141"M7"
                #142"M8"
                #143"M9"
                #144"MS0"
                #145"MS1"
                #146"MS2"
                #147"MS3"
                #148"MS4"
                #149"MS5"
                #150"MS6"
                #151"N0"
                #152"N3"
                #153"N5"
                #154"O"
                #155"O0"
                #156"O1"
                #157"O2"
                #158"O3"
                #159"O4"
                #160"O5"
                #161"O6"
                #162"O7"
                #163"O8"
                #164"O9"
                #165"S0"
                #166"S1"
                #167"S2"
                #168"S3"
                #169"S4"
                #170"S5"
                #171"S6"
                #172"S7"
                #173"T"
                #174"T0"
                #175"T1"
                #176"T2"
                #177"T3"
                #178"T4"
                #179"T5"
                #180"T6"
                #181"T7"
                #182"T8"
                #183"T9"
                #184"TTS0"
                #185"TTS1"
                #186"TTS2"
                #187"TTS3"
                #188"TTS4"
                #189"TTS5"
                #190"TTS6"
                #191"TTS7"
                #192"TTS8"
                #193"TTS9"
                #194"W1"
                #195"W2"
                #196"W3"
                #197"W4"
                #198"W5"
                #199"W6"
                #200"W7"
                #201"W8"
                #202"W9"
                #203"WC0"
                #204"WC2"
                #205"WC5"
                #206"WC6"
                #207"WN0"
                #208"WN3"
                #209"WN5"
                #210"WNC0"
                #211"WO0"
                #212"Y0"
                #213"Y1"
                #214"Y2"
                #215"Y3"
                #216"Y4"
                #217"Y5"
                #218"Y6"
                #219"Y9"
            luminosity
            Collapse allstring

            Stars only. Luminosity of the star.
            Enum
            Collapse allarray
                #0"I"
                #1"II"
                #2"III"
                #3"IIIa"
                #4"IIIab"
                #5"IIIb"
                #6"IIa"
                #7"IIab"
                #8"IIb"
                #9"IV"
                #10"IVa"
                #11"IVab"
                #12"IVb"
                #13"Ia"
                #14"Ia0"
                #15"Iab"
                #16"Ib"
                #17"O"
                #18"V"
                #19"VI"
                #20"VII"
                #21"Va"
                #22"Vab"
                #23"Vb"
                #24"Vz"
            absoluteMagnitude
            Collapse allnumber

            Stars only. Absolute magnitude of the star.
            solarMasses
            Collapse allnumber≥ 0

            Stars only. Mass of the star, as a ratio of the mass of Sol.
            solarRadius
            Collapse allnumber≥ 0

            Stars only. Radius of the star, as a ratio of the radius of Sol.
            surfaceTemperature
            Collapse allnumber≥ 0

            Surface temperature of the body, measured in Kelvin.
            rotationalPeriod
            Collapse allnumber

            Rotational period of the body, measured in Days.
            rotationalPeriodTidallyLocked
            Collapse allboolean

            Whether the rotational period of the body is locked to the tides.
            axialTilt
            Collapse allnumber

            Axial tilt of the body, measured in radians.
            parents
            Collapse allarray<object>

            Parents of the body, mapping each parent body type to it's ID within the system.
            Items
            Collapse allobject
            Additional properties
            number
            isLandable
            Collapse allboolean

            Planets only. Whether the planet is landable or not.
            gravity
            Collapse allnumber≥ 0

            Planets only. Gravity of the planet, as a ratio of the gravity of Earth.
            earthMasses
            Collapse allnumber≥ 0

            Planets only. Mass of the planet, as a ratio of the mass of Earth.
            radius
            Collapse allnumber≥ 0

            Planets only. Radius of the planet, measured in Kilimetres.
            surfacePressure
            Collapse allnumber≥ 0

            Planets only. Surface pressure of the planet, measured in atmospheres.
            volcanismType
            Collapse allstring

            Planets only. Volcanism type of the planet.
            Enum
            Collapse allarray
                #0"Carbon Dioxide Geysers"
                #1"Major Carbon Dioxide Geysers"
                #2"Major Metallic Magma"
                #3"Major Rocky Magma"
                #4"Major Silicate Vapour Geysers"
                #5"Major Water Geysers"
                #6"Major Water Magma"
                #7"Metallic Magma"
                #8"Minor Ammonia Magma"
                #9"Minor Carbon Dioxide Geysers"
                #10"Minor Metallic Magma"
                #11"Minor Methane Magma"
                #12"Minor Nitrogen Magma"
                #13"Minor Rocky Magma"
                #14"Minor Silicate Vapour Geysers"
                #15"Minor Water Geysers"
                #16"Minor Water Magma"
                #17"No volcanism"
                #18"Rocky Magma"
                #19"Silicate Vapour Geysers"
                #20"Water Geysers"
                #21"Water Magma"
            atmosphereType
            Collapse allstring

            Planets only. Atmosphere type of the planet.
            Enum
            Collapse allarray
                #0null
                #1"Ammonia"
                #2"Ammonia and Oxygen"
                #3"Ammonia-rich"
                #4"Argon"
                #5"Argon-rich"
                #6"Carbon dioxide"
                #7"Carbon dioxide-rich"
                #8"Helium"
                #9"Hot Argon"
                #10"Hot Argon-rich"
                #11"Hot Carbon dioxide"
                #12"Hot Carbon dioxide-rich"
                #13"Hot Metallic vapour"
                #14"Hot Silicate vapour"
                #15"Hot Sulphur dioxide"
                #16"Hot Water"
                #17"Hot Water-rich"
                #18"Hot thick Ammonia"
                #19"Hot thick Ammonia-rich"
                #20"Hot thick Argon"
                #21"Hot thick Argon-rich"
                #22"Hot thick Carbon dioxide"
                #23"Hot thick Carbon dioxide-rich"
                #24"Hot thick Metallic vapour"
                #25"Hot thick Methane"
                #26"Hot thick Methane-rich"
                #27"Hot thick Nitrogen"
                #28"Hot thick Silicate vapour"
                #29"Hot thick Sulphur dioxide"
                #30"Hot thick Water"
                #31"Hot thick Water-rich"
                #32"Hot thin Carbon dioxide"
                #33"Hot thin Metallic vapour"
                #34"Hot thin Silicate vapour"
                #35"Hot thin Sulphur dioxide"
                #36"Methane"
                #37"Methane-rich"
                #38"Neon-rich"
                #39"Nitrogen"
                #40"No atmosphere"
                #41"Oxygen"
                #42"Suitable for water-based life"
                #43"Sulphur dioxide"
                #44"Thick Ammonia"
                #45"Thick Ammonia and Oxygen"
                #46"Thick Ammonia-rich"
                #47"Thick Argon"
                #48"Thick Argon-rich"
                #49"Thick Carbon dioxide"
                #50"Thick Carbon dioxide-rich"
                #51"Thick Helium"
                #52"Thick Methane"
                #53"Thick Methane-rich"
                #54"Thick Nitrogen"
                #55"Thick No atmosphere"
                #56"Thick Suitable for water-based life"
                #57"Thick Sulphur dioxide"
                #58"Thick Water"
                #59"Thick Water-rich"
                #60"Thin Ammonia"
                #61"Thin Ammonia and Oxygen"
                #62"Thin Ammonia-rich"
                #63"Thin Argon"
                #64"Thin Argon-rich"
                #65"Thin Carbon dioxide"
                #66"Thin Carbon dioxide-rich"
                #67"Thin Helium"
                #68"Thin Methane"
                #69"Thin Methane-rich"
                #70"Thin Neon"
                #71"Thin Neon-rich"
                #72"Thin Nitrogen"
                #73"Thin Oxygen"
                #74"Thin Sulphur dioxide"
                #75"Thin Water"
                #76"Thin Water-rich"
                #77"Water"
                #78"Water-rich"
            atmosphereComposition
            Collapse allobject

            Planets only. Atmosphere composition of the planet, mapping each element to it's percentage.
            Additional properties
            number
            solidComposition
            Collapse allobject

            Planets only. Solid composition of the planet, mapping each element to it's percentage.
            Additional properties
            number
            terraformingState
            Collapse allstring

            Planets only. Terraforming state of the planet.
            Enum
            Collapse allarray
                #0"Not terraformable"
                #1"Terraformable"
                #2"Terraformed"
                #3"Terraforming"
            materials
            Collapse allobject

            Planets only. Materials which can be found on the planet, mapping each material to it's percentage.
            Additional properties
            number
            signals
            Collapse allobject

            Planets only. The signals that can be found on the planet.
                signals
                Collapse allobject
                Additional properties
                number
                updateTime
                Collapse allstringdate-time

                The timestamp that the signals were last updated, in UTC.
                genuses
                Collapse allarray<string>

                Genuses which can be found on this planet.
                Items
                Collapse allstring
                Enum
                Collapse allarray
                    #0"$Codex_Ent_Aleoids_Genus_Name;"
                    #1"$Codex_Ent_Bacterial_Genus_Name;"
                    #2"$Codex_Ent_Brancae_Name;"
                    #3"$Codex_Ent_Cactoid_Genus_Name;"
                    #4"$Codex_Ent_Clypeus_Genus_Name;"
                    #5"$Codex_Ent_Conchas_Genus_Name;"
                    #6"$Codex_Ent_Cone_Name;"
                    #7"$Codex_Ent_Electricae_Genus_Name;"
                    #8"$Codex_Ent_Fonticulus_Genus_Name;"
                    #9"$Codex_Ent_Fumerolas_Genus_Name;"
                    #10"$Codex_Ent_Fungoids_Genus_Name;"
                    #11"$Codex_Ent_Ground_Struct_Ice_Name;"
                    #12"$Codex_Ent_Osseus_Genus_Name;"
                    #13"$Codex_Ent_Recepta_Genus_Name;"
                    #14"$Codex_Ent_Shrubs_Genus_Name;"
                    #15"$Codex_Ent_Sphere_Name;"
                    #16"$Codex_Ent_Stratum_Genus_Name;"
                    #17"$Codex_Ent_Tubus_Genus_Name;"
                    #18"$Codex_Ent_Tussocks_Genus_Name;"
                    #19"$Codex_Ent_Tube_Name;"
                    #20"$Codex_Ent_Vents_Name;"
            Additional propertiesforbidden
            reserveLevel
            Collapse allstring

            Planets only. Reserve level of the planet.
            Enum
            Collapse allarray
                #0"Common"
                #1"Depleted"
                #2"Low"
                #3"Major"
                #4"Pristine"
            rings
            Collapse allarray<object>

            Rings associated with the body.
            Items
            Collapse allobject
                name
                Collapse allstring

                Name of the belt or ring.
                type
                Collapse allstring

                Type of the ring or belt.
                Enum
                Collapse allarray
                    #0"Icy"
                    #1"Metal Rich"
                    #2"Metallic"
                    #3"Rocky"
                mass
                Collapse allnumber≥ 0

                Mass of the belt or ring, measured in Megatonnes.
                innerRadius
                Collapse allnumber≥ 0

                Inner radius of the belt or ring, measured in Kilometres.
                outerRadius
                Collapse allnumber≥ 0

                Outer radius of the belt or ring, measured in Kilometres.
                id64
                Collapse allinteger≥ 0

                ID64 of the belt or ring, a 64 bit unsigned integer.
                signals
                Collapse allobject

                The signals that can be found within the belt or ring.
                    signals
                    Collapse allobject
                    Additional properties
                    number
                    updateTime
                    Collapse allstringdate-time

                    The timestamp that the signals were last updated, in UTC.
                Additional propertiesforbidden
            Additional propertiesforbidden
            belts
            Collapse allarray<object>

            Belts associated with the body.
            Items
            Collapse allobject
                name
                Collapse allstring

                Name of the belt or ring.
                type
                Collapse allstring

                Type of the ring or belt.
                Enum
                Collapse allarray
                    #0"Icy"
                    #1"Metal Rich"
                    #2"Metallic"
                    #3"Rocky"
                mass
                Collapse allnumber≥ 0

                Mass of the belt or ring, measured in Megatonnes.
                innerRadius
                Collapse allnumber≥ 0

                Inner radius of the belt or ring, measured in Kilometres.
                outerRadius
                Collapse allnumber≥ 0

                Outer radius of the belt or ring, measured in Kilometres.
                id64
                Collapse allinteger≥ 0

                ID64 of the belt or ring, a 64 bit unsigned integer.
                signals
                Collapse allobject

                The signals that can be found within the belt or ring.
                    signals
                    Collapse allobject
                    Additional properties
                    number
                    updateTime
                    Collapse allstringdate-time

                    The timestamp that the signals were last updated, in UTC.
                Additional propertiesforbidden
            Additional propertiesforbidden
        Additional propertiesforbidden
        stations
        Collapse allarray<object>

        All space based stations of the system.
        Items
        Collapse allobject
            name
            Collapse allstring

            Name of the station
            id
            Collapse allinteger≥ 0

            Market ID of the station.
            updateTime
            Collapse allstringdate-time

            Timestamp of the last update of the station, in UTC.
            realName
            Collapse allstring

            Real name of the station, for colonisation stations.
            carrierName
            Collapse allstring

            Player given name of the station, for fleet carriers.
            controllingFaction
            Collapse allstring

            Controlling faction of the station.
            controllingFactionState
            Collapse allstring

            State of the controlling faction of the station.
            Enum
            Collapse allarray
                #0null
                #1"Blight"
                #2"Boom"
                #3"Bust"
                #4"Civil Liberty"
                #5"Civil Unrest"
                #6"Civil War"
                #7"Drought"
                #8"Election"
                #9"Expansion"
                #10"Famine"
                #11"Infrastructure Failure"
                #12"Investment"
                #13"Lockdown"
                #14"Natural Disaster"
                #15"None"
                #16"Outbreak"
                #17"Pirate Attack"
                #18"Public Holiday"
                #19"Retreat"
                #20"Terrorist Attack"
                #21"War"
            distanceToArrival
            Collapse allnumber≥ 0

            Distance to the system arrival point of the station, measured in Kilometres.
            primaryEconomy
            Collapse allstring

            Primary economy for the station.
            Enum
            Collapse allarray
                #0null
                #1"Agriculture"
                #2"Colony"
                #3"Extraction"
                #4"High Tech"
                #5"Industrial"
                #6"Military"
                #7"None"
                #8"Prison"
                #9"Private Enterprise"
                #10"Refinery"
                #11"Repair"
                #12"Rescue"
                #13"Service"
                #14"Terraforming"
                #15"Tourism"
            secondaryEconomy
            Collapse allstring

            Secondary economy for the station.
            Enum
            Collapse allarray
                #0null
                #1"Agriculture"
                #2"Colony"
                #3"Extraction"
                #4"High Tech"
                #5"Industrial"
                #6"Military"
                #7"None"
                #8"Prison"
                #9"Private Enterprise"
                #10"Refinery"
                #11"Repair"
                #12"Rescue"
                #13"Service"
                #14"Terraforming"
                #15"Tourism"
            economies
            Collapse allobject

            All econommies for the station, mapping each economy as a proportion of the stations economies.
            Additional properties
            number
            allegiance
            Collapse allstring

            Allegiance of the station.
            Enum
            Collapse allarray
                #0null
                #1"Alliance"
                #2"Empire"
                #3"Federation"
                #4"Frontline Solutions"
                #5"Guardian"
                #6"Independent"
                #7"Pilots Federation"
                #8"Thargoid"
            government
            Collapse allstring

            Government type of the station.
            Enum
            Collapse allarray
                #0null
                #1"Anarchy"
                #2"Communism"
                #3"Confederacy"
                #4"Cooperative"
                #5"Corporate"
                #6"Democracy"
                #7"Dictatorship"
                #8"Engineer"
                #9"Feudal"
                #10"Megaconstruction"
                #11"None"
                #12"Patronage"
                #13"Prison"
                #14"Prison Colony"
                #15"Private Ownership"
                #16"Theocracy"
            services
            Collapse allarray<string>

            Servies provided by the station.
            Items
            Collapse allstring
            Enum
            Collapse allarray
                #0"Flight Controller"
                #1"Station Operations"
                #2"Dock"
                #3"Autodock"
                #4"Station Menu"
                #5"Contacts"
                #6"Refuel"
                #7"Market"
                #8"Repair"
                #9"Workshop"
                #10"Missions"
                #11"Search and Rescue"
                #12"Missions Generated"
                #13"Restock"
                #14"Social Space"
                #15"Black Market"
                #16"Interstellar Factors Contact"
                #17"Powerplay"
                #18"System Colonisation"
                #19"Crew Lounge"
                #20"Universal Cartographics"
                #21"Outfitting"
                #22"Livery"
                #23"Construction Services"
                #24"Shop"
                #25"Bartender"
                #26"Vista Genomics"
                #27"Shipyard"
                #28"Pioneer Supplies"
                #29"Apex Interstellar"
                #30"Tuning"
                #31"Fleet Carrier Fuel"
                #32"Fleet Carrier Management"
                #33"Frontline Solutions"
                #34"Refinery Contact"
                #35"Redemption Office"
                #36"Technology Broker"
                #37"Material Trader"
                #38"Squadron Bank"
                #39"Fleet Carrier Administration"
                #40"On Dock Mission"
                #41"Fleet Carrier Vendor"
            type
            Collapse allstring

            Type of the station.
            Enum
            Collapse allarray
                #0"Asteroid base"
                #1"Coriolis Starport"
                #2"Dockable Planet Station"
                #3"Dodec Starport"
                #4"Drake-Class Carrier"
                #5"Mega ship"
                #6"Ocellus Starport"
                #7"Orbis Starport"
                #8"Outpost"
                #9"Planetary Construction Depot"
                #10"Planetary Outpost"
                #11"Planetary Port"
                #12"Settlement"
                #13"Space Construction Depot"
                #14"Surface Settlement"
            state
            Collapse allstring

            State of the station.
            Enum
            Collapse allarray
                #0"Construction"
                #1"Damaged"
                #2"DamagedHuman"
                #3"UnderAttack"
                #4"UnderRepairs"
            latitude
            Collapse allnumber

            Planetary stations only. Latitude of the station.
            longitude
            Collapse allnumber

            Planetary stations only. Longitude of the station.
            landingPads
            Collapse allobject

            Breakdown of the number of landing pads of the station.
                large
                Collapse allinteger≥ 0

                Numer of large landing pads of the station.
                medium
                Collapse allinteger≥ 0

                Numer of medium landing pads of the station.
                small
                Collapse allinteger≥ 0

                Numer of small landing pads of the station.
            Additional propertiesforbidden
            carrierDockingAccess
            Collapse allstring

            Carrier only. Access control of the station.
            market
            Collapse allobject

            Commodity market information about the station.
                commodities
                Collapse allarray<object>

                Commodities that can be bought and sold at about the station.
                Items
                Collapse allobject
                    name
                    Collapse allstring

                    Name of the commidity..
                    Enum
                    Collapse allarray
                        #0"AI Relics"
                        #1"Advanced Catalysers"
                        #2"Advanced Medicines"
                        #3"Aepyornis Egg"
                        #4"Aganippe Rush"
                        #5"Agri-Medicines"
                        #6"Agronomic Treatment"
                        #7"Alacarakmo Skin Art"
                        #8"Albino Quechua Mammoth Meat"
                        #9"Alexandrite"
                        #10"Algae"
                        #11"Altairian Skin"
                        #12"Aluminium"
                        #13"Alya Body Soap"
                        #14"Ancient Artefact"
                        #15"Ancient Key"
                        #16"Anduliga Fire Works"
                        #17"Animal Meat"
                        #18"Animal Monitors"
                        #19"Anomaly Particles"
                        #20"Antimatter Containment Unit"
                        #21"Antique Jewellery"
                        #22"Antiquities"
                        #23"Any Na Coffee"
                        #24"Apa Vietii"
                        #25"Aquaponic Systems"
                        #26"Arouca Conventual Sweets"
                        #27"Articulation Motors"
                        #28"Assault Plans"
                        #29"Atmospheric Processors"
                        #30"Auto-Fabricators"
                        #31"Az Cancri Formula 42"
                        #32"Azure Milk"
                        #33"Baked Greebles"
                        #34"Baltah'sine Vacuum Krill"
                        #35"Banki Amphibious Leather"
                        #36"Basic Medicines"
                        #37"Bast Snake Gin"
                        #38"Bastnasite"
                        #39"Battle Weapons"
                        #40"Bauxite"
                        #41"Beer"
                        #42"Belalans Ray Leather"
                        #43"Benitoite"
                        #44"Bertrandite"
                        #45"Beryllium"
                        #46"Bioreducing Lichen"
                        #47"Biowaste"
                        #48"Bismuth"
                        #49"Black Box"
                        #50"Bone Fragments"
                        #51"Bootleg Liquor"
                        #52"Borasetani Pathogenetics"
                        #53"Bromellite"
                        #54"Buckyball Beer Mats"
                        #55"Building Fabricators"
                        #56"Burnham Bile Distillate"
                        #57"CD-75 Kitten Brand Coffee"
                        #58"CMM Composite"
                        #59"Caustic Tissue Sample"
                        #60"Centauri Mega Gin"
                        #61"Ceramic Composites"
                        #62"Ceremonial Heike Tea"
                        #63"Ceti Rabbits"
                        #64"Chameleon Cloth"
                        #65"Chateau De Aegaeon"
                        #66"Chemical Waste"
                        #67"Cherbones Blood Crystals"
                        #68"Chi Eridani Marine Paste"
                        #69"Classified Experimental Equipment"
                        #70"Clothing"
                        #71"Cobalt"
                        #72"Coffee"
                        #73"Coltan"
                        #74"Combat Stabilisers"
                        #75"Commercial Samples"
                        #76"Computer Components"
                        #77"Conductive Fabrics"
                        #78"Consumer Technology"
                        #79"Copper"
                        #80"Coquim Spongiform Victuals"
                        #81"Coral Sap"
                        #82"Crom Silver Fesh"
                        #83"Crop Harvesters"
                        #84"Cryolite"
                        #85"Crystalline Spheres"
                        #86"Curated Commodity Package"
                        #87"Cyst Specimen"
                        #88"Damaged Escape Pod"
                        #89"Damna Carapaces"
                        #90"Data Core"
                        #91"Delta Phoenicis Palms"
                        #92"Deuringas Truffles"
                        #93"Deuterium"
                        #94"Diamond"
                        #95"Diplomatic Bag"
                        #96"Diso Ma Corn"
                        #97"Domestic Appliances"
                        #98"Duradrives"
                        #99"Earth Relics"
                        #100"Eden Apples of Aerial"
                        #101"Eleu Thermals"
                        #102"Emergency Power Cells"
                        #103"Encrypted Correspondence"
                        #104"Encrypted Data Storage"
                        #105"Energy Grid Assembly"
                        #106"Eranin Pearl Whisky"
                        #107"Eshu Umbrellas"
                        #108"Esuseku Caviar"
                        #109"Ethgreze Tea Buds"
                        #110"Evacuation Shelter"
                        #111"Exhaust Manifold"
                        #112"Experimental Chemicals"
                        #113"Explosives"
                        #114"Fish"
                        #115"Food Cartridges"
                        #116"Fossil Remnants"
                        #117"Fruit and Vegetables"
                        #118"Fujin Tea"
                        #119"Galactic Travel Guide"
                        #120"Gallite"
                        #121"Gallium"
                        #122"Geawen Dance Dust"
                        #123"Gene Bank"
                        #124"Geological Equipment"
                        #125"Geological Samples"
                        #126"Gerasian Gueuze Beer"
                        #127"Giant Irukama Snails"
                        #128"Giant Verrix"
                        #129"Gilya Signature Weapons"
                        #130"Gold"
                        #131"Goman Yaupon Coffee"
                        #132"Goslarite"
                        #133"Grain"
                        #134"Grandidierite"
                        #135"Guardian Casket"
                        #136"Guardian Orb"
                        #137"Guardian Relic"
                        #138"Guardian Tablet"
                        #139"Guardian Totem"
                        #140"Guardian Urn"
                        #141"H.E. Suits"
                        #142"HIP 10175 Bush Meat"
                        #143"HIP 118311 Swarm"
                        #144"HIP Organophosphates"
                        #145"HIP Proto-Squid"
                        #146"HN Shock Mount"
                        #147"HR 7221 Wheat"
                        #148"Haematite"
                        #149"Hafnium 178"
                        #150"Haiden Black Brew"
                        #151"Hardware Diagnostic Sensor"
                        #152"Harma Silver Sea Rum"
                        #153"Havasupai Dream Catcher"
                        #154"Heatsink Interlink"
                        #155"Helium"
                        #156"Helium-3"
                        #157"Helvetitj Pearls"
                        #158"Holva Duelling Blades"
                        #159"Honesty Pills"
                        #160"Hostages"
                        #161"Hydrogen Fuel"
                        #162"Hydrogen Peroxide"
                        #163"Imperial Slaves"
                        #164"Impure Spire Mineral"
                        #165"Indi Bourbon"
                        #166"Indite"
                        #167"Indium"
                        #168"Insulating Membrane"
                        #169"Ion Distributor"
                        #170"Iridium"
                        #171"Jadeite"
                        #172"Jaques Quinentian Still"
                        #173"Jaradharre Puzzle Box"
                        #174"Jaroua Rice"
                        #175"Jotun Mookah"
                        #176"Kachirigin Filter Leeches"
                        #177"Kamitra Cigars"
                        #178"Kamorin Historic Weapons"
                        #179"Karetii Couture"
                        #180"Karsuki Locusts"
                        #181"Kinago Violins"
                        #182"Kongga Ale"
                        #183"Koro Kung Pellets"
                        #184"LTT Hyper Sweet"
                        #185"Land Enrichment Systems"
                        #186"Landmines"
                        #187"Lanthanum"
                        #188"Large Survey Data Cache"
                        #189"Lavian Brandy"
                        #190"Leather"
                        #191"Leathery Eggs"
                        #192"Leestian Evil Juice"
                        #193"Lepidolite"
                        #194"Liquid oxygen"
                        #195"Liquor"
                        #196"Lithium Hydroxide"
                        #197"Lithium"
                        #198"Live Hecate Sea Worms"
                        #199"Low Temperature Diamonds"
                        #200"Lucan Onionhead"
                        #201"Lyrae Weed"
                        #202"Magnesite"
                        #203"Magnetic Emitter Coil"
                        #204"Marine Equipment"
                        #205"Master Chefs"
                        #206"Mechucos High Tea"
                        #207"Medb Starlube"
                        #208"Medical Diagnostic Equipment"
                        #209"Meta-Alloys"
                        #210"Methane Clathrate"
                        #211"Methanol Monohydrate Crystals"
                        #212"Micro Controllers"
                        #213"Micro-weave Cooling Hoses"
                        #214"Microbial Furnaces"
                        #215"Military Grade Fabrics"
                        #216"Military Intelligence"
                        #217"Military Plans"
                        #218"Mineral Extractors"
                        #219"Mineral Oil"
                        #220"Modular Terminals"
                        #221"Moissanite"
                        #222"Mokojing Beast Feast"
                        #223"Mollusc Brain Tissue"
                        #224"Mollusc Fluid"
                        #225"Mollusc Membrane"
                        #226"Mollusc Mycelium"
                        #227"Mollusc Soft Tissue"
                        #228"Mollusc Spores"
                        #229"Momus Bog Spaniel"
                        #230"Monazite"
                        #231"Motrona Experience Jelly"
                        #232"Mukusubii Chitin-os"
                        #233"Mulachi Giant Fungus"
                        #234"Muon Imager"
                        #235"Musgravite"
                        #236"Mysterious Idol"
                        #237"Nanobreakers"
                        #238"Nanomedicines"
                        #239"Narcotics"
                        #240"Natural Fabrics"
                        #241"Neofabric Insulation"
                        #242"Neritus Berries"
                        #243"Nerve Agents"
                        #244"Ngadandari Fire Opals"
                        #245"Nguna Modern Antiques"
                        #246"Njangari Saddles"
                        #247"Non Euclidian Exotanks"
                        #248"Non-Lethal Weapons"
                        #249"Occupied Escape Pod"
                        #250"Ochoeng Chillies"
                        #251"Olivine"
                        #252"Onionhead Alpha Strain"
                        #253"Onionhead Beta Strain"
                        #254"Onionhead Gamma Strain"
                        #255"Onionhead"
                        #256"Ophiuch Exino Artefacts"
                        #257"Organ Sample"
                        #258"Orrerian Vicious Brew"
                        #259"Osmium"
                        #260"Painite"
                        #261"Palladium"
                        #262"Pantaa Prayer Sticks"
                        #263"Pavonis Ear Grubs"
                        #264"Performance Enhancers"
                        #265"Periclase Dunite"
                        #266"Personal Effects"
                        #267"Personal Gifts"
                        #268"Personal Weapons"
                        #269"Pesticides"
                        #270"Platinum Alloy"
                        #271"Platinum"
                        #272"Pod Core Tissue"
                        #273"Pod Dead Tissue"
                        #274"Pod Mesoglea"
                        #275"Pod Outer Tissue"
                        #276"Pod Shell Tissue"
                        #277"Pod Surface Tissue"
                        #278"Pod Tissue"
                        #279"Political Prisoners"
                        #280"Polymers"
                        #281"Power Converter"
                        #282"Power Generators"
                        #283"Power Transfer Bus"
                        #284"Praseodymium"
                        #285"Precious Gems"
                        #286"Progenitor Cells"
                        #287"Prohibited Research Materials"
                        #288"Protective Membrane Scrap"
                        #289"Prototype Tech"
                        #290"Pyrophyllite"
                        #291"Quartz Pyroxenite"
                        #292"Radiation Baffle"
                        #293"Rajukru Multi-Stoves"
                        #294"Rapa Bao Snake Skins"
                        #295"Rare Artwork"
                        #296"Reactive Armour"
                        #297"Rebel Transmissions"
                        #298"Reinforced Mounting Plate"
                        #299"Resonating Separators"
                        #300"Rhodplumsite"
                        #301"Robotics"
                        #302"Rockforth Fertiliser"
                        #303"Ruby"
                        #304"Rusani Old Smokey"
                        #305"Rutile"
                        #306"SAP 8 Core Container"
                        #307"Samarium"
                        #308"Sanuma Decorative Meat"
                        #309"Sapphire"
                        #310"Saxon Wine"
                        #311"Scientific Research"
                        #312"Scientific Samples"
                        #313"Scrap"
                        #314"Semi-Refined Spire Mineral"
                        #315"Semiconductors"
                        #316"Serendibite"
                        #317"Shan's Charis Orchid"
                        #318"Silver"
                        #319"Skimmer Components"
                        #320"Slaves"
                        #321"Small Survey Data Cache"
                        #322"Soontill Relics"
                        #323"Sothis Crystalline Gold"
                        #324"Space Pioneer Relics"
                        #325"Steel"
                        #326"Structural Regulators"
                        #327"Superconductors"
                        #328"Surface Stabilisers"
                        #329"Survival Equipment"
                        #330"Synthetic Fabrics"
                        #331"Synthetic Meat"
                        #332"Synthetic Reagents"
                        #333"Taaffeite"
                        #334"Tactical Data"
                        #335"Tanmark Tranquil Tea"
                        #336"Tantalum"
                        #337"Tarach Spice"
                        #338"Tauri Chimes"
                        #339"Tea"
                        #340"Technical Blueprints"
                        #341"Telemetry Suite"
                        #342"Terra Mater Blood Bores"
                        #343"Thallium"
                        #344"Thargoid Basilisk Tissue Sample"
                        #345"Thargoid Biological Matter"
                        #346"Thargoid Cyclops Tissue Sample"
                        #347"Thargoid Glaive Tissue Sample"
                        #348"Thargoid Heart"
                        #349"Thargoid Hydra Tissue Sample"
                        #350"Thargoid Link"
                        #351"Thargoid Medusa Tissue Sample"
                        #352"Thargoid Orthrus Tissue Sample"
                        #353"Thargoid Probe"
                        #354"Thargoid Resin"
                        #355"Thargoid Scout Tissue Sample"
                        #356"Thargoid Scythe Tissue Sample"
                        #357"Thargoid Sensor"
                        #358"Thargoid Technology Samples"
                        #359"The Hutton Mug"
                        #360"The Waters of Shintara"
                        #361"Thermal Cooling Units"
                        #362"Thorium"
                        #363"Thortveitite"
                        #364"Thrutis Cream"
                        #365"Tiegfries Synth Silk"
                        #366"Time Capsule"
                        #367"Tiolce Waste2Paste Units"
                        #368"Titan Deep Tissue Sample"
                        #369"Titan Drive Component"
                        #370"Titan Maw Deep Tissue Sample"
                        #371"Titan Maw Partial Tissue Sample"
                        #372"Titan Maw Tissue Sample"
                        #373"Titan Partial Tissue Sample"
                        #374"Titan Tissue Sample"
                        #375"Titanium"
                        #376"Tobacco"
                        #377"Toxandji Virocide"
                        #378"Toxic Waste"
                        #379"Trade Data"
                        #380"Trinkets of Hidden Fortune"
                        #381"Tritium"
                        #382"Ultra-Compact Processor Prototypes"
                        #383"Unclassified Relic"
                        #384"Unoccupied Escape Pod"
                        #385"Unstable Data Core"
                        #386"Uraninite"
                        #387"Uranium"
                        #388"Uszaian Tree Grub"
                        #389"Utgaroar Millennial Eggs"
                        #390"Uzumoku Low-G Wings"
                        #391"V Herculis Body Rub"
                        #392"Vanayequi Ceratomorpha Fur"
                        #393"Vega Slimweed"
                        #394"Vidavantian Lace"
                        #395"Void Extract Coffee"
                        #396"Void Opal"
                        #397"Volkhab Bee Drones"
                        #398"Water Purifiers"
                        #399"Water"
                        #400"Wheemete Wheat Cakes"
                        #401"Wine"
                        #402"Witchhaul Kobe Beef"
                        #403"Wolf Fesh"
                        #404"Wreckage Components"
                        #405"Wulpa Hyperbore Systems"
                        #406"Wuthielo Ku Froth"
                        #407"Xenobiological Prison Pod"
                        #408"Xihe Biomorphic Companions"
                        #409"Yaso Kondi Leaf"
                        #410"Zeessze Ant Grub Glue"
                    symbol
                    Collapse allstring

                    Frontier symbol identifier of the commodity.
                    category
                    Collapse allstring

                    Category of the commodity.
                    Enum
                    Collapse allarray
                        #0"Chemicals"
                        #1"Consumer Items"
                        #2"Foods"
                        #3"Industrial Materials"
                        #4"Legal Drugs"
                        #5"Machinery"
                        #6"Medicines"
                        #7"Metals"
                        #8"Minerals"
                        #9"Salvage"
                        #10"Slavery"
                        #11"Technology"
                        #12"Textiles"
                        #13"Waste"
                        #14"Weapons"
                    commodityId
                    Collapse allinteger

                    Frontier numeric identifier of the commodity.
                    demand
                    Collapse allinteger≥ 0

                    Demand for the commodity.
                    supply
                    Collapse allinteger≥ 0

                    Supply for the commodity.
                    buyPrice
                    Collapse allinteger≥ 0

                    Price the player can buy the commodity for.
                    sellPrice
                    Collapse allinteger≥ 0

                    Price the player can sell the commodity for.
                Additional propertiesforbidden
                prohibitedCommodities
                Collapse allarray<string>

                Commodities that are illegal on the station.
                Items
                string
                updateTime
                Collapse allstringdate-time

                Timestamp of the last update of the marketplace for the station, in UTC.
            Additional propertiesforbidden
            shipyard
            Collapse allobject

            Shipyard information about the station.
                ships
                Collapse allarray<object>

                Ships that can be bought at the station.
                Items
                Collapse allobject
                    name
                    Collapse allstring

                    Ship restrictions for the module.
                    Enum
                    Collapse allarray
                        #0"Adder"
                        #1"Alliance Challenger"
                        #2"Alliance Chieftain"
                        #3"Alliance Crusader"
                        #4"Anaconda"
                        #5"Asp Explorer"
                        #6"Asp Scout"
                        #7"Beluga Liner"
                        #8"Caspian Explorer"
                        #9"Cobra MkIII"
                        #10"Cobra MkIV"
                        #11"Cobra MkV"
                        #12"Corsair"
                        #13"Diamondback Explorer"
                        #14"Diamondback Scout"
                        #15"Dolphin"
                        #16"Eagle"
                        #17"Federal Assault Ship"
                        #18"Federal Corvette"
                        #19"Federal Dropship"
                        #20"Federal Gunship"
                        #21"Fer-de-Lance"
                        #22"Hauler"
                        #23"Imperial Clipper"
                        #24"Imperial Courier"
                        #25"Imperial Cutter"
                        #26"Imperial Eagle"
                        #27"Keelback"
                        #28"Kestrel Mk II"
                        #29"Krait MkII"
                        #30"Krait Phantom"
                        #31"Lynx Highliner"
                        #32"Mamba"
                        #33"Mandalay"
                        #34"Orca"
                        #35"Panther Clipper MkII"
                        #36"Python"
                        #37"Python MkII"
                        #38"Sidewinder"
                        #39"Type-10 Defender"
                        #40"Type-11 Prospector"
                        #41"Type-6 Transporter"
                        #42"Type-7 Transporter"
                        #43"Type-8 Transporter"
                        #44"Type-9 Heavy"
                        #45"Viper MkIII"
                        #46"Viper MkIV"
                        #47"Vulture"
                    symbol
                    Collapse allstring

                    Frontier symbol identifier of the ship.
                    shipId
                    Collapse allnumber

                    Frontier numeric identifier of the ship.
                Additional propertiesforbidden
                updateTime
                Collapse allstringdate-time

                Timestamp of the last update of the shipyard for the station, in UTC.
            Additional propertiesforbidden
            outfitting
            Collapse allobject

            Outfitting information about the station.
                modules
                Collapse allarray<object>

                Outfitting modules that can be bought at the station.
                Items
                Collapse allobject
                    name
                    Collapse allstring

                    Name of the module.
                    Enum
                    Collapse allarray
                        #0"AX Missile Rack"
                        #1"AX Multi-Cannon"
                        #2"Abrasion Blaster"
                        #3"Advanced Docking Computer"
                        #4"Advanced Discovery Scanner"
                        #5"Advanced Missile Rack"
                        #6"Advanced Multi-Cannon"
                        #7"Advanced Planetary Approach Suite"
                        #8"Advanced Plasma Accelerator"
                        #9"Auto Field-Maintenance Unit"
                        #10"Balanced Power Distributor"
                        #11"Basic Discovery Scanner"
                        #12"Beam Laser"
                        #13"Bi-Weave Shield Generator"
                        #14"Burst Laser"
                        #15"Business Class Passenger Cabin"
                        #16"Cannon"
                        #17"Cargo Rack"
                        #18"Cargo Scanner"
                        #19"Caustic Sink Launcher"
                        #20"Chaff Launcher"
                        #21"Collector Limpet Controller"
                        #22"Concord Cannon"
                        #23"Corrosion Resistant Cargo Rack"
                        #24"Cytoscrambler Burst Laser"
                        #25"Decontamination Limpet Controller"
                        #26"Detailed Surface Scanner"
                        #27"Double Screaming Fragment Cannon"
                        #28"Economy Class Passenger Cabin"
                        #29"Electronic Countermeasure"
                        #30"Enduring Feedback Rail Gun"
                        #31"Enforcer Cannon"
                        #32"Enhanced AX Missile Rack"
                        #33"Enhanced AX Multi-Cannon"
                        #34"Enhanced Performance Thrusters"
                        #35"Enhanced Xeno Scanner"
                        #36"Enzyme Missile Rack"
                        #37"Experimental Weapon Stabiliser"
                        #38"Exposing Missiles"
                        #39"Extended Cargo Rack"
                        #40"Far-Reaching Abrasion Blaster"
                        #41"Fighter Hangar"
                        #42"First Class Passenger Cabin"
                        #43"Force Impact Cannon"
                        #44"Fragment Cannon"
                        #45"Frame Shift Drive (SCO)"
                        #46"Frame Shift Drive Interdictor"
                        #47"Frame Shift Drive"
                        #48"Frame Shift Wake Scanner"
                        #49"Fuel Scoop"
                        #50"Fuel Tank"
                        #51"Fuel Transfer Limpet Controller"
                        #52"Guardian FSD Booster"
                        #53"Guardian Gauss Cannon"
                        #54"Guardian Hull Reinforcement"
                        #55"Guardian Hybrid Power Distributor"
                        #56"Guardian Hybrid Power Plant"
                        #57"Guardian Module Reinforcement"
                        #58"Guardian Nanite Torpedo Pylon"
                        #59"Guardian Plasma Charger"
                        #60"Guardian Shard Cannon"
                        #61"Guardian Shield Reinforcement"
                        #62"Hatch Breaker Limpet Controller"
                        #63"Heat Sink Launcher"
                        #64"Heavy Duty Module Reinforcement Package"
                        #65"High-Yield Enzyme Missile Rack"
                        #66"Hull Reinforcement Package"
                        #67"Imperial Hammer Rail Gun"
                        #68"Intermediate Discovery Scanner"
                        #69"Kill Warrant Scanner"
                        #70"Large Planetary Vehicle Hangar"
                        #71"Life Support"
                        #72"Lightweight Alloy"
                        #73"Lockdown Seeker Missile Rack"
                        #74"Long Range Detailed Surface Scanner"
                        #75"Long Range Mining Laser"
                        #76"Luxury Class Passenger Cabin"
                        #77"Meta Alloy Hull Reinforcement"
                        #78"Military Grade Composite"
                        #79"Mine Launcher"
                        #80"Mining Lance"
                        #81"Mining Laser"
                        #82"Mining Multi Limpet Controller"
                        #83"Mining Volley Repeater"
                        #84"Mirrored Surface Composite"
                        #85"Missile Rack"
                        #86"Mk II Ablative Lightweight Alloys"
                        #87"Mk II Ablative Military Grade Composite"
                        #88"Mk II Ablative Mirrored Surface Composite"
                        #89"Mk II Ablative Reactive Surface Composite"
                        #90"Mk II Ablative Reinforced Alloys"
                        #91"Mk II Agile Boost Thrusters"
                        #92"Mk II Business Class Passenger Cabin"
                        #93"Mk II Cargo Rack"
                        #94"Mk II Economy Class Passenger Cabin"
                        #95"Mk II Gravity Optimised Thrusters"
                        #96"Mk II Large Planetary Vehicle Hangar"
                        #97"Mk II Mining Multi-Limpet Controller"
                        #98"Mk II Plasma Shock Accelerator"
                        #99"Mk II Supercharge Optimised Frame Shift Drive (SCO)"
                        #100"Mk II Vessel Hangar"
                        #101"MkII Business Class Passenger Cabin"
                        #102"MkII Economy Class Passenger Cabin"
                        #103"Module Reinforcement Package"
                        #104"Multi-Cannon"
                        #105"Operations Multi Limpet Controller"
                        #106"Overloaded Beam Laser"
                        #107"Pacifier Frag-Cannon"
                        #108"Pack-Hound Missile Rack"
                        #109"Planetary Approach Suite"
                        #110"Planetary Vehicle Hangar"
                        #111"Plasma Accelerator"
                        #112"Point Defence"
                        #113"Power Distributor"
                        #114"Power Plant"
                        #115"Prismatic Shield Generator"
                        #116"Prospector Limpet Controller"
                        #117"Pulse Disruptor Laser"
                        #118"Pulse Laser"
                        #119"Pulse Wave Analyser"
                        #120"Pulse Wave Xeno Scanner"
                        #121"Rail Gun"
                        #122"Rapid Phase Multi-Cannon"
                        #123"Reactive Surface Composite"
                        #124"Recon Limpet Controller"
                        #125"Refinery"
                        #126"Regenerative Burst Laser"
                        #127"Reinforced Alloy"
                        #128"Remote Release Flak Launcher"
                        #129"Remote Release Flechette Launcher"
                        #130"Repair Limpet Controller"
                        #131"Rescue Multi Limpet Controller"
                        #132"Research Limpet Controller"
                        #133"Retributor Beam Laser"
                        #134"Rocket Propelled FSD Disruptor"
                        #135"Seeker Missile Rack"
                        #136"Seismic Charge Launcher"
                        #137"Sensors"
                        #138"Shield Booster"
                        #139"Shield Cell Bank"
                        #140"Shield Generator"
                        #141"Shock Cannon"
                        #142"Shock Mine Launcher"
                        #143"Shutdown Field Neutraliser"
                        #144"Standard Docking Computer"
                        #145"Sub-Surface Displacement Missile"
                        #146"Sub-Surface Extraction Missile"
                        #147"Supercruise Assist"
                        #148"Support Focused Power Distributor"
                        #149"Thargoid Pulse Neutraliser"
                        #150"Thrusters"
                        #151"Torpedo Pylon"
                        #152"Universal Multi Limpet Controller"
                        #153"Vessel Hangar"
                        #154"Xeno Multi Limpet Controller"
                        #155"Xeno Scanner"
                    symbol
                    Collapse allstring

                    Frontier symbol identifier of the module.
                    moduleId
                    Collapse allnumber

                    Frontier numeric identifier of the module.
                    class
                    Collapse allinteger

                    Class of the module.
                    Enum
                    Collapse allarray
                        #01
                        #13
                        #22
                        #35
                        #44
                        #57
                        #66
                        #78
                        #80
                    rating
                    Collapse allstring

                    Rating of the module.
                    Enum
                    Collapse allarray
                        #0"E"
                        #1"D"
                        #2"C"
                        #3"I"
                        #4"B"
                        #5"A"
                        #6"F"
                        #7"G"
                        #8"H"
                    category
                    Collapse allstring

                    Category of the module.
                    Enum
                    Collapse allarray
                        #0"hardpoint"
                        #1"internal"
                        #2"utility"
                        #3"standard"
                        #4"mercgear"
                    ship
                    Collapse all(string | null)

                    Ship restrictions for the module.
                    One of
                    Collapse all(string | null)
                        #0
                        Collapse allstring

                        Ship restrictions for the module.
                        Enum
                        Collapse allarray
                            #0"Adder"
                            #1"Alliance Challenger"
                            #2"Alliance Chieftain"
                            #3"Alliance Crusader"
                            #4"Anaconda"
                            #5"Asp Explorer"
                            #6"Asp Scout"
                            #7"Beluga Liner"
                            #8"Caspian Explorer"
                            #9"Cobra MkIII"
                            #10"Cobra MkIV"
                            #11"Cobra MkV"
                            #12"Corsair"
                            #13"Diamondback Explorer"
                            #14"Diamondback Scout"
                            #15"Dolphin"
                            #16"Eagle"
                            #17"Federal Assault Ship"
                            #18"Federal Corvette"
                            #19"Federal Dropship"
                            #20"Federal Gunship"
                            #21"Fer-de-Lance"
                            #22"Hauler"
                            #23"Imperial Clipper"
                            #24"Imperial Courier"
                            #25"Imperial Cutter"
                            #26"Imperial Eagle"
                            #27"Keelback"
                            #28"Kestrel Mk II"
                            #29"Krait MkII"
                            #30"Krait Phantom"
                            #31"Lynx Highliner"
                            #32"Mamba"
                            #33"Mandalay"
                            #34"Orca"
                            #35"Panther Clipper MkII"
                            #36"Python"
                            #37"Python MkII"
                            #38"Sidewinder"
                            #39"Type-10 Defender"
                            #40"Type-11 Prospector"
                            #41"Type-6 Transporter"
                            #42"Type-7 Transporter"
                            #43"Type-8 Transporter"
                            #44"Type-9 Heavy"
                            #45"Viper MkIII"
                            #46"Viper MkIV"
                            #47"Vulture"
                        #1
                        null
                Additional propertiesforbidden
                updateTime
                Collapse allstringdate-time

                Timestamp of the last update of the outfitting for the station, in UTC.
            Additional propertiesforbidden
        Additional propertiesforbidden
        controllingFaction
        Collapse allobject

        Controlling faction of the system.
            name
            Collapse allstring

            Name of the faction of the system.
            state
            Collapse allstring

            State of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Blight"
                #2"Boom"
                #3"Bust"
                #4"Civil Liberty"
                #5"Civil Unrest"
                #6"Civil War"
                #7"Drought"
                #8"Election"
                #9"Expansion"
                #10"Famine"
                #11"Infrastructure Failure"
                #12"Investment"
                #13"Lockdown"
                #14"Natural Disaster"
                #15"None"
                #16"Outbreak"
                #17"Pirate Attack"
                #18"Public Holiday"
                #19"Retreat"
                #20"Terrorist Attack"
                #21"War"
            allegiance
            Collapse allstring

            Allegiance of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Alliance"
                #2"Empire"
                #3"Federation"
                #4"Frontline Solutions"
                #5"Guardian"
                #6"Independent"
                #7"Pilots Federation"
                #8"Thargoid"
            government
            Collapse allstring

            Government type of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Anarchy"
                #2"Communism"
                #3"Confederacy"
                #4"Cooperative"
                #5"Corporate"
                #6"Democracy"
                #7"Dictatorship"
                #8"Engineer"
                #9"Feudal"
                #10"Megaconstruction"
                #11"None"
                #12"Patronage"
                #13"Prison"
                #14"Prison Colony"
                #15"Private Ownership"
                #16"Theocracy"
            influence
            Collapse allnumber[0, 1]

            Influence of the faction.
            activeStates
            Collapse allarray<object>

            Currently active states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
            pendingStates
            Collapse allarray<object>

            Pending states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
            recoveringStates
            Collapse allarray<object>

            Recovering states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
        Additional propertiesforbidden
        factions
        Collapse allarray<object>

        All factions with influence in the system.
        Items
        Collapse allobject

        Full faction state
            name
            Collapse allstring

            Name of the faction of the system.
            state
            Collapse allstring

            State of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Blight"
                #2"Boom"
                #3"Bust"
                #4"Civil Liberty"
                #5"Civil Unrest"
                #6"Civil War"
                #7"Drought"
                #8"Election"
                #9"Expansion"
                #10"Famine"
                #11"Infrastructure Failure"
                #12"Investment"
                #13"Lockdown"
                #14"Natural Disaster"
                #15"None"
                #16"Outbreak"
                #17"Pirate Attack"
                #18"Public Holiday"
                #19"Retreat"
                #20"Terrorist Attack"
                #21"War"
            allegiance
            Collapse allstring

            Allegiance of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Alliance"
                #2"Empire"
                #3"Federation"
                #4"Frontline Solutions"
                #5"Guardian"
                #6"Independent"
                #7"Pilots Federation"
                #8"Thargoid"
            government
            Collapse allstring

            Government type of the faction of the system.
            Enum
            Collapse allarray
                #0null
                #1"Anarchy"
                #2"Communism"
                #3"Confederacy"
                #4"Cooperative"
                #5"Corporate"
                #6"Democracy"
                #7"Dictatorship"
                #8"Engineer"
                #9"Feudal"
                #10"Megaconstruction"
                #11"None"
                #12"Patronage"
                #13"Prison"
                #14"Prison Colony"
                #15"Private Ownership"
                #16"Theocracy"
            influence
            Collapse allnumber[0, 1]

            Influence of the faction.
            activeStates
            Collapse allarray<object>

            Currently active states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
            pendingStates
            Collapse allarray<object>

            Pending states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
            recoveringStates
            Collapse allarray<object>

            Recovering states for this faction.
            Items
            Collapse allobject
                state
                Collapse allstring

                Actual state of the state.
                Enum
                Collapse allarray
                    #0null
                    #1"Blight"
                    #2"Boom"
                    #3"Bust"
                    #4"Civil Liberty"
                    #5"Civil Unrest"
                    #6"Civil War"
                    #7"Drought"
                    #8"Election"
                    #9"Expansion"
                    #10"Famine"
                    #11"Infrastructure Failure"
                    #12"Investment"
                    #13"Lockdown"
                    #14"Natural Disaster"
                    #15"None"
                    #16"Outbreak"
                    #17"Pirate Attack"
                    #18"Public Holiday"
                    #19"Retreat"
                    #20"Terrorist Attack"
                    #21"War"
                trend
                Collapse allnumber

                Trend of the state of the faction.
            Additional propertiesforbidden
        Additional propertiesforbidden
        powerState
        Collapse allstring

        State of the controlling power of the system.
        Enum
        Collapse allarray
            #0null
            #1"Exploited"
            #2"Fortified"
            #3"Stronghold"
            #4"Unoccupied"
        powerConflictProgress
        Collapse allarray<object>
        Items
        Collapse allobject
            power
            Collapse allstring
            Enum
            Collapse allarray
                #0null
                #1"Aisling Duval"
                #2"A. Lavigny-Duval"
                #3"Archon Delaine"
                #4"Denton Patreus"
                #5"Edmund Mahon"
                #6"Felicia Winters"
                #7"Jerome Archer"
                #8"Li Yong-Rui"
                #9"Nakato Kaine"
                #10"Pranav Antal"
                #11"Yuri Grom"
                #12"Zemina Torval"
            progress
            Collapse allnumber≥ 0

            Progress of the power in the conflict.
        Additional propertiesforbidden
        powers
        Collapse allarray<string>

        Powers with influence in the system.
        Items
        Collapse allstring

        Name of the powers.
        Enum
        Collapse allarray
            #0null
            #1"Aisling Duval"
            #2"A. Lavigny-Duval"
            #3"Archon Delaine"
            #4"Denton Patreus"
            #5"Edmund Mahon"
            #6"Felicia Winters"
            #7"Jerome Archer"
            #8"Li Yong-Rui"
            #9"Nakato Kaine"
            #10"Pranav Antal"
            #11"Yuri Grom"
            #12"Zemina Torval"
        timestamps
        Collapse allobject

        Update timestamps for individual attributes, mapping attribute to last updated timestamp.
        Additional properties
        string
        controllingPower
        Collapse allstring

        Name of the controlling power of the system.
        Enum
        Collapse allarray
            #0null
            #1"Aisling Duval"
            #2"A. Lavigny-Duval"
            #3"Archon Delaine"
            #4"Denton Patreus"
            #5"Edmund Mahon"
            #6"Felicia Winters"
            #7"Jerome Archer"
            #8"Li Yong-Rui"
            #9"Nakato Kaine"
            #10"Pranav Antal"
            #11"Yuri Grom"
            #12"Zemina Torval"
        powerStateControlProgress
        Collapse allnumber

        Progress of the controlling power in controlling the system.
        powerStateReinforcement
        Collapse allnumber≥ 0

        Progress of the controlling power in reinforcing the system.
        powerStateUndermining
        Collapse allnumber≥ 0

        Progress of the controlling power in losing the system.
        thargoidWar
        Collapse allobject

        State of the Thargoid war in this system.
            currentState
            Collapse allstring

            Current Thargoid state in this system.
            Enum
            Collapse allarray
                #0null
                #1"None"
                #2"Thargoid Controlled"
                #3"Thargoid Harvest"
                #4"Thargoid Probing"
                #5"Thargoid Recovery"
                #6"Thargoid Stronghold"
            successState
            Collapse allstring

            Thargoid state in this system if the war is won by the players.
            Enum
            Collapse allarray
                #0null
                #1"None"
                #2"Thargoid Controlled"
                #3"Thargoid Harvest"
                #4"Thargoid Probing"
                #5"Thargoid Recovery"
                #6"Thargoid Stronghold"
            failureState
            Collapse allstring

            Thargoid state in this system if the war is lost by the players.
            Enum
            Collapse allarray
                #0null
                #1"None"
                #2"Thargoid Controlled"
                #3"Thargoid Harvest"
                #4"Thargoid Probing"
                #5"Thargoid Recovery"
                #6"Thargoid Stronghold"
            progress
            Collapse allnumber[0, 1]

            Progress of the Thargoid war in this system.
            daysRemaining
            Collapse allnumber≥ 0

            Days remaining of the Thargoid war in this system.
            portsRemaining
            Collapse allnumber≥ 0

            Posts remaining in the Thargoid war in this system.
            successReached
            Collapse allboolean

            Have the players won the Thargoid war in this system.
    Additional propertiesforbidden

# Nederlands (Dutch)

## Date and Time

- "hoe laat is het?"
- "wat is de datum?"

## Weather and Temperature

- "wat voor weer is het?"
    - Requires a [weather][] entity to be configured
- "wat voor weer is het in New York?"
    - Requires a [weather][] entity named "New York"
- "wat is de temperatuur?"
    - Requires a [climate][] entity to be configured
- "wat is de temperatuur van de EcoBee?"
    - Requires a [climate][] entity named "EcoBee"
    
## Lights

- "zet de lampen aan"
    - Requires voice satellite to be in an [area][]
- "zet de Staande Lamp aan"
    - Requires a [light][] entity named "standing light"
- "doe alle lampen in het Kantoor uit"
    - Requires an [area][] named "Kantoor"
- "zet alle lampen op de Eerste Verdieping aan"
    - Requires a [floor][] named "Eerste Verdieping"
- "zet de kleur van de Keuken op groen"
    - Requires an [area][] named "Keuken" with at least one [light][] entity in it that supports setting color
- "zet de helderheid van de Staande Lamp 50 procent"
    - Requires a [light][] entity named "Staande Lamp" that supports setting brightness
    - Brightness from 10-100 by 10s

## Doors and Windows

- "open/sluit Garagedeur"
    - Requires a [cover][] entity named "Garagedeur"
- "is de Garagedeur open?"
    - Requires a [cover][] entity named "Garagedeur"
    
## Locks

- "vergrendel/ontgrendel de Voordeur"
    - Requires a [lock][] entity named "Voordeur"
- "is de Voordeur vergrendeld/ontgrendeld"
    - Requires a [lock][] entity named "Voordeur"

## Media

- "pauzeer"
    - Requires a [media player][] entity that is playing
- "hervat"
    - Requires a [media player][] entity that is paused
- "volgende nummer"
    - Requires a [media player][] entity to that is playing and supports next track
- "zet het volume op 50%"
    - Requires a  entity that supports volume control
"zet het volume harder/zachter"
    - Requires a  entity that supports volume control

## Timers

- "zet een timer voor 5 minuten"
    - minutes from 1-10, 15, 20, 30, 40, 45, 50-100 by 10s
- "zet een timer voor 30 seconde"
    - seconds from 10-100 by 5s
- "zet een timer voor 3 uur en 10 minuten"
    - hours from 1-24
- "pauzeer/hervat timer"
- "annuleer timer"
- "annuleer alle timers"
- "timer status"

## Scripts 

 - "start het Script Goede Nacht"
     - Requires a  entity named "Goede Nacht"

## Scenes
 - "activeer de Scène Avond"
     - Requires a  entity named "Avond"

## Climate
  - "zet de thermostaat op 21 graden"
     - Requires a  entity that supports temperature control

  - "verhoog/verlaag de temperatuur met 2 graden"
     - Requires a  entity that supports temperature control

## Miscellaneous

- "laat maar"

<!-- Links -->
[area]: https://www.home-assistant.io/docs/organizing/#area
[climate]: https://www.home-assistant.io/integrations/climate/
[cover]: https://www.home-assistant.io/integrations/cover/
[floor]: https://www.home-assistant.io/docs/organizing/#floor
[light]: https://www.home-assistant.io/integrations/light/
[lock]: https://www.home-assistant.io/integrations/lock/
[media player]: https://www.home-assistant.io/integrations/media_player/
[scene]: https://www.home-assistant.io/integrations/scene/
[script]: https://www.home-assistant.io/integrations/script/
[weather]: https://www.home-assistant.io/integrations/weather/

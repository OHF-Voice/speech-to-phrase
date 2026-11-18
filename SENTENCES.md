# Sentences

Available voice commands by category and language code.

* `ca` - Catalan
* `cs` - Czech
* `de` - German
* `el` - Greek
* `en` - English
* `es` - Spanish
* `eu` - Basque
* `fa` - Persian/Farsi
* `fi` - Finnish
* `fr` - French
* `hi` - Hindi
* `it` - Italian
* `mn` - Mongolian
* `nl` - Dutch
* `pl` - Polish
* `pt_PT` - Portuguese
* `ro` - Romanian
* `ru` - Russian
* `sl` - Slovenian
* `sv` - Swedish
* `sw` - Swahili
* `tr` - Turkish

**NOTE:**  Entities must first be [exposed][] in Home Assistant.

<!----------------------------------------------------------------------------->

## Cancel

Cancels the current command and does nothing:

| Language | Command      |
|----------|--------------|
| `ca`     | cancela      |
| `cs`     | nevadí       |
| `de`     | vergiss es   |
| `el`     | άστο         |
| `en`     | nevermind    |
| `es`     | no importa   |
| `eu`     | ez kezkatu   |
| `fa`     | مهم نیست     |
| `fi`     | ei mitään    |
| `fr`     | oublie       |
| `hi`     | कोई बात नहीं  |
| `it`     | lascia stare |
| `mn`     | зүгээр       |
| `nl`     | laat maar    |
| `pl`     | nieważne     |
| `pt_PT`  | esquece      |
| `ro`     | lasă         |
| `ru`     | Неважно      |
| `sl`     | prekini      |
| `sv`     | stopp        |
| `sw`     | usijali      |
| `tr`     | önemli değil |

<!----------------------------------------------------------------------------->

## Devices

Works with these [entity domains][entities]:

* [light][light]
* [switch][switch]
* [fan][fan]
* [media_player][media_player]
* [input_boolean][input_boolean]

| Language | Command                                          |
|----------|--------------------------------------------------|
| `ca`     | encén/apaga `{name}`                             |
| `cs`     | zapni/vypnout [světlo] `{name}`                  |
| `de`     | schalte/mache `{name}` an/aus                    |
| `el`     | άναψε/σβήσε `{name}`                             |
| `en`     | turn on/off `{name}`                             |
| `es`     | enciende/prende/apaga `{name}`                   |
| `eu`     | piztu/itzali/aktibatu/desaktibatu `{name}`       |
| `fa`     | `{name}` را/رو روشن/خاموش کن                     |
| `fi`     | kytke päälle/päältä `{name}`                     |
| `fr`     | allume/éteins/éteindre `{name}`                  |
| `hi`     | `{name}` को चालू/बंद करो                           |
| `it`     | accendi/spegni `{name}`                          |
| `mn`     | `{name}` асаа/унтраа                             |
| `nl`     | zet/doe `{name}` aan/uit                         |
| `pl`     | włącz/uruchom/wyłącz/zatrzymaj `{name}`          |
| `pt_PT`  | liga/desliga/ativa/apaga `{name}`                |
| `ro`     | pornește/oprește/activează/dezactivează `{name}` |
| `ru`     | включи/выключи/отключи `{name}`                  |
| `sl`     | vklopi/izklopi `{name}`                          |
| `sv`     | slå på / stäng av `{name}`                       |
| `sw`     | washa/zima `{name}`                              |
| `tr`     | `{name}` aç/yak/çalıştır/kapat/söndür            |

<!----------------------------------------------------------------------------->

## Date and Time

| Language | Command                                                |
|----------|--------------------------------------------------------|
| `ca`     | - quina hora és <br> - quin dia és                     |
| `cs`     | - kolik je hodin <br> - jaké je datum                  |
| `de`     | - wie spät ist es <br> - welchen tag haben wir heute   |
| `en`     | - what time is it? <br> - what's the date?             |
| `es`     | - qué hora es? <br> - qué día es?                      |
| `fi`     | - Paljonko kello on? <br> - mikä päivä tänään?         |
| `fr`     | - quel jour sommes-nous? <br> - quelle heure est-il?   |
| `nl`     | - hoe laat is het? <br> - wat is de tijd?              |
| `pl`     | - jaką mamy godzinę? <br> - jaka jest dzisiejsza data? |
| `pt_PT`  | - que horas são? <br> - que dia é hoje?                |
| `ro`     | - cat este ora? <br> - ce dată este astăzi?            |
| `ru`     | какое сегодня число                                    |
| `sl`     | - koliko je ura? <br> - kateri dan je danes?           |
| `sv`     | - Vad är klockan? <br> - Vilket datum är det?          |

<!----------------------------------------------------------------------------->

## Lights

Requires at least one [light][] entity in the same [area][] as the voice satellite:

| Language | Command                             |
|----------|-------------------------------------|
| `en`     | turn on/off the lights              |
| `es`     | enciende/prende/apaga las luces     |
| `fr`     | allume/éteins/éteindre les lumières |
| `it`     | accendi/spegni le luci              |
| `nl`     | zet/doe lamp aan/uit                |
| `sv`     | slå av/på lamporna                  |

Requires at least one [light][] entity in an [area][] with the specific name or [alias][aliases]:

| Language | Command                                           |
|----------|---------------------------------------------------|
| `en`     | turn on/off lights in the `{area}`                |
| `es`     | enciende/prende/apaga las luces `{area}`          |
| `fr`     | allume/éteins/éteindre les lumières dans `{area}` |
| `it`     | accendi/spegni le luci in `{area}`                |
| `nl`     | zet/doe lampen in `{area}` aan/uit                |
| `sv`     | slå av/på lamprona i `{area}`                     |

### Brightness

Requires at least one [light][] entity that supports setting brightness in the same [area][] as the voice satellite:

| Language | Command                                  |
|----------|------------------------------------------|
| `en`     | set the brightness to 50 percent         |
| `fr`     | règle/régler la luminosité à 50 pourcent |
| `sv`     | sätt/ändra ljusstyrkan till 50 percent   |

Requires at least one [light][] entity that supports setting brightness in an [area][] with the specific name or [alias][aliases]:

| Language | Command                                                |
|----------|--------------------------------------------------------|
| `en`     | set `{area}` brightness to 50 percent                  |
| `es`     | ajusta el brillo `{area}` al 50 por ciento             |
| `fr`     | règle/régler la luminosité dans `{area}` à 50 pourcent |
| `it`     | imposta la luminosità in `{area}` al 50 percento       |
| `nl`     | maak helderheid van `{area}` naar 50 procent           |
| `sv`     | sätt/ändra `{area}` ljusstyrka till 50 percent         |

Requires a [light][] entity that supports setting brightness with the specific name or [alias][aliases]:

| Language | Command                                           |
|----------|---------------------------------------------------|
| `en`     | set `{name}` brightness to 50 percent             |
| `es`     | ajusta el brillo de `{name}` al 50 por ciento     |
| `fr`     | règle/régler la luminosité `{name}` à 50 pourcent |
| `it`     | imposta la luminosità `{name}` al 50 percento     |
| `nl`     | maak helderheid van {name} naar 50 procent        |
| `sv`     | sätt/ändra `{name}` ljusstyrka till 50 percent    |

### Color

Requires at least one [light][] entity that supports setting color in the same [area][] as the voice satellite:

| Language | Command                                   |
|----------|-------------------------------------------|
| `en`     | set lights to red                         |
| `fr`     | allume/règle/régler les lumières en rouge |
| `sv`     | sätt/ändra lamporna till röd              |

Requires at least one [light][] entity that supports setting color in an [area][] with the specific name or [alias][aliases]:

| Language | Command                                            |
|----------|----------------------------------------------------|
| `en`     | set `{area}` lights to red                         |
| `es`     | ajusta el color de las luces `{area}` a rojo       |
| `fr`     | allume/règle/régler les lumières `{area}` en rouge |
| `it`     | imposta le luci in `{area}` su rosso               |
| `nl`     | maak `{area}` naar rood                            |
| `sv`     | sätt/ändra `{area}` lampor till röd                |

Requires a [light][] entity that supports setting color with the specific name or [alias][aliases]:

| Language | Command                               |
|----------|---------------------------------------|
| `en`     | set `{name}` to red                   |
| `es`     | ajusta el color de `{name}` a rojo    |
| `fr`     | allume/règle/régler `{name}` en rouge |
| `it`     | imposta `{name}` su rosso             |
| `nl`     | maak `{name}` naar rood               |
| `sv`     | sätt/ändra `{name}` till röd          |

<!----------------------------------------------------------------------------->

## Weather

Requires a [weather][] entity to be configured:

| Language | Command               |
|----------|-----------------------|
| `de`     | wie ist das Wetter?   |
| `el`     | τι καιρό κάνει        |
| `en`     | what's the weather?   |
| `es`     | qué tiempo hace?      |
| `fr`     | quel temps fait-il?   |
| `it`     | che tempo fa?         |
| `nl`     | wat voor weer is het? |
| `ru`     | какая сейчас погода?  |
| `sv`     | hur/vad är vädret?        |

Requires a [weather][] entity with the specific name or [alias][aliases]:

| Language | Command                                |
|----------|----------------------------------------|
| `de`     | wie ist das Wetter in `{name}`?        |
| `el`     | τι καιρό κάνει στο `{name}`            |
| `en`     | what's the weather in `{name}`?        |
| `es`     | qué tiempo hace en `{name}`?           |
| `fr`     | quel temps fait-il à `{name}`?         |
| `it`     | che tempo fa a `{name}`?               |
| `nl`     | wat voor weer is het voor in `{name}`? |
| `ru`     | Какая погода в `{name}`?               |
| `sv`     | Vad är vädret i `{name}`?              |

<!----------------------------------------------------------------------------->

## Temperature

Requires a [climate][] entity to be configured:

| Language | Command                    |
|----------|----------------------------|
| `en`     | what's the temperature?    |
| `es`     | cuál es la temperatura?    |
| `fr`     | quelle est la température? |
| `it`     | qual è la temperatura?     |
| `nl`     | wat is de temperatuur?     |
| `sv`     | Vad är temperaturen?       |


Requires a [climate][] entity with the specific name or [alias][aliases]:

| Language | Command                                 |
|----------|-----------------------------------------|
| `en`     | what's the temperature of the `{name}`? |
| `es`     | cuál es la temperatura de `{name}`?     |
| `nl`     | wat is de `{name}` temperatuur?         |
| `sv`     | Vad är temperaturen på `{name}`?        |


<!----------------------------------------------------------------------------->

## Doors and Windows

Requires a [cover][] entity with the specific name or [alias][aliases]:

| Language | Command                                                            |
|----------|--------------------------------------------------------------------|
| `de`     | - öffne/schließe `{name}`                                          |
| `en`     | - open/close the `{name}` <br> - is the `{name}` open/closed?      |
| `es`     | - abre/cierra/cerrá `{name}` <br> - está `{name}` abierta/cerrada? |
| `fr`     | - ouvre/ouvrir/ferme `{name}`                                      |
| `it`     | - apri/chiudi `{name}`                                             |
| `nl`     | - open/sluit  `{name}` <br> - is/staat `{name}` gesloten/dicht     |
| `sv`     | - öppna/ stäng `{name}` <br> - är `{name}` öppen/stängd?           |

<!----------------------------------------------------------------------------->

## Locks

Requires a [lock][] entity with the specific name or [alias][aliases]:

| Language | Command                                                                                                                      |
|----------|------------------------------------------------------------------------------------------------------------------------------|
| `en`     | - lock/unlock the `{name}` <br> - is the `{name}` locked/unlocked?                                                           |
| `es`     | - cierra/cerrá con llave `{name}` <br> - abre `{name}` <br> - está cerrada con llave `{name}`? <br> - está abierta `{name}`? |
| `fr`     | - verrouille/déverrouille `{name}`                                                                                           |
| `nl`     | - vergrendel/ontgrendel   `{name}` <br> - is/staat `{name}` op slot/vergrendeld/open/ontgrendeld                             |
| `sv`     | - lås/lås upp `{name}` <br> - är `{name}` låst/upplåst?                                                                      |

<!----------------------------------------------------------------------------->

## Sensors

Requires a [sensor][] entity with the specific name or [alias][aliases]:

| Language | Command                            |
|----------|------------------------------------|
| `en`     | what is the value of the `{name}`? |
| `es`     | cuál es `{name}`?                  |
| `fr`     | quel est `{name}`?                 |
| `nl`     | wat is de status van `{name}`?     |
| `sv`     | vad är värdet på `{name}`?         |

<!----------------------------------------------------------------------------->

## Media

Requires a [media player][media_player] entity in the same [area][] as the voice satellite:

| Language | Command                                   |
|----------|-------------------------------------------|
| `de`     | pause/Weiter/nächster Titel               |
| `en`     | pause/resume/next                         |
| `es`     | pausa/continúa/siguiente canción          |
| `fr`     | pause/reprends/lecture/suivant            |
| `it`     | pausa/riprendi/vai avanti                 |
| `nl`     | pauzeer/stop/hervat/volgende/sla dit over |
| `sv`     | pausa/försätt/nästa                       |

The media player must be in the appropriate state and support the command.

Requires a [media player][media_player] entity with the specific name or [alias][aliases]:

| Language | Command                                                                                                 |
|----------|---------------------------------------------------------------------------------------------------------|
| `en`     | - pause/resume the `{name}` <br> - next on the `{name}`                                                 |
| `es`     | - pausa/continúa `{name}` <br> - siguiente canción en `{name}`                                          |
| `fr`     | - mets/mettre `{name}` en pause <br> - reprends/reprendre la lecture sur `{name}`                       |
| `nl`     | - pauzeer/stop/hervat `{name}` <br> - volgende nummer/track op `{name}` <br> - sla dit op `{name}` over |
| `sv`     | - pausa/försätt `{name}` <br> - nästa på `{name}`                                                       |

The media player must be in the appropriate state and support the command.

<!----------------------------------------------------------------------------->

## Timers

Supported durations:

* 10-60 seconds in steps of 5
* 1-19 and 20-60 minutes in steps of 5
* 1-24 hours


| Language | Command                                                                                                           |
|----------|-------------------------------------------------------------------------------------------------------------------|
| `en`     | - set a timer for 30 seconds <br> - set a timer for 5 minutes <br> - set a timer for 1 hour                       |
| `es`     | - inicia temporizador de 30 segundos <br> - inicia temporizador de 5 minutos <br> - inicia temporizador de 1 hora |
| `fr`     | - minuteur 30 secondes <br> - minuteur 5 minutes <br> - minuteur 1 heure                                          |
| `it`     | - imposta timer di 30 secondi <br> - imposta timer 10 minuti <br> - imposta un timer 1 ora                        |
| `nl`     | - zet/maak timer voor 30 seconden <br> - zet/maak timer voor 5 minuten <br> - zet/maak timer voor 1 uur           |
| `sv`     | - sätt en timer på¨30 sekunder <br> - sätt en timer på 5 minuter <br> - sätt en timer på 1 timme                  |

Minutes and seconds may be combined as well as hours and minutes:

| Language | Command                                                                                          |
|----------|--------------------------------------------------------------------------------------------------|
| `en`     | - set a timer for 5 minutes and 30 seconds <br> - set a timer for 1 hour and 5 minutes           |
| `es`     | - inicia temporizador de 10 minutos 45 segundos <br> - inicia temporizador de 1 hora y 8 minutos |
| `fr`     | - minuteur 10 minutes et 30 secondes <br> - minuteur 1 heure et 20 minutes                       |
| `it`     | imposta un timer 1 ora e 1 minuto                                                                |
| `nl`     | zet/maak timer voor 1 uur en 5 minuten minuto                                                    |
| `sv`     | - sätt en timer på 5 minuter och 30 sekunder <br> - sätt en timer på 1 timme och 5 minuter       |

Requires a timer to be set:

| Language | Command                                                                                                                                        |
|----------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `en`     | - pause/resume/cancel timer <br> - cancel all timers <br> - timer status                                                                       |
| `es`     | - pausa/continúa/cancela timer <br> - cancela todos los temporizadores <br> - estado de temporizador                                           |
| `fr`     | - mets/mettre le minuteur en pause <br> - supprime/reprends le minuteur <br> - supprimer tous les minuteurs <br> - combien de temps reste-t-il |
| `it`     | - annulla/cancella/metti in pausa/riprendi/continua timer <br> - annulla/cancella tutti timer <br> - stato timer                               |
| `nl`     | - annuleer/stop/pauzeer/hervat timer <br> - annuleer/stop/pauzeer/hervat alle de timer <br> - timer status                                     |
| `sv`     | - pausa/forsätt/avsluta timer <br> -stoppa alla timers <br> - timer status                                                                       |

<!----------------------------------------------------------------------------->

## Scenes and Scripts

Requires a [scene][] with the specific name or [alias][aliases]:

| Language | Command                   |
|----------|---------------------------|
| `de`     | aktiviere `{name}` Szene |
| `en`     | activate `{name}` scene   |
| `es`     | activa `{name}`           |
| `fr`     | active/lancer `{name}`    |
| `nl`     | activeer `{name}`         |
| `sv`     | aktivera `{name}` scen    |

Requires a [script][] with the specific name or [alias][aliases]:

| Language | Command                  |
|----------|--------------------------|
| `de`     | aktiviere `{name}` Skript |
| `en`     | run `{name}` script      |
| `es`     | ejecuta `{name}`         |
| `fr`     | active/lancer `{name}`   |
| `nl`     | start `{name}`           |
| `sv`     | kör/trigga `{name}`             |

<!----------------------------------------------------------------------------->

<!-- Links -->
[aliases]: https://www.home-assistant.io/voice_control/aliases/
[area]: https://www.home-assistant.io/docs/organizing/#area
[climate]: https://www.home-assistant.io/integrations/climate/
[cover]: https://www.home-assistant.io/integrations/cover/
[entities]: https://www.home-assistant.io/docs/configuration/entities_domains/
[exposed]: https://www.home-assistant.io/voice_control/voice_remote_expose_devices/
[fan]: https://www.home-assistant.io/integrations/fan/
[input_boolean]: https://www.home-assistant.io/integrations/input_boolean/
[light]: https://www.home-assistant.io/integrations/light/
[lock]: https://www.home-assistant.io/integrations/lock/
[media_player]: https://www.home-assistant.io/integrations/media_player/
[scene]: https://www.home-assistant.io/integrations/scene/
[script]: https://www.home-assistant.io/integrations/script/
[sensor]: https://www.home-assistant.io/integrations/sensor/
[switch]: https://www.home-assistant.io/integrations/switch/
[weather]: https://www.home-assistant.io/integrations/weather/

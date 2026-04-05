# Greek

## Date and Time

- "τι ώρα είναι;"
- "ποια είναι η ημερομηνία;"

## Weather and Temperature

- "πως είναι ο καιρός;"
    -  Requires a [weather][] entity to be configured
- "πως είναι ο καιρος στη Νέα Υόρκη;"
    - Requires a [weather][] entity named "New York"
- "ποια είναι η θερμοκρασία;"
    - Requires a [climate][] entity to be configured
- " ποια είναι η θερμοκρασία του EcoBee;"
    - Requires a [climate][] entity named "EcoBee"

## Lights

- "άναψε/σβήσε τα φώτα"
    - Requires voice satellite to be in an [area][]
- "άναψε/σβήσε το standing light"
    - Requires a [light][] entity named "standing light"
- "άναψε/σβήσε τα φώτα στην κουζίνα"
    - Requires an [area][] named "κουζίνα"
- "άναψε/σβήσε τα φώτα στον πρώτο όροφο"
    - Requires a [floor][] named "πρώτο όροφο"
- "όρισε τα φώτα της κουζίνας σε πράσινο"
    - Requires an [area][] named "κουζίνα" with at least one [light][] entity in it that supports setting color
- "όρισε τη φωτεινότητα του bed light στο 100 τοις εκατό"
    - Requires a [light][] entity named "bed light" that supports setting brightness
    - Brightness from 10-100 by 10s

## Sensors

- "ποια είναι η εξωτερική υγρασία"
    - Requires a [sensor][] entity named "εξωτερική υγρασία"

## Doors and Windows

- "άνοιξε/κλείσε την γκαραζόπορτα"
    - Requires a [cover][] entity named "γκαραζόπορτα"
- "είναι η γκαραζόπορτα ανοικτή/κλεστή;"
    - Requires a [cover][] entity named "γκαραζόπορτα"

## Locks

- "κλείδωσε/ξεκλείδωσε την μπροστινή πόρτα"
    - Requires a [lock][] entity named "μπροστινή πόρτα"
- "είναι η μπροστινή πόρτα κλειδωμένη/ξεκλείδωτη;"
    - Requires a [lock][] entity named "μπροστινή πόρτα"

## Media

- "παύση"
    - Requires a [media player][] entity that is playing 
- "συνέχισε"
    - Requires a [media player][] entity that is paused
- "επόμενο"
    - Requires a [media player][] entity that is playing and supports next track

## Timers

- "όρισε ένα χρονόμετρο για πέντε λεπτά"
    - minutes from 1-10, 15, 20, 30, 40, 45, 50 - 100 by 10s
- "όρισε ένα χρονόμετρο για τριάντα δευτερόλεπτα"
    - seconds from 10-100 by 5s
- "όρισε ένα χρονόμετρο για τρεις ώρες και δέκα λεπτά"
    - hours from 1-24
- "παύση/συνέχισε το χρονόμετρο"
- "ακύρωσε το χρονόμετρο"
- "ακύρωσε όλα τα χρονόμετρα"
- "πόσος χρόνος απομένει στο χρονόμετρο;"

## Scenes and Scripts

- "εκτέλεσε το party time"
    - Requires a [script][] named "party time"
- "ενεργοποίησε το mood lighting"
    - Requires a [scene][] named "mood lighting" 

## Miscellaneous

- "άκυρο"

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
[sensor]: https://www.home-assistant.io/integrations/sensor/
[weather]: https://www.home-assistant.io/integrations/weather/
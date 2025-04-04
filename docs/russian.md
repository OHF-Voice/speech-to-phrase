# Russian (Русский)

## Дата и время

- "который сейчас час?"
- "какое сегодня число?"

## Погода и температура

- "какая сейчас погода?"
    - Requires a [weather][] entity to be configured
- "какая погода в Нью-Йорке?"
    - Requires a [weather][] entity named "New York"
- "какая температура?"
    - Requires a [climate][] entity to be configured
- "какая температура в EcoBee?"
    - Requires a [climate][] entity named "EcoBee"
    
## Свет

- "включи/выключи свет"
    - Requires voice satellite to be in an [area][]
- "включи/выключи светильник"
    - Requires a [light][] entity named "светильник"
- "включи/выключи свет на кухне"
    - Requires an [area][] named "кухня"
- "включи/выключи свет на первом этаже"
    - Requires a [floor][] named "первый этаж"
- "включи зеленый свет на кухне"
    - Requires an [area][] named "кухня" with at least one [light][] entity in it that supports setting color
- "установи яркость ночника на 100 процентов"
    - Requires a [light][] entity named "ночник" that supports setting brightness
    - Brightness from 10-100 by 10s

## Датчики

- "какая влажность на улице?"
    - Requires a [sensor][] entity named "влажность на улице"

## Двери и окна

- "открой/закрой гаражные ворота"
    - Requires a [cover][] entity named "гаражные ворота"
- "гаражные ворота открыты/закрыты?"
    - Requires a [cover][] entity named "гаражные ворота"
    
## Замки

- "Запри/отопри входную дверь"
    - Requires a [lock][] entity named "входная дверь"
- "Входная дверь заперта/незаперта?"
    - Requires a [lock][] entity named "входная дверь"

## Мультимедиа

- "пауза"
    - Requires a [media player][] entity that is playing
- "продолжи"
    - Requires a [media player][] entity that is paused
- "дальше"
    - Requires a [media player][] entity to that is playing and supports next track

## Таймеры

- "установи таймер на пять минут"
    - minutes from 1-10, 15, 20, 30, 40, 45, 50-100 by 10s
- "установи таймер на тридцать секунд"
    - seconds from 10-100 by 5s
- "установи таймер на три часа и десять минут"
    - hours from 1-24
- "приостанови/возобнови таймер"
- "отмени таймер"
- "отмени все таймеры"
- "статус таймера"

## Сцены и сценарии

- "запусти вечеринку"
    - Requires a [script][] named "вечеринка"
- "активируй освещение по настроению"
    - Requires a [scene][] named "освещение по настроению"

## Разное

- "неважно"

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

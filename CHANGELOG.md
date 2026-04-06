# Changelog

## 1.4.3

- Fix for null names

## 1.4.2

- More German and Spanish sentences

## 1.4.1

- More robust parsing of `ask_question` answers from Home Assistant
- Remove intent probability normalization
- Revert to Kneser-Ney smoothing instead of Witten-Bell
- Re-add German timer sentences

## 1.4.0

- Load answers from `assist_satellite.ask_question` in automations and scripts
- Add supported features to `light`, `fan`, `cover`, and `media_player` domains (used in `requires_context`)
    - `light_supports_color` (color mode is hs/rgb/rgbw/rgbww/xy)
    - `light_supports_brightness` (color mode is hs/rgb/rgbw/rgbww/xy/brightness/white)
    - `fan_supports_speed` - fan has `SET_SPEED` feature
    - `cover_supports_position` - cover has `SET_POSITION` feature
    - `media_player_supports_pause` - media player has `PAUSE` feature
    - `media_player_supports_volume_set` - media player has `VOLUME_SET` feature
    - `media_player_supports_next_track` - media player has `NEXT_TRACK` feature
- Change timer minutes to 1-20

## 1.3.0

- Add Coqui STT
- Support range fractions in custom sentences (https://github.com/OHF-Voice/speech-to-phrase/issues/5)
- Do full re-train at startup (https://github.com/OHF-Voice/speech-to-phrase/issues/11)
- Remove websocket command message limit (https://github.com/OHF-Voice/speech-to-phrase/issues/6)
- Bump `unicode-rbnf` to 2.3.0 (https://github.com/OHF-Voice/speech-to-phrase/issues/15)

## 1.2.0

- Split words on dashes `-` and underscores `_`
- Remove template syntax from names (`[]<>{}()`)

## 1.1.0

- Add custom sentences

## 1.0.1

- Fix "turn on/off all of the lights in {area}" for English

## 1.0.0

- First public release

## 0.0.1

- Beta release

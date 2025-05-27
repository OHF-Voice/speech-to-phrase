# Contributing

Contributions to Speech-to-Phrase are welcome! There are two parts that are required for a language to be supported:

1. A [speech-to-text model](#speech-to-text-models)
2. A set of [sentence templates](#snetence-templates)

Not all speech-to-text models and sentence templates are usable in Speech-to-Phrase. All models must be able to run quickly on a Raspberry Pi 4 (less than 1 second of processing time), and all sentences must be [recognized by Home Assistant](https://github.com/home-assistant/intents/).


## Speech-to-Text Models

There are currently two types of supported speech-to-text models:

* [Kaldi][kaldi]
* [Coqui STT][coqui-stt]

Pre-packaged models are available to [download from HuggingFace][model-download].

### Kaldi

These are [nnet3][] models that also have a [Phonetisaurus][] grapheme-to-phoneme (g2p) model for guessing word pronunciations. 

Some of the models were trained with [ipa2kaldi][]. See the [English model][english-model] for an example.

### Coqui STT

These models were [downloaded from GitHub][coqui-models] and repackaged for Speech-to-Phrase. Fortunately, the scorers are not needed because we only use the raw probabilities from the Coqui STT model. The language model probabilities are generated during Speech-to-Phrase's training.

<!----------------------------------------------------------------------------->

## Sentence Templates

Speech-to-Phrase trains itself based on Home Assistant's [exposed][]:

* [entities][]
* [areas][area]
* [floors][floor]

Importantly, all of the sentences that Speech-to-Phrase can match must be recognizable by [Home Assistant][intents]. If a sentence is not supported, it must be added by the appropriate [language leader][language-leaders].

Sentence templates for each language are stored in `speech_to_phrase/sentences` and have the following YAML format:

```yaml
language: "<language code>"

lists:
  <list_name>:
    - "list value 1"
    - "list value 2"
    - "..."
    
data:
  - "[a] sentence template"
  - "..."
  - sentences:
      - "sentence template with {name}"
      - "..."
    domains:
      - "{name} domain 1"
      - "{name} domain 2"
      - "..."
```

Sentence templates are written using the [hassil][hassil-syntax] syntax with some restrictions:

* No expansion rules (`<rule_name>`)
* List names cannot be inside an optional (`[{list_name}]`) or alternative (`(a|{list_name})`)

These restrictions are intended to reduce the possible complexity of Speech-to-Phrase sentence templates. The performance of the [speech-to-text models](#speech-to-text-models) degrades as the number of possible sentences increases, so it's best to keep it small.

There are 3 builtin lists that come from Home Assistant:

* `{name}` - entity names/aliases + domains
* `{area}` - area names/aliases
* `{floor}` - floor names/aliases

When using `{name}`, you **must** use a sentence block (`sentences`) and provide the entity `domains` that can be matched. 

When writing sentences for light brightness and timers, the following shared lists should be used:

* `{brightness}` - brightness levels from 0-100 in steps of 10
* `{seconds}` - seconds from 10-100 in steps of 5
* `{minutes}` - minutes from 2-20, then 20-100 in steps of 10, plus 45
* `{hours}` - hours from 2-24

These lists strike a balance between covering what users will likely use and keeping the number of possible sentences small. Note that `{seconds}`, `{minutes}`, and `{hours}` do not include the value 1. Since this is almost always handled differently grammatically (1 minute vs. 2 minutes), you need to add timer sentences specifically for values of 1.

### Supported Features

A sentence block can be restricted to entities with specific features, such as whether or not a light supports setting its brightness level or color:

```yaml
data:
  - sentences:
      - "set {name} brightness to {brightness}"
    domains:
      - "light"
    light_supports_brightness: true

  - sentences:
      - "set {name} color to {color}"
    domains:
      - "light"
    light_supports_color: true
```

The following features are available:

* `light_supports_brightness` - light entity supports setting brightness level
* `light_supports_color` - light entity supports setting color
* `fan_supports_speed` - fan entity supports setting speed
* `cover_supports_position` - cover entity supports setting position
* `media_player_supports_pause` - media player entity can be paused
* `media_player_supports_next_track` - media player entity can skip to next track
* `media_player_supports_volume_set` - media player entity volume can be set

### List Transformations

Some languages, such as French and Italian, have sentences that contain parts like `l'{name}` and `dell'{name}` where `{name}` should only start with a vowel (or "h" in French). Speech-to-Phrase needs to be aware of these language rules to avoid generating unnecessary possible sentences.

A transformed list can be created by first specifying a transformation:

```yaml
transformations:
  le:
    # If the regular expression matches...
    - match: "^[hàâäéèêëîïôöùûüÿaeiou]"
      # ...output these strings with the matching value:
      outputs:
        - "l'{value}"
        - "{value}"
    # If no matches, output these strings with the value:
    - outputs:
        - "le {value}"
        - "la {value}"
        - "les {value}"
        - "{value}"
```

When applied to a value, the `le` transformation will try to match a vowel or "h" at the start. If it matches, it will output the value with `l'` prefixed as well as the plain value. If the match fails, the prefixes `le/la/les` are added instead.

Now a transformed list can be defined:

```yaml
transformed_lists:
  le_name:
    source: "name"
    transformations:
      - "le"
```

The transformed `{name}` list can now be accessed as `{le_name}`. This is like a smart version of `[le |la |les |l']{name}` that will only output `l'{name}` if `{name}` starts with a vowel or "h".

Multiple transformed lists can be created from the same transformation:

```yaml
transformed_lists:
  le_name:
    source: "name"
    transformations:
      - "le"
  le_area:
    source: "area"
    transformations:
      - "le"
  le_floor:
    source: "floor"
    transformations:
      - "le"
```

### Tests

Sentence templates are tested to ensure that every possible sentence can be recognized by Home Assistant. This can be slow if there are many possible sentences, which is another reason to keep things as small as possible.

To test transcriptions, a fixtures file must be added at `tests/fixtures/<language>.yaml` with:

```yaml
language: "<language code>"

fixtures:
  floors:
    - name: "Floor name"
    - name: "..."

  areas:
    - name: "Area name"
    - name: "..."

  entities:
    - name: "Entity name"
      domain: "entity_domain"

    - name: "..."
      domain: "..."
```

Supported features can also be added to entities:

```yaml
fixtures:
  entities:
    - name: "Bed Light"
      domain: "light"
      light_supports_brightness: true
      light_supports_color: true
```


<!-- Links -->
[entities]: https://www.home-assistant.io/docs/configuration/entities_domains/
[area]: https://www.home-assistant.io/docs/organizing/#area
[floor]: https://www.home-assistant.io/docs/organizing/#floor
[exposed]: https://www.home-assistant.io/voice_control/voice_remote_expose_devices/
[intents]: https://github.com/home-assistant/intents
[language-leaders]: https://developers.home-assistant.io/docs/voice/language-leaders/
[kaldi]: https://kaldi-asr.org/
[coqui-stt]: https://stt.readthedocs.io/en/latest/
[nnet3]: https://kaldi-asr.org/doc/dnn3.html
[phonetisaurus]: https://github.com/AdolfVonKleist/Phonetisaurus
[model-download]: https://huggingface.co/datasets/rhasspy/rhasspy-speech/tree/main/models
[english-model]: https://huggingface.co/datasets/rhasspy/rhasspy-speech/resolve/main/models/en_US-rhasspy.tar.gz?download=true
[ipa2kaldi]: https://github.com/rhasspy/ipa2kaldi
[coqui-models]: https://github.com/coqui-ai/STT-models
[hassil]: https://github.com/home-assistant/hassil
[hassil-syntax]: https://github.com/home-assistant/hassil?tab=readme-ov-file#sentence-templates

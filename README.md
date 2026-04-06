<h1>
  <img src="icon.png" alt="Speech-to-phrase logo" height="42" align="top">
  Speech-to-Phrase
</h1>

A fast and local speech-to-text system that is personalized with your [Home Assistant](https://www.home-assistant.io/) device and area names.

Speech-to-phrase is not a general purpose speech recognition system. Instead of answering the question "what did the user say?", it answers "which of the phrases I know did the user say?".
This is accomplished by combining [pre-defined sentence templates](speech_to_phrase/sentences) with the names of your Home Assistant [entities, areas, and floors](https://www.home-assistant.io/getting-started/concepts-terminology/) that have been [exposed to Assist](https://www.home-assistant.io/voice_control/voice_remote_expose_devices/).

[![Show add-on](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_speech-to-phrase)

## Supported languages

- English
- Français (French)
- Deutsch (German)
- Nederlands (Dutch)
- Spanish (Español)
- Italian (Italiano)
- Русский (Russian)
- Čeština (Czech)
- Català (Catalan)
- Greek (Ελληνικά)
- Română (Romanian)
- Português (Portuguese, Portugal)
- Polski (Polish)
- हिन्दी (Hindi)
- Euskara (Basque)
- Suomi (Finnish)
- монгол хэл (Mongolian)
- Slovenščina (Slovenian)
- Kiswahili (Swahili)
- ภาษาไทย (Thai)
- Türkçe (Turkish)

[Supported voice commands](SENTENCES.md) vary by language.

## Custom sentences

You can add your [own sentences and list values][custom_sentences] with `--custom-sentences-dir <DIR>` where `<DIR>` contains directories of YAML files per language. For example:

``` sh
python3 -m speech_to_phrase ... --custom-sentences-dir /path/to/custom_sentences
```

For an English model, you could have `/path/to/custom_sentences/en/sentences.yaml` with:

``` yaml
language: "en"
lists:
  todo_item:
    values:
      - "apples"  # make sure to use quotes!
      - "bananas"
```

This would allow you to say "add apples to my shopping list" if you have a [todo][] entity in Home Assistant exposed with the name "shopping list".

You can also create lists with the same names as your [sentence trigger wildcards][sentence_wildcards] to make them usable in speech-to-phrase.

## Docker container

A Docker container is available that can be connected to Home Assistant via the [wyoming integration][wyoming]:

``` sh
docker run -it -p 10300:10300 \
  -v /path/to/download/models:/models \
  -v /path/to/train:/train \
  rhasspy/wyoming-speech-to-phrase \
  --hass-websocket-uri 'ws://homeassistant.local:8123/api/websocket' \
  --hass-token '<LONG_LIVED_ACCESS_TOKEN>' \
  --retrain-on-start
```

## Models and tools

Speech models and tools are downloaded automatically from [HuggingFace](https://huggingface.co/datasets/rhasspy/rhasspy-speech/tree/main)


## How it works

Speech-to-phrase combines [pre-defined sentence templates](speech_to_phrase/sentences) with the names of things from your Home Assistant to produce a [hassil](https://github.com/home-assistant/hassil) template file. This file compactly represents all of the possible sentences that can be recognized, which may be hundreds, thousands, or even millions.

Using techniques developed in the [Rhasspy project](https://rhasspy.readthedocs.io/en/latest/whitepaper/), speech-to-phrase converts the compact sentence templates into a [finite state transducer]((https://www.openfst.org)) (FST) which is then used to train a language model for [Kaldi](https://kaldi-asr.org/). The [opengrm](https://www.opengrm.org) tooling is crucial for efficiency during this step, as it avoids unpacking the sentence templates into every possible combination.

Each speech-to-phrase model contains a pre-built dictionary of word pronunciations as well as a [phonetisaurus](https://github.com/AdolfVonKleist/Phonetisaurus) model that will guess pronunciations for unknown words.

During training, a lot of "magic" happens to ensure that your entity, area, and floor names can be recognized automatically:

* Words with numbers are split apart ("PM2.5" becomes "PM 2.5")
* Initialisms are further split ("PM" or "P.M." becomes "P M")
* Digits are replaced with their [spoken word forms](https://github.com/rhasspy/unicode-rbnf) ("123" becomes "one hundred twenty three")
* Unknown words have their pronunciations guessed

To make phrase recognition more robust, a "fuzzy" layer is added on top of Kaldi's transcription output. This layer can correct small errors, such as duplicate or missing words, and also ensures that output names are exactly what you have in Home Assistant.


[custom_sentences]: https://www.home-assistant.io/voice_control/custom_sentences_yaml/#setting-up-sentences-in-the-config-directory
[todo]: https://www.home-assistant.io/integrations/todo
[sentence_wildcards]: https://www.home-assistant.io/docs/automation/trigger/#sentence-wildcards
[wyoming]: https://www.home-assistant.io/integrations/wyoming

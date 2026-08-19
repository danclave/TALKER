# languages.py
# static language tables shared by providers, settings menu and prompts

################################################################################################
# WHISPER LANGUAGES (99, ISO-639-1)
################################################################################################

LANGUAGES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "as": "Assamese",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fo": "Faroese",
    "fr": "French",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lb": "Luxembourgish",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "nn": "Nynorsk",
    "no": "Norwegian",
    "oc": "Occitan",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "tk": "Turkmen",
    "tl": "Tagalog",
    "tr": "Turkish",
    "tt": "Tatar",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "yue": "Cantonese",
    "zh": "Chinese",
}

# Menu display order: English and Russian first, everything else alphabetical by name.
_PRIORITY = ["en", "ru"]


def language_display_order():
    codes = sorted(
        (code for code in LANGUAGES if code not in _PRIORITY),
        key=lambda c: LANGUAGES[c].lower(),
    )
    return _PRIORITY + codes


def language_name(code):
    return LANGUAGES.get((code or "").lower())


################################################################################################
# VOSK SMALL MODELS (~40 MB each)
# Static map: language code -> (model folder name, download URL)
# Sourced from https://alphacephei.com/vosk/models - update rarely, if ever.
################################################################################################

VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/"

VOSK_MODELS = {
    "en": "vosk-model-small-en-us-0.15",
    "ru": "vosk-model-small-ru-0.22",
    "de": "vosk-model-small-de-0.15",
    "fr": "vosk-model-small-fr-0.22",
    "es": "vosk-model-small-es-0.42",
    "it": "vosk-model-small-it-0.22",
    "pt": "vosk-model-small-pt-0.3",
    "pl": "vosk-model-small-pl-0.22",
    "uk": "vosk-model-small-uk-v3-small",
    "tr": "vosk-model-small-tr-0.3",
    "nl": "vosk-model-small-nl-0.22",
    "cs": "vosk-model-small-cs-0.4-rhasspy",
    "ca": "vosk-model-small-ca-0.4",
    "fa": "vosk-model-small-fa-0.5",
    "hi": "vosk-model-small-hi-0.22",
    "vi": "vosk-model-small-vn-0.4",
    "zh": "vosk-model-small-cn-0.22",
    "ar": "vosk-model-small-ar-0.3",
    "ja": "vosk-model-small-ja-0.22",
}


def vosk_model_name(code):
    return VOSK_MODELS.get((code or "").lower())


def vosk_model_url(code):
    name = vosk_model_name(code)
    return name and (VOSK_MODEL_URL + name + ".zip")

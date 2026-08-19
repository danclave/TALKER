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
    # languages/accents below exist only for the Vosk provider (or as accent variants)
    "ar-tn": "Arabic (Tunisian)",
    "en-gb": "English (British)",
    "en-in": "English (Indian)",
    "eo": "Esperanto",
    "ky": "Kyrgyz",
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
# VOSK MODELS (latest versions, Aug 2026)
# Static map: language code -> (model folder name, approximate size in MB)
# Sourced from https://alphacephei.com/vosk/models - update rarely, if ever.
# Codes marked BIG (>= VOSK_BIG_MB) are large models: slow and resource hungry.
################################################################################################

VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/"
VOSK_BIG_MB = 150  # models at least this size get a "big" warning

VOSK_MODELS = {
    "ar":    ("vosk-model-small-ar-0.3", 100),
    "ar-tn": ("vosk-model-small-ar-tn-0.1-linto", 158),
    "br":    ("vosk-model-br-0.8", 78),
    "ca":    ("vosk-model-small-ca-0.4", 41),
    "zh":    ("vosk-model-small-cn-0.3", 32),
    "cs":    ("vosk-model-small-cs-0.4-rhasspy", 44),
    "de":    ("vosk-model-small-de-0.15", 44),
    "el":    ("vosk-model-el-gr-0.7", 1063),
    "en":    ("vosk-model-small-en-us-0.4", 36),
    "en-gb": ("vosk-model-small-en-gb-0.15", 41),
    "en-in": ("vosk-model-small-en-in-0.4", 36),
    "eo":    ("vosk-model-small-eo-0.42", 42),
    "es":    ("vosk-model-small-es-0.42", 38),
    "fa":    ("vosk-model-small-fa-0.5", 59),
    "fr":    ("vosk-model-small-fr-0.22", 40),
    "gu":    ("vosk-model-small-gu-0.42", 103),
    "hi":    ("vosk-model-small-hi-0.22", 42),
    "it":    ("vosk-model-small-it-0.4", 33),
    "ja":    ("vosk-model-small-ja-0.22", 47),
    "ka":    ("vosk-model-small-ka-0.42", 44),
    "kk":    ("vosk-model-small-kz-0.42", 57),
    "ko":    ("vosk-model-small-ko-0.22", 83),
    "ky":    ("vosk-model-small-ky-0.42", 49),
    "nl":    ("vosk-model-small-nl-0.22", 39),
    "pl":    ("vosk-model-small-pl-0.22", 51),
    "pt":    ("vosk-model-small-pt-0.3", 31),
    # ru: 0.22 kept over newer 0.4 - 0.4 mis-recognizes common words (benchmarked Aug 2026)
    "ru":    ("vosk-model-small-ru-0.22", 44),
    "sv":    ("vosk-model-small-sv-rhasspy-0.15", 289),
    "te":    ("vosk-model-small-te-0.42", 58),
    "tg":    ("vosk-model-small-tg-0.22", 49),
    "tl":    ("vosk-model-tl-ph-generic-0.6", 314),
    "tr":    ("vosk-model-small-tr-0.3", 35),
    "uk":    ("vosk-model-small-uk-v3-small", 137),
    "uz":    ("vosk-model-small-uz-0.22", 49),
    "vi":    ("vosk-model-small-vn-0.4", 32),
}


def vosk_model_info(code):
    """Return (model_name, size_mb) for a language code, or None."""
    entry = VOSK_MODELS.get((code or "").lower())
    return tuple(entry) if entry else None


def vosk_model_name(code):
    info = vosk_model_info(code)
    return info[0] if info else None


def vosk_model_url(code):
    name = vosk_model_name(code)
    return name and (VOSK_MODEL_URL + name + ".zip")


def vosk_model_is_big(code):
    info = vosk_model_info(code)
    return bool(info and info[1] >= VOSK_BIG_MB)

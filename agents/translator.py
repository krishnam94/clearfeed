from googletrans import Translator

def translate_summary(text, target_lang):
    translator = Translator()
    lang_map = {'Hindi': 'hi', 'Spanish': 'es', 'English': 'en'}
    lang_code = lang_map.get(target_lang, 'en')
    try:
        translated = translator.translate(text, dest=lang_code)
        return translated.text
    except Exception:
        return text

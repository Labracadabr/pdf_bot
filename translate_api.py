import requests
from config import config

# API connect
# https://rapidapi.com/googlecloud/api/google-translate1/
APIKey = config.translate_token
headers = {
    "content-type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "application/gzip",
    "X-RapidAPI-Key": APIKey,
    "X-RapidAPI-Host": "google-translate1.p.rapidapi.com"
}


# распознать язык
def detect_lang(query: str) -> str | bool:
    url = "https://google-translate1.p.rapidapi.com/language/translate/v2/detect"
    response = requests.post(url, data={'q': query}, headers=headers)
    print('detect_lang status_code', response.status_code)
    # если ошибка запроса
    if not response.ok:
        return False

    data = response.json().get('data')
    print(f'{data = }')
    language = data.get('detections')[0][0].get('language')
    return language


# перевести текст
def translate(query: str, source: str, target: str, ) -> str | bool:
    """
    пример
    payload = {
        "q": "Hello, world!",
        "source": "en",
        "target": "es",
        }
    """
    payload = {
        "q": query,
        "source": source,
        "target": target,
    }
    url = "https://google-translate1.p.rapidapi.com/language/translate/v2"
    response = requests.post(url, data=payload, headers=headers)
    print('translate status_code', response.status_code)
    # если ошибка запроса
    if not response.ok:
        return False

    data = response.json().get('data')
    print(f'{data = }')
    translation = data.get('translations')[0].get('translatedText')
    return translation


# для проверки - существует ли язык (тут просто 100 языков, можно больше, наверное)
valid_codes = ["af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca", "ceb", "ny", "zh-cn", "zh",
               "zh-tw", "co", "hr", "cs", "da", "nl", "en", "eo", "et", "tl", "fi", "fr", "fy", "gl", "ka",
               "de", "el", "gu", "ht", "ha", "haw", "iw", "he", "hi", "hmn", "hu", "is", "ig", "id", "ga",
               "it", "ja", "jw", "kn", "kk", "km", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", "mg",
               "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no", "or", "ps", "fa", "pl", "pt", "pa", "ro",
               "ru", "sm", "gd", "sr", "st", "sn", "sd", "si", "sk", "sl", "so", "es", "su", "sw", "sv", "tg",
               "ta", "tt", "te", "th", "tr", "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu"
               ]

if __name__ == "__main__":
    print(detect_lang('merhaba benim adim mehmet'))

    print(translate(query='merhaba benim adim mehmet', target='ru', source='tr'))

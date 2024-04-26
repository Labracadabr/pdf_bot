import requests
from config import config

# API connect
# https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-translator-text/
APIKey = config.translate_token
url = "https://microsoft-translator-text.p.rapidapi.com/translate"
headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": APIKey,
    "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
}


# перевести текст
def translate(query: str, source: str, target: str, ) -> str:
    """
    пример
    "query": "Hello, world!",
    "source": "en",  # в этой версии source определяется сам
    "target": "es",
    """
    querystring = {"to[0]": target, "api-version": "3.0", "profanityAction": "NoAction", "textType": "plain"}
    payload = [{"Text": query}]
    response = requests.post(url, json=payload, headers=headers, params=querystring)
    print('translate status_code', response.status_code)

    # если ошибка запроса
    if not response.ok:
        error_message = f'ERROR status_code {response.status_code}\n{str(response.json())}'
        print(f'{error_message = }')
        return error_message

    data = response.json()
    print(f'{data = }')
    translation = data[0].get('translations')[0].get('text')
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
    pass
    print(translate(query='merhaba benim adim mehmet', target='ru', source='tr'))

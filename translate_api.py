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
def translate(query: str, target: str, ) -> str:
    """
    Язык исходника распознается сам. Пример ввода:
    "query": "Hello, world!",
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


# для проверки - существует ли язык (тут всё, что поддерживает api OCR)
language_codes = {
    'ar': 'ara',
    'bg': 'bul',
    'chs': 'chs',
    'cht': 'cht',
    'hr': 'hrv',
    'cs': 'cze',
    'da': 'dan',
    'nl': 'dut',
    'en': 'eng',
    'fi': 'fin',
    'fr': 'fre',
    'de': 'ger',
    'el': 'gre',
    'hu': 'hun',
    'ko': 'kor',
    'it': 'ita',
    'ja': 'jpn',
    'pl': 'pol',
    'pt': 'por',
    'ru': 'rus',
    'sl': 'slv',
    'es': 'spa',
    'sv': 'swe',
    'tr': 'tur'
}


if __name__ == "__main__":
    pass
    print(translate(query='merhaba benim adim mehmet', target='ru', ))

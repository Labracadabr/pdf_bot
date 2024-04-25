import requests
from config import config


# connect
APIKey = config.translate_token
headers = {
    "content-type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "application/gzip",
    "X-RapidAPI-Key": APIKey,
    "X-RapidAPI-Host": "google-translate1.p.rapidapi.com"
}


def detect_lang(query: str) -> str | bool:
    url = "https://google-translate1.p.rapidapi.com/language/translate/v2/detect"
    response = requests.post(url, data={'q': query}, headers=headers)
    print('detect_lang status_code', response.status_code)
    if not response.ok:
        return False

    data = response.json().get('data')
    print(f'{data = }')
    language = data.get('detections')[0][0].get('language')
    return language


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
    if not response.ok:
        return False

    data = response.json().get('data')
    print(f'{data = }')
    return data.get('translations')[0].get('translatedText')


if __name__ == "__main__":
    print(detect_lang('merhaba benim adim mehmet'))

    print(translate(query='merhaba benim adim mehmet', target='ru', source='tr'))

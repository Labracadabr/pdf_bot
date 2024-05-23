import requests
from config import config
from api_integrations.translate_api import language_codes

# api connect
# https://ocr.space/OCRAPI
apikey = config.ocr_token
api_url = 'https://api.ocr.space/parse/image'


# оптическое распознавание символов на картинке с помощью компьютерного зрения
def ocr_image(filename, language='eng') -> str:
    # перевести код языка из 2 символов в 3, например "tr" > "tur"
    if len(language) == 2:
        language = language_codes.get(language)

    # запрос
    payload = {'apikey': apikey, 'language': language, }
    with open(filename, 'rb') as f:
        response = requests.post('https://api.ocr.space/parse/image', files={filename: f}, data=payload,)
    print('OCR status_code', response.status_code)

    # если ошибка запроса
    if not response.ok:
        print('response.text', response.text)
        error_message = f'ERROR status_code {response.status_code}\n{str(response.json())}'
        print(f'{error_message = }')
        return error_message

    # текст из результата
    data = response.json()
    print(f'{data = }')
    parsed_text = data.get("ParsedResults")[0].get('ParsedText')
    return parsed_text


if __name__ == "__main__":
    pdf_file_path = 'Заказ.pdf'
    pdf_file_path = 'test_pdf.pdf'


import requests
from config import config
from translate_api import language_codes

# api connect
# https://ocr.space/OCRAPI
apikey = config.ocr_token
api_url = 'https://api.ocr.space/parse/image'


# оптическое распознавание символов на картинке с помощью компьютерного зрения
def ocr_image(filename, overlay=False, language='eng') -> str:
    """ OCR.space API request with local file.
        Python3.5 - not tested on 2.7
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    # перевести код языка из 2 символов в 3, например "tr" > "tur"
    language = language_codes.get(language)

    # запрос
    payload = {'isOverlayRequired': overlay,
               'apikey': apikey,
               'language': language,
               }
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


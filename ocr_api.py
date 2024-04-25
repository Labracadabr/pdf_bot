import requests
from config import config

# api connect
apikey = config.ocr_token
api_url = 'https://api.ocr.space/parse/image'


def ocr_pdf(file_path):
    # Open the PDF file
    with open(file_path, 'rb') as file:
        # Prepare data for POST request
        payload = {
            'apikey': apikey,
            'filetype': 'PDF',
            'language': 'rus',  # Language code (e.g., 'eng' for English)
        }

        # POST request to OCR.Space API
        response = requests.post(api_url, files={file_path: file}, data=payload)

    print(f'{response.status_code = }')
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        parsed_text = result['ParsedResults'][0]['ParsedText']
        return parsed_text
    else:
        print("Error:", response.status_code)
        return None


def ocr_space_file(filename, overlay=False, language='eng'):
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

    payload = {'isOverlayRequired': overlay,
               'apikey': apikey,
               'language': language,
               }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image', files={filename: f}, data=payload,)
    return r.content.decode()


def ocr_space_url(url, overlay=False, language='eng'):
    """ OCR.space API request with remote file.
        Python3.5 - not tested on 2.7
    :param url: Image url.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'url': url,
               'isOverlayRequired': overlay,
               'apikey': apikey,
               'language': language,
               }
    r = requests.post('https://api.ocr.space/parse/image', data=payload,)
    return r.content.decode()


if __name__ == "__main__":
    pdf_file_path = 'Заказ.pdf'
    pdf_file_path = 'test_pdf.pdf'
    # Call the function with your PDF file path
    result_text = ocr_pdf(pdf_file_path)
    if result_text:
        print("OCR Result:")

        print(result_text)

    # Use examples:
    # test_file = ocr_space_file(filename='example_image.png', language='pol')
    # test_url = ocr_space_url(url='http://i.imgur.com/31d5L5y.jpg')

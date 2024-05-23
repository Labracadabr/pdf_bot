import cv2
import numpy as np
from fitz import fitz
from api_integrations.ocr_api import ocr_image


def read_sign(img_path, out_path=None):
    # прочитать фото и превратить в ЧБ
    print('read_sign:', img_path)
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # преобразовать в двоичное изображение
    _, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # инвертировать
    mask = cv2.bitwise_not(mask)

    # конвертация в RGBA
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # сделать черное прозрачным
    image[mask == 0] = [255, 255, 255, 0]

    # сохранить
    if out_path:
        cv2.imwrite(out_path, image)
    else:
        print('file not saved')


# обработка пдф
def process_pdf(pdf_path, xyz: dict = None, save_path=None,
                image_path=None,  page: int = 0, font: int = 30,
                put_text=None, temp_jpg_path=None, ):
    # открыть страницу пдф
    file_handle = fitz.open(pdf_path)
    target_page = file_handle[int(page)]

    # вставить рисунок либо текст
    if image_path:
        rectangle = fitz.Rect(x0=xyz['x0'], y0=xyz['y0'], x1=xyz['x1'], y1=xyz['y1'], )
        target_page.insert_image(rectangle, filename=image_path)
    elif put_text:
        target_page.insert_font(fontname="F0", fontbuffer=fitz.Font("tiro").buffer)  # кириллица
        point = fitz.Point(x=xyz['x0'], y=xyz['y0'])
        target_page.insert_text(text=put_text, point=point, fontsize=font,  fontname="F0", overlay=False)

    # рендер страницы
    if temp_jpg_path:
        pix = target_page.get_pixmap()
        # конвертация
        rendered_image = np.frombuffer(pix.samples, dtype=np.uint8)
        rendered_image = rendered_image.reshape((pix.height, pix.width, pix.n))
        if pix.n == 4:
            bgr_image = cv2.cvtColor(rendered_image, cv2.COLOR_RGBA2BGR)
        else:
            bgr_image = cv2.cvtColor(rendered_image, cv2.COLOR_RGB2BGR)

        # сохранить
        cv2.imwrite(temp_jpg_path, bgr_image)
        file_handle.close()
        return temp_jpg_path

    # сохранить ПДФ
    if save_path:
        file_handle.save(save_path)
        print(f'saved to {save_path}')
        return


# извлечение текста из pdf
def read_pdf_pages(pdf_path, output_path, read_mode, render_tmp_path=None, language=None):
    print(f'reading pdf, {read_mode = }, {pdf_path = }')
    output_text = ''
    page_split = f"{'_'*50}_#PAGE_num#_{'_'*50}\n"

    if read_mode == 'text':
        with fitz.open(pdf_path) as doc:
            for num, page in enumerate(doc, start=1):
                # нумерация страницы
                output_text += page_split.replace('num', str(num))
                # сам текст
                output_text += page.get_text()

    elif read_mode == 'ocr':
        assert (render_tmp_path and language)
        page = 0
        while True:
            print(f'ocr pdf {page = }')
            try:
                # рендер фото страницы
                process_pdf(pdf_path, page=page, temp_jpg_path=render_tmp_path)
                # чтение фото с ocr
                ocr_result = ocr_image(filename=render_tmp_path, language=language)

                # нумерация страницы
                output_text += page_split.replace('num', str(page+1))
                # сам текст
                output_text += ocr_result
                page += 1
            except IndexError:
                print('finished reading pdf', pdf_path)
                break
    else:
        raise AssertionError('no read mode')

    # сохранить текст из пдф
    with open(output_path, 'w', encoding='utf-8') as f:
        print(output_text, file=f)

    print('saved at', output_path)


# посчитать кол-во страниц в пдф
def count_pdf_pages(pdf_path) -> int:
    print(f'counting pages {pdf_path = }')
    file_handle = fitz.open(pdf_path)
    num_pages = file_handle.page_count
    file_handle.close()
    return num_pages


# удалить страницы из пдф
def delete_pdf_pages(in_pdf_path, out_pdf_path, pages: list) -> str:
    print(f'deleting pages {in_pdf_path = }, {pages = }')
    file_handle = fitz.open(in_pdf_path)

    # удалять с конца
    pages.sort(reverse=True)
    for page in pages:
        file_handle.delete_page(int(page)-1)  # номер на 1 меньше указанного

    # сохранить
    file_handle.save(out_pdf_path, garbage=4, deflate=True)
    file_handle.close()
    print(f'Saved modified PDF as {out_pdf_path}')
    return out_pdf_path


if __name__ == "__main__":
    pass
    path = r'C:\Users\Dmitrii\PycharmProjects\pdf_bot\users_data\992863889_raw.pdf'
    print(count_pdf_pages(path))

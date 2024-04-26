import cv2
import numpy as np
from fitz import fitz

# k = 19
a, b = 0, 0

# update thresholds
def upd_thresholds(a_value, b_value):
    global a, b
    a = a_value
    b = b_value

def read_sign(img_path, out_path=None):
    print('processing:', img_path)
    # Read the image
    image = cv2.imread(img_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to binary
    _, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Invert the mask
    mask = cv2.bitwise_not(mask)

    # Convert the image to RGBA
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Apply the mask to remove black areas
    image[mask == 0] = [255, 255, 255, 0]  # Set black areas to transparent
    # Save the transparent image
    if out_path:
        cv2.imwrite(out_path, image)
    else:
        print('file not saved')


# обработка пдф
def process_pdf(pdf_path, xyz: dict, save_path=None, image_path=None,  page: int = 0, font: int = 30,
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
def read_pdf_pages(pdf_path, output_path, read_mode):
    print(f'reading pdf, {read_mode = }, {pdf_path = }')
    output_text = ''
    page_split = f"{'_'*50}_#PAGE_num#_{'_'*50}\n"

    if read_mode == 'text':
        with fitz.open(pdf_path) as doc:
            for num, page in enumerate(doc, start=1):
                output_text += page_split.replace('num', str(num))
                output_text += page.get_text()

    elif read_mode == 'ocr':
        raise AssertionError('нету ocr')

    # сохранить текст из пдф
    with open(output_path, 'w', encoding='utf-8') as f:
        print(output_text, file=f)

    print('saved at', output_path)


if __name__ == "__main__":
    read_sign('signs\992863889_raw.jpg', 'signs/992863889_bin.png')


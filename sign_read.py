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

def trackbars(img_path):
    # Create window and trackbars
    cv2.namedWindow('Controls')
    cv2.createTrackbar('kernel', 'Controls', a, 50, lambda x: upd_thresholds(x, a))
    cv2.createTrackbar('thresh', 'Controls', b, 100, lambda x: upd_thresholds(b, x))

    while True:
        image = cv2.imread(img_path)

        # grayscale & binary
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, b, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Optionally, perform morphological operations to clean up the binary image
        kernel = np.ones((a, a), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # display
        binary = cv2.resize(binary, (500, 500))
        cv2.imshow('Binary', binary)

        # Exit on 'q' key press
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()


def transparent(img_path):
    print('transparent', img_path)
    # na = cv2.imread(img_path)
    na = img_path

    # Make a True/False mask of pixels whose BGR values sum to more than zero
    alpha = np.sum(na, axis=-1) > 0

    # Convert True/False to 0/255 and change type to "uint8" to match "na"
    alpha = np.uint8(alpha * 255)

    # Stack new alpha layer with existing image to go from BGR to BGRA, i.e. 3 channels to 4 channels
    result = np.dstack((na, alpha))
    return result


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


#
def process_pdf(xyz: dict, save_path=None, image_path=None, pdf_path=None, page: int = 0, font: int = 30,
                put_text=None, temp_jpg_path=None):
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



if __name__ == "__main__":
    read_sign('signs\992863889_raw.jpg', 'signs/992863889_bin.png')


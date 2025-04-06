import logging
from flask import Flask, request
from models.plate_reader import PlateReader, InvalidImage
import logging
import io
import requests


app = Flask(__name__)
plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')


@app.route('/')
def hello():
    user = request.args['user']
    return f'<h1 style="color:red;"><center>Hello {user}!</center></h1>'


# <url>:8080/greeting?user=me
# <url>:8080 : body: {"user": "me"}
# -> {"result": "Hello me"}
@app.route('/greeting', methods=['POST'])
def greeting():
    if 'user' not in request.json:
        return {'error': 'field "user" not found'}, 400

    user = request.json['user']
    return {
        'result': f'Hello {user}',
    }


# <url>:8080/readPlateNumber : body <image bytes>
# {"plate_number": "c180mv ..."}
IMAGE_BASE_URL = 'http://89.169.157.72:8080/images'


def fetch_and_recognize_plate(img_id):
    """
    Скачивает изображение по img_id и пытается распознать номер.
    Возвращает: (успешно: True, результат или ошибка)
    """
    image_url = f'{IMAGE_BASE_URL}/{img_id}'

    try:
        response = requests.get(image_url, timeout=5)
        response.raise_for_status()
        im = io.BytesIO(response.content)
    except requests.RequestException as e:
        logging.error(f'[img_id={img_id}] Failed to fetch: {e}')
        return False, {'error': 'download_failed'}

    try:
        result = plate_reader.read_text(im)
        return True, {'plate_number': result}
    except InvalidImage:
        logging.error(f'[img_id={img_id}] Invalid image')
        return False, {'error': 'invalid_image'}


@app.route('/readPlateNumber', methods=['POST'])
def read_plate_number():
    try:
        data = request.get_json()
        img_id = int(data['img_id'])
    except (KeyError, TypeError, ValueError):
        return {'error': 'img_id (int) is required in JSON body'}, 400

    success, result = fetch_and_recognize_plate(img_id)
    return result, 200 if success else 400


@app.route('/readMultiplePlateNumbers', methods=['POST'])
def read_multiple_plate_numbers():
    try:
        data = request.get_json()
        img_ids = data['img_ids']
        if not isinstance(img_ids, list) or not all(isinstance(i, int) for i in img_ids):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return {'error': 'Expected JSON: {"img_ids": [int, int, ...]}'}, 400

    results = {}

    for img_id in img_ids:
        success, result = fetch_and_recognize_plate(img_id)
        results[img_id] = result

    return results


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)

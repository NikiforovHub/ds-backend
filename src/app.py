from flask import Flask
import logging
from plate_reader import PlateReader


app = Flask(__name__)


@app.route('/')
def hello():
    return '<h1><center>hi!</center></h1>'


plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')
…
# <url>:8080/readPlateNumber : body <image bytes>
# {"plate_number": "c180mv ..."}
@app.route('/readPlateNumber', methods=['POST'])
def read_plate_number():
    im = request.get_data()
    im = io.BytesIO(im)
    
    try:
        res = plate_reader.read_text(im)
    except InvalidImage:
        logging.error('invalid image')
        return {'error': 'invalid image'}, 400
    
    return {'plate_number': res,}


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )
    app.json.ensure_ascii = False
    app.run(host='0.0.0.0', port=8080, debug=True)

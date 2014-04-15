from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
from shared import read_config, save_config
from flask import jsonify
import logging
from werkzeug import SharedDataMiddleware
import os

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='static',
    static_url_path='/static')
#app.wsgi_app = SharedDataMiddleware(app.wsgi_app, 
#    {'/': os.path.join(os.path.dirname(__file__), 'static')})

@app.route('/')
def root():
    return render_template('index.html')


@app.route('/server', methods=['GET', 'POST'])
def server():
    conf = read_config()
    if request.method == 'POST':
        conf.set('recorder', 'is_recording', 
            str(request.json['running']))
        save_config(conf)
    return jsonify({'running':
        conf.getboolean('recorder', 'is_recording')})

@app.route('/server/status')
def status():
    conf = read_config()
    dir = conf.get('directories', 'sessions')
    filename = os.path.join(dir, 'current_status.data')
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            data = f.readline().split(';')
        return jsonify({'signal_power': float(data[1]),
            'sleep_level': float(data[2]),
            'breath': float(data[4]),
            'hb': float(data[5]),
            'state': int(data[6])})
    else:
        return jsonify({'signal_power': 0.0,
            'sleep_level': 0.0,
            'breath': 0.0,
            'hb': 0.0,
            'state': 0})


if __name__ == '__main__':
    #app.config.from_object('server.default_settings')
    app.run(host='0.0.0.0', debug=True)

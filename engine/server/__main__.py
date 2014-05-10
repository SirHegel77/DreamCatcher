from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
from shared import read_config, save_config
from flask import jsonify
from flask import Response
from glob import glob, iglob
import json
import logging
from werkzeug import SharedDataMiddleware
import os

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='static',
    static_url_path='/static')

@app.route('/')
def root():
    return redirect('static/index.html')

def take_from(items, take, skip):
    if skip != None:
        for i in xrange(skip):
            items.next()
    while True:
        if take != None:
           if take == 0:
               raise StopIteration
           else:
               take -= 1
        yield items.next()    

def dream_info(timestamp):
    conf = read_config()
    session_dir = conf.get('directories', 'sessions')
    filename = os.path.join(session_dir, timestamp + '.data')
    firstline = os.popen("head -1 %s" % filename).read()
    if firstline:
        start = long(firstline.split(';')[0])
    else:
        start = 0

    lastline = os.popen("tail -n 1 %s" % filename).read()
    if lastline:
        end = long(lastline.split(';')[0])
    else:
        end = 0
    
    return {'id': long(timestamp), 'start': start, 'end': end}


def dream_summary(timestamp):
    conf = read_config()
    session_dir = conf.get('directories', 'sessions')
    filename = os.path.join(session_dir, timestamp + '.data')
    NOT_IN_BED = 0
    AWAKE = 1
    LIGHT_SLEEP = 2
    DEEP_SLEEP = 3
    result = [{'Name': 'Not in bed', 'Total':0, 'Percent': 0.0, 'Transitions': 0},
              {'Name': 'Awake', 'Total':0, 'Percent': 0.0, 'Transitions': 0},
              {'Name': 'Light sleep', 'Total':0, 'Percent': 0.0, 'Transitions': 0},
              {'Name': 'Deep sleep', 'Total':0, 'Percent': 0.0, 'Transitions': 0}]

    totaltime = 0
    previous_time = long(timestamp)
    previous_state = 0
    with open(filename, 'r') as f:
        for line in f:
            fields = line.split(';')
            timestamp = long(fields[0])
            state = int(fields[6])
            diff = timestamp - previous_time
            
            current_state = result[state]
            current_state['Total']+=diff
            if state <> previous_state:
                current_state['Transitions']+=1

            totaltime += diff
            previous_time = timestamp
            previous_state = state

    for state in result:
        state['Percent'] = float(state['Total']) / float(totaltime) * 100.0
    return result


def dream_data(timestamp):
    conf = read_config()
    session_dir = conf.get('directories', 'sessions')
    filename = os.path.join(session_dir, timestamp + '.data')
    result = []
    with open(filename, 'r') as f:
        for line in f:
            fields = line.split(';')
            values = {'timestamp': long(fields[0]),
                      'signal_power': float(fields[1]),
                      'sleep_level': float(fields[2]),
                      'breath': float(fields[4]),
                      'hb': float(fields[5]),
                      'state': int(fields[6])}
            result.append(values)

    return result

@app.route('/dreams')
def dreams():
    conf = read_config()
    session_dir = conf.get('directories', 'sessions')
    datafiles = sorted(glob(session_dir + '/*.data'), 
        key = os.path.getctime, reverse = True)
    timestamps = (os.path.splitext(os.path.split(fn)[1])[0] for fn in datafiles)    
    take = None
    if request.args.has_key('take'):
        take = int(request.args.get('take'))
    skip = None
    if request.args.has_key('skip'):
        skip = int(request.args.get('skip'))
        print "skip: ", take
    else:
        print "No skip"
    
    dreams = [{'id': ts} for ts in take_from(timestamps, take, skip)]
    return Response(json.dumps(dreams), mimetype='application/json')


@app.route('/dreams/<id>', methods=['GET'])
def dream(id):
    return jsonify(dream_info(id))

@app.route('/dreams/<id>/data', methods=['GET'])
def dreamdata(id):
    data = dream_data(id)
    return Response(json.dumps(data), mimetype='application/json')

@app.route('/dreams/<id>/summary', methods=['GET'])
def dreamsummary(id):
    data = dream_summary(id)
    return Response(json.dumps(data), mimetype='application/json')


@app.route('/recorder', methods=['GET', 'PUT'])
def recorder():
    conf = read_config()
    if request.method == 'PUT':
        conf.set('recorder', 'is_recording', 
            str(request.json['is_recording']))
        save_config(conf)
    return jsonify({'is_recording':
        conf.getboolean('recorder', 'is_recording')})


@app.route('/recorder/status')
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

from flask import Flask, request, render_template
from db import Database
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import glob
import time
from apscheduler.schedulers.background import BackgroundScheduler
from cfg import *
# import random
from db import create_database

device_files = []
for i in range(sensor_amount):
    device_folder = glob.glob(base_dir + '28*')[i]
    device_files.append(device_folder + '/w1_slave')

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

app = Flask('sensors-db')


def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    temperatures = []
    for device_file in device_files:
        lines = read_temp_raw(device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temperatures.append(temp_c)
    return temperatures

def generate_image(start, finish, path, sensor):

    def normalize_x(input, val):
        output = []
        for i in input:
            x = int(((ref - i[1])/60))
            y = int(i[val])
            output.append((x, y))

        return output[::-1 ]
    db = Database('database.db')
    result = db.fetch(f'{sensor}, timestamp', 'sensors', f'timestamp>{start} and timestamp<{finish}').fetchall()
    result.sort(key=lambda x: x[1])
    no_data = False
    try:
        ref = result[-1][1]
    except IndexError:
        no_data = True

    if not no_data:
        values_t = normalize_x(result, 0)
        y_t = [i[1] for i in values_t]
        x_t = [i[0] for i in values_t]

        x_t = [datetime.fromtimestamp(ref-(60*i)) for i in x_t]
    else:
        x_t = 0
        y_t = 0

    plt.plot(x_t,y_t, color='r')
    plt.grid()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gcf().autofmt_xdate()
    plt.ylim(ymin=0)
    plt.savefig(path)
    plt.close()

def read_sensors():
    # return [random.randint(10,30) for _ in range(sensor_amount)]
    return read_temp()

def sensors_db():
    readings = read_sensors()
    db = Database('database.db')
    db.insert('sensors', None, *readings, datetime.now().timestamp())
    db.delete('sensors', f'timestamp < {datetime.now().timestamp() - 60*60*24}')

@app.route('/', methods=["POST"])
def main_request():
    start = datetime.strptime(request.form['start'], '%Y-%m-%dT%H:%M').timestamp()
    finish = datetime.strptime(request.form['finish'], '%Y-%m-%dT%H:%M').timestamp()
    for i in range(sensor_amount):
        generate_image(start, finish, f"static/img{i}.jpg", f"t{i}")
    
    return render_template('template.html', image=[f"static/img{i}.jpg" for i in range(sensor_amount)])

@app.route('/')
def main_site():
    for i in range(sensor_amount):
        generate_image(datetime.now().timestamp()-60*60*2, datetime.now().timestamp(), f"static/img{i}.jpg", f"t{i}")

    return render_template('template.html', image=[f"static/img{i}.jpg" for i in range(sensor_amount)])

if __name__ == '__main__':
    if not os.path.isfile("database.py"):
        create_database()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=sensors_db, trigger="interval", seconds=30)
    scheduler.start()

    app.run(host='0.0.0.0', port=80, debug=False, threaded=False)

        

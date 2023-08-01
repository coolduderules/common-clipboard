import time
import webbrowser
from infi.systray import SysTrayIcon
from flask import Flask, request, render_template
from log import Log, Tag
from threading import Thread

app = Flask(__name__)


@app.route('/', methods=['GET'])
def show_connected():
    if request.remote_addr == '127.0.0.1' or request.remote_addr in connected_devices:
        for ip, device in list(connected_devices.items()):
            if time.time() - device[1] >= 5:
                del connected_devices[ip]
                log_file.log(Tag.INFO, f'Unregistered {device[0]}')
        return render_template('index.html', device_list=connected_devices), 200
    else:
        return render_template('restricted.html'), 401


@app.route('/register', methods=['POST'])
def register():
    device_info = request.get_json()
    try:
        name = device_info['name']
        connected_devices.update({request.remote_addr: [name, time.time()]})
        log_file.log(Tag.INFO, f"Registered {name} ({request.remote_addr})")
        return '', 204
    except KeyError:
        return 'Provided device information is invalid', 400


@app.route('/clipboard', methods=['GET'])
def get_clipboard():
    try:
        connected_devices[request.remote_addr][1] = time.time()
        return {'data': clipboard}, 200
    except KeyError:
        return unregistered_error


@app.route('/clipboard', methods=['POST'])
def update_clipboard():
    global clipboard

    received_data = request.get_json()
    try:
        connected_devices[request.remote_addr][1] = time.time()

        assert 'data' in received_data
        clipboard = received_data['data']
        log_file.log(Tag.INFO,
                     f'Received new clipboard data from {connected_devices[request.remote_addr][0]} ({request.remote_addr})')
        return '', 204
    except KeyError:
        return unregistered_error
    except AssertionError:
        return 'Missing clipboard data parameter', 400


def close_server():
    log_file.log(Tag.INFO, 'Server closed')


if __name__ == '__main__':
    port = 5000
    newline = '\n\t'
    unregistered_error = 'The requesting device is not registered to the server', 401

    clipboard = ''
    connected_devices = {}
    log_file = Log('server_log.txt')

    menu_options = (('View Connected Devices', None, lambda _: webbrowser.open(f'http://localhost:{port}')),)
    systray = SysTrayIcon('static/server_icon.ico', 'Common Clipboard Server', menu_options,
                          on_quit=lambda _: close_server())
    systray.start()

    log_file.log(Tag.INFO, 'Server started')
    server_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port}, daemon=True)
    server_thread.start()

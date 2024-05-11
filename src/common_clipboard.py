"""
Main file for application
"""

import requests
import time
import win32clipboard as clipboard
import sys
import os
import pickle
from socket import gethostbyname, gethostname
from threading import Thread
from multiprocessing import freeze_support, Value, Process
from multiprocessing.managers import BaseManager
from enum import Enum
from pystray import Icon, Menu, MenuItem
from PIL import Image
from io import BytesIO
from server import run_server
from device_list import DeviceList
from port_editor import PortEditor


class Format(Enum):
    TEXT = 'text'
    IMAGE = 'image'


def register(address):
    global server_url

    server_url = f'http://{address}:{port}'
    requests.post(server_url + '/register', json={'name': gethostname()})


def test_server_ip(index):
    global server_url
    global running_server

    try:
        tested_url = f'http://{base_ipaddr}.{index}:{port}'
        response = requests.get(tested_url + '/timestamp', timeout=5)
        if response.ok and float(response.text) < server_timestamp.value:
            register(base_ipaddr + '.' + index)
            running_server = False
            server_process.terminate()
            systray.title = f'{APP_NAME}: Connected'
    except (requests.exceptions.ConnectionError, AssertionError):
        return


def generate_ips():
    for i in range(0, 255):
        for j in range(0, 255):
            for k in range(0, 255):
                if i != int(split_ipaddr[1]) or j != int(split_ipaddr[2]) or k != int(split_ipaddr[3]):
                    test_url_thread = Thread(target=test_server_ip, args=(f'{i}.{j}.{k}',), daemon=True)
                    test_url_thread.start()


def find_server():
    global running_server
    global server_url

    try:
        requests.get(TEST_INTERNET_URL)
        start_server()
        register(ipaddr)
        systray.title = f'{APP_NAME}: Server Running'

        generator_thread = Thread(target=generate_ips)
        generator_thread.start()
    except requests.exceptions.ConnectionError:
        server_url = ''


def get_copied_data():
    try:
        clipboard.OpenClipboard()
        for fmt in CLIPBOARD_FORMATS.values():
            if clipboard.IsClipboardFormatAvailable(fmt):
                data = clipboard.GetClipboardData(fmt)
                return data, FORMAT_TO_ENUM[fmt]
        else:
            raise ValueError
    except ValueError:
        try:
            return current_data, current_format
        except NameError:
            return '', Format.TEXT
    finally:
        clipboard.CloseClipboard()


def detect_local_copy():
    global current_data
    global current_format

    new_data, new_format = get_copied_data()
    if new_data != current_data:
        current_data = new_data
        current_format = new_format

        file = BytesIO()
        file.write(current_data.encode() if current_format == Format.TEXT else current_data)
        file.seek(0)
        requests.post(server_url + '/clipboard', data=file, headers={'Data-Type': current_format.value})


def detect_server_change():
    global current_data
    global current_format

    headers = requests.head(server_url + '/clipboard', timeout=2)
    if headers.ok and headers.headers['Data-Attached'] == 'True':
        data_request = requests.get(server_url + '/clipboard')
        data_format = data_request.headers['Data-Type']
        data_content = data_request.content

        try:
            clipboard.OpenClipboard()
            clipboard.EmptyClipboard()

            if data_format == Format.TEXT.value:
                clipboard.SetClipboardData(CLIPBOARD_FORMATS['text'], data_content.decode())
            elif data_format == Format.IMAGE.value:
                image = Image.open(BytesIO(data_content))
                dib_file = BytesIO()
                image.save(dib_file, 'DIB')
                dib_data = dib_file.getvalue()
                dib_file.close()

                clipboard.SetClipboardData(CLIPBOARD_FORMATS['png_image'], data_content)
                clipboard.SetClipboardData(CLIPBOARD_FORMATS['dib_image'], dib_data)

            clipboard.CloseClipboard()
            current_data, current_format = get_copied_data()
        except BaseException:
            return


def mainloop():
    while run_app:
        try:
            # requests.head(TEST_INTERNET_URL)
            detect_server_change()
            detect_local_copy()
        except (requests.exceptions.ConnectionError, TimeoutError, OSError):
            systray.title = f'{APP_NAME}: Not Connected'
            if run_app:
                find_server()
        finally:
            if running_server:
                systray.update_menu()
            time.sleep(LISTENER_DELAY)


def start_server():
    global running_server
    global server_process

    if server_process is not None:
        server_process.terminate()

    connected_devices.clear()
    running_server = True
    server_process = Process(target=run_server, args=(port, connected_devices, server_timestamp,))
    server_process.start()


def close():
    global run_app

    run_app = False
    if server_process is not None:
        server_process.terminate()

    with open(preferences_file, 'wb') as save_file:
        pickle.dump(port, save_file)

    systray.stop()
    sys.exit(0)


def edit_port():
    global port

    port_dialog = PortEditor(port)
    new_port = port_dialog.port_number.get()
    if port_dialog.applied and new_port != port:
        port = new_port
        find_server()


def get_menu_items():
    menu_items = (
        MenuItem(f'Port: {port}', Menu(MenuItem('Edit', lambda _: edit_port()))),
        MenuItem('View Connected Devices', Menu(lambda: (
            MenuItem(f"{name} ({ip})", None) for ip, name in connected_devices.get_devices()
        ))) if running_server else None,
        MenuItem('Quit', close),
    )
    return (item for item in menu_items if item is not None)


if __name__ == '__main__':
    freeze_support()

    APP_NAME = 'Common Clipboard'
    LISTENER_DELAY = 0.3
    TEST_INTERNET_URL = 'https://8.8.8.8'
    TEST_INTERNET_DELAY = 1

    CLIPBOARD_FORMATS = {
        'text': clipboard.CF_UNICODETEXT,
        'png_image': clipboard.RegisterClipboardFormat('PNG'),
        'dib_image': clipboard.CF_DIB
    }

    FORMAT_TO_ENUM = {
        CLIPBOARD_FORMATS['text']: Format.TEXT,
        CLIPBOARD_FORMATS['png_image']: Format.IMAGE,
        CLIPBOARD_FORMATS['dib_image']: Format.IMAGE
    }

    server_url = ''
    ipaddr = gethostbyname(gethostname())
    split_ipaddr = [int(num) for num in ipaddr.split('.')]
    base_ipaddr = str(split_ipaddr[0])

    BaseManager.register('DeviceList', DeviceList)
    manager = BaseManager()
    manager.start()
    connected_devices = manager.DeviceList()
    server_timestamp = Value('d', 0)

    running_server = False
    server_process = None

    try:
        data_dir = os.path.join(os.getenv('LOCALAPPDATA'), APP_NAME)
    except TypeError:
        data_dir = os.getcwd()

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    preferences_file = os.path.join(data_dir, 'preferences.pickle')
    try:
        with open(preferences_file, 'rb') as preferences:
            port = pickle.load(preferences)
    except FileNotFoundError:
        port = 5000

    current_data, current_format = get_copied_data()

    icon = Image.open('systray_icon.ico')
    systray = Icon(APP_NAME, icon=icon, title=APP_NAME, menu=Menu(get_menu_items))
    systray.run_detached()

    run_app = True
    mainloop()

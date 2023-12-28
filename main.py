import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import socket
from datetime import datetime
import os
import threading
from queue import Queue

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):

        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}


        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

        send_to_socket_server(data_dict)

    def do_GET(self):

        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':

            self.send_html_file('index.html')

        elif pr_url.path == '/contact':

            self.send_html_file('contact.html')

        else:

            if pathlib.Path().joinpath(pr_url.path[1:]).exists():

                self.send_static()

            else:

                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:

            self.send_header("Content-type", mt[0])

        else:

            self.send_header("Content-type", 'text/plain')
        self.end_headers()

        with open(f'.{self.path}', 'rb') as file:

            self.wfile.write(file.read())

def send_to_socket_server(data_dict):

    data_queue.put(data_dict)

def socket_server():

    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    conn, address = server_socket.accept()
    print(f'Connection {address}')
    while True:

        msg = conn.recv(1024).decode()
        if not msg:

            break

        print(f'Received message {msg}')
        conn.send(msg.encode())
    conn.close()

    server_socket.close()

def process_data_queue():

    while True:

        if not data_queue.empty():

            data_dict = data_queue.get()
            handle_data(data_dict)

def handle_data(data_dict):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


    storage_dir = 'storage'
    if not os.path.exists(storage_dir):

        os.makedirs(storage_dir)


    data_file_path = os.path.join(storage_dir, 'data.json')
    if not os.path.exists(data_file_path):

        with open(data_file_path, 'w') as f:

            json.dump({}, f)


    with open(data_file_path, 'r') as f:

        existing_data = json.load(f)


    existing_data[timestamp] = data_dict


    with open(data_file_path, 'w') as f:
        json.dump(existing_data, f)

if __name__ == '__main__':
    data_queue = Queue()


    socket_thread = threading.Thread(target=socket_server)
    socket_thread.start()


    process_data_thread = threading.Thread(target=process_data_queue)
    process_data_thread.start()


    server_address = ('0.0.0.0', 3000)
    http_server = HTTPServer(server_address, HttpHandler)
    print('Starting server...')
    http_server.serve_forever()


    host = socket.gethostname()
    port = 5000

    client_socket = socket.socket()
    client_socket.connect((host, port))

    message = input('>>> ')

    while message.lower().strip():
        client_socket.send(message.encode())
        msg = client_socket.recv(1024).decode()
        if not msg:
            break
        print(f'Received message: {msg}')
        message = input('>>> ')

    client_socket.close()

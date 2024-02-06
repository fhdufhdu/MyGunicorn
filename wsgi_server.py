
import base64
from collections import deque
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
import importlib
import io
import multiprocessing
import os
from queue import Queue
import re
import select
import selectors
import signal
import socket
import subprocess
import traceback
from multiprocessing import Lock, Manager, Pool, Process, freeze_support
from typing import Any

from wsgiserver.wsgi import application

class MyGunicorn:
    def __init__(self):
        self.m = Manager()
        self.q = self.m.Queue()
        self.ss = self.__init_socket__()
        self.ps = []
    
    def __init_socket__(self):
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return ss

    @staticmethod
    def request(_ss:socket.socket, app_path:str):
        c_proc = multiprocessing.current_process()
        _from, _import = app_path.split(':', 1)

        module = importlib.import_module(_from)
        app = getattr(module, _import)

        with _ss as ss:
            while(True):
                print("START: ",c_proc.name," || ","PID: ",c_proc.pid)
                conn, address = ss.accept()
                
                byte = conn.recv(1048576)
                if not byte:
                    conn.close()
                    break
                data = byte.decode('utf-8').strip()

                if data:
                    data = data.replace('\r\n', '\n')
                    datas = data.split('\n\n', 1)
                    if len(datas) == 2:
                        headers, body = datas
                    else:
                        headers = data
                        body = ''
                    headers = headers.rsplit('\n')

                    method, path, version_of_protocol = headers[0].split(' ')
                    if '?' in path:
                        path, query = path.split('?', 1)
                    else:
                        path, query = path, ''
                    try:
                        environ = {
                            "REQUEST_METHOD": method,
                            "SERVER_PROTOCOL": version_of_protocol,
                            "SERVER_SOFTWARE": "WOOSEONG_WSGI",
                            "PATH_INFO": path,
                            "QUERY_STRING": query,
                            "REMOTE_HOST": address[0],
                            "REMOTE_ADDR": address[0],
                            "wsgi.input": io.BytesIO(body.encode('utf-8')),
                            "wsgi.url_scheme": 'http',
                            "wsgi.version": (1, 0)
                        }
                    except Exception as e:
                        print(e)

                    for idx, header in enumerate(headers):
                        if idx == 0: continue
                        key, value = re.split(r'\s*:\s*', header, 1)

                        key = key.replace('-', '_').upper() 
                        value = value.strip()

                        make_key = lambda x:'HTTP_'+x
                        if key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                            environ[key] = value
                        elif make_key(key) in environ:
                            environ[make_key(key)] += ','+value
                        else:
                            environ[make_key(key)] = value

                    sh = {
                        'status': 200,
                        'headers': []
                    }
                    def start_response(status, headers):
                        print(status, header)
                        sh['status'] = status
                        sh['headers'] = headers
                    
                    response_body = app(environ, start_response)
                    print(sh)
                    response = f"{version_of_protocol} {sh['status']}\r\n" + "\r\n".join(list(map(lambda x: f"{x[0]}: {x[1]}", sh['headers']))) + "\r\n\r\n"
                    response = response.encode('utf-8')
                    for b in response_body:
                        response += b
                    conn.send(response)
                conn.close()
            
                print("END: ",c_proc.name," || ","PID: ",c_proc.pid)
    
    def run(self, app_path: str, host:str = 'localhost', port:int = 1026, backlog: int = 100, worker=4):
        self.ss.bind((host, port))
        self.ss.listen(backlog)

        for _ in range(worker):
            Process(target=MyGunicorn.request, args=(self.ss, app_path)).start()
        

if __name__ == '__main__':
    MyGunicorn().run(app_path='wsgiserver.wsgi:application', worker=1)
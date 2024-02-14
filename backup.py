import importlib
import io
import multiprocessing
import re
import signal
import socket
from multiprocessing import Process


class MyGunicorn:
    def __init__(self):
        self.ss = self.__init_socket__()
        self.ps = []
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)

    def __init_socket__(self):
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return ss

    @staticmethod
    def request(_ss: socket.socket, app_path: str):
        try:
            c_proc = multiprocessing.current_process()
            _from, _import = app_path.split(":", 1)

            module = importlib.import_module(_from)
            app = getattr(module, _import)

            with _ss as ss:
                while True:
                    print("START: ", c_proc.name, " || ", "PID: ", c_proc.pid)
                    conn, address = ss.accept()

                    raw_data = conn.recv(1048576)
                    if not raw_data:
                        conn.close()
                        break

                    raw_data = raw_data.replace(b"\r\n", b"\n")
                    splited_raw_data = raw_data.split(b"\n\n", 1)

                    if len(splited_raw_data) == 2:
                        b_headers, b_body = splited_raw_data
                    else:
                        b_headers, b_body = (raw_data, b"")

                    headers = b_headers.decode("utf-8")
                    headers = headers.rsplit("\n")

                    method, path, version_of_protocol = headers[0].split(" ")
                    if "?" in path:
                        path, query = path.split("?", 1)
                    else:
                        path, query = path, ""
                    environ = {
                        "REQUEST_METHOD": method,
                        "SERVER_PROTOCOL": version_of_protocol,
                        "SERVER_SOFTWARE": "WOOSEONG_WSGI",
                        "PATH_INFO": path,
                        "QUERY_STRING": query,
                        "REMOTE_HOST": address[0],
                        "REMOTE_ADDR": address[0],
                        "wsgi.input": io.BytesIO(b_body),
                        "wsgi.url_scheme": "http",
                        "wsgi.version": (1, 0),
                    }

                    for idx, header in enumerate(headers):
                        if idx == 0:
                            continue
                        key, value = re.split(r"\s*:\s*", header, 1)

                        key = key.replace("-", "_").upper()
                        value = value.strip()

                        make_key = lambda x: "HTTP_" + x
                        if key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                            environ[key] = value
                        elif make_key(key) in environ:
                            environ[make_key(key)] += "," + value
                        else:
                            environ[make_key(key)] = value

                    sh = {"status": 200, "headers": []}

                    def start_response(status, headers):
                        sh["status"] = status
                        sh["headers"] = headers

                    response_body = app(environ, start_response)
                    # 응답 첫번째 라인 구성
                    response_first = f"{version_of_protocol} {sh['status']}"
                    # 응답 헤더부분 구성
                    response_headers = "\r\n".join(
                        list(map(lambda x: f"{x[0]}: {x[1]}", sh["headers"]))
                    )
                    # 응답 첫번째 라인 + 헤더 부분
                    response = (
                        response_first
                        + ("\r\n" if response_headers else "")
                        + response_headers
                        + "\r\n\r\n"
                    )
                    # byte로 인코딩
                    response = response.encode("utf-8")
                    # response_body 붙이기
                    for b in response_body:
                        response += b

                    conn.send(response)
                    conn.close()

                    print("END: ", c_proc.name, " || ", "PID: ", c_proc.pid)
        except KeyboardInterrupt:
            pass

    def run(
        self,
        app_path: str,
        host: str = "localhost",
        port: int = 1026,
        backlog: int = 100,
        worker=4,
    ):
        self.ss.bind((host, port))
        self.ss.listen(backlog)

        for _ in range(worker):
            Process(target=MyGunicorn.request, args=(self.ss, app_path)).start()

    def close(self, signum, frame):
        print(f"shutdown: {signum}")
        self.ss.close()


if __name__ == "__main__":
    MyGunicorn().run(app_path="wsgiserver.wsgi:application", worker=16, backlog=1000)

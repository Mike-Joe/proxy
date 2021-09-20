# Don't forget to change this file's name before submission.
import sys
import os
import enum
import socket
import threading

class HttpRequestInfo(object):

    def __init__(self, client_info, method: str, requested_host: str,
                 requested_port: int,
                 requested_path: str,
                 headers: list):
        self.method = method
        self.client_address_info = client_info
        self.requested_host = requested_host
        self.requested_port = requested_port
        self.requested_path = requested_path
        self.headers = headers

    def to_http_string(self):
        # print("*" * 50)
        # print("[to_http_string] Implement me!")
        # print("*" * 50)
        http_str = self.method + " " + self.requested_path + " " + "HTTP/1.0\r\n"
        for i in range(len(self.headers)):
            http_str += self.headers[i][0] + ": " + self.headers[i][1] + "\r\n"
        http_str += "\r\n"
        return http_str

    def to_byte_array(self, http_string):
        return bytes(http_string, "UTF-8")

    def display(self):
        print(f"Client:", self.client_address_info)
        print(f"Method:", self.method)
        print(f"Host:", self.requested_host)
        print(f"Port:", self.requested_port)
        stringified = [": ".join([k, v]) for (k, v) in self.headers]
        print("Headers:\n", "\n".join(stringified))


class HttpErrorResponse(object):

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def to_http_string(self):
        http_str = "HTTP/1.0" + " " + str(self.code) + " " + self.message + "\r\n"
        return http_str

    def to_byte_array(self, http_string):
        return bytes(http_string, "UTF-8")

    def display(self):
        print(self.to_http_string())


class HttpRequestState(enum.Enum):
    INVALID_INPUT = 0
    NOT_SUPPORTED = 1
    GOOD = 2
    PLACEHOLDER = -1

cache = {}

def entry_point(proxy_port_number):
    
    cl_pr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    pr_address = ('127.0.0.1', int(proxy_port_number))
    cl_pr_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    cl_pr_sock.bind(pr_address)
    cl_pr_sock.listen(15)
    
    while 1:
        cl_sock, cl_address = cl_pr_sock.accept()

        con = threading.Thread(target=enter, args=(cl_sock, cl_address,))
        con.start()
    


def enter(cl_sock, cl_address):
    cl_req = cl_sock.recv(512).decode("utf-8")

    while 1:
        cl_headers = cl_sock.recv(512).decode("utf-8")
        if cl_headers == "\r\n":
            break
        cl_req = cl_req + "\r\n" + cl_headers

    if cl_req in cache:
        cl_sock.send(cache.get(cl_req))
    else:
        pr_response = http_request_pipeline(cl_address, cl_req)
        if isinstance(pr_response, HttpErrorResponse):
            cl_sock.send(pr_response.to_byte_array(pr_response.to_http_string()))
            cache.update({cl_req: pr_response.to_byte_array(pr_response.to_http_string())})
        else:
            ser_address = (pr_response.requested_host, pr_response.requested_port)
            pr_ser_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                pr_ser_sock.connect(ser_address)
            except:
                pr_response = HttpErrorResponse(404, "Not found")
                cl_sock.send(pr_response.to_byte_array(pr_response.to_http_string()))
                cache.update({cl_req: pr_response.to_byte_array(pr_response.to_http_string())})
                cl_sock.close()
                return
            pr_ser_sock.send(pr_response.to_byte_array(pr_response.to_http_string()))
            ser_response = pr_ser_sock.recv(512)
            cl_sock.send(ser_response)
            cache.update({cl_req: ser_response})

    cl_sock.close()

    # print("*" * 50)
    # print("[entry_point] Implement me!")
    # print("*" * 50)
    return None




def http_request_pipeline(source_addr, http_raw_data):
    # print("*" * 50)
    # print("[http_request_pipeline] Implement me!")
    # print("*" * 50)
    parsed = ""
    try:
        parsed = parse_http_request(source_addr, http_raw_data)
        validity = check_http_request_validity(parsed)
    except:
        return HttpErrorResponse(400, "Invalid HTTP Request")
        
    if validity == HttpRequestState.GOOD:
        return sanitize_http_request(parsed)
    elif validity == HttpRequestState.NOT_SUPPORTED:
        return HttpErrorResponse(501, "Not Implemented")
    else:
        return HttpErrorResponse(400, "Bad Request")


def parse_http_request(source_addr, http_raw_data) -> HttpRequestInfo:
    # print("*" * 50)
    # print("[parse_http_request] Implement me!")
    # print("*" * 50)
    http_split_data = http_raw_data.split("\r\n")
    http_split_data[0]=http_split_data[0].split(" ")

    requested_path = "/"
    method = http_split_data[0][0]
    requested_host = ""
    requested_port = 80
    headers = []

    for i in range(1,len(http_split_data)):
        http_split_data[i]=http_split_data[i].split(": ")
        if len(http_split_data[i])>1:
            if http_split_data[i][0]=="Host":
                requested_host=http_split_data[i][1]
            # # else :
            headers.append((http_split_data[i][0],http_split_data[i][1]))

    if requested_host=="":
        requested_host=http_split_data[0][1]
    else:
        requested_path=http_split_data[0][1]

    if "http://" in requested_host:
        requested_host = requested_host[7:]

    requested_host = requested_host.strip("/")

    if "/" in requested_host:
        requested_path = requested_host[requested_host.index("/"):]
        requested_host = requested_host[:requested_host.index("/")]

    if ":" in requested_host:
        i = requested_host.index(":")
        requested_port = int(requested_host[i + 1:])
        requested_host = requested_host[:i]

    ret = HttpRequestInfo(source_addr, method, requested_host, requested_port, requested_path, headers)
    return ret


def check_http_request_validity(http_request_info: HttpRequestInfo) -> HttpRequestState:
    # print("*" * 50)
    # print("[check_http_request_validity] Implement me!")
    # print("*" * 50)
    if http_request_info.requested_host == "":
        return HttpRequestState.INVALID_INPUT
    if http_request_info.method == "GET":
        return HttpRequestState.GOOD
    elif http_request_info.method in ["HEAD", "POST", "PUT"]:
        return HttpRequestState.NOT_SUPPORTED
    else:
        return HttpRequestState.INVALID_INPUT


def sanitize_http_request(request_info: HttpRequestInfo) -> HttpRequestInfo:
    # print("*" * 50)
    # print("[sanitize_http_request] Implement me!")
    # print("*" * 50)
    flag = True
    for i in range(len(request_info.headers)):
        if request_info.headers[i][0] == "Host":
            flag = False
            break
    if flag:
        request_info.headers.append(("Host", request_info.requested_host))

    ret = HttpRequestInfo(request_info.client_address_info, request_info.method,
                          request_info.requested_host, request_info.requested_port,
                          request_info.requested_path, request_info.headers)
    return ret


#######################################
# Leave the code below as is.
#######################################


def get_arg(param_index, default=None):
    try:
        return sys.argv[param_index]
    except IndexError as e:
        if default:
            return default
        else:
            print(e)
            print(
                f"[FATAL] The comand-line argument #[{param_index}] is missing")
            exit(-1)  # Program execution failed.


def check_file_name():
    script_name = os.path.basename(__file__)
    import re
    matches = re.findall(r"(\d{4}_){2}lab2\.py", script_name)
    if not matches:
        print(f"[WARN] File name is invalid [{script_name}]")


def main():
    print("\n\n")
    print("*" * 50)
    print(f"[LOG] Printing command line arguments [{', '.join(sys.argv)}]")
    check_file_name()
    print("*" * 50)
    # This argument is optional, defaults to 18888
    proxy_port_number = get_arg(1, 18888)
    
    entry_point(proxy_port_number)
        


if __name__ == "__main__":
    main()

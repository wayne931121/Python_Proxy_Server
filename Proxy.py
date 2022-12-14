#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# 參考資料
# https://docs.python.org/3/library/socket.html
# https://stackoverflow.com/questions/24218058/python-https-proxy-tunnelling
# https://stackoverflow.com/questions/68008233/proxy-server-with-python/73851150#73851150

import sys
#import ssl
import time
import signal
import socket
#import certifi
import threading

with open("log.txt", "w") as f:
    f.write("")

def signal_handler(sig, frame):
    print('Proxy is Stopped.')
    sys.exit(0)

def write(*content, prt=False):
    if prt : 
        if len(content[0])<100:
            print(*content)
        else:
            print("This message is too long not print in cmd but will store at log.txt.")
    if type(content[0])==bytes:
        content = b" ".join(content)
    else:
        content = bytes(" ".join(content), encoding="utf-8")
    with open("log.txt", "ab") as f:
        f.write(content+b"\n")  

class Proxy:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creating a tcp socket
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse the socket
        self.ip = "127.0.0.1"
        self.port = 8080
#         self.host = socket.gethostbyname(socket.gethostname())+":%s"%self.port
        self.sock.bind((self.ip, self.port))
        self.sock.listen(10)
        print("Proxy Server Is Start, See log.txt get log.")
        print("Press Ctrl+C to Stop.")
        start_multirequest = threading.Thread(target=self.multirequest)
        start_multirequest.setDaemon(True)
        start_multirequest.start()
        while 1:
            time.sleep(0.01)
            signal.signal(signal.SIGINT, signal_handler)
    
    def multirequest(self):
        while True:
            (clientSocket, client_address) = self.sock.accept() # establish the connection
            client_process = threading.Thread(target=self.main, args=(clientSocket, client_address))
            client_process.setDaemon(True)
            client_process.start()
            
    def main(self, client_conn, client_addr): # client_conn is the connection by proxy client like browser.
        origin_request = client_conn.recv(4096)
        request = origin_request.decode(encoding="utf-8") # get the request from browser
        first_line = request.split("\r\n")[0] # parse the first line
        url = first_line.split(" ")[1] # get url
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
        webserver = ""
        port = -1
        port_pos = temp.find(":")
        webserver_pos = temp.find("/") # find end of web server
        if webserver_pos == -1:
            webserver_pos = len(temp)
        if port_pos == -1 or webserver_pos < port_pos: # default port
            port = 80
            webserver = temp[:webserver_pos]
        else: # specific port
            port = int(temp[(port_pos + 1):])
            webserver = temp[:port_pos]
        write("Connected by", str(client_addr))
        write("ClientSocket", str(client_conn))
        write("Browser Request:")
        write(request)
        server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_conn.settimeout(1000)
        try:
            server_conn.connect((webserver, port)) # "server_conn" connect to public web server, like www.google.com:443.
        except: # socket.gaierror: [Errno 11001] getaddrinfo failed
            client_conn.close()
            server_conn.close()
            return
        if port==443:
            client_conn.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
            client_conn.setblocking(0)
            server_conn.setblocking(0)
            write("Connection established")
            # now = time.time()
            client_browser_message = b""
            website_server_message = b""
            error = ""
            while 1:
                # if time.time()-now>1: # SET TIMEOUT
                    # server_conn.close()
                    # client_conn.close()
                    # break
                try:
                    reply = client_conn.recv(1024)
                    if not reply: break
                    server_conn.send(reply)
                    client_browser_message += reply
                except Exception as e:
                    pass
                    # error += str(e)
                try:
                    reply = server_conn.recv(1024)
                    if not reply: break
                    client_conn.send(reply)
                    website_server_message += reply
                except Exception  as e:
                    pass
            # error += str(e)
            write("Client Browser Message:")
            write(client_browser_message+b"\n")
            write("Website Server Message:")
            write(website_server_message+b"\n")
            # write("Error:")
            # write(error+"\n")
            server_conn.shutdown(socket.SHUT_RDWR)
            server_conn.close()
            client_conn.close()
            return
        server_conn.sendall(origin_request)
        write("Website Host Result:")
        while 1:
            # receive data from web server
            data = server_conn.recv(4096)
            try:
                write(data.decode(encoding="utf-8"))
            except:
                write(data)
            if len(data) > 0:
                client_conn.send(data)  # send to browser/client
            else:
                break
        server_conn.shutdown(socket.SHUT_RDWR)
        server_conn.close()
        client_conn.close()
Proxy()
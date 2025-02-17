import socket
import threading
import time
import json

class MiniRedis:
    def __init__(self):
        self.store = {}

    def processData(self, data):
        data = data.split(" ")
        if len(data) <= 1:
            return "Invalid Command"
        command = data[0].upper()
        message = data[1:]

        if command == "SET":
            if len(message) != 2:
                return "Error"
            self.store[message[0].rstrip()] = message[1].rstrip()
            return "Successfully added to store"
        elif command == "GET":
            if len(message) != 1:
                return "Error"
            if message[0].rstrip() in self.store:
                return self.store[message[0].rstrip()]
            return "Key not in store"

    def handleClient(self, conn, addr):
        print(f"Connected by {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                ret = self.processData(data.decode())
                conn.sendall((ret + "\r\n").encode())

    def startTCPServer(self, host="127.0.0.1", port=12345):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
            server.listen()
            print(f"Server listening on {host}:{port} ")

            while True:
                conn, addr = server.accept()
                client_thread = threading.Thread(target=self.handleClient, args=(conn, addr))
                client_thread.start()
                



def main():
    obj = MiniRedis()
    obj.startTCPServer()

if __name__ == "__main__":
    main()
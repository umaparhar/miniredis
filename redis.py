import socket
import threading
import os
import json
import datetime

class MiniRedis:
    def __init__(self, filename=""):
        self.store = {}
        self.expirations = {}
        self.filename = filename
        if self.filename != "":
            self.load_from_file()
        self.lock = threading.Lock()

    def load_from_file(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self.store = json.load(f)
                print("Database loaded successfully")
            except Exception as e:
                print("Error loading database")
        else:
            print("No previous database found, starting fresh")

    def save(self):
        with self.lock:
            try:
                with open(self.filename, "w") as f:
                    json.dump(self.store, f)
                return "Database saved successfully"
            except Exception as e:
                return "Error saving database"

    def processData(self, data):
        with self.lock:
            data = data.split(" ")
            if len(data) <= 1:
                return "Invalid Command"
            command = data[0].upper()
            message = data[1:]

            if command == "SET":
                if len(message) < 2:
                    return "Invalid SET command"
                key = message[0].rstrip()
                val = message[1].rstrip()
                if len(message) == 2:
                    self.store[key] = val
                else:
                    exp_command = message[2].upper()
                    curr_time = datetime.datetime.now()
                    if len(message) < 4:
                        return "Invalid SET command"
                    exp_time = float(message[3].rstrip())
                    if exp_command == "EX":
                        self.store[key] = val
                        self.expirations[key] = curr_time + datetime.timedelta(seconds=exp_time)
                    elif exp_command == "PX":
                        self.store[key] = val
                        self.expirations[key] = curr_time + datetime.timedelta(milliseconds=exp_time)
                    else:
                        return "Invalid SET command"
                return "Successfully added to store"
            elif command == "GET" or command == "EXISTS":
                if len(message) != 1:
                    if command == "GET":
                        return "Invalid GET command"
                    return "Invalid EXISTS command"
                key = message[0].rstrip()
                if key in self.store:
                    if key in self.expirations:
                        if self.expirations[key] < datetime.datetime.now():
                            del self.expirations[key]
                            del self.store[key]
                            return "Key not in store"
                        else:
                            if command == "GET":
                                return self.store[key]
                            else:
                                return "Key exists in store"
                    else:
                        if command == "GET":
                            return self.store[key]
                        else:
                            return "Key exists in store"
                return "Key not in store"
            elif command == "DEL":
                if len(message) != 1:
                    return "Invalid DEL Command"
                key = message[0].rstrip()
                if key not in self.store:
                    return "Key not in store"
                else:
                    if key in self.expirations:
                        del self.expirations[key]
                    del self.store[key]
                    return "Successfully deleted key from store"
            elif command == "INCR" or command == "DECR":
                if len(message) != 1:
                    if command == "INCR":
                        return "Invalid INCR command"
                    else:
                        return "Invalid DECR command"
                key = message[0].rstrip()
                if key not in self.store:
                    return "Key not in store"
                if not self.store[key].isnumeric():
                    if command == "INCR":
                        return "Invalid INCR command, value is not a number"
                    return "Invalid DECR command, value is not a number"
                else:
                    val = int(self.store[key])
                    if command == "INCR":
                        self.store[key] = str(val + 1)
                        return "Successfully incremented key"
                    else:
                        self.store[key] = str(val - 1)
                        return "Successfully decremented key"
            elif command == "SAVE":
                if self.filename != "":
                    return self.save()
                else:
                    if len(message) != 1:
                        return "Invalid SAVE command"
                    self.filename = message[0].rstrip()
                    return self.save()

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
import logging
import socket
from typing import Any, Callable
from os.path import exists
from os import mkdir
from importlib import import_module, reload
from yaml import safe_load, dump

logging.getLogger('hbank_database_system').setLevel(logging.INFO)


# CODES TABLE
#  200 - OK
#  303 - Client Quit
#  400 - Invalid Args
#  404 - Invalid Command
#  511 - Kill Server

class Response:
    def __init__(self, code: int, value: str):
        self.code, self.value = code, value

    def __str__(self) -> str:
        return f"{self.code};{self.value}"

    def __bytes__(self):
        return self.__str__().encode()

    def fabricate(self) -> bytes:
        return bytes(self)


class Request:
    def __init__(self, data: list, address: tuple[str, int]):
        self.response = None
        self.data, self.address = data, address

    def fabricate_response(self, code: int, value: str) -> Response:
        response = Response(code, value)
        self.response = response
        return self.response


class ServerModule:
    commands: dict[str, Callable[[Request], Response]] = {}
    __overwrites__: dict[str, Callable[['ServerModule'], None]] = {}
    __parent__: 'Server'
    
    def __init__(self, namespace: str):
        self.commands = {}
        self.namespace = namespace

    def get_server(self) -> 'Server':
        return self.__parent__

    def on(self, cmd: str):
        def args(func: Callable[[Request], Response]):
            def wrapper():
                logging.getLogger('hbank_database_system').warning("This Cannot Be Called")

            self.commands[cmd] = func
            return wrapper

        return args

    def overwrite(self, func: Callable[['ServerModule'], None]):
        def wrapper():
            logging.getLogger('hbank_database_system').warning("This Cannot Be Called")

        self.__overwrites__[func.__name__] = func
        return wrapper

class Server:
    __none__: None = None
    kill = False
    commands: dict[str, Callable[[Request], Response]] = {}
    __internal_commands__: dict[str, Callable[[Request], Response]] = {}

    def __init__(self, address: tuple[str, int]):
        self.allow_modules: bool = False
        self.config: Any | None = None
        self.address = address
        self.load_config()
        self.__config__()
        if not exists('./modules'):
            mkdir('./modules')

    def on(self, cmd: str):
        def args(func: Callable[[Request], Response]):
            def wrapper():
                logging.getLogger('hbank_database_system').warning("This Cannot Be Called")

            self.__internal_commands__[cmd] = func
            self.commands[cmd] = func
            return wrapper

        return args

    def load(self, module: str):
        server_modules: list[ServerModule] = []
        try:
            imported_ = import_module(f'modules.{module}', module)
            imported = reload(imported_)
        except ImportError as _:
            logging.getLogger('hbank_database_system').error(
                f"[MODULES]: Cannot find '{module}'"
            )
            return
        if imported is None:
            return
        server_modules += [
            imported.__dict__[v] for v in dir(imported) if type(imported.__dict__[v]) is ServerModule
        ]

        for serverModule in server_modules:
            serverModule.__parent__ = self
            logging.getLogger('hbank_database_system').info(
                f"[MODULES]: Loaded '{serverModule.namespace}' from '{module}'"
            )
            self.commands |= serverModule.commands
            self.__overwrites__(serverModule, '__init__')

    def load_config(self):
        if not exists('./server.yml'):
            logging.getLogger('hbank_database_system').warning(
                "[CONFIG]: Cannot find 'server.yml' in current directory, creating it"
            )
            config_file = open("server.yml", 'w')
            data = {
                'aliases': {
                    'reload': [
                        'rl'
                    ]
                },
                'allow_modules': False,
                'modules': [
                    'example_module'
                ]
            }
            dump(data, config_file)
            config_file.close()
        config_file = open("server.yml", 'r')
        config: dict[str, str | dict[str, Any] | list[Any] | int | float | bool] = safe_load(config_file)
        config_file.close()
        self.config = config

    def reload(self):
        self.commands = self.__internal_commands__
        self.load_config()
        self.__config__()
    
    def __overwrites__(self, module: ServerModule, event: str):
        for key in module.__overwrites__:
            if key == event:
                module.__overwrites__[key](module)

    def __config__(self):
        if self.config is None:
            return
        self.allow_modules = self.config['allow_modules']
        if self.allow_modules:
            for module in self.config['modules']:
                self.load(module)
        self.aliases: dict[str, str] = {}
        for i in self.config['aliases']:
            for alias in self.config['aliases'][i]:
                self.aliases[alias] = i

    def call(self, cmd: str, request: Request):
        if cmd in self.commands:
            response: Response = self.commands[cmd](request)
            return response
        if cmd in self.aliases:
            response: Response = self.commands[self.aliases[cmd]](request)
            return response
        return Response(404, "")

    def __handle_client__(self, client_socket: socket.socket, address: tuple[str, int]):
        while True:
            val = self.__handle__(client_socket, address)
            if val == 5:
                self.kill = True
            if val != 0:
                return val

    def __handle__(self, client_socket: socket.socket, address: tuple[str, int]):
        try:
            # Receive data from the client
            received_data = client_socket.recv(1024).decode('utf-8').strip()

            print(f"[{address[0]}] -> [127.0.0.1]: {received_data}")

            args: list = received_data.split(" ")

            request: Request = Request(args, address)

            response: Response = self.call(args[0], request)

            client_socket.send(response.fabricate())

            print(f"[127.0.0.1] <- [{address[0]}]: {response}")

            if response.code == 511:
                return 5

            return 0
        except (ConnectionResetError, ConnectionAbortedError) as _:
            print(f"[{address[0]}]: CONNECTION DIED")

            return 1

    def serve(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # Bind the socket to the host and port
            server_socket.bind(self.address)

            # Listen for incoming connections
            server_socket.listen(5)
            print("Socket server listening on port", self.address[1])
            while True:
                client_socket, address = server_socket.accept()
                self.__handle_client__(client_socket, address)
                if self.kill:
                    server_socket.close()
                    break

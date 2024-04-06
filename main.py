from Server import Server, Request, Response

server = Server(('0.0.0.0', 12345))


"""
THIS IS A SERVER TEMPLATE
ITS RECOMMENDED THAT YOU DO NOT MODIFY THIS FILE
"""


@server.on('echo')
def echo(request: Request) -> Response:
    if len(request.data) < 2:
        return request.fabricate_response(400, '')
    return request.fabricate_response(200, ' '.join(request.data[1:]))


@server.on('info')
def info(request: Request) -> Response:
    return request.fabricate_response(200, 'Example Server v1.0 by TheHSI')


@server.on('kill')
def kill(request: Request) -> Response:
    return request.fabricate_response(511, '')


@server.on('quit')
def quit_client(request: Request) -> Response:
    return request.fabricate_response(303, '')


@server.on('reload')
def reload(request: Request) -> Response:
    server.reload()
    return request.fabricate_response(200, 'Reloading...')


server.serve()

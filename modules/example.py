from Server import ServerModule, Request, Response

server = ServerModule('Example Module')


@server.on("example")
def example(request: Request) -> Response:
    return request.fabricate_response(200, 'This is an Example Module')

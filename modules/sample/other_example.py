from Server import ServerModule, Request, Response

module = ServerModule('Another Example Module')


@module.overwrite
def __init__(self: ServerModule):
    print(f'This will also be shown when the plugin is initilized or reloaded')

@module.on("sample")
def example(request: Request) -> Response:
    return request.fabricate_response(200, f'Here is the servre IP: {module.get_server().address[0]}')

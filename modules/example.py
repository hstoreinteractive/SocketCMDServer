from Server import ServerModule, Request, Response

module = ServerModule('Example Module')


@module.overwrite
def __init__(self: ServerModule):
    print(f'This will be shown when the plugin is initilized or reloaded')

@module.on("example")
def example(request: Request) -> Response:
    return request.fabricate_response(200, 'This is an Example Module')

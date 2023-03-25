from starlette.routing import WebSocketRoute
from .views import ChatWebsocketTestEndpoint

routes = [
    WebSocketRoute('/ws/test_app', ChatWebsocketTestEndpoint),
]

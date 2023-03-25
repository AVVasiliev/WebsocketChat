from starlette.routing import Mount

from webchat.routes import routes as webchat_routes

# TODO: split auth and api
routes = [
    Mount("/websocket", routes=webchat_routes),
]
#
#    Mount("/openapi", routes=apispec_routes),
#    AdminMount("/admin", app=admin.get_app(), name="admin"),
#    Mount("/static", app=StaticFiles(directory=settings.STATIC["ROOT_DIR"]), name="static"),
#    Route("/health_check/", HealthCheckAPIView),
#    WebSocketRoute("/ws/test_websocket_base", BaseWebsocketTestEndpoint),
#    WebSocketRoute("/ws/test_websocket_cancel", CancellationWebsocketTestEndpoint),
#    WebSocketRoute("/ws/test_websocket_auth", AuthenticationWebsocketTestEndpoint),
#    WebSocketRoute("/ws/test_websocket_finite_periodic", FinitePeriodicTaskWebsocketTestEndpoint),
#    WebSocketRoute(
#        "/ws/test_websocket_infinite_periodic", InfinitePeriodicTaskWebsocketTestEndpoint
#    ),
#    WebSocketRoute("/ws/test_websocket_chat", ChatWebsocketTestEndpoint),
#]

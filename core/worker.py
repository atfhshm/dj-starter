from uvicorn.workers import UvicornWorker

__all__ = [
    "ASGIWorker",
]


class ASGIWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "lifespan": "off",
    }

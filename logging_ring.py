import logging, socket, time
from collections import deque

class RingBufferHandler(logging.Handler):
    def __init__(self, maxlen: int = 1000, service: str = "service"):
        super().__init__()
        self.buffer = deque(maxlen=maxlen)
        self.service = service
        self.hostname = socket.gethostname()
        self.setFormatter(logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.buffer.append({
                "ts": record.created,
                "time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "service": self.service,
                "host": self.hostname,
            })
        except Exception:
            self.handleError(record)

def attach_log_api(app, handler: RingBufferHandler):
    """
    Adds GET /ops/logs to either a FastAPI or Starlette app.
    Query params: ?since=<float>&limit=<int>&level=DEBUG|INFO|WARNING|ERROR|CRITICAL|ALL
    """
    # Fast path: FastAPI
    if hasattr(app, "include_router"):
        from fastapi import APIRouter, Query
        router = APIRouter()

        @router.get("/ops/logs")
        def get_logs(
            since: float = Query(0.0),
            limit: int = Query(200, ge=1, le=1000),
            level: str = Query("ALL"),
        ):
            items = list(handler.buffer)
            if level != "ALL":
                items = [x for x in items if x["level"] == level]
            items = [x for x in items if x["ts"] > since]
            if len(items) > limit:
                items = items[-limit:]
            next_since = items[-1]["ts"] if items else since
            return {"items": items, "next_since": next_since}

        app.include_router(router)
        return

    # Starlette branch
    # If AGSI app is from starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    async def get_logs(request: Request):
        qp = request.query_params
        try:
            since = float(qp.get("since", "0") or "0")
        except ValueError:
            since = 0.0
        try:
            limit = int(qp.get("limit", "200") or "200")
        except ValueError:
            limit = 200
        level = qp.get("level", "ALL").upper()

        items = list(handler.buffer)
        if level != "ALL":
            items = [x for x in items if x["level"] == level]
        items = [x for x in items if x["ts"] > since]
        if len(items) > limit:
            items = items[-limit:]
        next_since = items[-1]["ts"] if items else since
        return JSONResponse({"items": items, "next_since": next_since})

    # Starlette doesn’t have include_router; add a route directly
    app.add_route("/ops/logs", get_logs, methods=["GET"])

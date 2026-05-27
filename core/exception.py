from dataclasses import dataclass
from typing import Any, Optional
from core.events import bus, Event


# -------------------------
# BASE ERROR
# -------------------------

@dataclass
class CXError(Exception):
    code: str
    message: str
    module: str = "CORE"
    status: int = 500
    context: Optional[Any] = None

    # -------------------------
    # SERIALIZATION
    # -------------------------

    def to_dict(self):
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "module": self.module,
            "status": self.status,
            "context": self.context,
        }

    # -------------------------
    # EVENT EMISSION
    # -------------------------

    def emit(self):
        bus.emit(Event(
            name="exception",
            source=self.module,
            level="ERROR",
            data={
                "code": self.code,
                "message": self.message,
                "status": self.status,
                "context": self.context,
            }
        ))


# -------------------------
# 4xx CLIENT / AI ERRORS
# -------------------------

class CXBadRequest(CXError):
    def __init__(self, msg, module="CORE"):
        super().__init__("CX400", msg, module, 400)


class CXNotFound(CXError):
    def __init__(self, msg, module="FILESYSTEM"):
        super().__init__("CX404", msg, module, 404)


class CXForbidden(CXError):
    def __init__(self, msg, module="SECURITY"):
        super().__init__("CX403", msg, module, 403)


class CXInvalidOperation(CXError):
    def __init__(self, msg, module="CORE"):
        super().__init__("CX422", msg, module, 422)


# -------------------------
# 5xx SYSTEM ERRORS
# -------------------------

class CXInternalError(CXError):
    def __init__(self, msg, module="CORE"):
        super().__init__("CX500", msg, module, 500)


class CXToolFailure(CXError):
    def __init__(self, msg, module="TOOLS"):
        super().__init__("CX502", msg, module, 502)
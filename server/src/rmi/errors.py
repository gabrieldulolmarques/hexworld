import Pyro5.api

ERROR_TAG = "hexworld.HexworldError"

class HexworldError(Exception):
    """Domain error carrying a stable code, propagated to clients over Pyro."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

def _hexworld_error_to_dict(error: HexworldError) -> dict:
    return {"__class__": ERROR_TAG, "code": error.code}

def register_error_serialization() -> None:
    Pyro5.api.register_class_to_dict(HexworldError, _hexworld_error_to_dict)

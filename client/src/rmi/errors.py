import Pyro5.api

ERROR_TAG = "hexworld.HexworldError"

class HexworldError(Exception):
    """Mirror of the server's domain error, reconstructed from the wire."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

def _hexworld_error_from_dict(classname: str, payload: dict) -> HexworldError:
    return HexworldError(payload.get("code", "unexpected_error"))

def register_error_serialization() -> None:
    Pyro5.api.register_dict_to_class(ERROR_TAG, _hexworld_error_from_dict)

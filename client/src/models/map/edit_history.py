from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal

_DEFAULT_HISTORY_LIMIT = 256

class EditHistory(QObject):
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)

    def __init__(self, *, limit: int = _DEFAULT_HISTORY_LIMIT) -> None:
        super().__init__()
        self._undo_stack: deque[dict] = deque(maxlen=limit)
        self._redo_stack: deque[dict] = deque(maxlen=limit)
        self._replaying = False

    @property
    def replaying(self) -> bool:
        return self._replaying

    @replaying.setter
    def replaying(self, value: bool) -> None:
        self._replaying = bool(value)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def record(self, action: dict) -> None:
        if self._replaying:
            return
        before = self._stack_state()
        self._undo_stack.append(action)
        self._redo_stack.clear()
        self._emit_state_changes(before)

    def undo(self) -> dict | None:
        if not self._undo_stack:
            return None
        before = self._stack_state()
        action = self._undo_stack.pop()
        self._redo_stack.append(action)
        self._emit_state_changes(before)
        return action

    def redo(self) -> dict | None:
        if not self._redo_stack:
            return None
        before = self._stack_state()
        action = self._redo_stack.pop()
        self._undo_stack.append(action)
        self._emit_state_changes(before)
        return action

    def clear(self) -> None:
        before = self._stack_state()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._replaying = False
        self._emit_state_changes(before)

    def _stack_state(self) -> tuple[bool, bool]:
        return self.can_undo, self.can_redo

    def _emit_state_changes(self, before: tuple[bool, bool]) -> None:
        can_undo, can_redo = self._stack_state()
        if before[0] != can_undo:
            self.can_undo_changed.emit(can_undo)
        if before[1] != can_redo:
            self.can_redo_changed.emit(can_redo)

"""
Event system definitions for IntelliSearch.

This module defines all event types, event data structures, and event result types
for the event system. Events are used as abstract interfaces between business logic
and UI/system control layers.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, List
from dataclasses import dataclass


class EventType(Enum):
    """Event type enumeration"""

    # User interaction events
    USER_SELECT = "user_select"
    USER_INPUT = "user_input"
    USER_CONFIRM = "user_confirm"

    # System control events
    GLOBAL_SHUTDOWN = "global_shutdown"
    STOP_SESSION = "stop_session"


class BaseEvent(ABC):
    """Base event class (not a dataclass)"""

    event_type: EventType

    @abstractmethod
    def validate(self) -> bool:
        """Validate event data"""
        pass


@dataclass
class UserSelectEvent(BaseEvent):
    """
    User select event - request user to select one or multiple options.

    Attributes:
        event_type: Event type
        message: Prompt message to display to user
        options: List of selectable options
        default_index: Default selected index for single selection
        allow_multiple: Whether multiple selection is allowed
        default_indices: Default selected indices for multiple selection
        cancel_allowed: Whether user can cancel the selection
    """

    event_type: EventType = EventType.USER_SELECT
    message: str = ""
    options: Optional[List[str]] = None
    default_index: int = 0
    allow_multiple: bool = False
    default_indices: Optional[List[int]] = None
    cancel_allowed: bool = True

    def __post_init__(self):
        if self.options is None:
            self.options = []

    def validate(self) -> bool:
        """Validate event data"""
        if not self.message:
            return False
        if not self.options:
            return False
        if self.default_index < 0 or self.default_index >= len(self.options):
            return False
        if self.allow_multiple and self.default_indices:
            for idx in self.default_indices:
                if idx < 0 or idx >= len(self.options):
                    return False
        return True


@dataclass
class UserInputEvent(BaseEvent):
    """
    User input event - request user to input text.

    Attributes:
        event_type: Event type
        message: Prompt message to display to user
        placeholder: Placeholder text for input
        default_value: Default value for input
        validator: Validation rule (email, url, number, etc.)
        min_length: Minimum length of input
        max_length: Maximum length of input
        password: Whether input is password (should be masked)
        multiline: Whether multiline input is allowed
        cancel_allowed: Whether user can cancel the input
    """

    event_type: EventType = EventType.USER_INPUT
    message: str = ""
    placeholder: str = ""
    default_value: str = ""
    validator: Optional[str] = None
    min_length: int = 0
    max_length: int = 1000
    password: bool = False
    multiline: bool = False
    cancel_allowed: bool = True

    def validate(self) -> bool:
        """Validate event data"""
        if not self.message:
            return False
        if self.min_length < 0:
            return False
        if self.max_length <= self.min_length:
            return False
        return True


@dataclass
class UserConfirmEvent(BaseEvent):
    """
    User confirm event - request user to confirm an action.

    Attributes:
        event_type: Event type
        message: Confirmation message
        title: Dialog title
        default_choice: Default choice (True=confirm, False=cancel)
        cancel_allowed: Whether user can cancel
    """

    event_type: EventType = EventType.USER_CONFIRM
    message: str = ""
    title: str = "确认操作"
    default_choice: bool = False
    cancel_allowed: bool = True

    def validate(self) -> bool:
        """Validate event data"""
        return bool(self.message)


@dataclass
class GlobalShutdownEvent(BaseEvent):
    """
    Global shutdown event - shutdown the entire application.

    Attributes:
        event_type: Event type
        message: Shutdown message
        force: Whether to force shutdown
        save_state: Whether to save state before shutdown
    """

    event_type: EventType = EventType.GLOBAL_SHUTDOWN
    message: str = "系统正在关闭..."
    force: bool = False
    save_state: bool = True

    def validate(self) -> bool:
        """Validate event data"""
        return True


@dataclass
class StopSessionEvent(BaseEvent):
    """
    Stop session event - interrupt current thinking/dialogue process.

    Attributes:
        event_type: Event type
        message: Stop message
        reason: Reason for stopping
        save_partial_result: Whether to save partial results
    """

    event_type: EventType = EventType.STOP_SESSION
    message: str = "操作已取消"
    reason: str = ""
    save_partial_result: bool = False

    def validate(self) -> bool:
        """Validate event data"""
        return True


# Event result types
class EventResult:
    """Base event result"""

    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error


class SelectResult(EventResult):
    """User select event result"""

    def __init__(
        self,
        success: bool,
        selected_indices: Optional[List[int]] = None,
        selected_options: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        super().__init__(success, selected_options, error)
        self.selected_indices = selected_indices


class InputResult(EventResult):
    """User input event result"""

    def __init__(
        self, success: bool, input_text: str = "", error: Optional[str] = None
    ):
        super().__init__(success, input_text, error)
        self.input_text = input_text


class ConfirmResult(EventResult):
    """User confirm event result"""

    def __init__(
        self, success: bool, confirmed: bool = False, error: Optional[str] = None
    ):
        super().__init__(success, confirmed, error)

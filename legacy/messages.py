"""Predefined messages for Samsung TV."""

from enum import Enum

class MessageType(Enum):
    """Predefined message types."""
    SLEEP_TIME = "지금은 취침시간입니다"
    REST_TIME = "지금은 휴식시간입니다"
    WAKE_UP = "일어날 시간입니다"
    STUDY_TIME = "공부 시간입니다"
    BREAK_TIME = "휴식 시간입니다"
    MEAL_TIME = "식사 시간입니다"
    EXERCISE_TIME = "운동 시간입니다"
    GOODBYE = "안녕히 가세요"
    WELCOME = "환영합니다"
    MAINTENANCE = "유지보수 중입니다"
    UPDATE = "업데이트 진행 중입니다"


class PresetMessages:
    """Preset message templates."""
    
    @staticmethod
    def sleep_time() -> str:
        """Sleep time message."""
        return "지금은 취침시간입니다"
    
    @staticmethod
    def rest_time() -> str:
        """Rest time message."""
        return "지금은 휴식시간입니다"
    
    @staticmethod
    def wake_up() -> str:
        """Wake up message."""
        return "일어날 시간입니다"
    
    @staticmethod
    def study_time() -> str:
        """Study time message."""
        return "공부 시간입니다"
    
    @staticmethod
    def break_time() -> str:
        """Break time message."""
        return "휴식 시간입니다"
    
    @staticmethod
    def meal_time() -> str:
        """Meal time message."""
        return "식사 시간입니다"
    
    @staticmethod
    def exercise_time() -> str:
        """Exercise time message."""
        return "운동 시간입니다"
    
    @staticmethod
    def goodbye() -> str:
        """Goodbye message."""
        return "안녕히 가세요"
    
    @staticmethod
    def welcome() -> str:
        """Welcome message."""
        return "환영합니다"
    
    @staticmethod
    def maintenance() -> str:
        """Maintenance message."""
        return "유지보수 중입니다"
    
    @staticmethod
    def update() -> str:
        """Update message."""
        return "업데이트 진행 중입니다"
    
    @staticmethod
    def custom(text: str) -> str:
        """Custom message."""
        return text
    
    @staticmethod
    def get_all_presets() -> dict[str, str]:
        """Get all preset messages."""
        return {
            "sleep": PresetMessages.sleep_time(),
            "rest": PresetMessages.rest_time(),
            "wake_up": PresetMessages.wake_up(),
            "study": PresetMessages.study_time(),
            "break": PresetMessages.break_time(),
            "meal": PresetMessages.meal_time(),
            "exercise": PresetMessages.exercise_time(),
            "goodbye": PresetMessages.goodbye(),
            "welcome": PresetMessages.welcome(),
            "maintenance": PresetMessages.maintenance(),
            "update": PresetMessages.update(),
        }


class MessageTemplate:
    """Message templates with placeholders."""
    
    @staticmethod
    def time_based(time_str: str) -> str:
        """Time-based message.
        
        Args:
            time_str: Time string (e.g., "9:00 AM")
        
        Returns:
            Message with time
        """
        return f"{time_str}입니다"
    
    @staticmethod
    def greeting(name: str) -> str:
        """Greeting message.
        
        Args:
            name: Person's name
        
        Returns:
            Greeting message
        """
        return f"{name}님 환영합니다"
    
    @staticmethod
    def notification(event: str) -> str:
        """Notification message.
        
        Args:
            event: Event name
        
        Returns:
            Notification message
        """
        return f"{event} 알림입니다"
    
    @staticmethod
    def reminder(task: str) -> str:
        """Reminder message.
        
        Args:
            task: Task description
        
        Returns:
            Reminder message
        """
        return f"{task} 상기합니다"
    
    @staticmethod
    def warning(issue: str) -> str:
        """Warning message.
        
        Args:
            issue: Issue description
        
        Returns:
            Warning message
        """
        return f"주의: {issue}"
    
    @staticmethod
    def status(status_text: str) -> str:
        """Status message.
        
        Args:
            status_text: Status description
        
        Returns:
            Status message
        """
        return f"상태: {status_text}"

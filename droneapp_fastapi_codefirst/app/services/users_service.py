from typing import Optional
from app.accessors.users_accessor import UsersAccessor
from app.models.models import User


class UsersService:
    """
    Сервис для бизнес-логики работы с пользователями.
    Не зависит от FastAPI напрямую, работает только с моделями и accessors.
    """
    
    def __init__(self, users_accessor: UsersAccessor):
        self.users_accessor = users_accessor
    
    def deactivate_user(self, user_id: int) -> None:
        """
        Деактивирует пользователя (soft delete).
        
        Raises:
            ValueError: если пользователь не найден или произошла ошибка при деактивации
        """
        user = self.users_accessor.deactivate_user(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
    
    def activate_user(self, user_id: int) -> None:
        """
        Активирует пользователя.
        
        Raises:
            ValueError: если пользователь не найден или произошла ошибка при активации
        """
        user = self.users_accessor.activate_user(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
    
    def get_attempts_limit(self, user: User) -> int:
        """
        Возвращает лимит попыток для пользователя на основе его плана.
        
        Rules:
        - Free => 2
        - Pro => 999
        - Fallback => 2 (если план не определен или имя неизвестно)
        
        Args:
            user: Объект пользователя (должен иметь связанный plan)
            
        Returns:
            Лимит попыток
        """
        if not user.plan:
            return 2
        
        plan_name = user.plan.name.lower() if user.plan.name else ""
        
        if plan_name == "free":
            return 2
        elif plan_name == "pro":
            return 999
        else:
            # Fallback для любых других планов
            return 2
    
    def get_remaining_attempts(self, user: User) -> int:
        """
        Возвращает количество оставшихся попыток для пользователя.
        
        Args:
            user: Объект пользователя
            
        Returns:
            Количество оставшихся попыток (limit - used)
        """
        limit = self.get_attempts_limit(user)
        used = user.free_attempts_used or 0
        return max(0, limit - used)
    
    def ensure_can_run_analysis(self, user: User) -> None:
        """
        Проверяет, может ли пользователь запустить анализ.
        
        Raises:
            ValueError: если лимит попыток исчерпан
        
        Args:
            user: Объект пользователя
        """
        remaining = self.get_remaining_attempts(user)
        if remaining <= 0:
            raise ValueError("Лимит попыток исчерпан. Перейдите на Pro.")


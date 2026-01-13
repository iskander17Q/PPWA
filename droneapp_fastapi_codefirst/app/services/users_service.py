from typing import Optional, List
import logging
from app.accessors.users_accessor import UsersAccessor
from app.models.models import User
from app.services.cache_service import MemoryCacheService

logger = logging.getLogger(__name__)


class UsersService:
    """
    Сервис для бизнес-логики работы с пользователями.
    Не зависит от FastAPI напрямую, работает только с моделями и accessors.
    """
    
    def __init__(self, users_accessor: UsersAccessor, cache_service: Optional[MemoryCacheService] = None):
        self.users_accessor = users_accessor
        self.cache_service = cache_service
    
    def list_users(self, active_only: bool = True) -> List[User]:
        """
        Возвращает список пользователей с кэшированием.
        
        Args:
            active_only: Если True, возвращает только активных пользователей
            
        Returns:
            Список пользователей
        """
        cache_key = f"users:list:active" if active_only else "users:list:all"
        
        if self.cache_service:
            cached = self.cache_service.get(cache_key)
            if cached is not None:
                logger.info(f"cache hit: {cache_key}")
                return cached
            logger.info(f"cache miss: {cache_key}")
        
        users = self.users_accessor.list_users(active_only=active_only)
        
        if self.cache_service:
            self.cache_service.set(cache_key, users, ttl_seconds=60)
        
        return users
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Возвращает пользователя по ID с кэшированием.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Пользователь или None
        """
        cache_key = f"users:detail:{user_id}"
        
        if self.cache_service:
            cached = self.cache_service.get(cache_key)
            if cached is not None:
                return cached
        
        user = self.users_accessor.get_user(user_id)
        
        if self.cache_service and user:
            self.cache_service.set(cache_key, user, ttl_seconds=60)
        
        return user
    
    def deactivate_user(self, user_id: int) -> None:
        """
        Деактивирует пользователя (soft delete).
        Сбрасывает кэш пользователей после успешного выполнения.
        
        Raises:
            ValueError: если пользователь не найден или произошла ошибка при деактивации
        """
        user = self.users_accessor.deactivate_user(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Сбрасываем кэш после успешного изменения
        if self.cache_service:
            self.cache_service.remove_by_prefix("users:")
    
    def activate_user(self, user_id: int) -> None:
        """
        Активирует пользователя.
        Сбрасывает кэш пользователей после успешного выполнения.
        
        Raises:
            ValueError: если пользователь не найден или произошла ошибка при активации
        """
        user = self.users_accessor.activate_user(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        # Сбрасываем кэш после успешного изменения
        if self.cache_service:
            self.cache_service.remove_by_prefix("users:")
    
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


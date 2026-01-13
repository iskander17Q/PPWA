from typing import Optional, List
import logging
from sqlalchemy.orm import Session
from app.models.models import User, SubscriptionPlan
from app.services.cache_service import MemoryCacheService

logger = logging.getLogger(__name__)


class PlansService:
    """
    Сервис для бизнес-логики работы с тарифными планами.
    Не зависит от FastAPI напрямую, работает только с моделями и сессией БД.
    """
    
    def __init__(self, db: Session, cache_service: Optional[MemoryCacheService] = None):
        self.db = db
        self.cache_service = cache_service
    
    def list_plans(self) -> List[SubscriptionPlan]:
        """
        Возвращает список тарифных планов с кэшированием.
        
        Returns:
            Список тарифных планов
        """
        cache_key = "plans:list"
        
        if self.cache_service:
            cached = self.cache_service.get(cache_key)
            if cached is not None:
                logger.info(f"cache hit: {cache_key}")
                return cached
            logger.info(f"cache miss: {cache_key}")
        
        plans = self.db.query(SubscriptionPlan).order_by(SubscriptionPlan.name).all()
        
        if self.cache_service:
            self.cache_service.set(cache_key, plans, ttl_seconds=60)
        
        return plans
    
    def delete_plan_hard(self, plan_id: int) -> None:
        """
        Выполняет hard delete тарифного плана после проверки безопасности.
        
        Business rules:
        - Если существует хотя бы один пользователь с users.plan_id=plan_id,
          удаление запрещено и выбрасывается ValueError.
        - Иначе план удаляется из БД и изменения коммитятся.
        
        Args:
            plan_id: ID плана для удаления
            
        Raises:
            ValueError: если план не найден или на него ссылаются пользователи
        """
        plan = self.db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError(f"План с ID {plan_id} не найден")
        
        # Проверка: есть ли пользователи с этим планом
        users_count = self.db.query(User).filter(User.plan_id == plan_id).count()
        if users_count > 0:
            raise ValueError(f"Нельзя удалить тариф '{plan.name}': есть пользователи на этом тарифе.")
        
        # Hard delete
        try:
            self.db.delete(plan)
            self.db.commit()
            
            # Сбрасываем кэш после успешного удаления
            if self.cache_service:
                self.cache_service.remove_by_prefix("plans:")
                self.cache_service.remove_by_prefix("users:")  # user.plan зависит от планов
        except Exception as exc:
            self.db.rollback()
            raise ValueError(f"Ошибка при удалении плана: {str(exc)}") from exc


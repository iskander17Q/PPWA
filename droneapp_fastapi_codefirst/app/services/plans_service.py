from sqlalchemy.orm import Session
from app.models.models import User, SubscriptionPlan


class PlansService:
    """
    Сервис для бизнес-логики работы с тарифными планами.
    Не зависит от FastAPI напрямую, работает только с моделями и сессией БД.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
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
        except Exception as exc:
            self.db.rollback()
            raise ValueError(f"Ошибка при удалении плана: {str(exc)}") from exc


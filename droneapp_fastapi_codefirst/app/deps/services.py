"""
Dependency Injection (DI) слой для сервисов и accessors.

Демонстрация разных lifetime зависимостей в FastAPI:
- Singleton: создается один раз при старте приложения (например, настройки)
- Scoped: создается один раз на HTTP запрос (например, DB session)
- Transient: создается новый экземпляр при каждом вызове dependency (например, сервисы)
"""
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.accessors.users_accessor import UsersAccessor
from app.services.users_service import UsersService
from app.services.plans_service import PlansService


# ============================================================================
# Scoped Dependency (один на HTTP запрос)
# ============================================================================
# get_db() уже определен в app/db.py и является scoped dependency.
# FastAPI создает один экземпляр Session на каждый HTTP запрос и закрывает его после завершения.
# Это оптимально для работы с базой данных.


# ============================================================================
# Transient Dependencies (новый экземпляр при каждом вызове)
# ============================================================================
# В FastAPI по умолчанию все зависимости являются transient, если не указано иное.
# Каждый раз, когда dependency вызывается, создается новый экземпляр.

def get_users_accessor(db: Session = Depends(get_db)) -> UsersAccessor:
    """
    Dependency для получения UsersAccessor.
    
    Lifetime: Transient (создается новый экземпляр при каждом вызове)
    Каждый вызов получает новый UsersAccessor с текущей DB сессией.
    """
    return UsersAccessor(db)


def get_users_service(accessor: UsersAccessor = Depends(get_users_accessor)) -> UsersService:
    """
    Dependency для получения UsersService.
    
    Lifetime: Transient (создается новый экземпляр при каждом вызове)
    Зависит от UsersAccessor, который в свою очередь зависит от DB сессии.
    """
    return UsersService(accessor)


def get_plans_service(db: Session = Depends(get_db)) -> PlansService:
    """
    Dependency для получения PlansService.
    
    Lifetime: Transient (создается новый экземпляр при каждом вызове)
    Получает DB сессию напрямую, так как PlansService работает напрямую с БД.
    """
    return PlansService(db)


# ============================================================================
# Singleton Dependency (один экземпляр на всё приложение)
# ============================================================================
# Пример singleton dependency для настроек приложения (только демонстрация)

@lru_cache()
def get_app_settings() -> dict:
    """
    Пример singleton dependency с использованием @lru_cache.
    
    Lifetime: Singleton (создается один раз при первом вызове и кешируется)
    Используется для конфигурации, которая не меняется во время работы приложения.
    
    Пример использования:
        @router.get("/config")
        def get_config(settings: dict = Depends(get_app_settings)):
            return settings
    
    Важно: @lru_cache() делает функцию singleton, результат кешируется навсегда.
    """
    return {
        "app_name": "DroneApp",
        "version": "1.0.0",
        "max_upload_size": 10 * 1024 * 1024,  # 10MB
    }


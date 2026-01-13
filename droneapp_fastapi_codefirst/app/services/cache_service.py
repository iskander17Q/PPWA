"""
In-memory cache service для кэширования данных приложения.
Простая реализация на основе dict с поддержкой TTL.
"""
import time
from typing import Any, Optional, Dict, Tuple


class MemoryCacheService:
    """
    Простой in-memory cache с поддержкой TTL.
    
    Хранит данные в формате: {key: (expires_at, value)}
    Автоматически очищает истекшие записи при get/is_set.
    """
    
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получает значение из кэша по ключу.
        
        Args:
            key: Ключ для поиска
            
        Returns:
            Значение или None, если ключ не найден или истек TTL
        """
        if key not in self._cache:
            return None
        
        expires_at, value = self._cache[key]
        
        # Проверка TTL
        if time.time() > expires_at:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """
        Сохраняет значение в кэш с указанным TTL.
        
        Args:
            key: Ключ для сохранения
            value: Значение для сохранения
            ttl_seconds: Время жизни в секундах (по умолчанию 60)
        """
        expires_at = time.time() + ttl_seconds
        self._cache[key] = (expires_at, value)
    
    def is_set(self, key: str) -> bool:
        """
        Проверяет, существует ли ключ в кэше (и не истек ли TTL).
        
        Args:
            key: Ключ для проверки
            
        Returns:
            True, если ключ существует и не истек, False иначе
        """
        if key not in self._cache:
            return False
        
        expires_at, _ = self._cache[key]
        
        # Проверка TTL
        if time.time() > expires_at:
            del self._cache[key]
            return False
        
        return True
    
    def remove(self, key: str) -> None:
        """
        Удаляет ключ из кэша.
        
        Args:
            key: Ключ для удаления
        """
        self._cache.pop(key, None)
    
    def remove_by_prefix(self, prefix: str) -> None:
        """
        Удаляет все ключи, начинающиеся с указанного префикса.
        
        Args:
            prefix: Префикс для поиска ключей
        """
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
    
    def clear(self) -> None:
        """
        Очищает весь кэш.
        """
        self._cache.clear()


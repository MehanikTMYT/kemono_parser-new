"""
Система регистрации и управления модулями.
Позволяет динамически загружать и выгружать модули.
"""

from typing import Dict, List, Optional, Type
from importlib import import_module
import logging
import os

from modules.base_module import BaseModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Реестр модулей системы"""
    
    _instance = None
    _modules: Dict[str, BaseModule] = {}
    _module_classes: Dict[str, Type[BaseModule]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_class(self, module_class: Type[BaseModule]) -> None:
        """Регистрация класса модуля"""
        name = module_class.name
        if name in self._module_classes:
            logger.warning(f"Модуль {name} уже зарегистрирован")
            return
        self._module_classes[name] = module_class
        logger.info(f"Зарегистрирован класс модуля: {name}")
    
    def register_instance(self, module: BaseModule) -> None:
        """Регистрация экземпляра модуля"""
        name = module.name
        if name in self._modules:
            logger.warning(f"Экземпляр модуля {name} уже существует")
            return
        self._modules[name] = module
        logger.info(f"Зарегистрирован экземпляр модуля: {name}")
    
    def create_module(self, name: str, config: dict = None) -> Optional[BaseModule]:
        """Создание экземпляра модуля по имени"""
        if name not in self._module_classes:
            logger.error(f"Модуль {name} не найден")
            return None
        
        module_class = self._module_classes[name]
        module = module_class(config)
        self.register_instance(module)
        return module
    
    def get_module(self, name: str) -> Optional[BaseModule]:
        """Получение экземпляра модуля"""
        return self._modules.get(name)
    
    def get_all_modules(self) -> List[BaseModule]:
        """Получение всех модулей"""
        return list(self._modules.values())
    
    def initialize_module(self, name: str, config: dict = None) -> bool:
        """Инициализация модуля"""
        module = self.get_module(name)
        if not module:
            module = self.create_module(name, config)
        
        if not module:
            return False
        
        # Проверка зависимостей
        for dep in module.dependencies:
            if dep not in self._modules:
                logger.error(f"Зависимость {dep} не найдена для {name}")
                return False
        
        success = module.initialize()
        if success:
            logger.info(f"Модуль {name} инициализирован")
        else:
            logger.error(f"Ошибка инициализации модуля {name}")
        
        return success
    
    def shutdown_all(self) -> None:
        """Остановка всех модулей"""
        for module in self._modules.values():
            try:
                module.shutdown()
            except Exception as e:
                logger.error(f"Ошибка остановки {module.name}: {e}")
        self._modules.clear()
    
    def auto_discover(self, modules_dir: str = "modules") -> None:
        """Автоматическое обнаружение модулей"""
        if not os.path.exists(modules_dir):
            return
        
        for item in os.listdir(modules_dir):
            if item.startswith('_') or item.startswith('.'):
                continue
            
            module_path = os.path.join(modules_dir, item)
            if not os.path.isdir(module_path):
                continue
            
            module_file = os.path.join(module_path, f"{item.replace('/', '_')}_module.py")
            if os.path.exists(module_file):
                try:
                    module_name = f"{modules_path}.{item}.{item.replace('/', '_')}_module"
                    module = import_module(module_name)
                    # Ищем классы наследники BaseModule
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseModule) and 
                            attr != BaseModule):
                            self.register_class(attr)
                except Exception as e:
                    logger.error(f"Ошибка загрузки модуля {item}: {e}")
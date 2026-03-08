"""
Тесты для модулей системы.
"""

import pytest
from unittest.mock import Mock, patch
from modules.base_module import BaseModule, ModuleState


class DemoTestModule(BaseModule):
    """Тесты базового модуля"""
    
    class TestModule(BaseModule):
        name = "test_module"
        version = "1.0.0"
        description = "Test module"
        
        def initialize(self):
            self._set_state(ModuleState.READY)
            return True
        
        def execute(self, **kwargs):
            return {"result": "ok"}
    
    def test_module_init(self):
        """Инициализация модуля"""
        module = self.TestModule()
        assert module.name == "test_module"
        assert module.state == ModuleState.UNINITIALIZED
    
    def test_module_initialize(self):
        """Инициализация состояния"""
        module = self.TestModule()
        result = module.initialize()
        assert result == True
        assert module.state == ModuleState.READY
    
    def test_module_execute(self):
        """Выполнение модуля"""
        module = self.TestModule()
        module.initialize()
        result = module.execute()
        assert result == {"result": "ok"}
    
    def test_module_info(self):
        """Информация о модуле"""
        module = self.TestModule()
        info = module.get_info()
        assert "name" in info
        assert "version" in info
        assert "state" in info
    
    def test_module_shutdown(self):
        """Завершение модуля"""
        module = self.TestModule()
        module.initialize()
        module.shutdown()
        assert module.state == ModuleState.UNINITIALIZED


class TestModuleRegistry:
    """Тесты реестра модулей"""
    
    def test_registry_singleton(self):
        """Реестр - синглтон"""
        from core.registry import ModuleRegistry
        r1 = ModuleRegistry()
        r2 = ModuleRegistry()
        assert r1 is r2
    
    def test_registry_register_class(self):
        """Регистрация класса"""
        from core.registry import ModuleRegistry
        registry = ModuleRegistry()
        
        class TestMod(BaseModule):
            name = "test_reg_module"
            version = "1.0.0"
            description = "Test"
            
            def initialize(self): return True
            def execute(self, **kwargs): return {}
        
        registry.register_class(TestMod)
        assert "test_reg_module" in registry._module_classes
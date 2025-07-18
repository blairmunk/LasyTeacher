"""Базовые тесты для проверки утилит"""

from django.test import TestCase
from latex_generator.utils import sanitize_latex, sanitize_filename

class BasicUtilsTest(TestCase):
    """Базовые тесты утилит"""
    
    def test_sanitize_latex_basic(self):
        """Тест базового экранирования"""
        result = sanitize_latex("Простой текст")
        self.assertEqual(result, "Простой текст")
        
        result = sanitize_latex("Цена $5 & скидка 10%")
        self.assertEqual(result, "Цена \\$5 \\& скидка 10\\%")
    
    def test_sanitize_filename_basic(self):
        """Тест очистки имен файлов"""
        result = sanitize_filename("test_file.tex")
        self.assertEqual(result, "test_file.tex")
        
        result = sanitize_filename("file<>*.tex")
        self.assertEqual(result, "file___.tex")

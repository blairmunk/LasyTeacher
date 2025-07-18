"""Утилиты для компиляции LaTeX в PDF"""

import os
import subprocess
from pathlib import Path

def compile_latex_to_pdf(latex_file, output_dir):
    """Компилирует LaTeX файл в PDF"""
    try:
        # Меняем рабочую директорию для pdflatex
        old_cwd = os.getcwd()
        os.chdir(output_dir)
        
        # Запускаем pdflatex дважды (для правильных ссылок)
        for i in range(2):
            result = subprocess.run([
                'pdflatex', 
                '-interaction=nonstopmode',
                '-halt-on-error',
                latex_file.name
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                print(f"❌ Ошибка компиляции LaTeX (проход {i+1}):")
                print(result.stderr)
                print("Лог компиляции:")
                print(result.stdout[-1000:])  # Последние 1000 символов лога
                os.chdir(old_cwd)
                return None
        
        os.chdir(old_cwd)
        
        pdf_file = latex_file.with_suffix('.pdf')
        return pdf_file if pdf_file.exists() else None
            
    except FileNotFoundError:
        print("❌ pdflatex не найден. Установите TeX Live:")
        print("sudo apt-get install texlive-latex-extra texlive-lang-cyrillic")
        return None
    except Exception as e:
        print(f"❌ Ошибка при компиляции: {e}")
        return None

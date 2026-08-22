import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless

from django.test import SimpleTestCase

from infrastructure.services.latex_document_payloads import (
    LATEX_TEXT_FIELDS,
    LatexTaskPayloadFormatter,
)
from infrastructure.services.latex_formula_processor import (
    latex_formula_processor,
    sanitize_latex,
)


class TaskLatexRenderingCasesTests(SimpleTestCase):
    def test_escapes_plain_text_without_corrupting_safe_escapes(self):
        cases = (
            ('A & B 20% #1_x', r'A \& B 20\% \#1\_x'),
            (r'Цена \$5 и 20\%', r'Цена \$5 и 20\%'),
            (r'Команда \alpha', r'Команда \textbackslash{}alpha'),
            ('<x> ~ y ^ 2', r'\textless{}x\textgreater{} \textasciitilde{} y \textasciicircum{} 2'),
            ('Строка 1\nСтрока 2', r'Строка 1\\ Строка 2'),
        )

        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(sanitize_latex(source), expected)

    def test_preserves_supported_math_and_escapes_surrounding_text(self):
        cases = (
            (
                r'Сила & $F=ma$',
                r'Сила \& \(F=ma\)',
            ),
            (
                r'Цена \$5, \(x_1=2\)',
                r'Цена \$5, \(x_1=2\)',
            ),
            (
                '$$\\begin{aligned}F&=ma\\\\a&=F/m\\end{aligned}$$',
                '\\[\\begin{aligned}F&=ma\\\\a&=F/m\\end{aligned}\\]',
            ),
            (
                r'Вычислите $(3{,}5-1{,}2)\cdot4$',
                r'Вычислите \((3{,}5-1{,}2)\cdot4\)',
            ),
        )

        for source, expected in cases:
            with self.subTest(source=source):
                result = latex_formula_processor.render_for_latex_safe(source)

                self.assertEqual(result['content'], expected)
                self.assertEqual(result['errors'], [])

    def test_blocks_dangerous_commands_inside_and_outside_math(self):
        inside = latex_formula_processor.render_for_latex_safe(
            r'Опасно $\input{secret}$',
        )
        with self.assertLogs(
            'core_logic.services.formula_processor',
            level='WARNING',
        ):
            outside = latex_formula_processor.render_for_latex_safe(
                r'Опасно \input{secret}',
            )

        self.assertIn('[ЗАБЛОКИРОВАННАЯ КОМАНДА]', inside['content'])
        self.assertTrue(inside['errors'])
        self.assertNotIn(r'\input', outside['content'])
        self.assertIn('[ЗАБЛОКИРОВАНО]', outside['content'])

    def test_formats_every_latex_capable_task_field(self):
        formatter = LatexTaskPayloadFormatter()
        payload = {
            field_name: rf'{field_name}: $x_{{1}}^2$ & текст'
            for field_name in LATEX_TEXT_FIELDS
        }

        result = formatter.format_task_payload(payload)

        for field_name in LATEX_TEXT_FIELDS:
            with self.subTest(field_name=field_name):
                escaped_label = field_name.replace('_', r'\_')
                self.assertEqual(
                    result[field_name],
                    rf'{escaped_label}: \(x_{{1}}^2\) \& текст',
                )
        self.assertEqual(result['latex_content'], result['text'])
        self.assertFalse(result['has_formula_errors'])


class TaskLatexCompilationTests(SimpleTestCase):
    @skipUnless(shutil.which('xelatex'), 'xelatex is not installed')
    def test_representative_task_latex_corpus_compiles(self):
        task_texts = (
            r'Условие: A & B, 20\%, цена \$5.',
            r'Плотность $\rho=\frac{m}{V}$.',
            r'Модуль $v=\sqrt{v_x^2+v_y^2}$.',
            r'Сила $\vec{F}=m\vec{a}$, $F_1=2\cdot10^{-3}\,\mathrm{N}$.',
            r'Интервал \(x\in[0;1]\), $\alpha\leq\beta$.',
            '$$\\begin{aligned}F&=ma\\\\a&=F/m\\end{aligned}$$',
            '$$\\begin{cases}x+y=2\\\\x-y=0\\end{cases}$$',
            r'Десятичная дробь $(3{,}5-1{,}2)\cdot4$.',
            r'Пояснение $\text{дано}:\quad v=5\,\mathrm{m/s}$.',
        )
        rendered = [
            latex_formula_processor.render_for_latex_safe(text)['content']
            for text in task_texts
        ]
        document = '\n'.join((
            r'\documentclass{article}',
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage[T2A]{fontenc}',
            r'\usepackage[russian]{babel}',
            r'\usepackage{amsmath,amssymb}',
            r'\begin{document}',
            *[f'{index}. {text}\\par' for index, text in enumerate(rendered, 1)],
            r'\end{document}',
        ))

        with TemporaryDirectory() as directory:
            source_path = Path(directory) / 'task-latex-corpus.tex'
            source_path.write_text(document, encoding='utf-8')
            process = subprocess.run(
                [
                    'xelatex',
                    '-interaction=nonstopmode',
                    '-halt-on-error',
                    source_path.name,
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(
            process.returncode,
            0,
            process.stdout[-4000:] + process.stderr[-2000:],
        )

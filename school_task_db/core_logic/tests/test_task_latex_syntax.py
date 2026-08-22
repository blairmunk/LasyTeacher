from unittest import TestCase

from core_logic.services.formula_processor import FormulaProcessor


class TaskLatexDelimiterTests(TestCase):
    def setUp(self):
        self.processor = FormulaProcessor()

    def test_extracts_supported_inline_and_display_delimiters(self):
        cases = (
            ('$v=s/t$', 'inline', 'v=s/t'),
            ('$$E=mc^2$$', 'display', 'E=mc^2'),
            (r'\(a^2+b^2=c^2\)', 'inline', 'a^2+b^2=c^2'),
            (r'\[\frac{A}{t}\]', 'display', r'\frac{A}{t}'),
        )

        for text, formula_type, content in cases:
            with self.subTest(text=text):
                formulas = self.processor.extract_formulas(text)

                self.assertEqual(len(formulas), 1)
                self.assertEqual(formulas[0]['type'], formula_type)
                self.assertEqual(formulas[0]['content'], content)
                self.assertEqual(formulas[0]['original'], text)
                self.assertEqual(formulas[0]['position'], (0, len(text)))

    def test_extracts_adjacent_mixed_formulas_in_source_order(self):
        text = r'Дано $m=2$ кг, \(v=3\) м/с. $$E=mv^2/2$$'

        formulas = self.processor.extract_formulas(text)

        self.assertEqual(
            [(item['type'], item['content']) for item in formulas],
            [
                ('inline', 'm=2'),
                ('inline', 'v=3'),
                ('display', 'E=mv^2/2'),
            ],
        )
        self.assertEqual(self.processor.count_formulas(text), 3)

    def test_extracts_multiline_display_formula(self):
        text = '$$\\begin{aligned}\na &= b \\\\\nc &= d\n\\end{aligned}$$'

        formulas = self.processor.extract_formulas(text)

        self.assertEqual(len(formulas), 1)
        self.assertEqual(formulas[0]['type'], 'display')
        self.assertIn(r'\begin{aligned}', formulas[0]['content'])
        self.assertIn(r'\end{aligned}', formulas[0]['content'])

    def test_ignores_escaped_dollars_and_unclosed_delimiters(self):
        cases = (
            r'Цена \$5',
            'Незакрытая $x+1',
            r'Незакрытая \[x+1',
        )

        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(self.processor.has_math(text))
                self.assertEqual(self.processor.extract_formulas(text), [])

    def test_escaped_currency_does_not_consume_following_formula(self):
        text = r'Цена \$5, формула $x+1$.'

        formulas = self.processor.extract_formulas(text)

        self.assertEqual(len(formulas), 1)
        self.assertEqual(formulas[0]['content'], 'x+1')


class TaskLatexValidationTests(TestCase):
    def setUp(self):
        self.processor = FormulaProcessor()

    def test_accepts_representative_school_math_constructs(self):
        formulas = (
            r'\frac{m}{V}',
            r'\sqrt{x^2+y^2}',
            r'x_1+x_{n}^{2}',
            r'\vec{F}=m\vec{a}',
            r'\alpha+\beta\leq\gamma',
            r'3{,}5\cdot 10^{-2}\,\mathrm{m}',
            r'\left(\frac{a}{b}\right)^2',
            r'\left\{x \mid x>0\right\}',
            r'\text{дано}:\quad v=5\,\mathrm{m/s}',
            r'\begin{aligned}F&=ma\\a&=F/m\end{aligned}',
            r'\begin{cases}x+y=2\\x-y=0\end{cases}',
        )

        for formula in formulas:
            with self.subTest(formula=formula):
                validation = self.processor.validate_formula(formula)

                self.assertTrue(validation['is_valid'], validation['errors'])
                self.assertEqual(validation['errors'], [])

    def test_rejects_structurally_invalid_formulas(self):
        cases = (
            (r'\frac{x}{y', 'Несбалансированные скобки'),
            (r'\left(x+1', r'\left и \right'),
            (r'\begin{aligned}x&=1', 'Незакрытое окружение'),
        )

        for formula, message in cases:
            with self.subTest(formula=formula):
                validation = self.processor.validate_formula(formula)

                self.assertFalse(validation['is_valid'])
                self.assertTrue(
                    any(message in error for error in validation['errors']),
                    validation['errors'],
                )

    def test_rejects_dangerous_tex_commands(self):
        commands = (
            r'\input{secret}',
            r'\include{chapter}',
            r'\write18{command}',
            r'\openout1{file}',
            r'\read1',
            r'\def\x{unsafe}',
            r'\let\x\y',
            r'\csname command\endcsname',
            r'\expandafter\x',
            r'\directlua{unsafe}',
        )

        for command in commands:
            with self.subTest(command=command):
                validation = self.processor.validate_formula(command)

                self.assertFalse(validation['is_valid'])
                self.assertTrue(any(
                    'Опасная команда' in error
                    for error in validation['errors']
                ))


class TaskLatexHtmlRenderingTests(TestCase):
    def setUp(self):
        self.processor = FormulaProcessor()

    def test_preserves_supported_delimiters_for_mathjax(self):
        cases = (
            r'Скорость $v=s/t$.',
            r'Скорость \(v=s/t\).',
            r'$$\vec{F}=m\vec{a}$$',
            r'\[\frac{A}{t}\]',
            r'Цена \$5, затем $x=2$.',
        )

        for source in cases:
            with self.subTest(source=source):
                result = self.processor.render_for_html_safe(source)

                self.assertEqual(result['content'], source)
                self.assertEqual(result['errors'], [])

    def test_blocks_dangerous_formula_before_mathjax_rendering(self):
        result = self.processor.render_for_html_safe(
            r'Опасно $\input{secret}$.',
        )

        self.assertNotIn(r'\input', result['content'])
        self.assertIn('blocked-formula', result['content'])
        self.assertTrue(result['errors'])

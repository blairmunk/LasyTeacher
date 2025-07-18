"""
DEPRECATED: Используйте `python manage.py generate_latex work <id>` 
Эта команда оставлена для обратной совместимости
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'DEPRECATED: Используйте generate_latex work <id>'
    
    def add_arguments(self, parser):
        parser.add_argument('work_id', type=int, help='ID работы')
        parser.add_argument('--format', choices=['latex', 'pdf'], default='pdf')
        parser.add_argument('--with-answers', action='store_true')
        parser.add_argument('--output-dir', default='latex_output')
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '⚠️  Эта команда устарела. Используйте: python manage.py generate_latex work <id>'
            )
        )
        
        # Перенаправляем на новую команду
        new_args = ['generate_latex', 'work', str(options['work_id'])]
        new_options = {
            'format': options['format'],
            'output_dir': options['output_dir'],
            'with_answers': options['with_answers'],
        }
        
        call_command(*new_args, **new_options)

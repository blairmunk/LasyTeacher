"""Команда для просмотра доступных генераторов"""

from django.core.management.base import BaseCommand
from latex_generator.generators.registry import registry

class Command(BaseCommand):
    help = 'Показать список доступных генераторов LaTeX'
    
    def handle(self, *args, **options):
        self.stdout.write('📋 Доступные генераторы LaTeX:')
        
        for generator_type in registry.get_available_types():
            generator_class = registry.get_generator(generator_type)
            self.stdout.write(f'  • {generator_type}: {generator_class.__name__}')
        
        self.stdout.write('\n💡 Использование:')
        self.stdout.write('  python manage.py generate_latex <тип> <id> [опции]')
        self.stdout.write('\n🔧 Примеры:')
        self.stdout.write('  python manage.py generate_latex work 1 --format pdf')
        self.stdout.write('  python manage.py generate_latex work 1 --with-answers')

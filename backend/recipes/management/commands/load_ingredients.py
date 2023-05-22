import csv
from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из ingredients.csv'

    def handle(self, *args, **options):
        with open(
            file='../data/ingredients.csv',
            newline='',
            encoding='utf-8'
        ) as f:
            reader = csv.reader(f)
            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )

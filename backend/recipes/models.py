from colorfield.fields import ColorField
from django.db.models import Model, CharField, SlugField


class Tag(Model):
    """Модель тега, по которому можно фильтровать рецепты."""
    name = CharField(
        verbose_name='Название',
        help_text='Введите название.',
        max_length=200,
        unique=True,
        blank=False,
        null=False
    )
    color = ColorField(
        verbose_name='Цвет в HEX',
        help_text='Введите цвет в формате HEX.',
        unique=True,
        blank=False,
        null=False
    )
    slug = SlugField(
        verbose_name='Уникальный слаг',
        help_text='Введите уникальный слаг.',
        max_length=200,
        unique=True,
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(Model):
    """
    Модель ингредиента, связываемая с моделью рецепта через
    вспомогательную модель 'ингредиент рецепта'.
    """
    name = CharField(
        verbose_name='Название',
        help_text='Введите название.',
        max_length=200,
        unique=True,
        blank=False,
        null=False,
        db_index=True
    )
    measurement_unit = CharField(
        verbose_name='Единица измерения',
        help_text='Введите единицу измерения.',
        max_length=200,
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} в {self.measurement_unit}'

from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.db.models import (
    Model, CharField, SlugField, ForeignKey, CASCADE, ImageField,
    TextField, ManyToManyField, PositiveSmallIntegerField,
    DateTimeField
)

User = get_user_model()


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
    вспомогательную модель 'ингредиент в рецепте'.
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


class Recipe(Model):
    """Модель рецепта."""
    author = ForeignKey(
        to=User,
        on_delete=CASCADE,
        related_name='recipes',
        verbose_name='Автор',
        help_text='Укажите автора'
    )
    name = CharField(
        verbose_name='Название',
        help_text='Введите название.',
        max_length=200,
        blank=False,
        null=False
    )
    image = ImageField(
        verbose_name='Картинка',
        help_text='Загрузите картинку.',
        upload_to='recipes/',
        blank=False,
        null=False
    )
    text = TextField(
        verbose_name='Описание',
        help_text='Введите описание.',
        blank=False,
        null=False
    )
    ingredients = ManyToManyField(
        to=Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты.',
        blank=False,
        null=False
    )
    tags = ManyToManyField(
        to=Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите один или несколько тегов.',
        blank=False,
        null=False
    )
    cooking_time = PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Укажите время приготовления в минутах.',
        blank=False,
        null=False
    )
    pub_date = DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.name}, автор {self.author}'

from django.contrib.auth.models import AbstractUser
from django.db.models import EmailField, CharField


class User(AbstractUser):
    """Модель пользователя."""
    REQUIRED_FIELDS = ('email', 'first_name', 'last_name')
    email = EmailField(
        verbose_name='Адрес электронной почты',
        help_text='Введите адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    first_name = CharField(
        verbose_name='Имя',
        help_text='Введите имя',
        max_length=150,
        blank=False,
        null=False
    )
    last_name = CharField(
        verbose_name='Фамилия',
        help_text='Введите фамилию',
        max_length=150,
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = 'Пользователь',
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

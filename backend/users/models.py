from django.contrib.auth.models import AbstractUser
from django.db.models import (CASCADE, CharField, CheckConstraint, EmailField,
                              F, ForeignKey, Model, Q, UniqueConstraint)


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
        ordering = (-'date_joined',)

    def __str__(self):
        return self.username


class Follow(Model):
    """Модель для сервиса подписки на авторов."""
    user = ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user__username', 'author__username')
        constraints = (
            UniqueConstraint(
                fields=('user', 'author'),
                name='Cannot follow more then once.'
            ),
            CheckConstraint(
                check=~Q(user=F('author')),
                name='Cannot follow themselves.'
            ),
        )

    def __str__(self):
        return (
            f'Пользователь {self.user.get_username()} подписан на '
            f'автора {self.author.get_username()}'
        )

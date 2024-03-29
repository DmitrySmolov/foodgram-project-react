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
        ordering = ('-date_joined',)

    def __str__(self):
        return self.username


class Follow(Model):
    """Модель для сервиса подписки на авторов."""
    follower = ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=CASCADE,
        related_name='follows',
        verbose_name='Пользователь',
    )
    followee = ForeignKey(
        User,
        blank=False,
        null=False,
        on_delete=CASCADE,
        related_name='followed_by',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('follower__username', 'followee__username')
        constraints = (
            UniqueConstraint(
                fields=('follower', 'followee'),
                name='Cannot follow more then once.'
            ),
            CheckConstraint(
                check=~Q(follower=F('followee')),
                name='Cannot follow themselves.'
            ),
        )

    def __str__(self):
        return (
            f'Пользователь {self.follower.get_username()} подписан на '
            f'автора {self.followee.get_username()}'
        )

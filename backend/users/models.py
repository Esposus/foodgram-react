from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.constraints import UniqueConstraint

from .validators import validate_username


class User(AbstractUser):
    """Кастомный пользователь"""
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты',
        help_text='Адрес электронной почты'
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_username],
        verbose_name='Юзернейм',
        help_text='Уникальное имя пользователя'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Фамилия'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    @property
    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    """Подписчик"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Автор, на которого можно подписаться'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=['user', 'author'],
            name='unique_following'
        )]

    def ___str___(self) -> str:
        return f'{self.user} подписан на рецепты {self.author}'

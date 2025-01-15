from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        blank=False,
        null=False
    )
    avatar = models.ImageField(
        'Аватарка',
        upload_to='pics/users',
        blank=True,
        null=True,
    )
    subs = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        verbose_name='Подписки',
        blank=True,
    )
    fav = models.ManyToManyField(
        'recipes.Recipe',
        related_name='fav_by',
        verbose_name='Избранное',
        blank=True,
    )
    cart = models.ManyToManyField(
        'recipes.Recipe',
        related_name='in_cart_of',
        verbose_name='Список покупок',
        blank=True,
    )

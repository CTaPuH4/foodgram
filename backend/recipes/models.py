from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import TITLE_MAX_LENGTH, MAX_VALUE, MIN_VALUE
from users.models import CustomUser


class AbstractModel(models.Model):
    name = models.CharField(
        'Название',
        max_length=TITLE_MAX_LENGTH,
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Tag(AbstractModel):
    slug = models.SlugField('Слаг', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('pk',)


class Ingredient(AbstractModel):
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=TITLE_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('pk',)


class Recipe(AbstractModel):
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    image = models.ImageField('Картинка', upload_to='pics')
    text = models.TextField('Текстовое описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        through_fields=('recipe', 'ingredient'),
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE)
        ),
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pk',)


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipeingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридент',
        related_name='listingredients'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE)
        ),
    )

    class Meta:
        verbose_name = 'ингредиенты рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ('recipe', 'ingredient')
        ordering = ('pk',)

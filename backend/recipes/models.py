from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint

from ingredients.models import Ingredient
from tags.models import Tag
from users.models import User


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название',
        help_text='Название'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_author',
        verbose_name='Автор рецепта',
        help_text='Автор рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
        help_text='Изображение'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTags',
        verbose_name='Теги',
        help_text='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            message='Минимальное время приготовления - 1 минута'
        )],
        verbose_name='Время приготовления в минутах',
        help_text='Время приготовления в минутах'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Дата публикации'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=('name', 'author'),
            name='unique_name_author'
        )]
        ordering = ('pub_date',)
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_amount',
        verbose_name='Рецепт',
        help_text='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ингредиент для рецепта',
        help_text='Ингредиент для рецепта'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            message='Нужен хотя бы 1 ингредиент'
        )],
        verbose_name='Количество ингредиентов в рецепте',
        help_text='Количество ингредиентов в рецепте'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=('recipe', 'ingredient'),
            name='unique_ingredient'
        )]
        ordering = ('ingredient',)
        verbose_name = 'Количество ингредиентов в рецепте'
        verbose_name_plural = 'Количество ингредиентов в рецепте'

    def __str__(self):
        return (f'{self.ingredient.name} - '
                f'{self.amount} {self.ingredient.measurement_unit}')


class RecipeTags(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег рецепта',
        help_text='Тег рецепта'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='Рецепт',
        help_text='Рецепт'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=('recipe', 'tag'),
            name='unique_tag'
        )]
        ordering = ('tag',)
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return self.tag


class FavoriteRecipes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_favorites',
        verbose_name='Автор списка избранного',
        help_text='Автор списка избранного'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_favorites',
        verbose_name='Рецепт из списка избранного',
        help_text='Рецепт из списка избранного'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_favorite_recipes'
        )]
        ordering = ('recipe',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.recipe} в избранном у {self.user}'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_shoppinglist',
        verbose_name='Автор списка покупок',
        help_text='Автор списка покупок'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_shoppinglist',
        verbose_name='Список покупок',
        help_text='Список покупок'
    )

    class Meta:
        constraints = [UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_shoppinglist_recipe'
        )]
        verbose_name = 'Список покупок',
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.recipe} в списке покупок у {self.user}'

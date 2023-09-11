from django.contrib import admin

from .models import (Recipe,
                     RecipeIngredients,
                     RecipeTags,
                     FavoriteRecipes,
                     ShoppingList)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'text', 'author', 'cooking_time', 'pub_date')
    search_fields = ('name', 'text', 'author')
    list_filter = ('pub_date', 'name', 'author')
    empty_value_display = '-пусто-'


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('ingredient',)
    list_filter = ('recipe', 'ingredient')
    empty_value_display = '-пусто-'


@admin.register(RecipeTags)
class RecipeTagsAdmin(admin.ModelAdmin):
    list_display = ('tag', 'recipe')
    search_fields = ('tag',)
    list_filter = ('recipe', 'tag')
    empty_value_display = '-пусто-'


@admin.register(FavoriteRecipes)
class FavoriteRecipesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'

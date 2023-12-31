import django_filters as filters
from django_filters.widgets import BooleanWidget

from ingredients.models import Ingredient
from recipes.models import Recipe
from users.models import User


class IngredientNameFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = (
            'name',
            'measurement_unit'
        )


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited',
        method='get_is_favorited',
        widget=BooleanWidget()
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='get_is_in_shopping_cart',
        widget=BooleanWidget()
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(recipe_favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(recipe_shoppinglist__user=user)
        return queryset

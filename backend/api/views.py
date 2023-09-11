from http import HTTPStatus

from django.db.models import BooleanField, Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from ingredients.models import Ingredient
from recipes.models import FavoriteRecipes, Recipe, ShoppingList
from tags.models import Tag
from users.models import Follow, User

from .filters import IngredientNameFilter, RecipeFilter
from .pagination import Pagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    FollowSerialiser, IngredientSerializer, PasswordSerializer,
    RecipeCreateUpdateSerializer, RecipeSerializer, ShortRecipeSerializer,
    TagSerializer, CustomUserCreateSerializer, UserRecipesSerializer,
    CustomUserSerializer
)
from .utils import get_ingredients_for_shopping


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = Pagination
    permission_classes = (AllowAny,)
    search_fields = ('username', 'email')

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(detail=False,
            methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request, pk=None):
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = PasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user.set_password(serializer.data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = FollowSerialiser(
                Follow.objects.create(user=request.user, author=author),
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Follow.objects.filter(user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = Follow.objects.filter(user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = UserRecipesSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientNameFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('ingredients', 'tags')
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoriteRecipes.objects.filter(
                        user=user, recipe__pk=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(ShoppingList.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return queryset

    @staticmethod
    def add_recipe(model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(recipe=recipe, user=request.user)
        serializer = ShortRecipeSerializer(recipe)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    @staticmethod
    def delete_recipe(model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.filter(recipe=recipe, user=request.user).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(FavoriteRecipes, request, pk)
        return self.delete_recipe(FavoriteRecipes, request, pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def add_or_delete_recipe(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(Recipe, request, pk)
        return self.delete_recipe(Recipe, request, pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(ShoppingList, request, pk)
        return self.delete_recipe(ShoppingList, request, pk)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        return get_ingredients_for_shopping(user)

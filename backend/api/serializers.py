import webcolors
from django.db.models import Count
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from ingredients.models import Ingredient
from recipes.models import Recipe, RecipeIngredients, RecipeTags
from tags.models import Tag
from users.models import Follow, User


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(
                'Для этого цвета нет названия'
            )
        return webcolors.hex_to_name(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Создание пользователя"""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'first_name', 'last_name'
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj) -> bool:
        user = self.context['request'].user
        if not user or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class FollowSerialiser(serializers.ModelSerializer):
    """Подписка на автора"""
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [serializers.UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=('user', 'author'),
            message='Повторная подписка невозможна'
        )]

    def validate_following(self, obj):
        request = self.context.get('request')
        if request.user == obj:
            raise serializers.ValidationError('Подписка на себя запрещена')
        return obj


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeTags
        fields = ('tag', 'recipe')


class IngredientSerializer(serializers.ModelSerializer):
    """Вывод ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Вывод ингредиентов в рецепте"""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Добавление ингредиентов в рецепт"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Вывод рецептов"""
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientsSerializer(
        source='recipe_amount', many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'author', 'image', 'ingredients',
            'tags', 'cooking_time', 'is_favorited', 'is_in_shopping_cart')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецепта"""
    ingredients = CreateRecipeIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'image', 'ingredients',
            'tags', 'cooking_time', 'author'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        if ingredients is None:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент'
            )
        ingredients_list = []
        for ingredient in ingredients:
            name = ingredient['id']
            if name in ingredients_list:
                raise serializers.ValidationError(f'{name} уже добавлен')
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'В рецепте должен быть хотя бы 1 ингредиент'
                )
            ingredients_list.append(name)
        tags = data['tags']
        if tags is None:
            raise serializers.ValidationError('Добавьте хотя бы один тег')
        cooking_time = data['cooking_time']
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                'Минимальное время приготовления - 1 минута'
            )
        return data

    def add_tag(self, tags, recipe):
        tags_list = []
        for tag in tags:
            current_tag = RecipeTags(tag=tag, recipe=recipe)
            tags_list.append(current_tag)
        RecipeTags.objects.bulk_create(tags_list)

    def add_ingredient(self, ingredients, recipe):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = RecipeIngredients(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            ingredients_list.append(current_ingredient)
        RecipeIngredients.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.add_tag(tags, recipe)
        self.add_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        updated_tags = validated_data.pop('tags')
        instance.tags.clear()
        self.add_tag(updated_tags, instance)
        updated_ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.add_ingredient(updated_ingredients, instance)
        instance.save()
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткая форма рецепта"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserRecipesSerializer(serializers.ModelSerializer):
    """Автор с рецептами"""
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_queryset(self):
        return super().get_queryset().annotate(recipes_count=Count('recipes'))

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit is not None:
            queryset = Recipe.objects.filter(author=obj.author)[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

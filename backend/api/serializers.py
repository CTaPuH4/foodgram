import re

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MaxLengthValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.constants import NAME_MAX_LENGTH
from recipes.constants import MAX_VALUE, MIN_VALUE
from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag
from users.models import CustomUser


class IsSubscribedMixin(serializers.Serializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj in user.subs.all()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.SlugField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CustomUserSerializer(serializers.ModelSerializer, IsSubscribedMixin):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all()),
            MaxLengthValidator(
                NAME_MAX_LENGTH,
                f'Длина не должна превышать {NAME_MAX_LENGTH}')]
    )
    first_name = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(
                NAME_MAX_LENGTH,
                f'Длина не должна превышать {NAME_MAX_LENGTH}')]
    )
    last_name = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(
                NAME_MAX_LENGTH,
                f'Длина не должна превышать {NAME_MAX_LENGTH}')]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=(validate_password,)
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'avatar',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if (request and request.method == 'POST'):
            self.fields.pop('avatar', None)
            self.fields.pop('is_subscribed', None)

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            avatar=validated_data.get('avatar', None),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError('Неверное имя пользователя.')
        return value


class SubscriptionSerializer(serializers.Serializer):

    def validate(self, data):
        user = self.context['request'].user
        sub = self.context['view'].get_object()

        if self.context['request'].method == 'POST':
            if user.pk == sub.pk:
                raise serializers.ValidationError(
                    {'detail': 'Вы не можете подписаться на себя самого.'}
                )
            if user.subs.filter(pk=sub.pk).exists():
                raise serializers.ValidationError(
                    {'detail': 'Вы уже подписаны на данного пользователя.'}
                )

        elif self.context['request'].method == 'DELETE':
            if not user.subs.filter(pk=sub.pk).exists():
                raise serializers.ValidationError(
                    {'detail': 'Вы не подписаны на данного пользователя.'}
                )

        return data

    def save(self):
        user = self.context['request'].user
        sub = self.context['view'].get_object()

        if self.context['request'].method == 'POST':
            user.subs.add(sub)
            return sub

        elif self.context['request'].method == 'DELETE':
            user.subs.remove(sub)
            return None


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False
    )
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='recipeingredients',
        required=True,
        allow_empty=False
    )
    image = Base64ImageField(
        required=True,
    )
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, data):
        ingredient_ids = [
            ingredient['ingredient'].id for ingredient in data
        ]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться.'
            )
        return data

    def validate_tags(self, data):
        if len(data) != len(set(data)):
            raise serializers.ValidationError(
                'Теги не могут повторяться.'
            )
        return data

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError('Поле не может быть пустым.')
        return value

    def validate(self, attrs):
        request_method = self.context['request'].method
        if request_method == 'PATCH':
            if not attrs.get('tags'):
                raise serializers.ValidationError({
                    'tags': 'Это поле обязательно для заполнения.'
                })
            if not attrs.get('recipeingredients'):
                raise serializers.ValidationError({
                    'ingredients': 'Это поле обязательно для заполнения.'
                })
        return super().validate(attrs)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        recipe.tags.set(tags_data)
        recipe_ingredients = [
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient_obj['ingredient'],
                amount=ingredient_obj['amount']
            )
            for ingredient_obj in ingredients_data
        ]

        RecipeIngredients.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        ingredients_data = validated_data.pop('recipeingredients')
        recipe_ingredients = [
            RecipeIngredients(
                recipe=instance,
                ingredient=ingredient_obj['ingredient'],
                amount=ingredient_obj['amount']
            )
            for ingredient_obj in ingredients_data
        ]
        RecipeIngredients.objects.bulk_create(recipe_ingredients)

        instance.tags.clear()
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        user = self.context('request').user
        if user.is_authenticated:
            return user.fav.filter(id=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context('request').user
        if user.is_authenticated:
            return user.cart.filter(id=obj.id).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags, many=True).data
        return representation


class RelatedRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserRecipesSerializer(serializers.ModelSerializer,
                                  IsSubscribedMixin):
    recipes = RelatedRecipeSerializer(many=True)
    recipes_count = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                representation['recipes'] = (
                    representation['recipes'][:recipes_limit]
                )
            except ValueError:
                pass
        return representation


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=(validate_password,)
    )
    current_password = serializers.CharField(write_only=True, required=True,)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный пароль.')
        return value

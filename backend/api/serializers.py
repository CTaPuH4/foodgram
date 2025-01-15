from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag
from users.serializers import CustomUserSerializer


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
        for ingredient_obj in ingredients_data:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj['ingredient'],
                amount=ingredient_obj['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        ingredients_data = validated_data.pop('recipeingredients')
        for ingredient_obj in ingredients_data:
            RecipeIngredients.objects.create(
                recipe=instance,
                ingredient=ingredient_obj['ingredient'],
                amount=ingredient_obj['amount']
            )

        instance.tags.clear()
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.fav.filter(id=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.cart.filter(id=obj.id).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags, many=True).data
        return representation

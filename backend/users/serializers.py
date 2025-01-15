import re

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MaxLengthValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.constants import NAME_MAX_LENGTH
from recipes.models import Recipe
from users.mixins import IsSubscribedMixin
from users.models import CustomUser


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

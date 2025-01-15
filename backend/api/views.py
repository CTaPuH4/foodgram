from collections import defaultdict

from rest_framework import mixins, permissions, viewsets
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filtersets import RecipeFilterSet
from api.mixins import RecipeActionMixin
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             TagSerializer)
from recipes.models import Ingredient, Recipe, Tag
from users.permissions import AuthorOrAdmin


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet, RecipeActionMixin):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet
    permission_classes = (AuthorOrAdmin,
                          permissions.IsAuthenticatedOrReadOnly)

    def update(self, request, *args, **kwargs):
        if request.method == 'PUT':
            raise MethodNotAllowed(method='PUT')
        return super().update(request, *args, **kwargs)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='favorite')
    def fav_add(self, request, pk=None):
        recipe = self.get_object()
        return self.related_field_add(
            user=request.user,
            related_field='fav',
            recipe=recipe
        )

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='shopping_cart')
    def cart_add(self, request, pk=None):
        recipe = self.get_object()
        return self.related_field_add(
            user=request.user,
            related_field='cart',
            recipe=recipe
        )

    @action(detail=True,
            methods=['get'],
            permission_classes=[],
            url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        url = reverse('recipes-detail', kwargs={'pk': recipe.pk})
        short_link = request.build_absolute_uri(url)
        return Response({"short-link": short_link})

    @action(detail=False,
            methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user

        ingredients_dict = defaultdict(int)
        ingredients_units = {}

        for recipe in user.cart.all():
            for recipe_ingredient in recipe.recipeingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                ingredient_amount = recipe_ingredient.amount
                ingredient_unit = recipe_ingredient.ingredient.measurement_unit

                ingredients_dict[ingredient_name] += ingredient_amount
                if ingredient_name not in ingredients_units:
                    ingredients_units[ingredient_name] = ingredient_unit

        shopping_list = []
        for ingredient, amount in ingredients_dict.items():
            unit = ingredients_units.get(ingredient)
            shopping_list.append(f"{ingredient} ({unit}) — {amount} {unit}")

        shopping_list_text = "\n".join(shopping_list)

        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="list.txt"'
        return response

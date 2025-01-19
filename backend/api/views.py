from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filtersets import RecipeFilterSet
from api.mixins import RecipeActionMixin
from api.paginators import CustomPagination
from api.permissions import AuthorOrAdmin
from api.serializers import (AvatarUpdateSerializer, ChangePasswordSerializer,
                             CustomUserRecipesSerializer, CustomUserSerializer,
                             IngredientSerializer, RecipeSerializer,
                             SubscriptionSerializer, TagSerializer)
from recipes.models import Ingredient, Recipe, Tag
from users.models import CustomUser


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
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self.fav_add(
            user=request.user,
            recipe=recipe
        )

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self.cart_add(
            user=request.user,
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
        return Response({'short-link': short_link})

    @action(detail=False,
            methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = (
            user.cart.all()
            .prefetch_related('recipeingredients__ingredient')
            .values(
                ingredient_name=F('recipeingredients__ingredient__name'),
                measurement_unit=F(
                    'recipeingredients__ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('recipeingredients__amount'))
            .order_by('ingredient_name')
        )

        shopping_list = [
            f"{ingredient['ingredient_name']} "
            f"({ingredient['measurement_unit']}) — "
            f"{ingredient['total_amount']} {ingredient['measurement_unit']}"
            for ingredient in ingredients
        ]
        shopping_list_text = '\n'.join(shopping_list)

        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="list.txt"'
        return response


class CustomUserViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = []

    @action(detail=False,
            methods=('get',),
            permission_classes=[permissions.IsAuthenticated],
            url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False,
            methods=('put', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='me/avatar')
    def update_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(
                instance=user,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='subscribe')
    def subs_add(self, request, pk=None):
        serializer = SubscriptionSerializer(
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            subscription = serializer.save()
            subscription_data = CustomUser.objects.annotate(
                recipes_count=Count('recipes')
            ).get(pk=subscription.pk)
            response_serializer = CustomUserRecipesSerializer(
                subscription_data,
                context={'request': request}
            )
            return Response(
                response_serializer.data, status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',),
            permission_classes=[permissions.IsAuthenticated],
            url_path='subscriptions')
    def subs_list(self, request):
        user = request.user
        subscriptions = user.subs.annotate(recipes_count=Count('recipes'))

        paginator = CustomPagination()
        paginated_data = paginator.paginate_queryset(subscriptions, request)

        serializer = CustomUserRecipesSerializer(
            paginated_data,
            many=True,
            context={'request': self.request}
        )
        return paginator.get_paginated_response(serializer.data)


class ChangePasswordViewSet(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

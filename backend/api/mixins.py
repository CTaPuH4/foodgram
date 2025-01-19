from rest_framework import status
from rest_framework.response import Response

from api.serializers import RelatedRecipeSerializer


class RecipeActionMixin:
    def add_cart(self, user, recipe):
        if self.request.method == 'POST':
            if user.cart.filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': 'Этот рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.cart.add(recipe)
            serializer = RelatedRecipeSerializer(
                recipe,
                context={'request': self.request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == 'DELETE':
            if not user.cart.filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': 'Этого рецепта нет в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.cart.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def add_favorite(self, user, recipe):
        if self.request.method == 'POST':
            if user.fav.filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': 'Этот рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.fav.add(recipe)
            serializer = RelatedRecipeSerializer(
                recipe,
                context={'request': self.request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == 'DELETE':
            if not user.fav.filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': 'Этого рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.fav.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

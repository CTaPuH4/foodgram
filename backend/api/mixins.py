from rest_framework.response import Response
from rest_framework import status

from users.serializers import RelatedRecipeSerializer


class RecipeActionMixin:
    def related_field_add(self, user, related_field, recipe):
        """Обрабатывает добавление/удаление рецепта для поля (cart или fav)."""
        if self.request.method == 'POST':
            if getattr(user, related_field).filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': f'Этот рецепт уже в {related_field}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            getattr(user, related_field).add(recipe)
            serializer = RelatedRecipeSerializer(
                recipe,
                context={'request': self.request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == 'DELETE':
            if not getattr(user, related_field).filter(pk=recipe.pk).exists():
                return Response(
                    {'detail': f'Этого рецепта нет в {related_field}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            getattr(user, related_field).remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

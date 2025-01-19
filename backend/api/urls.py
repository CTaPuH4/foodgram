from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (ChangePasswordViewSet, CustomUserViewSet,
                       IngredientViewSet, RecipeViewSet, TagViewSet)

v1_router = DefaultRouter()
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('recipes', RecipeViewSet, basename='recipes')

v1_router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/set_password/',
         ChangePasswordViewSet.as_view(),
         name='change_password'),
    path('', include(v1_router.urls)),
]

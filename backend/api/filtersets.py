from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilterSet(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.CharFilter(
        method='filter_by_tags'
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(fav_by=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_cart_of=user)
        return queryset

    def filter_by_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')
        return queryset.filter(tags__slug__in=tags).distinct()

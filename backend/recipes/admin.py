from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 0
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    list_editable = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
    )
    list_editable = (
        'name',
        'author',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeIngredientsInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'slug',
        'name'
    )
    list_editable = ('name',)
    search_fields = ('name',)

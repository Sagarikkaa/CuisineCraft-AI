from django.contrib import admin
from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'cuisine', 'ingredients', 'created_at')
    list_filter = ('cuisine', 'created_at')
    search_fields = ('ingredients', 'cuisine', 'recipe_body')
    readonly_fields = ('created_at',)

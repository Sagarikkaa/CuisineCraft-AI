"""
The Archivist Agent — Database & State Management
Manages the lifecycle of recipe data via Django ORM + SQLite
"""
from django.db import models


class Recipe(models.Model):
    """Model storing user input and all agent outputs."""
    ingredients = models.TextField(help_text="Comma-separated list of ingredients from the user")
    cuisine = models.CharField(max_length=100, help_text="Cuisine preference, e.g. Italian, Indian")
    recipe_body = models.TextField(blank=True, default='', help_text="Markdown recipe from the Sous-Chef agent")
    nutrition_summary = models.TextField(blank=True, default='', help_text="Nutritional analysis from the Nutritionist agent")
    audio_blob_path = models.CharField(max_length=255, blank=True, default='', help_text="Path to audio file from the Narrator agent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Recipe #{self.pk} — {self.cuisine} ({self.created_at:%Y-%m-%d %H:%M})"

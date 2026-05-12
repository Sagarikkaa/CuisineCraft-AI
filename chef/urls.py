"""
URL routing for the chef app.
"""
from django.urls import path
from . import views

app_name = 'chef'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/generate-recipe/', views.generate_recipe, name='generate-recipe'),
    path('api/analyze-nutrition/', views.analyze_nutrition, name='analyze-nutrition'),
    path('api/recipes/', views.recipe_history, name='recipe-history'),
]

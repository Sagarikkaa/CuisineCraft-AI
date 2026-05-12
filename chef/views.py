"""
Views — API endpoints and page rendering for the Culinary Assistant.

POST /api/generate-recipe/   → triggers Sous-Chef agent
POST /api/analyze-nutrition/  → triggers Nutritionist + Narrator agents
GET  /                        → serves the dashboard
GET  /api/recipes/            → returns saved recipe history
"""
import json
import os
import uuid
import traceback

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import Recipe
from .agents import sous_chef_generate, nutritionist_analyze, narrator_synthesize, pcm_to_wav


def dashboard(request):
    """Render the single-page dashboard."""
    return render(request, 'dashboard.html')


@csrf_exempt
@require_POST
def generate_recipe(request):
    """
    Endpoint: POST /api/generate-recipe/
    Triggers the Sous-Chef agent and the Archivist (saves to DB).
    Returns the recipe body and the new recipe ID.
    """
    try:
        data = json.loads(request.body)
        ingredients = data.get('ingredients', '').strip()
        cuisine = data.get('cuisine', '').strip()

        if not ingredients or not cuisine:
            return JsonResponse({'error': 'Both ingredients and cuisine are required.'}, status=400)

        # ── Agent 1: Sous-Chef ──
        recipe_body = sous_chef_generate(ingredients, cuisine)

        # ── Agent 4: Archivist (save) ──
        recipe = Recipe.objects.create(
            ingredients=ingredients,
            cuisine=cuisine,
            recipe_body=recipe_body,
        )

        return JsonResponse({
            'id': recipe.pk,
            'recipe_body': recipe.recipe_body,
            'created_at': recipe.created_at.isoformat(),
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def analyze_nutrition(request):
    """
    Endpoint: POST /api/analyze-nutrition/
    Triggers the Nutritionist agent, then the Narrator agent sequentially.
    Updates the existing Recipe record via the Archivist.
    """
    try:
        data = json.loads(request.body)
        recipe_id = data.get('id')

        if not recipe_id:
            return JsonResponse({'error': 'Recipe ID is required.'}, status=400)

        recipe = Recipe.objects.get(pk=recipe_id)

        # ── Agent 2: Nutritionist ──
        nutrition_summary = nutritionist_analyze(recipe.recipe_body, recipe.ingredients)
        recipe.nutrition_summary = nutrition_summary

        # ── Agent 3: Narrator ──
        # Create a concise narration text from the nutrition summary
        narration_text = f"Here is the nutritional analysis for your {recipe.cuisine} recipe. {nutrition_summary}"

        pcm_data = narrator_synthesize(narration_text)

        # Wrap PCM in WAV header and save to media/
        wav_data = pcm_to_wav(pcm_data)
        os.makedirs(settings.MEDIA_ROOT / 'audio', exist_ok=True)
        filename = f"audio/nutrition_{recipe.pk}_{uuid.uuid4().hex[:8]}.wav"
        filepath = settings.MEDIA_ROOT / filename
        with open(filepath, 'wb') as f:
            f.write(wav_data)

        recipe.audio_blob_path = filename
        recipe.save()

        return JsonResponse({
            'id': recipe.pk,
            'nutrition_summary': recipe.nutrition_summary,
            'audio_url': f'{settings.MEDIA_URL}{filename}',
        })

    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found.'}, status=404)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def recipe_history(request):
    """Return the latest 20 saved recipes."""
    recipes = Recipe.objects.all()[:20]
    data = []
    for r in recipes:
        data.append({
            'id': r.pk,
            'ingredients': r.ingredients,
            'cuisine': r.cuisine,
            'recipe_body': r.recipe_body,
            'nutrition_summary': r.nutrition_summary,
            'audio_url': f'{settings.MEDIA_URL}{r.audio_blob_path}' if r.audio_blob_path else '',
            'created_at': r.created_at.isoformat(),
        })
    return JsonResponse({'recipes': data})

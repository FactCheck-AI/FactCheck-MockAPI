import json

from urllib.parse import unquote
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from .models import APIKey, Dataset, Fact, SerpContent, Link
from .utils import validate_api_key, load_mock_data


def index(request):
    """Main page for API key generation"""
    return render(request, 'mockapi/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_api_key(request):
    """Create new API key for user"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        key_name = data.get('key_name', 'Default Key')

        if not username or not email:
            return JsonResponse({
                'error': 'Username and email are required'
            }, status=400)

        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )

        # Create API key
        api_key = APIKey.objects.create(
            user=user,
            name=key_name
        )

        print(f"API key created: {api_key.key} for user {user.username}")

        return JsonResponse({
            'success': True,
            'api_key': api_key.key,
            'message': 'API key created successfully!'
        })

    except Exception as e:
        print(e)
        return JsonResponse({
            'error': f'Error creating API key: {str(e)}'
        }, status=500)

@csrf_exempt
def api_datasets(request):
    """List all available datasets"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    datasets = Dataset.objects.filter(is_active=True).values(
        'name', 'description', 'created_at'
    )

    return JsonResponse({
        'datasets': list(datasets),
        'count': len(datasets)
    })

@csrf_exempt
def api_dataset_facts(request, dataset_name):
    """List all facts in a dataset"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    dataset = get_object_or_404(Dataset, name=dataset_name, is_active=True)
    facts = dataset.facts.all().values('fact_id', 'created_at')

    return JsonResponse({
        'dataset': dataset_name,
        'facts': list(facts),
        'count': len(facts)
    })


@csrf_exempt
def api_serp_content(request, url):
    """Get SERP content for a specific URL with path parameter"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    try:
        # The URL comes already decoded from Django's URL resolver
        decoded_url = unquote(url) if url != unquote(url) else url

        if not decoded_url.endswith('/'):
            decoded_url += '/'

        # Find the link and its content
        try:
            link = Link.objects.get(url=decoded_url, is_active=True)
            serp_content = link.serp_content
        except Link.DoesNotExist:
            # Try with the original URL (sometimes encoding issues)
            try:
                link = Link.objects.get(url=url, is_active=True)
                serp_content = link.serp_content
                decoded_url = url
            except Link.DoesNotExist:
                return JsonResponse({
                    'error': 'URL not found',
                    'url_tried': [decoded_url, url],
                    'suggestion': 'Use query parameter method: /api/serp-content/?url=YOUR_URL'
                }, status=404)
        except SerpContent.DoesNotExist:
            return JsonResponse({
                'error': 'SERP content not available for this URL',
                'url': decoded_url
            }, status=404)

        # Get selected fields from query parameters
        fields_param = request.GET.get('fields')
        if fields_param:
            selected_fields = [f.strip() for f in fields_param.split(',') if f.strip()]
        else:
            selected_fields = None

        # Get content data
        content_data = serp_content.get_selected_fields(selected_fields)

        # Update API key usage
        api_key.usage_count += 1
        api_key.last_used = timezone.now()
        api_key.save()

        # Update link scrape count
        link.scrape_count += 1
        link.last_scraped = timezone.now()
        link.save()

        return JsonResponse({
            'success': True,
            'url': decoded_url,
            'fields_requested': selected_fields,
            'scraped_at': serp_content.scraped_at.isoformat(),
            'data': content_data
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}',
            'url': url
        }, status=500)

@csrf_exempt
def api_serp_content_query(request):
    """Get SERP content using query parameter (RECOMMENDED METHOD)"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    url = request.GET.get('url')
    if not url:
        return JsonResponse({
            'error': 'URL parameter is required',
            'usage': 'GET /api/serp-content/?url=https://example.com'
        }, status=400)

    try:
        # Find the link and its content
        try:
            link = Link.objects.get(url=url, is_active=True)
            serp_content = link.serp_content
        except Link.DoesNotExist:
            return JsonResponse({
                'error': 'URL not found',
                'url': url
            }, status=404)
        except SerpContent.DoesNotExist:
            return JsonResponse({
                'error': 'SERP content not available for this URL',
                'url': url
            }, status=404)

        # Get selected fields from query parameters
        fields_param = request.GET.get('fields')
        if fields_param:
            selected_fields = [f.strip() for f in fields_param.split(',') if f.strip()]
        else:
            selected_fields = None

        # Get content data
        content_data = serp_content.get_selected_fields(selected_fields)

        # Update API key usage
        api_key.usage_count += 1
        api_key.last_used = timezone.now()
        api_key.save()

        # Update link scrape count
        link.scrape_count += 1
        link.last_scraped = timezone.now()
        link.save()

        return JsonResponse({
            'success': True,
            'url': url,
            'fields_requested': selected_fields,
            'scraped_at': serp_content.scraped_at.isoformat(),
            'data': content_data
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}',
            'url': url
        }, status=500)

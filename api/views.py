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
from .models import APIKey, Dataset, Fact, SerpContent, Link, Question, HtmlContent
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

@csrf_exempt
def api_fact_questions(request, dataset_name, fact_id):
    """Get all fetchable questions for a specific fact, sorted by score with fetch_id"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    # Get dataset and fact
    dataset = get_object_or_404(Dataset, name=dataset_name, is_active=True)
    fact = get_object_or_404(Fact, dataset=dataset, fact_id=fact_id)

    # Get all fetchable questions ordered by score (highest first)
    questions = Question.objects.filter(
        fact=fact,
    ).order_by('-score')

    # Build response with synthetic fetch_id
    questions_data = []
    for index, question in enumerate(questions):
        questions_data.append({
            'fetch_id': index,  # Synthetic ID based on ranking
            'text': question.text,
            'score': question.score,
            'is_fetchable': question.is_fetchable
        })

    # Update API key usage
    api_key.usage_count += 1
    api_key.last_used = timezone.now()
    api_key.save()

    return JsonResponse({
        'success': True,
        'dataset': dataset_name,
        'fact_id': fact_id,
        'questions': questions_data,
        'count': len(questions_data)
    })

@csrf_exempt
def api_fact_question_page(request, dataset_name, fact_id, question_rank):
    """Get HTML content and available URLs for a specific question by rank"""
    api_key = validate_api_key(request)
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    try:
        # Get dataset and fact
        dataset = get_object_or_404(Dataset, name=dataset_name, is_active=True)
        fact = get_object_or_404(Fact, dataset=dataset, fact_id=fact_id)

        # Get all fetchable questions ordered by score (highest first)
        questions = Question.objects.filter(
            fact=fact,
            is_fetchable=True
        ).order_by('-score')

        # Check if question_rank is valid
        if question_rank >= len(questions) or question_rank < 0:
            return JsonResponse({
                'error': f'Question rank {question_rank} not found. Available ranks: 0-{len(questions)-1}'
            }, status=404)

        # Get the question at the specified rank
        question = questions[question_rank]

        # Get HTML content for this question
        try:
            html_content = question.html_content
        except HtmlContent.DoesNotExist:
            return JsonResponse({
                'error': f'No HTML content available for question at rank {question_rank}'
            }, status=404)

        # Get all available URLs for this HTML content
        available_urls = []
        html_content_urls = html_content.htmlcontenturl_set.select_related('link').filter(
            link__is_active=True
        ).order_by('rank')

        for html_url in html_content_urls:
            link = html_url.link
            url_data = {
                'url': link.url,
                'domain': link.domain,
                'title': link.title,
                'description': link.description,
                'rank': html_url.rank,
                'scrape_count': link.scrape_count,
                'last_scraped': link.last_scraped.isoformat() if link.last_scraped else None,
                'has_serp_content': hasattr(link, 'serp_content')
            }
            available_urls.append(url_data)

        # Update API key usage
        api_key.usage_count += 1
        api_key.last_used = timezone.now()
        api_key.save()

        return JsonResponse({
            'success': True,
            'dataset': dataset_name,
            'fact_id': fact_id,
            'question_rank': question_rank,
            'question': {
                'text': question.text,
                'score': question.score,
                'is_fetchable': question.is_fetchable
            },
            'html_content': {
                'content': html_content.content
            },
            'available_urls': available_urls,
            'total_urls': len(available_urls)
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)

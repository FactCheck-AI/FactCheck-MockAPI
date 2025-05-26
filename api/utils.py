from django.utils import timezone
from .models import APIKey

def validate_api_key(request):
    """Validate API key from request headers"""
    api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')

    if not api_key:
        return None

    try:
        key_obj = APIKey.objects.get(key=api_key, is_active=True)
        return key_obj
    except APIKey.DoesNotExist:
        return None

def load_mock_data():
    """Load mock data from filesystem into database"""
    from django.conf import settings
    from .models import Dataset, Fact, File
    import os
    import json

    mock_data_dir = settings.MOCK_DATA_DIR
    if not os.path.exists(mock_data_dir):
        print(f"Mock data directory {mock_data_dir} does not exist")
        return

    for dataset_name in os.listdir(mock_data_dir):
        dataset_path = os.path.join(mock_data_dir, dataset_name)
        if not os.path.isdir(dataset_path):
            continue

        # Create or get dataset
        dataset, created = Dataset.objects.get_or_create(
            name=dataset_name,
            defaults={'description': f'Mock dataset: {dataset_name}'}
        )

        for fact_id in os.listdir(dataset_path):
            fact_path = os.path.join(dataset_path, fact_id)
            if not os.path.isdir(fact_path):
                continue

            # Create or get fact
            fact, created = Fact.objects.get_or_create(
                dataset=dataset,
                fact_id=fact_id
            )

            # Load files
            for filename in os.listdir(fact_path):
                file_path = os.path.join(fact_path, filename)
                if os.path.isfile(file_path):

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Determine file type
                    if filename.endswith('.html'):
                        file_type = 'html'
                    elif filename.endswith('.json'):
                        file_type = 'json'
                        # If it's questions.json, update fact's questions_data
                        if filename == 'questions.json':
                            try:
                                fact.questions_data = json.loads(content)
                                fact.save()
                            except json.JSONDecodeError:
                                pass
                    else:
                        file_type = 'text'

                    # Create or update file
                    File.objects.update_or_create(
                        fact=fact,
                        filename=filename,
                        defaults={
                            'file_type': file_type,
                            'content': content
                        }
                    )

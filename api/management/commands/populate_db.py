# api/management/commands/populate_db.py
import json
import os
import random
import re
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from api.models import (
    APIKey, Dataset, Fact, Question, Link, SerpContent,
    HtmlContent, HtmlContentUrl
)

DATASET_NAME_MAP = {
    'yago': 'YAGO',
    'dbpedia': 'DBpedia',
    'factbench': 'FactBench'
}


def load_dataset(dataset_name: str = "FactBench", dataset_file: str = "kg.json"):
    print('Load {} dataset.'.format(dataset_name))
    # get target dataset
    with open('/Users/farzad/Documents/Thesis/Project/dataset/' + dataset_name + f'/data/{dataset_file}', 'r') as f:
        id2triple = json.load(f)

    # set KG as [(id, triple), ...]
    kg = [(k, v) for k, v in id2triple.items()]

    if dataset_name in ["FactBench"]:
        kg = [(k, v[0]) for k, v in id2triple.items()]
        kg = [p for p in kg if
              'correct_' in p[0] or
              'wrong_mix_domain' in p[0] or
              'wrong_mix_range' in p[0] or
              'wrong_mix_domainrange' in p[0] or
              'wrong_mix_property' in p[0] or
              'wrong_mix_random' in p[0]]

    return kg

def parse_publish_date(date_value):
    """
    Parse and convert publish_date to timezone-aware datetime.
    Handles various date formats and ensures timezone awareness.
    """
    if not date_value:
        return None

    # If it's already a datetime object
    if isinstance(date_value, datetime):
        # Check if it's naive (no timezone info)
        if timezone.is_naive(date_value):
            # Make it timezone-aware using the default timezone
            return timezone.make_aware(date_value)
        return date_value

    # If it's a string, try to parse it
    if isinstance(date_value, str):
        # Try parsing with Django's parse_datetime first
        parsed_date = parse_datetime(date_value)
        if parsed_date:
            if timezone.is_naive(parsed_date):
                return timezone.make_aware(parsed_date)
            return parsed_date

        # If that fails, try some common formats
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_value, fmt)
                return timezone.make_aware(parsed_date)
            except ValueError:
                continue

    # If all parsing attempts fail, return None
    return None

def load_questions(dataset_name: str, fact:str):
    """Load questions for a given dataset and fact"""
    fact_id = fact if dataset_name == 'factbench' else f'{dataset_name.lower()}_{fact}'
    try:
        with open(f'/Users/farzad/Documents/Thesis/Project/docs/{fact_id}/questions.json', 'r') as f:
            questions_data = json.load(f)['questions']

        # sort questions by score in descending order and for top three questions add is_fetchable=True
        questions_data = sorted(questions_data, key=lambda x: x['score'], reverse=True)
        for i, question in enumerate(questions_data):
            if i < 3:
                question['is_fetchable'] = True
            else:
                question['is_fetchable'] = False

        return questions_data
    except FileNotFoundError:
        print(f"Questions file for {fact_id} not found. Returning empty list.")
        return {}

class Command(BaseCommand):
    help = 'Populate database with fake sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Creating sample data...')

        # Create sample users and API keys
        users = self.create_users()

        # Create datasets
        datasets = self.create_datasets()
        print(f'Datasets created: {[dataset.name for dataset in datasets]}')

        # # Create facts for each dataset
        all_facts = []
        for dataset in datasets:
            facts = self.create_facts(dataset)
            all_facts.extend(facts)
        print(f'Facts created: {len(all_facts)}')

        # # Create questions for each fact
        all_questions = []
        for fact in all_facts:
            questions = self.create_questions(fact)
            all_questions.extend(questions)
        print(f'Questions created: {len(all_questions)}')

        for dataset in datasets:
            self.create_questions_main_query(dataset)

        # # Create links and SERP content
        self.create_links_and_serp_content()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'- {len(users)} users with API keys\n'
                f'- {len(datasets)} datasets\n'
                f'- {len(all_facts)} facts\n'
                f'- {len(all_questions)} questions\n'
                f'- HTML content for fetchable questions'
            )
        )

    def clear_data(self):
        """Clear existing data"""
        HtmlContentUrl.objects.all().delete()
        HtmlContent.objects.all().delete()
        SerpContent.objects.all().delete()
        Link.objects.all().delete()
        Question.objects.all().delete()
        Fact.objects.all().delete()
        Dataset.objects.all().delete()
        APIKey.objects.all().delete()
        # Don't delete users as they might be system users

    def create_users(self):
        """Create sample users with API keys"""
        users_data = [
            {'username': 'IIIA', 'email': 'silvello@dei.unipd.it', 'key_name': 'IIIA HUB'},
        ]

        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']}
            )

            # Create API key
            api_key, created = APIKey.objects.get_or_create(
                user=user,
                name=user_data['key_name'],
                defaults={
                    'usage_count': random.randint(10, 100),
                    'last_used': timezone.now() - timedelta(days=random.randint(1, 30))
                }
            )

            users.append(user)

        return users

    def create_datasets(self):
        """Create sample datasets"""
        dataset_templates = [
            {
                'name': 'yago',
                'description': 'YAGO is a KG derived from Wikipedia, WordNet and GeoNames.'
            },
            {
                'name': 'dbpedia',
                'description': 'DBPedia is a KG derived from structured information extracted from Wikipedia.'
            },
            {
                'name': 'factbench',
                'description': 'FactBench is a benchmark designed to evaluate fact validation algorithms. It contains 10 different specific relations.'
            }
        ]

        datasets = []
        for template in dataset_templates:
            dataset, created = Dataset.objects.get_or_create(
                name=template['name'],
                defaults={
                    'description': template['description'],
                    'is_active': True
                }
            )
            datasets.append(dataset)

        return datasets

    def create_facts(self, dataset):
        """Create sample facts for a dataset"""
        kg = load_dataset(DATASET_NAME_MAP[dataset.name], dataset_file='kg.json' if dataset.name != 'DBpedia' else 'kg_modified.json')
        templates = [identifier for identifier, _ in kg]

        facts = []
        for i in range(len(templates)):
            fact_id = templates[i]

            fact, created = Fact.objects.get_or_create(
                dataset=dataset,
                fact_id=fact_id,
            )
            facts.append(fact)

        return facts

    def create_questions(self, fact):
        """Create sample questions for a fact"""
        questions = load_questions(fact.dataset.name, fact.fact_id)
        questions_created = []
        for qu in questions:
            question = Question.objects.create(
                fact=fact,
                text=qu['question'],
                score=qu['score'],
                is_fetchable=qu['is_fetchable']
            )
            questions_created.append(question)

        return questions_created

    def create_questions_main_query(self, dataset):
        kg = load_dataset(DATASET_NAME_MAP[dataset.name], dataset_file='kg.json' if dataset.name != 'DBpedia' else 'kg_modified.json')
        for identifier, knowledge_graph in kg:
            if dataset.name == 'yago':
                knowledge_graph = re.sub(r'(?<=[a-z])([A-Z])', r' \1', " ".join(knowledge_graph))
            fact = Fact.objects.get(dataset__name=dataset.name, fact_id=identifier)
            Question.objects.create(
                fact=fact,
                text=knowledge_graph,
                score=1.00,
                is_fetchable=True
            )

    def create_links_and_serp_content(self):
        """Create sample links with SERP content"""
        # walk on the folder
        # and get all the files that start with yago_ or dbpedia_ or factbench_
        for _, dirs, _ in os.walk('/Users/farzad/Documents/Thesis/Project/docs'):
            for dir in dirs:
                if dir.startswith(('yago_', 'dbpedia_', 'correct', 'wrong')):
                # if dir.startswith(('yago_',)):
                    print(f'Processing directory: {dir}')
                    for _, _, files in os.walk(f'/Users/farzad/Documents/Thesis/Project/docs/{dir}/all_docs'):
                        # sort files by name to ensure consistent processing order
                        files = sorted(files, key=lambda x: x.lower())

                        selected_links = []

                        for file in files:
                            if file.endswith('.json'):
                                try:
                                    with open(f'/Users/farzad/Documents/Thesis/Project/docs/{dir}/all_docs/{file}', 'r') as f:
                                        data = json.load(f)

                                    id = data.get('id', '')
                                    rank = data.get('rank', 0)
                                    data = data.get('data', {})

                                    link, created = Link.objects.get_or_create(
                                        url=data.get('url'),
                                        defaults={
                                            'title': data.get('title', ''),
                                            'description': data.get('meta_description', '')
                                        }
                                    )

                                    # Create or update SERP content
                                    SerpContent.objects.update_or_create(
                                        link=link,
                                        defaults={
                                            'url': data.get('url'),
                                            'read_more_link': data.get('read_more_link', ''),
                                            'language': data.get('language', 'en'),
                                            'title': data.get('title', ''),
                                            'text': data.get('text', ''),
                                            'summary': data.get('summary', ''),
                                            'top_image': data.get('top_image', ''),
                                            'meta_img': data.get('meta_img', ''),
                                            'images': data.get('images', []),
                                            'movies': data.get('movies', []),
                                            'keywords': data.get('keywords', []),
                                            'tags': data.get('tags'),
                                            'authors': data.get('authors', []),
                                            'meta_keywords': data.get('meta_keywords', []),
                                            'meta_description': data.get('meta_description', ''),
                                            'meta_lang': data.get('meta_lang', ''),
                                            'meta_favicon': data.get('meta_favicon', ''),
                                            'meta_site_name': data.get('meta_site_name', ''),
                                            'canonical_link': data.get('canonical_link', None),
                                            'publish_date': parse_publish_date(data.get('publish_date')),  # Fixed line,
                                        }
                                    )

                                    selected_links.append((id, rank, link))

                                except FileNotFoundError:
                                    print(f"File {file} not found in directory {dir}. Skipping.")
                                    continue

                                except json.JSONDecodeError:
                                    print(f"Error decoding JSON from file {file} in directory {dir}. Skipping.")
                                    continue

                                except Exception as e:
                                    print(f"An error occurred while processing file {file} in directory {dir}: {e}")
                                    continue

                        for file_id, rank, link in selected_links:
                            with open(f'/Users/farzad/Documents/Thesis/Project/data/google/{file_id}.html', 'r') as html_file:
                                content = html_file.read()

                            split_id = file_id.split('_')
                            dataset_name = split_id[0]
                            fact_id = '_'.join(split_id[:-1])

                            if fact_id.startswith(('yago_', 'dbpedia_')):
                                fact_id = fact_id.replace('yago_', '').replace('dbpedia_', '')

                            if fact_id.startswith(('correct_','wrong_')):
                                dataset_name = 'factbench'

                            questions = Question.objects.filter(
                                fact__dataset__name=dataset_name,
                                fact__fact_id=fact_id,
                                is_fetchable=True
                            ).order_by('-score')

                            question = questions[int(split_id[-1])]

                            html_content, _ = HtmlContent.objects.get_or_create(
                                question=question,
                                content=content
                            )

                            HtmlContentUrl.objects.get_or_create(
                                html_content=html_content,
                                link=link,
                                rank=rank
                            )

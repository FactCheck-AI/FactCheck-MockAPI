import uuid
from django.db import models
from django.contrib.auth.models import User

class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Dataset(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Fact(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='facts')
    fact_id = models.CharField(max_length=50)
    questions_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['dataset', 'fact_id']

    def __str__(self):
        return f"{self.dataset.name} - {self.fact_id}"


class Question(models.Model):
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    score = models.FloatField()

    def __str__(self):
        return f"{self.fact} - {self.text}"



class Link(models.Model):
    """Model to index and manage URLs"""
    url = models.URLField(max_length=2000, unique=True, db_index=True)
    domain = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['domain']),
            models.Index(fields=['is_active', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        if self.url:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            self.domain = parsed.netloc
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.domain} - {self.title or self.url[:50]}"


class HtmlContent(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='html_content')
    content = models.TextField()

    urls = models.ManyToManyField(
        Link,
        through='HtmlContentUrl',
        related_name='html_contents',
        blank=True
    )

    def get_available_urls(self):
        """Get all fetchable URLs for this HTML content"""
        return self.urls.filter(
            is_active=True
        )

    def add_url(self, url_string, rank=0):
        """Add a URL to this HTML content"""
        # Create or get Link
        link = Link.objects.get(url=url_string)

        # Create or update relationship
        html_content_url, created = HtmlContentUrl.objects.get_or_create(
            html_content=self,
            link=link,
            defaults={'rank': rank}
        )

        return html_content_url

    def __str__(self):
        return f"HTML Content for {self.question.text}"

class HtmlContentUrl(models.Model):
    """Through model to manage relationship between HtmlContent and URLs"""
    html_content = models.ForeignKey(HtmlContent, on_delete=models.CASCADE)
    link = models.ForeignKey(Link, on_delete=models.CASCADE)

    rank = models.IntegerField(default=0)  # Lower number = higher priority

    class Meta:
        indexes = [models.Index(fields=['link'])]

    def __str__(self):
        return f"{self.html_content.question.text[:30]} -> {self.link.url[:50]} | rank: {self.rank}"


class SerpContent(models.Model):
    """Model to store scraped web content data"""
    link = models.OneToOneField(Link, on_delete=models.CASCADE, related_name='serp_content')

    # Basic content fields
    url = models.URLField(max_length=2000)
    read_more_link = models.URLField(max_length=2000, blank=True)
    language = models.CharField(max_length=10, default='en')
    title = models.CharField(max_length=500, blank=True)
    text = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    # Image fields
    top_image = models.URLField(max_length=1000, blank=True)
    meta_img = models.URLField(max_length=1000, blank=True)
    images = models.JSONField(default=list, blank=True)  # Array of image URLs

    # Media and content arrays
    movies = models.JSONField(default=list, blank=True)  # Array of movie URLs
    keywords = models.JSONField(default=list, blank=True)  # Array of keywords
    tags = models.JSONField(default=list, blank=True, null=True)  # Array of tags
    authors = models.JSONField(default=list, blank=True)  # Array of authors

    # Meta fields
    meta_keywords = models.JSONField(default=list, blank=True)
    meta_description = models.TextField(blank=True)
    meta_lang = models.CharField(max_length=10, blank=True)
    meta_favicon = models.URLField(max_length=1000, blank=True)
    meta_site_name = models.CharField(max_length=255, blank=True)
    canonical_link = models.URLField(max_length=2000, blank=True)

    # Publishing info
    publish_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scraped_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['language']),
            models.Index(fields=['publish_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title or self.url} ({self.language})"

    def get_selected_fields(self, fields=None):
        """Get only selected fields from the content"""
        if not fields:
            # Return all fields if none specified
            return {
                'url': self.url,
                'read_more_link': self.read_more_link,
                'language': self.language,
                'title': self.title,
                'top_image': self.top_image,
                'meta_img': self.meta_img,
                'images': self.images,
                'movies': self.movies,
                'keywords': self.keywords,
                'meta_keywords': self.meta_keywords,
                'tags': self.tags,
                'authors': self.authors,
                'publish_date': self.publish_date.isoformat() if self.publish_date else None,
                'summary': self.summary,
                'meta_description': self.meta_description,
                'meta_lang': self.meta_lang,
                'meta_favicon': self.meta_favicon,
                'meta_site_name': self.meta_site_name,
                'canonical_link': self.canonical_link,
                'text': self.text,
            }

        # Return only requested fields
        result = {}
        field_mapping = {
            'url': self.url,
            'read_more_link': self.read_more_link,
            'language': self.language,
            'title': self.title,
            'top_image': self.top_image,
            'meta_img': self.meta_img,
            'images': self.images,
            'movies': self.movies,
            'keywords': self.keywords,
            'meta_keywords': self.meta_keywords,
            'tags': self.tags,
            'authors': self.authors,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'summary': self.summary,
            'meta_description': self.meta_description,
            'meta_lang': self.meta_lang,
            'meta_favicon': self.meta_favicon,
            'meta_site_name': self.meta_site_name,
            'canonical_link': self.canonical_link,
            'text': self.text,
        }

        for field in fields:
            if field in field_mapping:
                result[field] = field_mapping[field]

        return result

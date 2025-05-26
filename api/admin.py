from django.contrib import admin
from django.db import models
from django.db.models import Count, Avg, Max, Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    APIKey, Dataset, Fact, Question, Link, SerpContent,
    HtmlContent, HtmlContentUrl
)

# Custom admin site configuration
admin.site.site_header = "MockAPI Admin Dashboard"
admin.site.site_title = "MockAPI Admin"
admin.site.index_title = "Knowledge Graph Validation System"

# Inline classes
class APIKeyInline(admin.TabularInline):
    model = APIKey
    extra = 0
    readonly_fields = ('key', 'usage_count', 'last_used', 'created_at')
    fields = ('name', 'key', 'is_active', 'usage_count', 'last_used')

class FactInline(admin.TabularInline):
    model = Fact
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('fact_id', 'created_at')
    show_change_link = True

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'score', 'is_fetchable')
    readonly_fields = ('score',)
    show_change_link = True

class HtmlContentUrlInline(admin.TabularInline):
    model = HtmlContentUrl
    extra = 0
    fields = ('link', 'rank')
    readonly_fields = ('link',)
    autocomplete_fields = ['link']

class SerpContentInline(admin.StackedInline):
    model = SerpContent
    extra = 0
    readonly_fields = ('scraped_at', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('url', 'title', 'language')
        }),
        ('Content', {
            'fields': ('text', 'summary'),
            'classes': ('collapse',)
        }),
        ('Meta Data', {
            'fields': ('meta_description', 'meta_site_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('scraped_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Custom Admin Classes
@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'masked_key', 'is_active', 'usage_count', 'created_at', 'last_used', 'usage_status']
    list_filter = ['is_active', 'created_at', 'last_used']
    search_fields = ['user__username', 'user__email', 'name', 'key']
    readonly_fields = ['key', 'usage_count', 'last_used', 'created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name')
        }),
        ('API Key Details', {
            'fields': ('key', 'is_active')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    actions = ['activate_keys', 'deactivate_keys', 'reset_usage_count']

    def masked_key(self, obj):
        """Display masked API key for security"""
        if obj.key:
            return f"{obj.key[:8]}...{obj.key[-4:]}"
        return "No key"
    masked_key.short_description = "API Key"

    def usage_status(self, obj):
        """Color-coded usage status"""
        if obj.usage_count == 0:
            color = 'gray'
            status = 'Unused'
        elif obj.usage_count < 50:
            color = 'green'
            status = 'Low'
        elif obj.usage_count < 200:
            color = 'orange'
            status = 'Medium'
        else:
            color = 'red'
            status = 'High'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    usage_status.short_description = "Usage Level"

    def activate_keys(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} API keys activated.')
    activate_keys.short_description = "Activate selected API keys"

    def deactivate_keys(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} API keys deactivated.')
    deactivate_keys.short_description = "Deactivate selected API keys"

    def reset_usage_count(self, request, queryset):
        updated = queryset.update(usage_count=0, last_used=None)
        self.message_user(request, f'Usage count reset for {updated} API keys.')
    reset_usage_count.short_description = "Reset usage count"

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_preview', 'facts_count', 'questions_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'facts_count', 'questions_count']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Dataset Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Statistics', {
            'fields': ('facts_count', 'questions_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    inlines = [FactInline]
    actions = ['activate_datasets', 'deactivate_datasets']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            facts_count=Count('facts'),
            questions_count=Count('facts__questions')
        )

    def description_preview(self, obj):
        """Show truncated description"""
        if obj.description:
            return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
        return "No description"
    description_preview.short_description = "Description"

    def facts_count(self, obj):
        """Show number of facts"""
        return obj.facts_count
    facts_count.short_description = "Facts"
    facts_count.admin_order_field = 'facts_count'

    def questions_count(self, obj):
        """Show number of questions"""
        return obj.questions_count
    questions_count.short_description = "Questions"
    questions_count.admin_order_field = 'questions_count'

    def activate_datasets(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} datasets activated.')
    activate_datasets.short_description = "Activate selected datasets"

    def deactivate_datasets(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} datasets deactivated.')
    deactivate_datasets.short_description = "Deactivate selected datasets"

@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'fact_id', 'questions_count', 'fetchable_questions_count', 'avg_score', 'created_at']
    list_filter = ['dataset', 'created_at']
    search_fields = ['fact_id', 'dataset__name']
    readonly_fields = ['created_at', 'questions_count', 'fetchable_questions_count', 'avg_score']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Fact Information', {
            'fields': ('dataset', 'fact_id')
        }),
        ('Statistics', {
            'fields': ('questions_count', 'fetchable_questions_count', 'avg_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    inlines = [QuestionInline]
    actions = ['export_facts']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dataset').annotate(
            questions_count=Count('questions'),
            fetchable_questions_count=Count('questions', filter=Q(questions__is_fetchable=True)),
            avg_score=Avg('questions__score')
        )

    def questions_count(self, obj):
        return obj.questions_count
    questions_count.short_description = "Questions"
    questions_count.admin_order_field = 'questions_count'

    def fetchable_questions_count(self, obj):
        return obj.fetchable_questions_count
    fetchable_questions_count.short_description = "Fetchable"
    fetchable_questions_count.admin_order_field = 'fetchable_questions_count'

    def avg_score(self, obj):
        if obj.avg_score:
            return f"{obj.avg_score:.3f}"
        return "No scores"
    avg_score.short_description = "Avg Score"
    avg_score.admin_order_field = 'avg_score'

    def export_facts(self, request, queryset):
        # Implementation for exporting facts
        self.message_user(request, f'Exported {queryset.count()} facts.')
    export_facts.short_description = "Export selected facts"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['fact_dataset', 'fact_id', 'text_preview', 'score', 'is_fetchable', 'has_html_content']
    list_filter = ['is_fetchable', 'fact__dataset', 'score']
    search_fields = ['text', 'fact__fact_id', 'fact__dataset__name']
    readonly_fields = ['fact_dataset', 'has_html_content']
    list_per_page = 50

    fieldsets = (
        ('Question Information', {
            'fields': ('fact', 'text', 'score', 'is_fetchable')
        }),
        ('Related Data', {
            'fields': ('fact_dataset', 'has_html_content'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_fetchable', 'mark_not_fetchable']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fact__dataset')

    def fact_dataset(self, obj):
        return obj.fact.dataset.name
    fact_dataset.short_description = "Dataset"
    fact_dataset.admin_order_field = 'fact__dataset__name'

    def fact_id(self, obj):
        return obj.fact.fact_id
    fact_id.short_description = "Fact ID"
    fact_id.admin_order_field = 'fact__fact_id'

    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = "Question Text"

    def has_html_content(self, obj):
        try:
            return bool(obj.html_content)
        except HtmlContent.DoesNotExist:
            return False
    has_html_content.short_description = "HTML Content"
    has_html_content.boolean = True

    def mark_fetchable(self, request, queryset):
        updated = queryset.update(is_fetchable=True)
        self.message_user(request, f'{updated} questions marked as fetchable.')
    mark_fetchable.short_description = "Mark as fetchable"

    def mark_not_fetchable(self, request, queryset):
        updated = queryset.update(is_fetchable=False)
        self.message_user(request, f'{updated} questions marked as not fetchable.')
    mark_not_fetchable.short_description = "Mark as not fetchable"

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['domain', 'title_preview', 'url_preview', 'is_active', 'scrape_count', 'has_serp_content', 'last_scraped', 'created_at']
    list_filter = ['is_active', 'domain', 'created_at', 'last_scraped']
    search_fields = ['url', 'title', 'domain', 'description']
    readonly_fields = ['domain', 'scrape_count', 'last_scraped', 'created_at', 'updated_at', 'has_serp_content']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Link Information', {
            'fields': ('url', 'domain', 'title', 'description', 'is_active')
        }),
        ('Usage Statistics', {
            'fields': ('scrape_count', 'last_scraped'),
            'classes': ('collapse',)
        }),
        ('Related Content', {
            'fields': ('has_serp_content',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [SerpContentInline]
    actions = ['activate_links', 'deactivate_links', 'update_scrape_time']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('serp_content')

    def title_preview(self, obj):
        if obj.title:
            return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        return "No title"
    title_preview.short_description = "Title"

    def url_preview(self, obj):
        if obj.url:
            return obj.url[:60] + '...' if len(obj.url) > 60 else obj.url
        return "No URL"
    url_preview.short_description = "URL"

    def has_serp_content(self, obj):
        try:
            return bool(obj.serp_content)
        except SerpContent.DoesNotExist:
            return False
    has_serp_content.short_description = "SERP Content"
    has_serp_content.boolean = True

    def activate_links(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} links activated.')
    activate_links.short_description = "Activate selected links"

    def deactivate_links(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} links deactivated.')
    deactivate_links.short_description = "Deactivate selected links"

    def update_scrape_time(self, request, queryset):
        updated = queryset.update(last_scraped=timezone.now())
        self.message_user(request, f'Updated scrape time for {updated} links.')
    update_scrape_time.short_description = "Update scrape time"

@admin.register(SerpContent)
class SerpContentAdmin(admin.ModelAdmin):
    list_display = ['title_preview', 'url_preview', 'language', 'meta_site_name', 'publish_date', 'word_count', 'scraped_at']
    list_filter = ['language', 'meta_site_name', 'publish_date', 'scraped_at']
    search_fields = ['title', 'url', 'text', 'summary', 'meta_description']
    readonly_fields = ['scraped_at', 'created_at', 'updated_at', 'word_count', 'image_count']
    list_per_page = 50
    date_hierarchy = 'scraped_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('link', 'url', 'title', 'language', 'read_more_link')
        }),
        ('Content', {
            'fields': ('text', 'summary', 'word_count')
        }),
        ('Images', {
            'fields': ('top_image', 'meta_img', 'images', 'image_count'),
            'classes': ('collapse',)
        }),
        ('Media & Keywords', {
            'fields': ('movies', 'keywords', 'tags', 'authors'),
            'classes': ('collapse',)
        }),
        ('Meta Data', {
            'fields': ('meta_keywords', 'meta_description', 'meta_lang', 'meta_favicon', 'meta_site_name', 'canonical_link'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('publish_date',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('scraped_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['update_scrape_time', 'clear_content']

    def title_preview(self, obj):
        if obj.title:
            return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
        return "No title"
    title_preview.short_description = "Title"

    def url_preview(self, obj):
        if obj.url:
            return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
        return "No URL"
    url_preview.short_description = "URL"

    def word_count(self, obj):
        if obj.text:
            return len(obj.text.split())
        return 0
    word_count.short_description = "Words"

    def image_count(self, obj):
        if obj.images:
            return len(obj.images)
        return 0
    image_count.short_description = "Images"

    def update_scrape_time(self, request, queryset):
        updated = queryset.update(scraped_at=timezone.now())
        self.message_user(request, f'Updated scrape time for {updated} content items.')
    update_scrape_time.short_description = "Update scrape time"

    def clear_content(self, request, queryset):
        updated = queryset.update(text='', summary='')
        self.message_user(request, f'Cleared content for {updated} items.')
    clear_content.short_description = "Clear text content"

@admin.register(HtmlContent)
class HtmlContentAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'fact_info', 'dataset_name', 'urls_count', 'content_size']
    list_filter = ['question__fact__dataset', 'question__is_fetchable']
    search_fields = ['question__text', 'question__fact__fact_id', 'content']
    readonly_fields = ['question_preview', 'fact_info', 'dataset_name', 'urls_count', 'content_size']
    list_per_page = 50

    fieldsets = (
        ('Question Information', {
            'fields': ('question', 'question_preview', 'fact_info', 'dataset_name')
        }),
        ('HTML Content', {
            'fields': ('content', 'content_size')
        }),
        ('Related URLs', {
            'fields': ('urls_count',),
            'classes': ('collapse',)
        })
    )

    inlines = [HtmlContentUrlInline]
    actions = ['clear_html_content']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'question__fact__dataset'
        ).prefetch_related('urls')

    def question_preview(self, obj):
        return obj.question.text[:100] + '...' if len(obj.question.text) > 100 else obj.question.text
    question_preview.short_description = "Question"

    def fact_info(self, obj):
        return f"{obj.question.fact.fact_id}"
    fact_info.short_description = "Fact ID"

    def dataset_name(self, obj):
        return obj.question.fact.dataset.name
    dataset_name.short_description = "Dataset"

    def urls_count(self, obj):
        return obj.urls.count()
    urls_count.short_description = "URLs"

    def content_size(self, obj):
        if obj.content:
            size = len(obj.content)
            if size > 1024 * 1024:
                return f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size} bytes"
        return "No content"
    content_size.short_description = "Content Size"

    def clear_html_content(self, request, queryset):
        updated = queryset.update(content='')
        self.message_user(request, f'Cleared HTML content for {updated} items.')
    clear_html_content.short_description = "Clear HTML content"

@admin.register(HtmlContentUrl)
class HtmlContentUrlAdmin(admin.ModelAdmin):
    list_display = ['html_content_preview', 'link_preview', 'rank', 'link_domain', 'link_active']
    list_filter = ['rank', 'link__domain', 'link__is_active']
    search_fields = ['html_content__question__text', 'link__url', 'link__title']
    readonly_fields = ['link_domain', 'link_active']
    list_per_page = 50
    autocomplete_fields = ['html_content', 'link']

    fieldsets = (
        ('Relationship', {
            'fields': ('html_content', 'link', 'rank')
        }),
        ('Link Information', {
            'fields': ('link_domain', 'link_active'),
            'classes': ('collapse',)
        })
    )

    actions = ['update_ranks', 'activate_links']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'html_content__question',
            'link'
        )

    def html_content_preview(self, obj):
        return obj.html_content.question.text[:50] + '...' if len(obj.html_content.question.text) > 50 else obj.html_content.question.text
    html_content_preview.short_description = "HTML Content"

    def link_preview(self, obj):
        return obj.link.url[:60] + '...' if len(obj.link.url) > 60 else obj.link.url
    link_preview.short_description = "Link"

    def link_domain(self, obj):
        return obj.link.domain
    link_domain.short_description = "Domain"

    def link_active(self, obj):
        return obj.link.is_active
    link_active.short_description = "Active"
    link_active.boolean = True

    def update_ranks(self, request, queryset):
        # Implement logic to update ranks
        self.message_user(request, f'Updated ranks for {queryset.count()} items.')
    update_ranks.short_description = "Update ranks"

    def activate_links(self, request, queryset):
        link_ids = queryset.values_list('link_id', flat=True)
        updated = Link.objects.filter(id__in=link_ids).update(is_active=True)
        self.message_user(request, f'Activated {updated} links.')
    activate_links.short_description = "Activate associated links"
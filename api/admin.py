from django.contrib import admin
from .models import APIKey, Dataset, Fact, SerpContent, Link


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'key', 'is_active', 'usage_count', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'name', 'key']
    readonly_fields = ['key', 'usage_count', 'last_used']

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'fact_id', 'created_at']
    list_filter = ['dataset', 'created_at']
    search_fields = ['fact_id', 'dataset__name']



@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['url', 'domain', 'title', 'is_active', 'scrape_count', 'created_at', 'last_scraped']
    list_filter = ['is_active', 'domain', 'created_at']
    search_fields = ['url', 'title', 'domain', 'description']
    readonly_fields = ['domain', 'scrape_count', 'last_scraped']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('serp_content')

@admin.register(SerpContent)
class SerpContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'language', 'meta_site_name', 'publish_date', 'scraped_at']
    list_filter = ['language', 'meta_site_name', 'publish_date', 'scraped_at']
    search_fields = ['title', 'url', 'text', 'summary', 'meta_description']
    readonly_fields = ['scraped_at', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('link', 'url', 'title', 'language', 'read_more_link')
        }),
        ('Content', {
            'fields': ('text', 'summary')
        }),
        ('Images', {
            'fields': ('top_image', 'meta_img', 'images')
        }),
        ('Media & Keywords', {
            'fields': ('movies', 'keywords', 'tags', 'authors')
        }),
        ('Meta Data', {
            'fields': ('meta_keywords', 'meta_description', 'meta_lang', 'meta_favicon', 'meta_site_name', 'canonical_link')
        }),
        ('Publishing', {
            'fields': ('publish_date',)
        }),
        ('Timestamps', {
            'fields': ('scraped_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
from django.urls import path, re_path
from . import views

urlpatterns = [
    # Frontend
    path('', views.index, name='index'),

    # API Key Management
    path('api/create-key/', views.create_api_key, name='create_api_key'),

    # API Endpoints
    path('api/datasets/', views.api_datasets, name='api_datasets'),
    path('api/datasets/<str:dataset_name>/facts/', views.api_dataset_facts, name='api_dataset_facts'),
    # path('api/datasets/<str:dataset_name>/facts/<str:fact_id>/questions/', views.api_fact_questions, name='api_fact_questions'),

    # path('api/datasets/<str:dataset_name>/facts/<str:fact_id>/questions/<int:question_rank>/', views.api_fact_question_page, name='api_fact_question_page'),
    re_path(r'^api/serp-content/(?P<url>.+)/$', views.api_serp_content, name='api_serp_content'),
    path('api/serp-content/', views.api_serp_content_query, name='api_serp_content_query'),
]


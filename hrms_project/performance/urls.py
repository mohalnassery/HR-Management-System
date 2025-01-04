from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('', views.performance_list, name='performance_list'),
    path('review/create/', views.review_create, name='review_create'),
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/create/', views.goal_create, name='goal_create'),
]

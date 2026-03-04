from django.urls import path
from .views import JobViewSet

job_create = JobViewSet.as_view({'post':'create'})
job_retrieve = JobViewSet.as_view({'get':'retrieve'})

urlpatterns = [
    path('jobs/', job_create, name='job-create'),
    path('jobs/<uuid:pk>/', job_retrieve, name='job-retrieve'),
]

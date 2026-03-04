from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ваши API
    path('api/auth/', include('auth_service.urls')),
    path('api/orchestrator/', include('orchestrator.urls')),

    # OpenAPI схема
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Redoc (альтернативная документация)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

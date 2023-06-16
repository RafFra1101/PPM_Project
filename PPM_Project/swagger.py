from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import environ

"""env = environ.Env(
    API_URL=str,
)"""

schema_view = get_schema_view(
    openapi.Info(
        title="pollsAPI",
        default_version='v1',
        description="API documentation",
        contact=openapi.Contact(email="raffaele.mentina@stud.unifi.it"),
        license=openapi.License(name="BSD License"),
    ),
    #url=env('API_URL'),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

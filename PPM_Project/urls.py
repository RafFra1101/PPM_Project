"""
URL configuration for PPM_Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from pollsAPI import views as viewsAPI
from polls import views
from .swagger import urlpatterns as swagger_urls


router = routers.DefaultRouter()
router.register(r'users', viewsAPI.UserViewSet, basename='user')
#router.register(r'groups', viewsAPI.GroupViewSet)
router.register(r'polls', viewsAPI.PollViewSet, basename='poll')
router.register(r'choice', viewsAPI.ChoiceViewSet, 'choice')
#router.register(r'auth', viewsAPI.UserAuthentication, 'auth')


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/register/', viewsAPI.register, name="APIRegister"),
    path('api/login/', viewsAPI.login, name="APILogin"),
    path('api/userInfo/<str:info>', viewsAPI.userInfo),
    path('admin/', admin.site.urls),
    
    path("<int:poll_id>/", views.PollView.as_view(template_name="polls/detail.html"), name="detail"),
    path("<int:poll_id>/results/", views.PollView.as_view(template_name="polls/results.html"), name="results"),
    path("<int:poll_id>/vote/", views.vote, name="vote"),
] + swagger_urls

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
from polls.forms import LoginForm, RegisterForm


router = routers.DefaultRouter()
router.register('user', viewsAPI.UserViewSet, basename='user')
#router.register(r'groups', viewsAPI.GroupViewSet)
router.register('poll', viewsAPI.PollViewSet, basename='poll')
router.register('choice', viewsAPI.ChoiceViewSet, 'choice')
#router.register(r'auth', viewsAPI.UserAuthentication, 'auth')


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("register", views.RegisterLoginView.as_view(template_name="polls/register.html", form_class=RegisterForm), name="register"),
    path("login", views.RegisterLoginView.as_view(template_name="polls/login.html", form_class=LoginForm), name="login"),
    path("logout", views.ProfileView.logout, name="logout"),
    path("profile", views.ProfileView.as_view(), name="profile"),
    path("profile/votedPolls", views.VotedPollsView.as_view(), name="votedPolls"),
    path("profile/ownPolls", views.OwnPollsView.as_view(), name="ownPolls"),
    path("profile/ownPolls/deletePoll/<int:poll_id>", views.OwnPollsView.deletePoll, name="deletePoll"),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/register/', viewsAPI.register, name="APIregister"),
    path('api/login/', viewsAPI.login, name="APIlogin"),
    path('admin/', admin.site.urls),
    path("<int:poll_id>/", views.PollView.as_view(template_name="polls/detail.html"), name="detail"),
    path("<int:poll_id>/results/", views.PollView.as_view(template_name="polls/results.html"), name="results"),
    path("<int:poll_id>/vote/", views.vote, name="vote"),
] + swagger_urls

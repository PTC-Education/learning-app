from django.urls import path 
from .import views

app_name = 'grader'
urlpatterns = [
    path('',views.home), 
    path('home/<str:os_user_id>/',views.home, name="home"),
    path('oauthSignin/', views.login, name='login'), 
    path('oauthRedirect/', views.authorize, name='authorize'), 
    path('index/<str:os_user_id>/', views.index, name='index'), 
    path('grader/<str:os_user_id>/', views.grader, name='grader'),
    path('grade/<str:os_user_id>/<str:ref_url>/', views.grade_model, name="grade"), 
    path('grade/<str:os_user_id>/', views.grade_model, name="grade")
]
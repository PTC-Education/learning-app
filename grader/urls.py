from django.urls import path 
from .import views

app_name = 'grader'
urlpatterns = [
    path('',views.index), 
    path('oauthSignin/', views.login, name='login'), 
    path('oauthRedirect/', views.authorize, name='authorize'), 
    path('index/<str:os_user_id>/', views.index, name='index'), 
    path('grader/<str:os_user_id>/', views.grader, name='grader'),
    path('generic_grader/<str:os_user_id>/', views.generic_grader, name='generic_grader'),
    path('filelist/<str:os_user_id>/', views.filelist, name='filelist'),
    path('classlist/<str:os_user_id>/', views.classlist, name='classlist'),
    path('grade/<str:os_user_id>/<str:ref_url>/', views.grade_model, name="grade"), 
    path('grade/<str:os_user_id>/', views.grade_model, name="grade")
]
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
    path('listdocs/<str:os_user_id>/<str:did>/<str:wid>/', views.listdocs, name='listdocs'),
    path('enable_csv/<str:os_user_id>/', views.enable_csv, name='enable_csv'),
    path('upload_csv/<str:os_user_id>/csv', views.upload_csv, name='upload_csv'),
    path('grade/<str:os_user_id>/<str:ref_url>/', views.grade_model, name="grade"), 
    path('grade/<str:os_user_id>/', views.grade_model, name="grade"),
    path('comparewithurl/<str:os_user_id>/<str:usertype>/', views.comparewithurl, name="comparewithurl"),
]
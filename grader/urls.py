from django.urls import path 
from .import views

app_name = 'grader'
urlpatterns = [
    path('',views.index), 
    path('oauthSignin/', views.login, name='login'), 
    path('oauthRedirect/', views.authorize, name='authorize'), 
    path('index/<str:os_user_id>/', views.index, name='index'), 
    path('grade/<str:os_user_id>/<str:ref_url>/', views.grade_model, name="grade"), 
    path('grade/<str:os_user_id>/', views.grade_model, name="grade"),
    path('urlinputpage/<str:os_user_id>/<str:usertype>/', views.urlinputpage, name="urlinputpage"),
]
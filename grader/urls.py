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
    path('url_input_page/<str:os_user_id>/<str:user_type>/', views.url_input_page, name="url_input_page"),
    path('checker/<str:os_user_id>/', views.check_model, name="check_model"),
    path('doc_info_checker/<str:os_user_id>/', views.doc_info_checker, name="doc_info_checker"),
    path('doc_info_checker/<str:os_user_id>/<str:element_list>/', views.doc_info_checker, name="doc_info_checker"),
]
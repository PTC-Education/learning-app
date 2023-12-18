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
    path('list_classes/<str:os_user_id>/', views.list_classes, name="list_classes"),
    path('list_assignments/<str:os_user_id>/<str:class_id>/<str:class_name>', views.list_assignments, name="list_assignments"),
    path('list_members/<str:os_user_id>/<str:class_id>/<str:class_name>/<str:assignment_id>/<str:assignment_name>', views.list_members, name="list_members"),
    path('doc_info_checker/<str:os_user_id>/', views.doc_info_checker, name="doc_info_checker"),
    path('microversions_checker/<str:os_user_id>/', views.microversions_checker, name="microversions_checker"),
    path('update_html/<str:os_user_id>/<str:wm>/<str:wmid>', views.update_html, name='update_html')
]
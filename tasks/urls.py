from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # 認証
    path('signup/', views.signup, name='signup'),
    path('login/', LoginView.as_view(template_name='tasks/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # タスク
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/done/', views.task_done, name='task_done'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('users/', views.user_task_summary, name='user_summary'),
]
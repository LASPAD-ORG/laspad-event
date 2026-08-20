from django.urls import path
from . import views

app_name = 'planning'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('entrer/<str:token>/', views.auth_view, name='auth'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('agenda/', views.agenda_view, name='agenda'),
    path('ajouter/', views.add_view, name='add'),
    path('modifier/<uuid:pk>/', views.edit_view, name='edit'),
]

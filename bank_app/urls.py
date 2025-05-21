from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'), 

      
    # Nouvelles routes
    path('virement/', views.virement, name='virement'),
    path('retrait/', views.retrait, name='retrait'),
    path('versement/', views.versement, name='versement'),
    path('creer-compte-epargne/', views.creer_compte_epargne, name='creer_compte_epargne'),
    path('historique/', views.historique, name='historique'),
    path('profil/', views.profil, name='profil'),
    path('contact/', views.contact, name='contact'),

]



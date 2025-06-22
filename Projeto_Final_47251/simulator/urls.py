from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('simuladoresdisponiveis/', views.available_simulators, name='simuladoresDisponiveis'),
    path('simulator/', views.simulator, name='simulator_c'),
    path('simulatori/',views.simulador_i_view, name='simulator_i'),
    path('simulatorp/', views.simulator_personalizado, name='simulator_personalizado'),
    path('results/', views.results, name='escolha_historico'),
    path('historico/<str:tipo>/', views.historico, name='historico'),
    path('historico/<str:tipo>/<int:simulador_id>/', views.historico_promenor, name='historico_promenor'),
    path('historico/<str:tipo>/<int:simulador_id>/<int:utilizador_id>/', views.results_grupo, name='historico_pormenor_utilizador'),
    path('registo/', views.register, name='registo'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('instanciar/', views.instanciar_simulador, name='instanciar_simulador'),
    path('acessar/', views.acessar_simulador, name='acessar_simulador'),

    
]

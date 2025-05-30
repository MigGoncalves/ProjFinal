from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('simuladoresdisponiveis/', views.available_simulators, name='simuladoresDisponiveis'),
    path('simulator/', views.simulator, name='ecrã1'),
    path('simulatori/',views.simulador_i_view, name='simuator_i'),
    path('results/', views.results, name='ecrã2'),
    path('historico/', views.historico, name='historico'),
    path('historico/<int:simulador_id>/', views.historico_promenor, name='historico_promenor'),
    path('historico/<int:simulador_id>/<int:grupo_id>/', views.results_grupo, name='historico_pormenor_grupo'),
    path('registo/', views.register, name='registo'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('instanciar/', views.instanciar_simulador, name='instanciar_simulador')
    
]

from django.shortcuts import render

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

# Create your views here.


def index(request):
    return render(request, 'simulator/index.html')

def available_simulators(request):
    return render(request, 'simulator/simuladoresdisponiveis.html')

def registo(request):
    return render(request, 'simulator/register.html')

def login_view(request):
    return render(request, 'simulator/login.html')




from django.shortcuts import render, redirect
from .models import Simulador
from .utils import calcular_resultados
import random
import uuid

def simulator(request):
    # Se for um POST (submissão de dados)
    if request.method == 'POST':
        # Obter o ID da sessão atual ou criar um novo
        simulador_id = request.session.get('simulador_id')
        if not simulador_id:
            return redirect('simulator')
        
        # Buscar a última ronda deste simulador
        ultima = Simulador.objects.filter(simulador_id=simulador_id).order_by('-ronda').first()
        
        if not ultima:
            return redirect('simulator')
        
        # Processar dados do formulário
        c0 = float(request.POST.get('c0', 0.0))
        
        # Calcular resultados
        c1, s, U0, U0_max, percentagem = calcular_resultados(
            ultima.y0, ultima.y1, ultima.r, ultima.rho, c0
        )

        # Atualizar registro atual
        ultima.c0 = c0
        ultima.c1 = c1
        ultima.s = s
        ultima.U0 = U0
        ultima.U0_max = U0_max
        ultima.percentagem = percentagem
        ultima.save()

        # Se for a 5ª ronda, limpa a sessão e redireciona para index
        if ultima.ronda >= 5:
            request.session.pop('simulador_id', None)
            return redirect('index')
        
        # Criar próxima ronda
        nova_ronda = ultima.ronda + 1
        y0, y1, r, rho = ultima.y0, ultima.y1, ultima.r, ultima.rho
        
        if nova_ronda == 2:
            y0 = random.uniform(1000, 2000)
        elif nova_ronda == 3:
            y1 = random.uniform(1000, 2000)
        elif nova_ronda == 4:
            r = random.uniform(0.01, 0.25)
        elif nova_ronda == 5:
            rho = random.uniform(0.01, 0.25)
        
        Simulador.objects.create(
            simulador_id=simulador_id,
            ronda=nova_ronda, 
            y0=y0, 
            y1=y1, 
            r=r, 
            rho=rho
        )
        
        return redirect('ecrã1')

    # Se for GET (acesso normal à página)
    else:
        # Verificar se já tem um simulador em andamento na sessão
        simulador_id = request.session.get('simulador_id')
        
        if simulador_id:
            ultima = Simulador.objects.filter(simulador_id=simulador_id).order_by('-ronda').first()
            
            # Se já tiver a 5ª ronda completa, cria novo simulador
            if ultima and ultima.ronda >= 5 and ultima.c0 is not None:
                simulador_id = None
        
        if not simulador_id:
            # Cria novo ID de simulador
            simulador_id = str(uuid.uuid4())
            request.session['simulador_id'] = simulador_id
            
            # Cria primeira ronda
            nova_ronda = 1
            y0 = random.uniform(1000, 2000)
            y1 = random.uniform(1000, 2000)
            r = random.uniform(0.01, 0.25)
            rho = random.uniform(0.01, 0.25)
            
            simulador = Simulador.objects.create(
                simulador_id=simulador_id,
                ronda=nova_ronda, 
                y0=y0, 
                y1=y1, 
                r=r, 
                rho=rho
            )
        else:
            # Mostra a última ronda existente deste simulador
            simulador = ultima
            nova_ronda = simulador.ronda

        historicosimulador =  Simulador.objects.filter(simulador_id=simulador_id).order_by('ronda')

        contexto = {
            'ronda': nova_ronda,
            'y0': simulador.y0,
            'y1': simulador.y1,
            'r': simulador.r,
            'rho': simulador.rho,
            'rondas_anteriores': historicosimulador
        }
        return render(request, 'simulator/simulator.html', contexto)


from .models import SimuladorI
from .utils import calcular_consumo_utilidade

from django.shortcuts import render, redirect
from .models import SimuladorI
from .utils import calcular_consumo_utilidade
import random
import uuid

def simulador_i_view(request):
    # Obter ou criar simulador_id da sessão
    simulador_id = request.session.get('simulador_id_i')
    if not simulador_id:
        simulador_id = str(uuid.uuid4())
        request.session['simulador_id_i'] = simulador_id

    # Buscar última ronda
    ultima = SimuladorI.objects.filter(simulador_id_i=simulador_id).order_by('-ronda').first()

    if request.method == 'POST':
        # Verificar se existe ronda anterior
        if not ultima:
            return redirect('simulator_i')  # Caso não haja uma ronda anterior, cria nova

        # Obter investimento do formulário
        investimento = float(request.POST.get('investimento', 0.0))

        # Calcular resultados
        K, V0, K_opt, V0_max,percentagem = calcular_consumo_utilidade(
            ultima.A, investimento, ultima.alpha, ultima.delta, ultima.r
        )

        # Atualizar registro atual
        ultima.investimento = investimento
        ultima.K = K
        ultima.V0 = V0
        ultima.K_opt = K_opt
        ultima.V0_max = V0_max
        ultima.percentagem = percentagem
        ultima.save()

        # Se for a 5ª ronda, limpa a sessão e redireciona
        if ultima.ronda >= 5:
            request.session.pop('simulador_id_i', None)
            return redirect('index')

        # Criar próxima ronda
        nova_ronda = ultima.ronda + 1
        r, A, alpha, delta = ultima.r, ultima.A, ultima.alpha, ultima.delta

        # Alterar um parâmetro diferente a cada ronda
        if nova_ronda == 2:
            A = random.uniform(10, 25)  # Valores exemplo para A
        elif nova_ronda == 3:
            alpha = random.uniform(0.1, 0.9)  # alpha deve estar entre 0 e 1
        elif nova_ronda == 4:
            r = random.uniform(0.01, 0.25)
        elif nova_ronda == 5:
            delta = random.uniform(0.05, 0.2)

        SimuladorI.objects.create(
            simulador_id_i=simulador_id,
            ronda=nova_ronda,
            r=r,
            A=A,
            alpha=alpha,
            delta=delta
        )

        return redirect('simuator_i')

    else:
        # Requisição GET
        if simulador_id:
            ultima = SimuladorI.objects.filter(simulador_id_i=simulador_id).order_by('-ronda').first()

            # Se não encontrar uma ronda, cria a primeira
            if not ultima:
                nova_ronda = 1
                r = random.uniform(0.01, 0.25)
                A = random.uniform(10, 25)
                alpha = random.uniform(0.1, 0.9)
                delta = random.uniform(0.05, 0.2)

                simulador = SimuladorI.objects.create(
                    simulador_id_i=simulador_id,
                    ronda=nova_ronda,
                    r=r,
                    A=A,
                    alpha=alpha,
                    delta=delta
                )
            else:
                # Se existir uma última ronda, continua a partir dela
                nova_ronda = ultima.ronda
                simulador = ultima
        else:
            # Cria um novo simulador se o simulador_id não existir
            nova_ronda = 1
            simulador_id = str(uuid.uuid4())
            request.session['simulador_id_i'] = simulador_id
            r = random.uniform(0.01, 0.25)
            A = random.uniform(1.0, 2.0)
            alpha = random.uniform(0.1, 0.9)
            delta = random.uniform(0.01, 0.5)

            simulador = SimuladorI.objects.create(
                simulador_id_i=simulador_id,
                ronda=nova_ronda,
                r=r,
                A=A,
                alpha=alpha,
                delta=delta
            )

            # Buscar todas as rondas do simulador atual
        todas_as_rondas = SimuladorI.objects.filter(
            simulador_id_i=simulador_id,
            investimento__isnull=False
            ).order_by('ronda')


        contexto = {
            'ronda': nova_ronda,
            'r': simulador.r,
            'A': simulador.A,
            'alpha': simulador.alpha,
            'delta': simulador.delta,
            'investimento': simulador.investimento,
            'V0': simulador.V0,
            'V0_max': simulador.V0_max,
            'resultado': simulador.investimento is not None,
            'percentagem': simulador.percentagem,
            'rondas_anteriores': todas_as_rondas
        }

        return render(request, 'simulator/simulator_i.html', contexto)


def login(request):
    return render(request, 'login.html')


def register(request):
    return render(request, 'register.html')

def results(request):
    return render(request, 'simulator/results.html')

def historico(request):
    return render(request, 'simulator/historico.html')


# Dados fictícios (dummy data)
dados = [
    {
        'id': 1,
        'nome': 'Simulador A',
        'data': '2025-04-01',
        'resultado': 'Resultado 1',
        'grupos': [
            {
                'grupo_id': 1,
                'nome_grupo': 'Grupo 1',
                'valor': 'Detalhe Grupo 1',
                'resultado_1': '42.5',
                'resultado_2': '15.0',
                'resultado_final': '57.5'
            },
            {
                'grupo_id': 2,
                'nome_grupo': 'Grupo 2',
                'valor': 'Detalhe Grupo 2',
                'resultado_1': '30.0',
                'resultado_2': '25.0',
                'resultado_final': '55.0'
            },
            # Adiciona mais grupos se quiseres
        ]
    }
]




def historico_promenor(request, simulador_id):
    # Encontrar o simulador com o ID fornecido
    simulador = next((sim for sim in dados if sim['id'] == simulador_id), None)
    
    # Passar os dados do simulador para o template
    return render(request, 'simulator/historico_promenor.html', {'simulador': simulador})

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource,HoverTool

def results_grupo(request, simulador_id, grupo_id):
    simulador = next((sim for sim in dados if sim['id'] == simulador_id), None)
    grupo = next((grp for grp in simulador['grupos'] if grp['grupo_id'] == grupo_id), None) if simulador else None

    etapas = ["Resultado 1", "Resultado 2", "Resultado Final"]
    valores = [float(grupo['resultado_1']), float(grupo['resultado_2']), float(grupo['resultado_final'])]

    # Usar ColumnDataSource para usar nomes personalizados no Hover
    source = ColumnDataSource(data=dict(etapas=etapas, valores=valores))

    p = figure(x_range=etapas, height=350, title="Resultados do Grupo", toolbar_location=None, tools="")

    # Adiciona linha e círculos
    p.line(x='etapas', y='valores', source=source, line_width=2)
    p.circle(x='etapas', y='valores', source=source, size=10, color="blue")

    # Hover só com valores
    hover = HoverTool(tooltips=[("Valor", "@valores")])
    p.add_tools(hover)

    script, div = components(p)

    return render(request, 'simulator/results_grupo.html', {
        'grupo': grupo,
        'bokeh_script': script,
        'bokeh_div': div
    })
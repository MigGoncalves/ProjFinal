from django.shortcuts import render

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import Utilizador


# Create your views here.

# View da página inicial
def index(request):
    return render(request, 'simulator/index.html')

def available_simulators(request):
    return render(request, 'simulator/simuladoresdisponiveis.html')



# View de registo
def register(request):
    # caso o utilizador já esteja autenticado, redireciona para a página inicial
    if request.method == 'POST':
        email = request.POST['email']
        idade = request.POST['idade']
        nacionalidade = request.POST['nacionalidade']
        nome = request.POST['nome']
        foto = request.FILES.get('foto', None)
        password = request.POST['password']
        password2 = request.POST['password2']

        # Verifica se as senhas coincidem
        if password != password2:
            messages.error(request, "As senhas não coincidem!")
            return redirect('register')

        # Cria o utilizador
        try:
            user = Utilizador.objects.create_user(email=email, idade=idade, nacionalidade=nacionalidade,nome=nome, foto=foto, password=password)
            login(request, user)
            return redirect('index')  # Redireciona o utilizador para a página inicial 
        except Exception as e:
            messages.error(request, f"Erro ao criar utilizador: {e}")
            return redirect('register')

    return render(request, 'simulator/register.html')

# View de login
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            
            # Verifica se é docente ou não
            if not user.is_docente:
                return redirect('acessar_simulador')  # Vai direto para o simulador
            else:
                return redirect('index')  # Ou dashboard, se quiseres

        else:
            messages.error(request, "Email ou senha inválidos!")
            return redirect('login')

    return render(request, 'simulator/login.html')



from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('index')  

from .models import InstanciaSimulador

from django.shortcuts import render, redirect
from .models import InstanciaSimulador

def acessar_simulador(request):
    erro = None
    # Verifica se o utilizador já está autenticado
    if request.method == 'POST':
        senha = request.POST.get('senha')

        instancia = InstanciaSimulador.objects.filter(senha=senha).first()
        # Se a instância existir, armazena os dados na sessão
         # Se a instância não existir, retorna um erro
        if instancia:
            request.session['nome'] = instancia.nome
            request.session['senha'] = senha
            request.session['simulador_id'] = str(instancia.simulador_id)
            request.session['tipo_simulador'] = instancia.tipo
            # Redireciona para o simulador correto com base no tipo
            if instancia.tipo == 'I':
                return redirect('ecrã1')  
            elif instancia.tipo == 'II':
                return redirect('simuator_i')  
            else:
                erro = "Tipo de simulador desconhecido."
        else:
            erro = "Senha inválida."

    return render(request, 'simulator/acessar_simulador.html', {'erro': erro})





from django.shortcuts import render, redirect
from .models import Simulador
from .utils import calcular_resultados
import random
import uuid
from .models import InstanciaSimulador

# Função auxiliar para obter um gerador de números aleatórios baseado em uma semente e ronda
def get_random_for_ronda(seed, ronda):
    rnd = random.Random(seed + ronda * 1000)
    return rnd

# View para o simulador de escolha intertemporal de consumo
def simulator(request):
    nome = request.session.get('nome')
    senha = request.session.get('senha')

    if not nome or not senha:
        return redirect('index')

    # Obter ou criar a instância com base no nome + senha
    instancia, _ = InstanciaSimulador.objects.get_or_create(nome=nome, senha=senha)

    random.seed(instancia.seed)

    utilizador = request.user  
    # Verifica se o utilizador está autenticado
    if request.method == 'POST':
        # Última ronda
        ultima = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda').first()

        if not ultima:
            return redirect('simulator')

        # Obter valor submetido
        c0 = float(request.POST.get('c0', 0.0))

        # Calcular resultados
        c1, s, U0, U0_max, percentagem = calcular_resultados(
            ultima.y0, ultima.y1, ultima.r, ultima.rho, c0
        )

        # Atualizar registo
        ultima.c0 = c0
        ultima.c1 = c1
        ultima.s = s
        ultima.U0 = U0
        ultima.U0_max = U0_max
        ultima.percentagem = percentagem
        ultima.save()
        # Se a última ronda já tiver sido concluída, limpa a sessão
        # e redireciona para a página inicial
         # Se a última ronda for 5, limpa a sessão e redireciona para a página inicial
        if ultima.ronda >= 5:
            request.session.pop('simulador_id', None)
            return redirect('index')

        # Próxima ronda
        
        nova_ronda = ultima.ronda + 1
        rnd = get_random_for_ronda(instancia.seed, nova_ronda)
        y0, y1, r, rho = ultima.y0, ultima.y1, ultima.r, ultima.rho
        # Atualiza os valores com base na ronda
        if nova_ronda == 2:
            y0 = rnd.uniform(1000, 2000)
        elif nova_ronda == 3:
            y1 = rnd.uniform(1000, 2000)
        elif nova_ronda == 4:
            r = rnd.uniform(0.01, 0.25)
        elif nova_ronda == 5:
            rho = rnd.uniform(0.01, 0.25)

        Simulador.objects.create(
            utilizador=utilizador,
            instancia=instancia,
            ronda=nova_ronda,
            y0=y0,
            y1=y1,
            r=r,
            rho=rho
        )

        return redirect('ecrã1')
    # Se for uma requisição GET
    else:
        # GET
        simulacoes = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda')
        ultima = simulacoes.first()

        if ultima and ultima.ronda >= 5 and ultima.c0 is not None:
            simulacoes.delete()
            ultima = None

        if not ultima:
            nova_ronda = 1
            y0 = random.uniform(1000, 2000)
            y1 = random.uniform(1000, 2000)
            r = random.uniform(0.01, 0.25)
            rho = random.uniform(0.01, 0.25)

            simulador = Simulador.objects.create(
                utilizador=utilizador,
                instancia=instancia,
                ronda=nova_ronda,
                y0=y0,
                y1=y1,
                r=r,
                rho=rho
            )
        else:
            simulador = ultima
            nova_ronda = simulador.ronda

        historicosimulador = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')

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
    # Verificar nome e senha na sessão
    nome = request.session.get('nome')
    senha = request.session.get('senha')
    if not nome or not senha:
        return redirect('index')

    utilizador = request.user

    # Obter ou criar instância associada ao utilizador, nome e senha
    instancia, _ = InstanciaSimulador.objects.get_or_create(
       
        nome=nome,
        senha=senha
    )

    random.seed(instancia.seed)

    # Buscar última ronda da instância
    ultima = SimuladorI.objects.filter(utilizador=utilizador,instancia=instancia).order_by('-ronda').first()

    if request.method == 'POST':
        if not ultima:
            return redirect('simuator_i')

        # Obter investimento do POST
        investimento = float(request.POST.get('investimento', 0.0))

        # Calcular resultados
        K, V0, K_opt, V0_max, percentagem = calcular_consumo_utilidade(
            ultima.A, investimento, ultima.alpha, ultima.delta, ultima.r
        )

        # Atualizar última ronda
        ultima.investimento = investimento
        ultima.K = K
        ultima.V0 = V0
        ultima.K_opt = K_opt
        ultima.V0_max = V0_max
        ultima.percentagem = percentagem
        ultima.save()

        if ultima.ronda >= 5:
            # Final da simulação, limpar sessão
            return redirect('index')

        # Preparar nova ronda
        nova_ronda = ultima.ronda + 1
        rnd = get_random_for_ronda(instancia.seed, nova_ronda)
        r, A, alpha, delta = ultima.r, ultima.A, ultima.alpha, ultima.delta

        if nova_ronda == 2:
            A = rnd.uniform(10, 25)
        elif nova_ronda == 3:
            alpha = rnd.uniform(0.1, 0.9)
        elif nova_ronda == 4:
            r = rnd.uniform(0.01, 0.25)
        elif nova_ronda == 5:
            delta = rnd.uniform(0.05, 0.2)

        SimuladorI.objects.create(
            utilizador=utilizador,
            instancia=instancia,
            ronda=nova_ronda,
            r=r,
            A=A,
            alpha=alpha,
            delta=delta
        )

        return redirect('simuator_i')

    else:
        # Requisição GET
        if not ultima:
            nova_ronda = 1
            r = random.uniform(0.01, 0.25)
            A = random.uniform(10, 25)
            alpha = random.uniform(0.1, 0.9)
            delta = random.uniform(0.05, 0.2)

            simulador = SimuladorI.objects.create(
                utilizador=utilizador,
                instancia=instancia,
                ronda=nova_ronda,
                r=r,
                A=A,
                alpha=alpha,
                delta=delta
            )
        else:
            nova_ronda = ultima.ronda
            simulador = ultima

        todas_as_rondas = SimuladorI.objects.filter(
            utilizador=utilizador,
            instancia=instancia,
            investimento__isnull=False
        ).order_by('ronda')

        rondas_completas = list(todas_as_rondas) + [simulador]

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
            'rondas_anteriores': rondas_completas
        }

        return render(request, 'simulator/simulator_i.html', contexto)




def results(request):
    return render(request, 'simulator/results.html')

def historico(request, tipo):
    print(f"Tipo recebido: {tipo}")
    simuladores = InstanciaSimulador.objects.filter(tipo=tipo)
    tipo_nome = dict(InstanciaSimulador.TIPO_CHOICES).get(tipo, 'Desconhecido')
    return render(request, 'simulator/historico.html', {
        'simuladores': simuladores,
        'tipo': tipo,
       
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import InstanciaSimulador

@login_required
def instanciar_simulador(request):
    if not getattr(request.user, 'is_docente', False):
        return HttpResponseForbidden("Apenas docentes podem aceder a esta página.")

    mensagem = None

    if request.method == 'POST':
        nome = request.POST.get('nome')
        senha = request.POST.get('senha')
        tipo = request.POST.get('tipo')

        # Verifica se já existe com o mesmo nome
        if InstanciaSimulador.objects.filter(nome=nome).exists():
            mensagem = "Já existe uma instância com esse nome."
        else:
            InstanciaSimulador.objects.create(
                nome=nome,
                senha=senha,
                tipo=tipo
            )
            mensagem = f"Instância '{nome}' criada com sucesso!"

    return render(request, 'simulator/instanciarsimulador.html', {'mensagem': mensagem})



# Dados fictícios (dummy data)
dados = [
    {
        'id': 1,
        'nome': 'Simulador A',
        'data': '2025-04-01',
        'resultado': 'Simulação com ρ = 0.9 e r = 0.05',
        'grupos': [
            {
                'grupo_id': 1,
                'nome_grupo': 'Grupo 1',
                'rondas': [
                    {
                        'ronda': 1,
                        'c0': 50.0,
                        'c1': 52.5,
                        's': 10.0,
                        'U0': 80.0,
                        'U0_max': 85.0,
                        'percentagem': 94.1
                    },
                    {
                        'ronda': 2,
                        'c0': 45.0,
                        'c1': 55.0,
                        's': 5.0,
                        'U0': 78.0,
                        'U0_max': 85.0,
                        'percentagem': 88.8
                    },
                    {
                        'ronda': 3,
                        'c0': 48.0,
                        'c1': 52.0,
                        's': 8.0,
                        'U0': 79.5,
                        'U0_max': 85.0,
                        'percentagem': 92.5
                    },
                    {
                        'ronda': 4,
                        'c0': 50.0,
                        'c1': 50.0,
                        's': 7.0,
                        'U0': 80.5,
                        'U0_max': 85.0,
                        'percentagem': 96.2
                    },
                    {
                        'ronda': 5,
                        'c0': 52.0,
                        'c1': 48.0,
                        's': 6.0,
                        'U0': 81.0,
                        'U0_max': 85.0,
                        'percentagem': 87.5
                    }
                ]
            },
            {
                'grupo_id': 2,
                'nome_grupo': 'Grupo 2',
                'rondas': [
                    {
                        'ronda': 1,
                        'c0': 40.0,
                        'c1': 60.0,
                        's': 15.0,
                        'U0': 75.0,
                        'U0_max': 85.0,
                        'percentagem': 88.2
                    },
                    {
                        'ronda': 2,
                        'c0': 42.0,
                        'c1': 58.0,
                        's': 12.0,
                        'U0': 76.5,
                        'U0_max': 85.0,
                        'percentagem': 90.0
                    }
                ]
            }
        ]
    }
]





from django.db.models import Avg

def historico_promenor(request, tipo, simulador_id):
    simulador = get_object_or_404(InstanciaSimulador, id=simulador_id, tipo=tipo)
    ordenar = request.GET.get("ordenar")

    utilizadores_com_media = []

    if tipo == 'I':
        simulacoes = Simulador.objects.filter(instancia=simulador)
        utilizadores = Utilizador.objects.filter(simulador__instancia=simulador).distinct()

        for u in utilizadores:
            media = Simulador.objects.filter(instancia=simulador, utilizador=u).aggregate(
                media=Avg("percentagem")
            )["media"] or 0
            utilizadores_com_media.append((u, round(media, 2)))

    elif tipo == 'II':
        simulacoes = SimuladorI.objects.filter(instancia=simulador)
        utilizadores = Utilizador.objects.filter(simuladori__instancia=simulador).distinct()

        for u in utilizadores:
            media = SimuladorI.objects.filter(instancia=simulador, utilizador=u).aggregate(
                media=Avg("percentagem")
            )["media"] or 0
            utilizadores_com_media.append((u, round(media, 2)))
    else:
        simulacoes = []
        utilizadores_com_media = []

    # Ordenar
    if ordenar == "media_asc":
        utilizadores_com_media.sort(key=lambda x: x[1])
    elif ordenar == "media_desc":
        utilizadores_com_media.sort(key=lambda x: x[1], reverse=True)

    return render(request, 'simulator/historico_promenor.html', {
        'tipo': tipo,
        'simulador': simulador,
        'utilizadores': utilizadores_com_media,
        'ordenar': ordenar,
    })




from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource, HoverTool
from django.shortcuts import render

from django.shortcuts import render, get_object_or_404
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.embed import components
from .models import InstanciaSimulador, Simulador, SimuladorI


# Exemplo simplificado com a estrutura do grupo
# (assume-se que o 'grupo' contém uma lista de 'rondas')
def results_grupo(request, tipo, simulador_id, utilizador_id):
    instancia = get_object_or_404(InstanciaSimulador, id=simulador_id)


    # Obter utilizador (grupo)
    utilizador = get_object_or_404(Utilizador, id=utilizador_id)

    # Verifica o tipo de simulador
    if instancia.tipo == 'I':
        rondas = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')
        if not rondas.exists():
            return render(request, 'simulator/results_grupo.html', {
                'grupo': utilizador,
                'bokeh_script': '',
                'bokeh_div': '',
                'erro': 'Nenhuma ronda encontrada para este grupo.'
            })

        # Preparar dados para gráfico do Simulador I (consumo)
        source = ColumnDataSource(data=dict(
            ronda_labels=[f"Ronda {r.ronda}" for r in rondas],
            percentagens=[r.percentagem for r in rondas],
            c0=[r.c0 for r in rondas],
            c1=[r.c1 for r in rondas],
            s=[r.s for r in rondas],
            U0=[r.U0 for r in rondas],
            U0_max=[r.U0_max for r in rondas],
        ))

        p = figure(
            x_range=source.data['ronda_labels'],
            height=350,
            title=f"Desempenho de {utilizador.nome} por Ronda (Simulador I)",
            toolbar_location=None,
            tools=""
        )

        p.line(x='ronda_labels', y='percentagens', source=source, line_width=2)
        p.circle(x='ronda_labels', y='percentagens', source=source, size=10, color="blue")

        hover = HoverTool(tooltips=[
            ("Ronda", "@ronda_labels"),
            ("c₀", "@c0{0.00}"),
            ("c₁", "@c1{0.00}"),
            ("Poupança", "@s{0.00}"),
            ("U₀", "@U0{0.00}"),
            ("U₀max", "@U0_max{0.00}"),
            ("% ótimo", "@percentagens{0.00}")
        ])
        p.add_tools(hover)

        p.xaxis.axis_label = "Rondas"
        p.yaxis.axis_label = "Percentagem de desempenho (%)"
        p.y_range.start = 0
        p.y_range.end = 110

    elif instancia.tipo == 'II':
        rondas = SimuladorI.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')
        if not rondas.exists():
            return render(request, 'simulator/results_grupo.html', {
                'grupo': utilizador,
                'bokeh_script': '',
                'bokeh_div': '',
                'erro': 'Nenhuma ronda encontrada para este grupo.'
            })

        # Preparar dados para gráfico do Simulador II (investimento)
        source = ColumnDataSource(data=dict(
            ronda_labels=[f"Ronda {r.ronda}" for r in rondas],
            percentagens=[r.percentagem for r in rondas],
            investimento=[r.investimento for r in rondas],
            V0=[r.V0 for r in rondas],
            V0_max=[r.V0_max for r in rondas],
        ))

        p = figure(
            x_range=source.data['ronda_labels'],
            height=350,
            title=f"Desempenho de {utilizador.nome} por Ronda (Simulador II)",
            toolbar_location=None,
            tools=""
        )

        p.line(x='ronda_labels', y='percentagens', source=source, line_width=2)
        p.circle(x='ronda_labels', y='percentagens', source=source, size=10, color="green")

        hover = HoverTool(tooltips=[
            ("Ronda", "@ronda_labels"),
            ("Investimento", "@investimento{0.00}"),
            ("V₀", "@V0{0.00}"),
            ("V₀max", "@V0_max{0.00}"),
            ("% ótimo", "@percentagens{0.00}")
        ])
        p.add_tools(hover)

        p.xaxis.axis_label = "Rondas"
        p.yaxis.axis_label = "Percentagem de desempenho (%)"
        p.y_range.start = 0
        p.y_range.end = 110

    else:
        return render(request, 'simulator/results_grupo.html', {
            'grupo': utilizador,
            'bokeh_script': '',
            'bokeh_div': '',
            'erro': 'Tipo de simulador desconhecido.'
        })

    # Gerar componentes Bokeh
    script, div = components(p)

    return render(request, 'simulator/results_grupo.html', {
        'utilizador': utilizador,
        'bokeh_script': script,
        'bokeh_div': div,
        'instancia': instancia,
        'rondas': rondas, 
        'tipo':  tipo,
    })
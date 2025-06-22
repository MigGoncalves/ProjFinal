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

# View da página de simuladores disponíveis
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

        #
        is_docente = request.POST.get('is_docente') == 'on'

        # Verifica se as senhas coincidem
        if password != password2:
            messages.error(request, "As senhas não coincidem!")
            return redirect('register')

        # Cria o utilizador
        try:
            user = Utilizador.objects.create_user(email=email, idade=idade, nacionalidade=nacionalidade,nome=nome, foto=foto, password=password,is_docente=is_docente)
            login(request, user)
             # Redirecionamento conforme o tipo de utilizador
            if is_docente:
                return redirect('index')  # Página inicial dos docentes
            else:
                return redirect('acessar_simulador')  # Página inicial dos utilizadores normais  # Redireciona o utilizador para a página inicial 
        except Exception as e:
            messages.error(request, f"Erro ao criar utilizador: {e}")
            return redirect('register')

    return render(request, 'simulator/register.html')

# View de login
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

# View de login
def login_view(request):
    # Se o utilizador já estiver autenticado, redireciona para a página inicial
    if request.method == 'POST':
        # Obtém os dados do formulário
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        # Se o utilizador for encontrado, faz login
        # e redireciona para a página inicial ou dashboard
         # Se o utilizador não for encontrado, exibe uma mensagem de erro
        if user is not None:
            login(request, user)
            
            # Verifica se é docente ou não
            if not user.is_docente:
                return redirect('acessar_simulador')  # Vai direto para o simulador
            else:
                return redirect('index') 

        else:
            # Se o utilizador não for encontrado, exibe uma mensagem de erro
            # e redireciona para a página de login
            messages.error(request, "Email ou senha inválidos!")
            return redirect('login')

    return render(request, 'simulator/login.html')



from django.contrib.auth import logout
from django.shortcuts import redirect

# View de logout
def logout_view(request):
    # Faz logout do utilizador e redireciona para a página inicial
    logout(request)
    return redirect('login')  

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
            # Armazena os dados na sessão
            request.session['nome'] = instancia.nome
            request.session['senha'] = senha
            request.session['simulador_id'] = str(instancia.simulador_id)
            request.session['tipo_simulador'] = instancia.tipo
            # Redireciona para o simulador correto com base no tipo
            if instancia.tipo == 'I':
                return redirect('simulator_c')  
            elif instancia.tipo == 'II':
                return redirect('simulator_i') 
            elif instancia.tipo == 'III':
                return redirect('simulator_personalizado') 
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
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import SimuladorI
from .utils import calcular_consumo_utilidade

from django.shortcuts import render, redirect
from .models import SimuladorI
from .utils import calcular_consumo_utilidade
import random
import uuid

# Função auxiliar para obter um gerador de números aleatórios baseado em uma semente e ronda
def get_random_for_ronda(seed, ronda):
    rnd = random.Random(seed + ronda * 1000)
    return rnd

# View para o simulador de escolha intertemporal de consumo
def simulator(request):
    nome = request.session.get('nome')
    senha = request.session.get('senha')

    if not nome or not senha:
        return redirect('acessar_simulador')

    # Obter ou criar a instância com base no nome + senha
    instancia, _ = InstanciaSimulador.objects.get_or_create(nome=nome, senha=senha)
    # Definir a semente aleatória com base na instância
    random.seed(instancia.seed)
    # Verifica se o utilizador está autenticado
    utilizador = request.user  

    # Verifica se a instância é do tipo I
    if request.method == 'POST':
        # Verificar tempo limite da ronda
        inicio_str = request.session.get('inicio_ronda')
        tempo_expirado = False

        # Se o tempo de início da ronda estiver definido, verifica se o tempo expirou
        if inicio_str:
            try:
                inicio = timezone.datetime.fromisoformat(inicio_str)
            except Exception:
                inicio = timezone.datetime.fromisoformat(inicio_str.replace('Z', '+00:00'))
            tempo_expirado = timezone.now() - inicio > timedelta(seconds=30)

        # Última ronda
        ultima = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda').first()
        if not ultima:
            return redirect('simulator')

        if not tempo_expirado:
            # Obter valor submetido
            try:
                c0 = float(request.POST.get('c0', '0').replace(',', '.'))
            except ValueError:
                c0 = 0.0  # ou dá erro ao utilizador

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
        else:
            messages.warning(request, "Tempo esgotado nesta ronda. A resposta não foi considerada.")

        # Se a última ronda for 5, limpa a sessão e redireciona para a página do acessar simulador
        if ultima.ronda >= 5:
            request.session.pop('simulador_id', None)
            request.session.pop('inicio_ronda', None)
            return redirect('acessar_simulador')

        # Próxima ronda
        nova_ronda = ultima.ronda + 1
        rnd = get_random_for_ronda(instancia.seed, nova_ronda)
        y0, y1, r, rho = ultima.y0, ultima.y1, ultima.r, ultima.rho

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

        # Atualiza tempo de início da nova ronda
        request.session['inicio_ronda'] = timezone.now().isoformat()

        return redirect('simulator_c')

    else:
        # GET
        simulacoes = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda')
        ultima = simulacoes.first()

        # Se a última ronda for 5 e já tiver resultados, limpa as simulações
        if ultima and ultima.ronda >= 5 and ultima.c0 is not None:
            simulacoes.delete()
            ultima = None

        # Se não houver uma última ronda, cria uma nova
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

        # Inicia o tempo da ronda
        request.session['inicio_ronda'] = timezone.now().isoformat()
        
        # Obtém o histórico de simulações
        # para o utilizador e a instância
        historicosimulador = Simulador.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')

        # Contexto para renderizar o template
        # Passa os dados necessários para o template
        contexto = {
            'ronda': nova_ronda,
            'y0': simulador.y0,
            'y1': simulador.y1,
            'r': simulador.r,
            'rho': simulador.rho,
            'rondas_anteriores': historicosimulador
        }
        return render(request, 'simulator/simulator.html', contexto)




def simulador_i_view(request):
    # Verifica se o utilizador está autenticado e se tem sessão ativa
    nome = request.session.get('nome')
    senha = request.session.get('senha')
    if not nome or not senha:
        return redirect('acessar_simulador')

    # Obtém ou cria a instância com base no nome + senha
    # e define a semente aleatória
    utilizador = request.user

    instancia, _ = InstanciaSimulador.objects.get_or_create(nome=nome, senha=senha)
    random.seed(instancia.seed)

    # Verifica se a instância é do tipo II
    ultima = SimuladorI.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda').first()

    # Se não houver uma última ronda, redireciona para a criação de uma nova ronda
    if request.method == 'POST':
        if not ultima:
            return redirect('simulator_i')

        # Verificar tempo limite
        inicio_str = request.session.get('inicio_ronda')
        tempo_expirado = False

        # Se o tempo de início da ronda estiver definido, verifica se o tempo expirou
        if inicio_str:
            try:
                inicio = timezone.datetime.fromisoformat(inicio_str)
            except Exception:
                inicio = timezone.datetime.fromisoformat(inicio_str.replace('Z', '+00:00'))
            tempo_expirado = timezone.now() - inicio > timedelta(seconds=30)

        # Se o tempo não tiver expirado, processa a resposta
        # Caso contrário, exibe uma mensagem de aviso
        if not tempo_expirado:
            investimento = float(request.POST.get('investimento', 0.0))
            K, V0, K_opt, V0_max, percentagem = calcular_consumo_utilidade(
                ultima.A, investimento, ultima.alpha, ultima.delta, ultima.r
            )

            ultima.investimento = investimento
            ultima.K = K
            ultima.V0 = V0
            ultima.K_opt = K_opt
            ultima.V0_max = V0_max
            ultima.percentagem = percentagem
            ultima.save()
        else:
            messages.warning(request, "Tempo esgotado nesta ronda. A resposta não foi considerada.")

        # Se a última ronda for 5, limpa a sessão e redireciona para a página inicial
        # Caso contrário, cria uma nova ronda com os valores atualizados
        if ultima.ronda >= 5:
            request.session.pop('inicio_ronda', None)
            return redirect('acessar_simulador')

        # Cria uma nova ronda com os valores atualizados
        # e aleatoriza os valores de A, alpha, r e delta
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

        request.session['inicio_ronda'] = timezone.now().isoformat()
        return redirect('simulator_i')

    # Se for um GET, renderiza a página com os dados da última ronda ou cria uma nova
    else:
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

        # Inicia o tempo da ronda
        # e armazena na sessão
        request.session['inicio_ronda'] = timezone.now().isoformat()

        # Obtém o histórico de rondas para o utilizador e a instância
        # e ordena por ronda
        todas_as_rondas = SimuladorI.objects.filter(
            utilizador=utilizador,
            instancia=instancia
        ).order_by('ronda')

        rondas_completas = list(todas_as_rondas) 

        # Contexto para renderizar o template
        # Passa os dados necessários para o template
        contexto = {
            'ronda': nova_ronda,
            'r': simulador.r,
            'A': simulador.A,
            'alpha': simulador.alpha,
            'delta': simulador.delta,
            'investimento': simulador.investimento,
            'K': simulador.K,
            'K_opt': simulador.K_opt,
            'V0': simulador.V0,
            'V0_max': simulador.V0_max,
            'resultado': simulador.investimento is not None,
            'percentagem': simulador.percentagem,
            'rondas_anteriores': rondas_completas
        }

        return render(request, 'simulator/simulator_i.html', contexto)
    

from .utils import calculo_sim_personalizado
from .models import SimuladorP
from.models import SimuladorPConfig

def simulator_personalizado(request):
    # Verifica se o utilizador está autenticado e se tem sessão ativa
    nome = request.session.get('nome')
    senha = request.session.get('senha')

    # Se não houver nome ou senha, redireciona para a página inicial
    if not nome or not senha:
        return redirect('acessar_simulador')

    # Obtém a instância do simulador com base no nome e senha
    # Se não encontrar, redireciona para a página inicial
    instancia = InstanciaSimulador.objects.filter(nome=nome, senha=senha).first()
    if not instancia:
        return redirect('acessar_simulador')
    
    config = SimuladorPConfig.objects.filter(nome=nome, senha = senha).first()
    if not config:
        return redirect('acessar_simulador')

    # Define a semente aleatória com base na instância
    utilizador = request.user
    # Verifica se o utilizador está autenticado
    if request.method == 'POST':
        inicio_str = request.session.get('inicio_ronda')
        tempo_expirado = False

        # Se o tempo de início da ronda estiver definido, verifica se o tempo expirou
        # Se o tempo não tiver expirado, processa a resposta
        if inicio_str:
            try:
                inicio = timezone.datetime.fromisoformat(inicio_str)
            except Exception:
                inicio = timezone.datetime.fromisoformat(inicio_str.replace('Z', '+00:00'))
            tempo_expirado = timezone.now() - inicio > timedelta(seconds=30)

        # Última ronda
        # Obtém a última simulação do utilizador e da instância
        ultima = SimuladorP.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda').first()
        if not ultima:
            return redirect('simulator_personalizado')

        # Se o tempo não tiver expirado, processa a resposta
        # Caso contrário, exibe uma mensagem de aviso
        if not tempo_expirado:
            try:
                p5 = float(request.POST.get('p5', '0').replace(',', '.'))
            except ValueError:
                p5 = 0.0

            percentagem, v1, v2, v3, v4 = calculo_sim_personalizado(
                ultima.p1, ultima.p2, ultima.p3, ultima.p4, p5
            )
            # Atualiza o registo da última ronda com os novos valores
            ultima.p5 = p5
            ultima.percentagem = percentagem
            ultima.valor1 = v1
            ultima.valor2 = v2
            ultima.valor3 = v3
            ultima.valor4 = v4
            ultima.save()
        else:
            messages.warning(request, "Tempo esgotado nesta ronda. A resposta não foi considerada.")

        # Se a última ronda for 5, limpa a sessão e redireciona para a página inicial
        # Caso contrário, cria uma nova ronda com os valores atualizados
        if ultima.ronda >= 5:
            request.session.pop('inicio_ronda', None)
            return redirect('acessar_simulador')

        nova_ronda = ultima.ronda + 1
        rnd = get_random_for_ronda(instancia.seed, nova_ronda)

        # Herda valores anteriores
        p1, p2, p3, p4 = ultima.p1, ultima.p2, ultima.p3, ultima.p4

        # Aleatorizar novo valor de p1 a p4 consoante a ronda
        if nova_ronda == 2:
            p1 = rnd.uniform(config.min_p1, config.max_p1)
        elif nova_ronda == 3:
            p2 = rnd.uniform(config.min_p2, config.max_p2)
        elif nova_ronda == 4:
            p3 = rnd.uniform(config.min_p3, config.max_p3)
        elif nova_ronda == 5:
            p4 = rnd.uniform(config.min_p4, config.max_p4)

        # Cria uma nova simulação com os valores atualizados
        # e armazena na base de dados
        SimuladorP.objects.create(
            utilizador=utilizador,
            instancia=instancia,
            ronda=nova_ronda,
            p1=p1,
            p2=p2,
            p3=p3,
            p4=p4
        )
        # Atualiza o tempo de início da nova ronda
        # e armazena na sessão
        request.session['inicio_ronda'] = timezone.now().isoformat()
        return redirect('simulator_personalizado')

    else:
        simulacoes = SimuladorP.objects.filter(utilizador=utilizador, instancia=instancia).order_by('-ronda')
        ultima = simulacoes.first()

        if ultima and ultima.ronda >= 5 and ultima.percentagem is not None:
            simulacoes.delete()
            ultima = None

        if not ultima:
            nova_ronda = 1
            p1 = random.uniform(config.min_p1, config.max_p1)
            p2 = random.uniform(config.min_p2, config.max_p2)
            p3 = random.uniform(config.min_p3, config.max_p3)
            p4 = random.uniform(config.min_p4, config.max_p4)

            simulador = SimuladorP.objects.create(
                utilizador=utilizador,
                instancia=instancia,
                ronda=nova_ronda,
                p1=p1,
                p2=p2,
                p3=p3,
                p4=p4
            )
        else:
            simulador = ultima
            nova_ronda = simulador.ronda

        request.session['inicio_ronda'] = timezone.now().isoformat()

        historico = SimuladorP.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')

        
        contexto = {
            'ronda': nova_ronda,
            'simulador': simulador,
            'instancia': instancia,
            'rondas_anteriores': historico,
            'p1': simulador.p1,
            'p2': simulador.p2,
            'p3': simulador.p3,
            'p4': simulador.p4,
            'p5': simulador.p5,
            'percentagem': simulador.percentagem,
            'valor1': simulador.valor1,
            'valor2': simulador.valor2,
            'valor3': simulador.valor3,
            'valor4': simulador.valor4,
        }
        return render(request, 'simulator/simulator_p.html', contexto)


# View para exibir os resultados
def results(request):
    return render(request, 'simulator/results.html')

# View para exibir o histórico de simulações
def historico(request, tipo):
    # Verifica se o tipo de simulador é válido
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

        # caso o tipo seja personalizado o config personalizado é criado
        if tipo == 'III':
            if InstanciaSimulador.objects.filter(nome=nome).exists() or SimuladorPConfig.objects.filter(nome=nome).exists():
                mensagem = "Já existe uma instância personalizada com esse nome."
            else:
                try:
                    p1_min = float(request.POST.get('param1_min'))
                    p1_max = float(request.POST.get('param1_max'))
                    p2_min = float(request.POST.get('param2_min'))
                    p2_max = float(request.POST.get('param2_max'))
                    p3_min = float(request.POST.get('param3_min'))
                    p3_max = float(request.POST.get('param3_max'))
                    p4_min = float(request.POST.get('param4_min'))
                    p4_max = float(request.POST.get('param4_max'))

                    # Cria o config personalizado
                    SimuladorPConfig.objects.create(
                        nome=nome,
                        senha=senha,
                        min_p1=p1_min, max_p1=p1_max,
                        min_p2=p2_min, max_p2=p2_max,
                        min_p3=p3_min, max_p3=p3_max,
                        min_p4=p4_min, max_p4=p4_max,
                    )
                    # Cria a instância simulador que vai validar a senha e o nome
                    InstanciaSimulador.objects.create(
                        nome=nome,
                        senha=senha,
                        tipo=tipo
                    )
                    mensagem = f"Simulador personalizado '{nome}' criado com sucesso!"
                except (TypeError, ValueError):
                    mensagem = "Por favor, insira valores numéricos válidos para os parâmetros."
        else:
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


from django.db.models import Avg

# View para exibir o histórico de simulações com detalhes
def historico_promenor(request, tipo, simulador_id):
    # Verifica se o tipo de simulador é válido
    simulador = get_object_or_404(InstanciaSimulador, id=simulador_id, tipo=tipo)
    ordenar = request.GET.get("ordenar")

    utilizadores_com_media = []

    # Obtém as simulações e utilizadores associados ao simulador de acordo com o tipo
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

    elif tipo == 'III':
        simulacoes = SimuladorP.objects.filter(instancia=simulador)
        utilizadores = Utilizador.objects.filter(simuladorp__instancia=simulador).distinct()

        for u in utilizadores:
            media = SimuladorP.objects.filter(instancia=simulador, utilizador=u).aggregate(
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

    elif instancia.tipo == 'III':
        rondas = SimuladorP.objects.filter(utilizador=utilizador, instancia=instancia).order_by('ronda')
        if not rondas.exists():
            return render(request, 'simulator/results_grupo.html', {
                'grupo': utilizador,
                'bokeh_script': '',
                'bokeh_div': '',
                'erro': 'Nenhuma ronda encontrada para este grupo.'
            })

        # Preparar dados para gráfico do Simulador III (personalizado)
        source = ColumnDataSource(data=dict(
            ronda_labels=[f"Ronda {r.ronda}" for r in rondas],
            percentagens=[r.percentagem for r in rondas],
            p1=[r.p1 for r in rondas],
            p2=[r.p2 for r in rondas],
            p3=[r.p3 for r in rondas],
            p4=[r.p4 for r in rondas],
            p5=[r.p5 for r in rondas],
            valor1=[r.valor1 for r in rondas],
            valor2=[r.valor2 for r in rondas],
            valor3=[r.valor3 for r in rondas],
            valor4=[r.valor4 for r in rondas],
        ))

        p = figure(
            x_range=source.data['ronda_labels'],
            height=350,
            title=f"Desempenho de {utilizador.nome} por Ronda (Simulador III)",
            toolbar_location=None,
            tools=""
        )

        p.line(x='ronda_labels', y='percentagens', source=source, line_width=2)
        p.circle(x='ronda_labels', y='percentagens', source=source, size=10, color="orange")

        hover = HoverTool(tooltips=[
            ("Ronda", "@ronda_labels"),
            ("p₁", "@p1{0.00}"),
            ("p₂", "@p2{0.00}"),
            ("p₃", "@p3{0.00}"),
            ("p₄", "@p4{0.00}"),
            ("p₅", "@p5{0.00}"),
            ("Valor 1", "@valor1{0.00}"),
            ("Valor 2", "@valor2{0.00}"),
            ("Valor 3", "@valor3{0.00}"),
            ("Valor 4", "@valor4{0.00}"),
            ("% ótimo", "@percentagens{0.00}")])
        
        p.add_tools(hover)

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
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.conf import settings 
import random

def generate_seed():
    return random.randint(1, 1000000)



class InstanciaSimulador(models.Model):
    TIPO_CHOICES = [
        ('I', 'Simulador Escolha Intertemporal de consumo'),
        ('II', 'Simulador Esocolha Intertemporal de investimento'),
    ]

    nome = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    simulador_id = models.UUIDField(default=uuid.uuid4, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)  # novo campo
    seed = models.IntegerField(default=generate_seed)  # novo campo para a semente



# -----------------------
# MODELO DO SIMULADOR
# -----------------------
class Simulador(models.Model):
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    instancia = models.ForeignKey(InstanciaSimulador, on_delete=models.CASCADE,null=True, blank=True)
    ronda = models.IntegerField()
    y0 = models.FloatField()
    y1 = models.FloatField()
    r = models.FloatField()
    rho = models.FloatField()
    c0 = models.FloatField(null=True, blank=True)
    c1 = models.FloatField(null=True, blank=True)
    s = models.FloatField(null=True, blank=True)
    U0 = models.FloatField(null=True, blank=True)
    U0_max = models.FloatField(null=True, blank=True)
    percentagem = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['instancia', 'ronda']




class SimuladorI(models.Model):
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    instancia = models.ForeignKey(InstanciaSimulador, on_delete=models.CASCADE,null=True, blank=True)
    ronda = models.IntegerField()
    r = models.FloatField()
    A = models.FloatField()
    alpha = models.FloatField()
    delta = models.FloatField()
    investimento = models.FloatField(null=True, blank=True)
    V0 = models.FloatField(null=True, blank=True)
    V0_max = models.FloatField(null=True, blank=True)
    percentagem = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['instancia', 'ronda']


# app/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UtilizadorManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Utilizador(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    idade = models.PositiveIntegerField()
    nacionalidade = models.CharField(max_length=100)
    nome = models.CharField(max_length=100, null=True, blank=True)
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_docente = models.BooleanField(default=False)

    objects = UtilizadorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['idade', 'nacionalidade','nome']

    def __str__(self):
        return self.email

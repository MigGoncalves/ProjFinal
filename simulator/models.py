from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

# -----------------------
# MODELO DO SIMULADOR
# -----------------------
class Simulador(models.Model):
    simulador_id = models.CharField(max_length=36, default=uuid.uuid4)
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
        ordering = ['simulador_id', 'ronda']




class SimuladorI(models.Model):
    simulador_id_i = models.CharField(max_length=36, default=uuid.uuid4)
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
        ordering = ['simulador_id_i', 'ronda']


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
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_docente = models.BooleanField(default=False)

    objects = UtilizadorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['idade', 'nacionalidade']

    def __str__(self):
        return self.email

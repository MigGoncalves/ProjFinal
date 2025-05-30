from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilizador

class UtilizadorAdmin(UserAdmin):
    model = Utilizador
    list_display = ('email', 'is_staff', 'is_superuser', 'is_docente')
    list_filter = ('is_staff', 'is_superuser', 'is_docente', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('idade', 'nacionalidade', 'foto')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_docente', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'idade', 'nacionalidade', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_docente')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(Utilizador, UtilizadorAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from administracion.forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Preguntas, Respuesta, Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administración del usuario personalizado, sin mostrar claves en texto plano."""

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    list_display = ('usuario', 'correo', 'activo', 'admin', 'tecnico')
    list_filter = ('activo', 'admin', 'tecnico')
    search_fields = ('usuario', 'correo', 'rut', 'nombre', 'apellido')
    ordering = ('usuario',)
    filter_horizontal = ()
    readonly_fields = ('last_login',)

    fieldsets = (
        (None, {'fields': ('usuario', 'correo', 'password')}),
        ('Datos personales', {'fields': ('nombre', 'apellido', 'rut', 'fecha_nacimiento')}),
        ('Permisos', {'fields': ('activo', 'admin', 'tecnico')}),
        ('Acceso', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('usuario', 'correo', 'password', 'password_2'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        campos = super().get_readonly_fields(request, obj)
        if obj and obj.pk == request.user.pk:
            return (*campos, 'activo', 'admin')
        return campos

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is None:
            return True
        if obj.pk == request.user.pk:
            return False
        if obj.admin and obj.activo:
            return Usuario.objects.filter(admin=True, activo=True).count() > 1
        return True

    def get_actions(self, request):
        # Se evita el borrado masivo porque el permiso depende de cada usuario.
        acciones = super().get_actions(request)
        acciones.pop('delete_selected', None)
        return acciones


@admin.register(Preguntas)
class PreguntasAdmin(admin.ModelAdmin):
    list_display = ('idPregunta', 'Titulo', 'Usuario', 'categoria', 'estado', 'Fecha_creacion')
    list_filter = ('categoria', 'estado')
    search_fields = ('Titulo', 'Pregunta', 'Usuario__usuario')
    ordering = ('-Fecha_creacion',)


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ('idRespuesta', 'id_Pregunta', 'Usuario', 'FechaHora')
    search_fields = ('Respuesta', 'Usuario__usuario', 'id_Pregunta__Titulo')
    ordering = ('-FechaHora',)

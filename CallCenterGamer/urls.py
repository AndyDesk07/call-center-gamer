"""CallCenterGamer URL Configuration"""

from django.contrib import admin
from django.urls import path
from online.views import Index, Inicio, RegisterView, LoginView, ViewRespuestas, logout_view, ListadoPreguntas, actualizarEstado, obtenerMensajes, consultar_ia
from administracion.views import IndexAdmin, BorrarPregunta, GestionUsuarios, EliminarUsuario, ModificarPregunta, AnalyticsIA, escritorioTecnico


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Index, name='index'),
    path('Administracion/', IndexAdmin, name='administracion'),
    path('Preguntas/', ListadoPreguntas, name='listado_preguntas'),
    path('AnalyticsIA/', AnalyticsIA, name='analytics_ia'),
    path('Login/', LoginView.as_view(), name='Login'),
    path('Register/', RegisterView.as_view(), name='Register'),
    path('Inicio/<int:id>/', Inicio, name='inicio'),
    path('ActualizarEstado/<int:idPregunta>/', actualizarEstado, name='actualizar_estado'),
    path('ConsultarIA/', consultar_ia, name='consultar_ia'),
    path('EscritorioTecnico/', escritorioTecnico, name='escritorio_tecnico'),

    # Usar vista personalizada para logout
    path('Logout/', logout_view, name='Logout'),

    path('Respuesta/<int:idUser>/<int:idPregunta>/', ViewRespuestas, name='respuestas'),
    path('BorrarPregunta/<int:idUser>/<int:idPregunta>/', BorrarPregunta, name='borrar_pregunta'),
    path('GestionUsuarios/', GestionUsuarios, name='gestion_usuarios'),
    path('EliminarUsuario/<int:idUser>/', EliminarUsuario, name='eliminar_usuario'),
    path('ModificarPregunta/<int:idPregunta>/', ModificarPregunta, name='modificar_pregunta'),
    path('ObtenerMensajes/<int:idPregunta>/', obtenerMensajes, name='obtener_mensajes'),
]

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.http import require_POST
from online.forms import RegisterForm, LoginForm, PreguntasForm, RespuestaForm
from django.views.generic import CreateView, FormView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from online.models import Preguntas, Usuario, Respuesta
from django.http import JsonResponse
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from online.gemini_chat import GeminiSinClaveError, responder_con_gemini

# Vista para la página principal
def Index(request):
    return render(request, "index.html")

# Vista para logout personalizada
@require_POST
def logout_view(request):
    logout(request)
    return redirect('Login')

# Vista de inicio de usuario
@login_required
def Inicio(request, id):
    try:
        User = Usuario.objects.get(id=id)
        if request.user.id != User.id:
            return redirect('/Inicio/' + str(request.user.id) + '/')
        preguntas = Preguntas.objects.filter(Usuario=User)
        now = timezone.now()
        form = PreguntasForm(initial={'Usuario': id, 'Fecha_creacion': now})

        if request.method == "POST":
            form = PreguntasForm(request.POST)
            if form.is_valid():
                pregunta = form.save(commit=False)
                pregunta.Usuario = User
                pregunta.Fecha_creacion = now
                pregunta.save()
                return redirect('/Inicio/' + str(id) + '/')

        return render(request, "inicio.html", {
            "Preguntas": preguntas,
            "form": form,
            "id": id
        })
    except Usuario.DoesNotExist:
        return redirect('/')

# Vista de respuestas (Chat)
@login_required
def ViewRespuestas(request, idUser, idPregunta):
    try:
        pregunta = Preguntas.objects.get(idPregunta=idPregunta)
        if not (
            request.user.id == pregunta.Usuario_id
            or request.user.admin
            or request.user.tecnico
        ):
            return redirect('/Inicio/' + str(request.user.id) + '/')

        now = timezone.now()
        MostrarRespuestas = Respuesta.objects.filter(id_Pregunta=pregunta).order_by('FechaHora')

        form = RespuestaForm(initial={
            'id_Pregunta': idPregunta,
            'Usuario': request.user.id,
            'FechaHora': now
        })

        if request.method == "POST":
            form = RespuestaForm(request.POST)
            if form.is_valid():
                respuesta = form.save(commit=False)
                respuesta.id_Pregunta = pregunta
                respuesta.Usuario = request.user
                respuesta.FechaHora = now
                respuesta.save()
                return redirect('/Respuesta/' + str(idUser) + "/" + str(idPregunta) + '/')

        return render(request, "Respuestas.html", {
            "Pregunta": pregunta,
            "form": form,
            "Respuestas": MostrarRespuestas
        })
    except Preguntas.DoesNotExist:
        return redirect('/')

# Vistas basadas en clases
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        user = form.save()
        login(request, user)
        if user.admin:
            return redirect('/Administracion/')
        return redirect('/Inicio/' + str(user.id) + '/')

class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        usuario = form.cleaned_data.get("Usuario")
        password = form.cleaned_data.get("password")
        remember_me = form.cleaned_data.get('remember_me', False)

        user = authenticate(request, username=usuario, password=password)
        
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)

            if user.admin:
                return redirect('/Administracion/')
            elif user.tecnico:
                return redirect('/EscritorioTecnico/')
            else:
                return redirect('/Inicio/' + str(user.id) + '/')
                
        form.add_error(None, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)
    
# Vista de listado de preguntas con busqueda y filtros
@login_required
def ListadoPreguntas(request):
    if not (request.user.admin or request.user.tecnico):
        return redirect('/Inicio/' + str(request.user.id) + '/')
    
    query=request.GET.get('q','')
    categoria=request.GET.get('categoria', '')
    estado=request.GET.get('estado','')

    preguntas=Preguntas.objects.all().order_by('-Fecha_creacion')

    if query:
        preguntas=preguntas.filter(Titulo__icontains=query)
    if categoria:
        preguntas=preguntas.filter(categoria=categoria)
    if estado:
        preguntas=preguntas.filter(estado=estado)

    return render(request, "listado_preguntas.html",{
        "Preguntas":preguntas,
        "query":query,
        "categoria":categoria,
        "estado":estado,
        "categorias":Preguntas.CATEGORIAS,
        "estados":Preguntas.ESTADOS,
    })

# Actualizar estado rápido desde el listado
@login_required
def actualizarEstado(request, idPregunta):
    if not (request.user.admin or request.user.tecnico):
        return redirect('/Inicio/' + str(request.user.id) + '/')
    
    if request.method == 'POST':
        pregunta = get_object_or_404(Preguntas, idPregunta=idPregunta)
        nuevo_estado = request.POST.get('estado')
        
        estados_validos = [estado[0] for estado in Preguntas.ESTADOS]
        if nuevo_estado in estados_validos:
            pregunta.estado = nuevo_estado
            pregunta.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'nuevo_estado': nuevo_estado})
            
    return redirect('/Preguntas/')

# Obtener mensajes para el chat en tiempo real
@login_required
def obtenerMensajes(request, idPregunta):
    try:
        pregunta = Preguntas.objects.get(idPregunta=idPregunta)
        if not (
            request.user.id == pregunta.Usuario_id
            or request.user.admin
            or request.user.tecnico
        ):
            return JsonResponse({'error': 'No tienes permiso para ver este ticket'}, status=403)

        respuestas = Respuesta.objects.filter(id_Pregunta=pregunta).order_by('FechaHora')
        
        lista_mensajes = []
        
        # Agregamos la pregunta inicial (CONVERTIMOS LA HORA A LOCAL)
        lista_mensajes.append({
            'id': f"preg_{pregunta.idPregunta}",
            'usuario': pregunta.Usuario.usuario,
            'es_mio': pregunta.Usuario.id == request.user.id,
            'es_tecnico': pregunta.Usuario.tecnico or pregunta.Usuario.admin,
            'mensaje': pregunta.Pregunta,
            'fecha': timezone.localtime(pregunta.Fecha_creacion).strftime('%d-%m-%Y %H:%M')
        })
        
        # Agregamos las respuestas (CONVERTIMOS LA HORA A LOCAL)
        for r in respuestas:
            lista_mensajes.append({
                'id': f"resp_{r.idRespuesta}",
                'usuario': r.Usuario.usuario,
                'es_mio': r.Usuario.id == request.user.id,
                'es_tecnico': r.Usuario.tecnico or r.Usuario.admin,
                'mensaje': r.Respuesta,
                'fecha': timezone.localtime(r.FechaHora).strftime('%d-%m-%Y %H:%M')
            })
            
        return JsonResponse({'mensajes': lista_mensajes})
    except Preguntas.DoesNotExist:
        return JsonResponse({'error': 'No existe'}, status=404)

# Asistente virtual con Gemini
@login_required
@require_POST
def consultar_ia(request):
    consulta_original = request.POST.get('consulta', '').strip()
    if not consulta_original:
        return JsonResponse({'error': 'Debes escribir una consulta'}, status=400)
    if len(consulta_original) > 1000:
        return JsonResponse({'error': 'La consulta no puede superar los 1000 caracteres'}, status=400)

    try:
        respuesta = responder_con_gemini(consulta_original)
    except GeminiSinClaveError:
        return JsonResponse({
            'error': 'El asistente no está configurado. Consulta con el administrador.'
        }, status=503)
    except ValueError:
        return JsonResponse({
            'error': 'No pude generar una respuesta. Intenta de nuevo o crea un ticket.'
        }, status=502)
    except Exception:
        return JsonResponse({
            'error': 'No pude conectarme con el asistente. Intenta más tarde o crea un ticket.'
        }, status=503)

    return JsonResponse({'respuesta': respuesta})

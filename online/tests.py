from django.test import TestCase
from django.test import override_settings
from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from online.models import Preguntas, Respuesta, Usuario
from online.forms import RegisterForm
from unittest.mock import MagicMock, patch
import json


class ConversationAccessTests(TestCase):
    def setUp(self):
        self.owner = self.create_user('owner', 'owner@example.com')
        self.other = self.create_user('other', 'other@example.com')
        self.question = Preguntas.objects.create(
            Titulo='Consulta',
            Pregunta='No inicia el juego',
            Fecha_creacion=timezone.now(),
            Usuario=self.owner,
        )

    def create_user(self, username, email, **fields):
        user = Usuario.objects.create(
            usuario=username,
            correo=email,
            **fields,
        )
        user.set_password('test-password-123')
        user.save()
        return user

    def test_user_cannot_view_another_users_conversation(self):
        self.client.force_login(self.other)

        response = self.client.get(
            reverse('respuestas', args=[self.other.id, self.question.idPregunta])
        )

        self.assertRedirects(response, f'/Inicio/{self.other.id}/')

    def test_user_cannot_read_another_users_messages_api(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('obtener_mensajes', args=[self.question.idPregunta])
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('mensajes', response.json())

    def test_owner_and_technician_can_read_messages_api(self):
        tecnico = self.create_user('tecnico', 'tecnico@example.com', tecnico=True)
        for usuario in (self.owner, tecnico):
            with self.subTest(usuario=usuario.usuario):
                self.client.force_login(usuario)
                response = self.client.get(
                    reverse('obtener_mensajes', args=[self.question.idPregunta])
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json()['mensajes']), 1)

    def test_admin_and_technician_can_view_conversations(self):
        for username, email, role in (
            ('admin', 'admin@example.com', {'admin': True}),
            ('tech', 'tech@example.com', {'tecnico': True}),
        ):
            with self.subTest(role=username):
                user = self.create_user(username, email, **role)
                self.client.force_login(user)
                response = self.client.get(
                    reverse('respuestas', args=[user.id, self.question.idPregunta])
                )
                self.assertEqual(response.status_code, 200)

    def test_reply_uses_url_question_not_tampered_hidden_question(self):
        another_question = Preguntas.objects.create(
            Titulo='Otra consulta',
            Pregunta='No hay audio',
            Fecha_creacion=timezone.now(),
            Usuario=self.other,
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('respuestas', args=[self.owner.id, self.question.idPregunta]),
            {
                'Respuesta': 'Prueba reiniciar el juego.',
                'id_Pregunta': another_question.idPregunta,
                'Usuario': self.other.id,
                'FechaHora': timezone.now().isoformat(),
            },
        )

        self.assertRedirects(
            response,
            f'/Respuesta/{self.owner.id}/{self.question.idPregunta}/',
        )
        respuesta = Respuesta.objects.get()
        self.assertEqual(respuesta.id_Pregunta_id, self.question.idPregunta)
        self.assertEqual(respuesta.Usuario_id, self.owner.id)

    def test_logout_requires_post(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('Logout'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_inactive_users_cannot_log_in(self):
        self.owner.activo = False
        self.owner.save()

        response = self.client.post(
            reverse('Login'),
            {'Usuario': self.owner.usuario, 'password': 'test-password-123'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertTrue(response.context['form'].non_field_errors())

    def test_ticket_category_is_saved(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('inicio', args=[self.owner.id]),
            {
                'Titulo': 'Sin sonido',
                'Pregunta': 'Mi computador no reproduce audio',
                'categoria': 'Hardware',
                'Usuario': self.other.id,  # La vista impide suplantar al dueño.
                'Fecha_creacion': timezone.now().isoformat(),
            },
        )
        self.assertRedirects(response, f'/Inicio/{self.owner.id}/')
        nueva = Preguntas.objects.get(Titulo='Sin sonido')
        self.assertEqual(nueva.categoria, 'Hardware')
        self.assertEqual(nueva.Usuario_id, self.owner.id)

    def test_technician_can_filter_and_change_ticket_state(self):
        tecnico = self.create_user('tecnico2', 'tecnico2@example.com', tecnico=True)
        self.question.categoria = 'Redes'
        self.question.save()
        self.client.force_login(tecnico)

        cambio = self.client.post(
            reverse('actualizar_estado', args=[self.question.idPregunta]),
            {'estado': 'En proceso'},
        )
        self.assertRedirects(cambio, '/Preguntas/')
        self.question.refresh_from_db()
        self.assertEqual(self.question.estado, 'En proceso')

        listado = self.client.get(reverse('listado_preguntas'), {
            'categoria': 'Redes', 'estado': 'En proceso', 'q': 'Consulta'
        })
        self.assertEqual(list(listado.context['Preguntas']), [self.question])

    def test_client_cannot_change_ticket_state(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse('actualizar_estado', args=[self.question.idPregunta]),
            {'estado': 'Cerrada'},
        )
        self.assertRedirects(response, f'/Inicio/{self.other.id}/')
        self.question.refresh_from_db()
        self.assertEqual(self.question.estado, 'Abierto')

    def test_register_form_validates_rut_check_digit(self):
        datos = {
            'usuario': 'nuevo', 'correo': 'nuevo@example.com',
            'rut': '12.345.678-5', 'password': 'clave-segura-123',
            'password_2': 'clave-segura-123',
        }
        formulario = RegisterForm(datos)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['rut'], '12345678-5')

        datos['rut'] = '12.345.678-9'
        formulario = RegisterForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn('rut', formulario.errors)


class DjangoAdminTests(TestCase):
    def setUp(self):
        self.administrador = Usuario.objects.create_user(
            correo='administrador@example.com',
            usuario='administrador',
            password='clave-segura-123',
            admin=True,
        )
        self.client.force_login(self.administrador)

    def test_modelos_aparecen_en_django_admin(self):
        respuesta = self.client.get(reverse('admin:index'))
        self.assertEqual(respuesta.status_code, 200)
        for modelo in ('usuario', 'preguntas', 'respuesta'):
            with self.subTest(modelo=modelo):
                ruta = reverse(f'admin:online_{modelo}_changelist')
                self.assertContains(respuesta, ruta)
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_crear_usuario_desde_admin_guarda_hash(self):
        respuesta = self.client.post(reverse('admin:online_usuario_add'), {
            'usuario': 'nuevo_admin',
            'correo': 'nuevo_admin@example.com',
            'password': 'clave-nueva-123',
            'password_2': 'clave-nueva-123',
            '_save': 'Guardar',
        })
        self.assertEqual(respuesta.status_code, 302)
        nuevo = Usuario.objects.get(usuario='nuevo_admin')
        self.assertTrue(nuevo.check_password('clave-nueva-123'))
        self.assertNotEqual(nuevo.password, 'clave-nueva-123')

    def test_administrador_no_puede_desactivarse_o_eliminarse(self):
        administrador_modelo = admin.site._registry[Usuario]
        solicitud = RequestFactory().get('/admin/online/usuario/')
        solicitud.user = self.administrador
        campos = administrador_modelo.get_readonly_fields(solicitud, self.administrador)
        self.assertIn('activo', campos)
        self.assertIn('admin', campos)
        self.assertFalse(
            administrador_modelo.has_delete_permission(solicitud, self.administrador)
        )


class GeminiChatTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            usuario='jugador',
            correo='jugador@example.com',
            password='clave-segura-123',
        )
        self.url = reverse('consultar_ia')

    def test_requiere_inicio_de_sesion(self):
        respuesta = self.client.post(self.url, {'consulta': 'Hola'})
        self.assertEqual(respuesta.status_code, 302)

    def test_no_acepta_metodo_get(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    @patch('online.views.responder_con_gemini')
    def test_valida_consulta_vacia_y_larga(self, consultar):
        self.client.force_login(self.usuario)
        for texto in ('', '   ', 'x' * 1001):
            with self.subTest(consulta=texto[:12]):
                respuesta = self.client.post(self.url, {'consulta': texto})
                self.assertEqual(respuesta.status_code, 400)
        consultar.assert_not_called()

    @override_settings(GEMINI_API_KEY='')
    def test_avisa_si_falta_la_clave(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, {'consulta': 'Mi juego no abre'})
        self.assertEqual(respuesta.status_code, 503)
        self.assertIn('configurado', respuesta.json()['error'])

    @override_settings(GEMINI_API_KEY='clave-de-prueba')
    @patch('online.gemini_chat.urlopen')
    def test_envia_solo_el_mensaje_escrito_y_devuelve_respuesta(self, abrir_url):
        Preguntas.objects.create(
            Titulo='Ticket privado',
            Pregunta='Contenido privado de un ticket guardado',
            Fecha_creacion=timezone.now(),
            Usuario=self.usuario,
        )
        conexion = MagicMock()
        conexion.read.return_value = json.dumps({
            'candidates': [{'content': {'parts': [{'text': 'Revisa tus controladores.'}]}}]
        }).encode('utf-8')
        abrir_url.return_value.__enter__.return_value = conexion

        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, {'consulta': 'Mi juego no abre'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['respuesta'], 'Revisa tus controladores.')

        solicitud = abrir_url.call_args.args[0]
        enviado = json.loads(solicitud.data.decode('utf-8'))
        self.assertEqual(enviado['contents'], [
            {'role': 'user', 'parts': [{'text': 'Mi juego no abre'}]}
        ])
        self.assertNotIn('Contenido privado', json.dumps(enviado))
        self.assertEqual(solicitud.get_method(), 'POST')

    @override_settings(GEMINI_API_KEY='clave-de-prueba')
    @patch('online.gemini_chat.urlopen', side_effect=TimeoutError())
    def test_falla_de_conexion_sin_mostrar_error_interno(self, abrir_url):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, {'consulta': 'Mi juego no abre'})
        self.assertEqual(respuesta.status_code, 503)
        self.assertNotIn('TimeoutError', str(respuesta.json()))

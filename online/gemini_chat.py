"""Consultas del asistente virtual mediante la API de Gemini."""

import json
from urllib.request import Request, urlopen

from django.conf import settings


MODELO = "gemini-3.5-flash-lite"
URL_API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent"


class GeminiSinClaveError(Exception):
    """No se configuró la clave de acceso a Gemini."""


def responder_con_gemini(consulta):
    """Envía a Gemini solamente la consulta escrita en el chat."""
    if not settings.GEMINI_API_KEY:
        raise GeminiSinClaveError()

    datos = {
        "systemInstruction": {
            "parts": [{"text": (
                "Eres el asistente virtual de CallCenterGamer, un servicio de soporte "
                "para problemas de videojuegos, computadores y conexiones. "
                "Responde en español, de manera breve, clara y práctica. "
                "Si no sabes algo, dilo. Nunca pidas contraseñas ni datos sensibles. "
                "Si no puedes resolverlo, sugiere crear un ticket de soporte."
            )}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": consulta}]}
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
        },
    }

    solicitud = Request(
        URL_API,
        data=json.dumps(datos).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
        method="POST",
    )

    with urlopen(solicitud, timeout=20) as respuesta:
        contenido = json.loads(respuesta.read().decode("utf-8"))

    candidatos = contenido.get("candidates") or []
    if not candidatos:
        raise ValueError("Gemini no entregó candidatos de respuesta")
    partes = (candidatos[0].get("content") or {}).get("parts") or []
    texto = "\n".join(
        p.get("text", "") for p in partes if p.get("text") and not p.get("thought")
    ).strip()
    if not texto:
        raise ValueError("Gemini no entregó una respuesta de texto")
    return texto

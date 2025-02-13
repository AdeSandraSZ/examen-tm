#tasks\views.py
import requests
import pandas as pd
from unidecode import unidecode
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


API_AUTH_URL = "http://104.154.142.250/apis/exam/auth"
API_POSITIONS_URL = "http://104.154.142.250/apis/exam/positions"
USER_CREDENTIALS = {"user": "csm", "password": "exam1csm"}

def get_api_token():    
    response = requests.post(API_AUTH_URL, json=USER_CREDENTIALS)
    if response.status_code == 200:
        return response.json().get("data", {}).get("jwt")
    return None

def fetch_positions_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_POSITIONS_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

@login_required(login_url="login") 
def index(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "Authentication failed"}, status=401)
    
    data = fetch_positions_data(token)

    usuario_es_agente = request.user.groups.filter(name="Agentes").exists()
    
    return render(request, "tasks/index.html", {"data": data, "es_agente": usuario_es_agente})

def exportExcel(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "La autenticación falló"}, status=401)

    data = fetch_positions_data(token)
    df = pd.DataFrame(data)

    filter_criteria = request.GET.get("query", "").lower()
    if filter_criteria:
        df = df[df.apply(lambda row: filter_criteria in row.to_string().lower(), axis=1)]

    # Creacion del archivo Excel
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=positions.xlsx"
    df.to_excel(response, index=False)
    return response

def generate_chart(data, key, title, color, sort_ascending=True):
    counts = {}
    for item in data:
        value = item.get(key, "Unknown").strip()
        normalized_value = unidecode(value.lower().title())
        counts[normalized_value] = counts.get(normalized_value, 0) + 1

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=not sort_ascending)
    labels, values = zip(*sorted_items) if sorted_items else ([], [])

    plt.figure(figsize=(12, 8))
    plt.barh(labels, values, color=color)
    plt.xlabel("Frecuencia")
    plt.ylabel(key.title())
    plt.title(title)

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    plt.close()
    return buffer

"""Esto genera los estados ordenados de menor a mayor"""
def statesChart(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "La autenticación falló"}, status=401)

    data = fetch_positions_data(token)
    buffer = generate_chart(data, key="state", title="Estados (Ordenados de menor a mayor)", color="#41194D", sort_ascending=True)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

"""Esto genera los ciudades ordenados de mayor a menor."""
def citiesChart(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "La autenticación falló"}, status=401)

    data = fetch_positions_data(token)
    buffer = generate_chart(data, key="country", title="Ciudades (Ordenados de mayor a menor)", color="blue", sort_ascending=False)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

def fetch_positions(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "Authentication failed"}, status=401)

    data = fetch_positions_data(token)
    return JsonResponse({"data": data})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Usuario o/y Contraseña incorrectas")
    
    return render(request, "tasks/login.html")

def logout_view(request):
    logout(request)
    return redirect('/login/')

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors

def generar_pdf(request):
    token = get_api_token()
    if not token:
        return JsonResponse({"error": "La autenticación falló"}, status=401)

    data = fetch_positions_data(token)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="dashboard.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elementos = []

    styles = getSampleStyleSheet()
    titulo = Paragraph("<b>Reporte del Dashboard</b>", styles["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    tabla_datos = [["Eco", "Latitud", "Longitud", "Estado", "Ciudad"]]
    for item in data:
        tabla_datos.append([
            item.get("eco", "N/A"),
            item.get("lat", "N/A"),
            item.get("lng", "N/A"),
            item.get("state", "N/A"),
            item.get("country", "N/A"),
        ])

    estilo_tabla = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.pink),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ])

    tabla = Table(tabla_datos, colWidths=[80, 80, 80, 100, 100])  # Esto es para ajustar ancho de columnas
    tabla.setStyle(estilo_tabla)
    elementos.append(tabla)
    elementos.append(Spacer(1, 20))

    def crear_grafica(data, key, titulo, color):
        conteo = {}
        for item in data:
            valor = item.get(key, "Desconocido").strip()
            conteo[valor] = conteo.get(valor, 0) + 1

        labels, valores = zip(*sorted(conteo.items(), key=lambda x: x[1], reverse=True)) if conteo else ([], [])
        
        plt.figure(figsize=(8, 5))
        plt.barh(labels, valores, color=color)
        plt.xlabel("Cantidad")
        plt.ylabel(key.title())
        plt.title(titulo)
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        plt.close()
        return buffer

    buffer_estado = crear_grafica(data, "state", "Distribución por Estado", "#41194D")
    imagen_estado = Image(buffer_estado, width=400, height=250)
    elementos.append(Paragraph("<b>Gráfico de Estado</b>", styles["Heading2"]))
    elementos.append(Spacer(1, 10))
    elementos.append(imagen_estado)
    elementos.append(Spacer(1, 20))

    buffer_ciudad = crear_grafica(data, "country", "Distribución por Ciudad", "blue")
    imagen_ciudad = Image(buffer_ciudad, width=400, height=250)
    elementos.append(Paragraph("<b>Gráfico de Ciudades</b>", styles["Heading2"]))
    elementos.append(Spacer(1, 10))
    elementos.append(imagen_ciudad)
    elementos.append(Spacer(1, 20))

    doc.build(elementos)
    return response

@staff_member_required
def admin_panel(request):
    return redirect("/admin/")


from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", views.index, name="index"),
    path("export/", views.exportExcel, name="export_to_excel"),
    path("states_chart/", views.statesChart, name="states_chart"),  # Gráfico para estados
    path("cities_chart/", views.citiesChart, name="cities_chart"),  # Gráfico para ciudades
    path("login/", views.login_view, name="login"),  # Ruta para login
    path("logout/", LogoutView.as_view(next_page='/login/'), name="logout"),
    path("fetch-positions/", views.fetch_positions, name="fetch_positions"), 
    path('generar-pdf/', views.generar_pdf, name='generarPdf'),
    path("admin-panel/", views.admin_panel, name="admin_panel"),


]




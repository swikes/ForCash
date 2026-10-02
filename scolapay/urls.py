from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ScolaPay — administration"
admin.site.site_title = "ScolaPay"
admin.site.index_title = "Gestion des écoles clientes"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ecoles.urls")),
]

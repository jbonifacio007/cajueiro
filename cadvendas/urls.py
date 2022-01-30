from django.urls import path

from .views import IndexView
from .views import registrar_venda, grafico, lotes_marcados, busca, busca_cor


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('registrar_venda/', registrar_venda, name='registrar_venda'),
    path('grafico/', grafico, name='grafico'),
    path('lotes_marcados/', lotes_marcados, name='lotes_marcados'),
    path('busca/', busca, name='busca'),
    path('<str:cor>', busca_cor, name='busca_cor'),

    #    path('teste/', TesteView.as_view(), name='teste')

]

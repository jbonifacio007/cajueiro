from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Venda,Lote,Cliente,Cotatotal

from django.db.models import Sum

from .forms import VendaForm

import random

from django.db.models.functions import Concat
from django.db.models import Q, Value
from django.core.paginator import Paginator





def grafico(request):
    tipos = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, c.nome,count(v.id) qtd, '#ff0000' cor from cadvendas_venda v "
        "right join cadvendas_corretor c "
        "on c.id = v.corretor_id "
        "group by c.nome ")
    cores = ['#0000ff','#ff0000','#0066cc','#009933','#ff0aff','#00ff00']

    i = 0
    for tipo in tipos:
        number_of_colors = 8
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                 for i in range(number_of_colors)]

        tipo.cor = color[i]
        i = i + 1
        if 1 > 8:
            i = 0



    tipos2 = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, c.nome,count(v.id) qtd, '#ff0000' cor from cadvendas_venda v "
        "right join cadvendas_cliente c "
        "on c.id = v.cliente_id "
        "group by c.nome ")

    cores = ['#0000ff','#ff0000','#0066cc','#009933','#ff0aff','#00ff00']

    i = 0
    for tipo in tipos2:
        number_of_colors = 8
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                 for i in range(number_of_colors)]

        tipo.cor = color[i]
        i = i + 1
        if 1 > 8:
            i = 0



    return render(request, "grafico.html", {'tipos' : tipos, 'tipos2' : tipos2})



def random_color():
    number_of_colors = 8
    color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(number_of_colors)]
    return color

@login_required
def registrar_venda(request):

    form = VendaForm

    if request.method == "POST":
        form = VendaForm(request.POST)

        if form.is_valid():
          venda =  form.save(commit=False)

          venda.quitado = True
          venda.usuario = request.user


          l = Lote.objects.get(id=venda.lote.id)

          l.largura = 88
          l.save()

          venda.save()

          messages.success(
              request,
              "Venda registrada com sucesso"
          )

          return redirect("index")



    context = {
        "nome_pagina": "RegistrarVenda",
        "form": form
    }

    return render(request, "registrar_venda.html", context)


# Create your views here.
class IndexView(TemplateView):

    template_name = 'index.html'

#    vendas2 = Venda.objects.raw('SELECT * FROM cadvendas_venda')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)


#        context['vendas'] = Venda.objects.order_by('-data_venda').all()
        context['vendas'] = Venda.objects.raw("select row_number() OVER (PARTITION by 0 order by ven.data_venda desc) sequencia, id, "
                                            "CASE WHEN SUBSTRING(RIGHT(to_char( ven.valor, '99G999G990D99'),3),1,1) = ',' THEN"
                                            " 	to_char( ven.valor, '99G999G990D99')"
                                            "ELSE "
                                            "	replace( "
                                            " 	replace( "
                                            "	replace(to_char( ven.valor, '99G999G990D99'),',','#') "
                                            "		   ,'.',',') "
                                            "		   ,'#','.') "
                                            " END valor_form "
                                            ",TO_CHAR(data_venda, 'DD/MM/YYYY') dt_venda  "  
                                            ",ven.* "
                                            "from cadvendas_venda ven "
                                            "order by ven.data_venda desc")

        context['qtd_vendas'] = Venda.objects.all().count()
        context['qtd_clientes'] = Cliente.objects.all().count()

        valor_temp = Lote.objects.all().filter(vendido=True).aggregate(total_area=Sum('area'))['total_area'] or 0
        context['lotes_vendidos'] = ajeitaValores(valor_temp)


        valor_temp = Lote.objects.all().filter(areamarcada=True).aggregate(total_area=Sum('area'))['total_area'] or 0
        context['area_lotes_marcados'] = ajeitaValores(valor_temp)

        valor_temp = Lote.objects.all().filter(areamarcada=True).filter(vendido=True).aggregate(total_area=Sum('area'))['total_area'] or 0
        context['area_lotes_marcados_vendidos'] = ajeitaValores(valor_temp)


        context['lotes_nao_vendidos'] = Lote.objects.all().filter(vendido=False).aggregate(total_area_nao=Sum('area'))['total_area_nao'] or 0

        valor_temp_cota = Cotatotal.objects.all().aggregate(total_valor_cota=Sum('areatotal'))['total_valor_cota'] or 0
        context['total_cota'] = ajeitaValores(valor_temp_cota)

        context['vendas2'] = Venda.objects.raw("select row_number() OVER (PARTITION by 0)  id, cor.nome, "

                                               " to_char( sum(ven.valor), '99G999G990D99') total1, "
                                            "CASE WHEN SUBSTRING(RIGHT(to_char( sum(ven.valor), '99G999G990D99'),3),1,1) = ',' THEN"
                                            " 	to_char( sum(ven.valor), '99G999G990D99')"
                                            "ELSE "
                                            "	replace( "
                                            " 	replace( "
                                            "	replace(to_char( sum(ven.valor), '99G999G990D99'),',','#') "
                                            "		   ,'.',',') "
                                            "		   ,'#','.') "
                                            " END total, "

                                               "count(*) qtd, "

                                               " to_char( sum(lot.area), '99G999G990D99') area1, "
                                            "CASE WHEN SUBSTRING(RIGHT(to_char( sum(lot.area), '99G999G990D99'),3),1,1) = ',' THEN"
                                            " 	to_char( sum(lot.area), '99G999G990D99')"
                                            "ELSE "
                                            "	replace( "
                                            " 	replace( "
                                            "	replace(to_char( sum(lot.area), '99G999G990D99'),',','#') "
                                            "		   ,'.',',') "
                                            "		   ,'#','.') "
                                            " END area "


                                               " ,sum(ven.valor)  valor_normal "
                                               'from cadvendas_venda ven '
                                               'inner join cadvendas_corretor cor  on cor.id=ven.corretor_id '
                                               'inner join cadvendas_lote lot  on lot.id=ven.lote_id '
                                               'group by cor.nome ')


        area_cota_qry = Cotatotal.objects.raw('select row_number() OVER (PARTITION by 0)  id, areatotal - (select SUM(area) tam '
                                                   'FROM cadvendas_lote WHERE vendido=True) areacota from cadvendas_cotatotal ')

        for p in area_cota_qry:
            area_cota_var = (p.areacota)

        context['vendas3'] = ajeitaValores(area_cota_var)



        return context

def ajeitaValores(valor):

    valor_final = ' '

    if valor:

      valor_str = '{:,}'.format(valor)
      pos_ponto = valor_str.find('.')
      tam = len(valor_str)

      parte_inteira_str = (valor_str[0:pos_ponto])
      parte_decimal_str = (valor_str[pos_ponto + 1:tam])
      parte_inteira_str = (parte_inteira_str.replace(',', '.'))
      parte_decimal_str = (parte_decimal_str[0:2])
      valor_final = '{0},{1}'.format(parte_inteira_str, parte_decimal_str)

    return valor_final


def lotes_marcados(request):
    context = {
    }

    context['vendas'] = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0 order by ven.data_venda desc) sequencia, id, "
        "CASE WHEN SUBSTRING(RIGHT(to_char( ven.valor, '99G999G990D99'),3),1,1) = ',' THEN"
        " 	to_char( ven.valor, '99G999G990D99')"
        "ELSE "
        "	replace( "
        " 	replace( "
        "	replace(to_char( ven.valor, '99G999G990D99'),',','#') "
        "		   ,'.',',') "
        "		   ,'#','.') "
        " END valor_form "
        ",TO_CHAR(data_venda, 'DD/MM/YYYY') dt_venda  "
        ",ven.* "
        "from cadvendas_venda ven "
        "order by ven.data_venda desc")

    return render(request, "lotes_marcados.html", context)

def busca(request):
    termo = request.GET.get('termo')
    campos = Concat('nome', Value(' '), 'nome')

    if termo is None or not(termo):
        #        raise Http404()
        messages.add_message(request, messages.ERROR, 'Campo Termo não pode ficar vazio!')
        return redirect('index')
    else:
        messages.add_message(request, messages.SUCCESS, 'Consulta realizada com sucesso!')


    contatos = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0 order by ven.data_venda desc) sequencia, id, "
        "CASE WHEN SUBSTRING(RIGHT(to_char( ven.valor, '99G999G990D99'),3),1,1) = ',' THEN"
        " 	to_char( ven.valor, '99G999G990D99')"
        "ELSE "
        "	replace( "
        " 	replace( "
        "	replace(to_char( ven.valor, '99G999G990D99'),',','#') "
        "		   ,'.',',') "
        "		   ,'#','.') "
        " END valor_form "
        ",TO_CHAR(data_venda, 'DD/MM/YYYY') dt_venda  "
        ",ven.* "
        "from cadvendas_venda ven "
        "order by ven.data_venda desc")


#    print(contatos.query)

    paginator = Paginator(contatos, 5)

    page = request.GET.get('p')
    contatos = paginator.get_page(page)

    return render(request,'lotes_marcados.html',{
        'vendas': contatos
    })

"""

def busca_cor(request, cor):

    contatos = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0 order by ven.data_venda desc) sequencia, ven.id, "
        "CASE WHEN SUBSTRING(RIGHT(to_char( ven.valor, '99G999G990D99'),3),1,1) = ',' THEN"
        " 	to_char( ven.valor, '99G999G990D99')"
        "ELSE "
        "	replace( "
        " 	replace( "
        "	replace(to_char( ven.valor, '99G999G990D99'),',','#') "
        "		   ,'.',',') "
        "		   ,'#','.') "
        " END valor_form "
        ",TO_CHAR(data_venda, 'DD/MM/YYYY') dt_venda  "
        ",ven.* "
        "from cadvendas_venda ven "
		"    inner join cadvendas_lote lot "
		"	  on ven.lote_id = lot.id "
        " where lot.cor = '" + cor +   "'  "
        "order by ven.data_venda desc")


#    print(contatos.query)

    paginator = Paginator(contatos, 5)

    page = request.GET.get('p')
    contatos = paginator.get_page(page)

    return render(request,'lotes_marcados.html',{
        'vendas': contatos
    })

"""


def busca_cor(request, cor):

    cor_style = ''
    cor_tit = ''
    filtro    = ' areamarcada '

    if cor == 'RosaV' or cor == 'RosaN' or cor == 'RosaT':
        cor_tit = 'Rosa'
    if cor == 'VerdeV' or cor == 'VerdeN' or cor == 'VerdeT':
        cor_tit = 'Verde'


    if cor == 'RosaV' or cor == 'RosaN':
        cor_style = 'hotpink'
    if cor == 'VerdeV' or cor == 'VerdeN':
        cor_style = 'limegreen'

    if not cor == 'Todos':
        if cor == 'VerdeT':
            filtro = " lot.cor = 'Verde' "
        else:
            if cor == 'VerdeV':
                filtro = " lot.cor = 'Verde' and lot.vendido  "
            else:
                filtro = " lot.cor = 'Verde' and not lot.vendido  "

        if cor == 'RosaT':
            filtro = " lot.cor = 'Rosa' "
        else:
            if cor == 'RosaV':
                filtro = " lot.cor = 'Rosa' and lot.vendido  "
            else:
                if cor == 'RosaN':
                    filtro = " lot.cor = 'Rosa' and not lot.vendido  "



    contatos = Lote.objects.raw(

        "select sequencia, t.id,  numero_lote "
        "      ,COALESCE(valor_form, '') valor_form "
        "      ,COALESCE(dt_venda, '')   dt_venda "
        "      ,nome_cli "
        "      ,cor_estilo "
        "from "
        "( "

        "		select "
        "		row_number() OVER (PARTITION by 0 order by qua.numero, lot.numero ) sequencia, lot.id"
        "		,lot.numero as numero_lote"
        "		,COALESCE(ven.valor,0) valor"
        "		,CASE WHEN SUBSTRING(RIGHT(to_char( ven.valor, '99G999G990D99'),3),1,1) = ',' THEN"
        "         	to_char( ven.valor, '99G999G990D99')"
        "        ELSE "
        "        	replace( "
        "         	replace( "
        "        	replace(to_char( ven.valor, '99G999G990D99'),',','#') "
        "        		   ,'.',',') "
        "        		   ,'#','.') "
        "         END valor_form "
        "        ,COALESCE(TO_CHAR(data_venda, 'DD/MM/YYYY'),'') dt_venda  "
        "        ,COALESCE(cli.nome,'') nome_cli  "
        "        ,lot.cor  "
        "		,CASE WHEN lot.Cor = 'Rosa' THEN 'hotpink' "
		"	          WHEN lot.Cor = 'Verde' THEN 'limegreen' " 
        "             ELSE 'black' END cor_estilo "
        "        ,lot.vendido "
        "        from cadvendas_lote lot "
        "		    inner join cadvendas_quadra qua"
        "			  on qua.id = lot.quadra_id "
        "		    left join cadvendas_venda ven"
        "			  on ven.lote_id = lot.id "
        "		    left join cadvendas_cliente cli"
        "			  on ven.cliente_id = cli.id "
#        "         where lot.cor = '" + cor + "'  "
#        "         where lot.cor in " + cor_busca + " "
        "         where " + filtro + " "
        "        order by qua.numero, lot.numero "
        " ) t "

    )


    quant = 0
    for p in contatos:
        quant = quant + 1

#    print(contatos.query)

    paginator = Paginator(contatos, 15)

    page = request.GET.get('p')
    contatos = paginator.get_page(page)

    return render(request,'lotes_marcados.html',{
        'vendas': contatos,
        'cor_tit': cor_tit,
        'cor_style': cor_style,
        'quant': quant,
    })


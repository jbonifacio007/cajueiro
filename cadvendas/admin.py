from django.contrib import admin
from . import models
from . import views
from django.utils.html import format_html

# Register your models here.


class VendaInline(admin.TabularInline):
    model = models.Venda
    list_display = ['lote','cliente','corretor','valor','formapagamento','quitado']
    exclude = ['usuario']
#    readonly_fields = ('lote','cliente','corretor','valor','formapagamento','quitado','usuario','obs')
    extra = 0

class LoteInline(admin.TabularInline):
    model = models.Lote
    extra = 1
#    readonly_fields = ('area',)

class QuadraAdmin(admin.ModelAdmin):
    inlines = [
        LoteInline
    ]
    list_display = ['numero','qtd_lotes','get_tamanho']
    readonly_fields = ('qtd_lotes','tamanho')

    def get_tamanho(self,obj):
        return views.ajeitaValores(obj.tamanho)

    get_tamanho.short_description = 'Tamanho'

class LoteAdmin(admin.ModelAdmin):
#    list_display = ['quadra','numero','largura','comprimento','vendido','area','areaMarcada','cor_html','esquina']
    list_display = ['quadra','numero_html','largura','comprimento','vendido','area','areamarcada','esquina']

    def cor_html(self, obj):
        if obj.cor == 'Verde':
            color = 'limegreen'
        elif obj.cor == 'Rosa':
            color = 'hotpink'
        else:
            color = 'black'
        return format_html('<strong><p style="color: {}">{}</p></strong>'.format(color, obj.cor))


    def numero_html(self, obj):
        if obj.cor == 'Verde':
            color = 'limegreen'
        elif obj.cor == 'Rosa':
            color = 'hotpink'
        else:
            color = 'black'
        return format_html('<strong><p style="color: {}">{}</p></strong>'.format(color, obj.numero))

    cor_html.short_description = 'Cor'
    numero_html.short_description = 'Número'


#    if ['esquina']:
#       readonly_fields = ('area',)
#    fieldsets = [("Name", {"fields": (("lastname", "firstname", "middlename"), "clocknumber")}),
#                 ]

class VendaAdmin(admin.ModelAdmin):
    list_display = ['lote','cliente','corretor','get_valor','formapagamento','quitado','usuario','get_data_venda']
    list_editable = ('formapagamento', 'quitado')
    search_fields = ['cliente__nome','cliente__cpf']
    exclude = ['usuario']
#   tira o butao add
#    def has_add_permission(self, request):
#        return False
    def get_data_venda(self,obj):
        return obj.data_venda.strftime('%d/%m/%Y')

    def get_valor(self,obj):
        return views.ajeitaValores(obj.valor)

    get_valor.short_description = 'Valor'
    get_data_venda.short_description = 'Data Venda'

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        super().save_model(request, obj, form, change)

#        c = models.Cliente.objects.get(id=obj.cliente.id)
#        c.comprou = True
#        c.save()



"""  exemplo de como salvar alguma coisa em outro model
        l = models.Lote.objects.get(id=obj.lote.id)
        l.largura = 17
        l.save()
"""

def validaCliente(idVenda,idCliente):
    venda_qry = models.Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, count(*) qtd "
        "FROM cadvendas_venda WHERE id <> " + str(idVenda) + " and cliente_id = " + str(idCliente))

    qtd = 0
    for p in venda_qry:
        qtd = (p.qtd)

    valor = False
    if (qtd==0):
        valor = True
    return valor



class CorretorAdmin(admin.ModelAdmin):
    list_display = ['nome','endereco']

class ClienteAdmin(admin.ModelAdmin):

    inlines = [
        VendaInline
    ]

#    list_display = ['nome','cpf','status','endereco','comprou']
    list_display = ['nome','cpf','endereco','comprou']
    search_fields = ['cpf','nome']
    list_filter = ('comprou',)
# linha abaixo usada para atribuir o usuário logado para o usuário da venda
# esse procedimento abaixo só serve se estiver usando TabularInline no caso estou usando a model venda
    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            list_venda = formset.save(commit=False)
            for venda in list_venda:
                venda.usuario = request.user
        return super().save_related(request, form, formsets, change)

# Abaixo só um exemplo de com usar cores e o comando format_html. Depos tem que colocar no list_display
    def status(self, obj):
        vStatus = ''
        if obj.comprou == True:
            color = 'green'
            vStatus = 'Comprou'
        elif obj.comprou == False:
            color = 'red'
            vStatus = 'Não Comprou'
        else:
            vStatus = 'Comprando'
            color = 'orange'
        return format_html('<strong><p style="color: {}">{}</p></strong>'.format(color, vStatus))

class CotatotalAdmin(admin.ModelAdmin):
    list_display = ['descricao','get_areatotal']

    def get_areatotal(self,obj):
        return views.ajeitaValores(obj.areatotal)

    get_areatotal.short_description = 'Area Total'



admin.site.site_header = 'Administração Village Cajueiro'
admin.site.site_title = 'Village Cajueiro'
admin.site.index_title = 'Gerenciamento de Vendas'

admin.site.register(models.Quadra, QuadraAdmin)
admin.site.register(models.Cliente, ClienteAdmin)
admin.site.register(models.Lote, LoteAdmin)
admin.site.register(models.Venda, VendaAdmin)
admin.site.register(models.Corretor, CorretorAdmin)
admin.site.register(models.Formapagamento)
admin.site.register(models.Cotatotal, CotatotalAdmin)


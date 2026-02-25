"""
-- CRIA A FUNCAO QUE ATUALIZA a qtd_lotes e o tamanho da quadra quando inseridos o alterados na tabela lote
CREATE OR REPLACE FUNCTION fc_atualizar_qtd_lote()
  RETURNS trigger AS
$BODY$
DECLARE
    n REAL DEFAULT 0;
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_quadra WHERE id = NEW.quadra_id ) THEN
        UPDATE cadvendas_quadra
		   SET qtd_lotes = (SELECT COUNT(*) QTD FROM cadvendas_lote WHERE quadra_id = NEW.quadra_id),
		       tamanho   = (SELECT SUM(area) TAM FROM cadvendas_lote WHERE quadra_id = NEW.quadra_id)
        WHERE id = NEW.quadra_id;
    END IF;

    RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;

-- CRIA A FUNCAO QUE ATUALIZA a qtd_lotes e o tamanho da quadra quando deleta um lote na tabela lote
CREATE OR REPLACE FUNCTION fc_atualizar_totais_lote_del()
  RETURNS trigger AS
$BODY$
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_quadra WHERE id = OLD.quadra_id ) THEN
        UPDATE cadvendas_quadra
		   SET qtd_lotes = (SELECT COUNT(*) QTD FROM cadvendas_lote WHERE quadra_id = OLD.quadra_id),
		       tamanho   = (SELECT COALESCE(SUM(area),0) TAM FROM cadvendas_lote WHERE quadra_id = OLD.quadra_id)
        WHERE id = OLD.quadra_id;
    END IF;
    RETURN OLD;
END;
$BODY$
LANGUAGE plpgsql;

--ATUALIZA O CAMPO VENDIDO NA TABELA LOTE
CREATE OR REPLACE FUNCTION fc_lote_vendido()
  RETURNS trigger AS
$BODY$
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_lote WHERE id = NEW.lote_id ) THEN
        UPDATE cadvendas_lote SET vendido = true WHERE id = NEW.lote_id;
    END IF;

    IF (NEW.lote_id <> OLD.lote_id) AND NOT(OLD.lote_id IS NULL)  THEN
        UPDATE cadvendas_lote SET vendido = false WHERE id = OLD.lote_id;
    END IF;

    RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;

CREATE FUNCTION public.fc_lote_vendido_del()
    RETURNS trigger
AS $BODY$
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_lote WHERE id = OLD.lote_id ) THEN
        UPDATE cadvendas_lote SET vendido = false WHERE id = OLD.lote_id;
    END IF;
    RETURN OLD;
END;
$BODY$
LANGUAGE plpgsql;


--ATUALIZA O CAMPO comprou NA TABELA cliente
CREATE OR REPLACE FUNCTION fc_cliente_comprou()
  RETURNS trigger AS
$BODY$
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_cliente WHERE id = NEW.cliente_id ) THEN
        UPDATE cadvendas_cliente SET comprou = true WHERE id = NEW.cliente_id;
    END IF;

    IF (NEW.cliente_id <> OLD.cliente_id) AND NOT(OLD.cliente_id IS NULL)
	   AND NOT EXISTS(SELECT 1 FROM cadvendas_venda WHERE id <> OLD.id AND cliente_id = OLD.cliente_id )  THEN
        UPDATE cadvendas_cliente SET comprou = false WHERE id = OLD.cliente_id;
    END IF;

    RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.fc_cliente_comprou_del()
    RETURNS trigger
AS $BODY$
BEGIN
    IF EXISTS( SELECT 1 FROM cadvendas_cliente WHERE id = OLD.cliente_id )
	   AND NOT EXISTS(SELECT 1 FROM cadvendas_venda WHERE id <> OLD.id AND cliente_id = OLD.cliente_id )  THEN
        UPDATE cadvendas_cliente SET comprou = false WHERE id = OLD.cliente_id;
    END IF;
    RETURN OLD;
END;
$BODY$
LANGUAGE plpgsql;



---As seguintes TRIGGER tem que ser criadas no banco
CREATE TRIGGER trg_atualizar_qtd_lote_quadra
AFTER INSERT OR UPDATE ON cadvendas_lote FOR EACH ROW EXECUTE PROCEDURE fc_atualizar_qtd_lote();

CREATE TRIGGER trg_atualizar_totais_quadra_DEL
AFTER DELETE ON cadvendas_lote FOR EACH ROW EXECUTE PROCEDURE fc_atualizar_totais_lote_del();

CREATE TRIGGER trg_atualizar_lote_vendido
AFTER INSERT OR UPDATE ON cadvendas_venda FOR EACH ROW EXECUTE PROCEDURE fc_lote_vendido();

CREATE TRIGGER trg_atualizar_lote_vendido_del
    AFTER DELETE
    ON cadvendas_venda
    FOR EACH ROW
    EXECUTE PROCEDURE fc_lote_vendido_del();

CREATE TRIGGER trg_atualizar_cliente_comprou
AFTER INSERT OR UPDATE ON cadvendas_venda FOR EACH ROW EXECUTE PROCEDURE fc_cliente_comprou();

CREATE TRIGGER trg_atualizar_cliente_comprou_del
    AFTER DELETE
    ON cadvendas_venda
    FOR EACH ROW
    EXECUTE PROCEDURE fc_cliente_comprou_del();


"""

"""
# essa linha aqui era pra criar um campo calculado
def _get_valor(self):
    if self.largura and self.comprimento:
        return self.largura * self.comprimento
    else:
        return 0


area = property(_get_valor)
"""



from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError


# Create your models here.

class Base(models.Model):
    criado = models.DateField('Criação', auto_now_add=True)
    modificado = models.DateField('Atualização', auto_now=True)

    class Meta:
        abstract = True

class Quadra(Base):
    numero = models.CharField('Numero', max_length=5)
    qtd_lotes = models.DecimalField('Qtd lotes', default=0, decimal_places=2,max_digits=10)
    tamanho = models.DecimalField('Tamanho', default=0, decimal_places=2,max_digits=10)

    # pegar o numero da quadra gravado no banco pra comparar com o que vai gravar

    def clean(self):
        numQuadra = ''
        if self.id:
            numQuadra = pegaNumQuadraBanco(self.id)

        if not(numQuadra == self.numero):
           if validaQuadra(self.numero):
               raise ValidationError("Quadra Já Existe!")

    class Meta:
        verbose_name = 'Quadra'
        verbose_name_plural = 'Quadras'
        ordering = ['numero']

    def __str__(self):
        return self.numero

class Lote(Base):
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, default=0)
    numero = models.CharField('Numero', max_length=3)
    largura = models.DecimalField('Largura', default=0, decimal_places=2,max_digits=10)
    comprimento = models.DecimalField('Comprimento', default=0, decimal_places=2,max_digits=10)
    vendido = models.BooleanField('Vendido?', default=False, editable=False)
    areamarcada = models.BooleanField('Área Marcada?', default=False)
    esquina = models.BooleanField('Esquina?', default=False)
    area = models.DecimalField('Area', default=0, decimal_places=2,max_digits=10)

    COR_CHOICES = (
        ('Rosa', 'Rosa'),
        ('Verde', 'Verde'),
    )
    cor = models.CharField('Cor', blank=True, max_length=40, choices = COR_CHOICES)



    def clean(self):

        if not(self.quadra.id):
            raise ValidationError({'numero': ('Quadra Ainda Não Gravada!')})

        if not(self.numero.isdigit()):
            raise ValidationError({'numero': ('Digite só números!')})

        self.numero = '{:0>2}'.format(self.numero)
        numLote = '0'
        vMaxPerda = pegaMaxPerda()
        # pegar o numero do lote gravado no banco pra comparar com o que vai gravar
        if self.id:
            numLote = pegaNumLoteBanco(self.id)

        if self.esquina:
            if (self.area == 0):
                raise ValidationError({'area': ('Digite a Área!')})
        if self.esquina:
            if (self.area > (self.largura * self.comprimento)):
                raise ValidationError({'area': ('Area Não pode SER MAIOR QUE L x C!')})
                #raise ValidationError("Area Não pode SER MAIOR QUE L x C!")

        if not (self.esquina):
            self.area = (self.largura * self.comprimento)

        if not(self.esquina):
            if not(self.area == (self.largura * self.comprimento)):
                raise ValidationError({'area': ('Area Incorreta!')})


        if not(numLote == self.numero):
           if validaLote(self.quadra,self.numero):
               raise ValidationError("Lote Já Existe Nessa quadra!")

        if (self.area < ((self.largura * self.comprimento) - vMaxPerda)):
           raise ValidationError({'area': ('Área muito inferior ao máximo de perda! '+str(vMaxPerda))})


        if (self.areamarcada and not(self.cor) ):
           raise ValidationError({'cor': ('Área Marcada tem que ter COR! ')})

        if (not(self.areamarcada) and (self.cor) ):
           raise ValidationError({'cor': ('Informe a COR só pra Lotes Área Marcada! ')})

    #    def save(self):
#        if not (self.esquina):
#            if not self.id:
#                self.area = (self.largura * self.comprimento)
#            self.area = (self.largura * self.comprimento)

#        super(Lote, self).save()

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['quadra','numero']

    def __str__(self):
        v = "Não Vendido"
        if self.vendido:
          v = "Vendido"
        return f'{self.numero} - {self.quadra.numero} - {v}  '

class Cliente(Base):
    nome = models.CharField('Nome', max_length=100)
    cpf = models.CharField('CPF', max_length=11)
    endereco = models.TextField('Endereço', max_length=200)
    comprou = models.BooleanField('Comprou?', default=False)

    def clean(self):

        if not(self.cpf.isdigit()):
            raise ValidationError({'cpf': ('Digite só números!')})

        if len(self.cpf) < 11:
            raise ValidationError({'cpf': ('Digite 11 dígitos!')})


        if not(validaCPF(self.cpf)):
            raise ValidationError({'cpf': ('CPF inválido!')})

        if not(self.id):
            if (cpfExiste(self.cpf)):
                raise ValidationError({'cpf': ('CPF já cadastrado!')})

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
#        return self.nome
        return  f'{self.nome} - {self.cpf}' 


class Corretor(Base):
    nome = models.CharField('Nome', max_length=100)
    endereco = models.TextField('Endereço', max_length=200)

    class Meta:
        verbose_name = 'Corretor'
        verbose_name_plural = 'Corretores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Formapagamento(Base):
    descricao = models.CharField('Descrição', max_length=100)

    class Meta:
        verbose_name = 'Forma pagamento'
        verbose_name_plural = 'Formas pagamento'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Venda(Base):
    valor = models.DecimalField('Valor', default=0, decimal_places=2,max_digits=12)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    corretor = models.ForeignKey(Corretor, on_delete=models.RESTRICT)
    formapagamento = models.ForeignKey(Formapagamento, on_delete=models.RESTRICT, verbose_name='Forma Pagamento' )
#    lote = models.OneToOneField(Lote,on_delete=models.RESTRICT, null=True, limit_choices_to={'vendido': False})
    lote = models.OneToOneField(Lote,on_delete=models.RESTRICT, null=True)
    data_venda = models.DateField('Data da venda', default=timezone.now)
    quitado = models.BooleanField('Quitado', default=False)
    obs = models.CharField('Obs', max_length=200, null=False)
    usuario = models.ForeignKey(get_user_model(), verbose_name='Usuário',on_delete=models.RESTRICT)


    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    def __str__(self):
        return f'Cliente: {self.cliente.nome} Quadra:{self.lote.quadra} Lote: {self.lote.numero}'

class Cotatotal(Base):
    descricao = models.CharField('Descrição', max_length=100)
    areatotal = models.DecimalField('Area Total', default=0, decimal_places=2,max_digits=12)
    maxperda = models.DecimalField('Máximo de Perda', default=0, decimal_places=2,max_digits=12)

    class Meta:
        verbose_name = 'Cota Total'
        verbose_name_plural = 'Cota Total'

    def __str__(self):
        return self.descricao

def validaLote(quadra,numero):
    lote_qry = Cotatotal.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, count(*) qtd "
        "FROM cadvendas_lote WHERE quadra_id = " + str(quadra.id) + " and numero = '" + numero + "' ")

    for p in lote_qry:
        lote_qry_var = (p.qtd)

    valor = False
    if not(lote_qry_var==0):
        valor = True
    return valor

def cpfExiste(cpf):
    cliente_qry = Cliente.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, count(*) qtd "
        "FROM cadvendas_cliente WHERE cpf = '" + cpf + "' ")

    for p in cliente_qry:
        qtd = (p.qtd)

    valor = False
    if not(qtd==0):
        valor = True
    return valor



def validaQuadra(numero):
    quadra_qry = Cotatotal.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, count(*) qtd "
        "FROM cadvendas_quadra WHERE numero = '" + numero + "' ")

    for p in quadra_qry:
        qtd = (p.qtd)

    valor = False
    if not(qtd==0):
        valor = True
    return valor


def validaCliente(idVenda,idCliente):
    venda_qry = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, count(*) qtd "
        "FROM cadvendas_venda WHERE id <> " + str(idVenda) + " and cliente_id = " + str(idCliente))

    qtd = 0
    for p in venda_qry:
        qtd = (p.qtd)

    valor = False
    if (qtd==0):
        valor = True
    return valor


def pegaNumLoteBanco(id):
    lote_qry = Cotatotal.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, numero "
        "FROM cadvendas_lote WHERE id = " + str(id) + " ")

    for p in lote_qry:
        lote_numero = (p.numero)

    return lote_numero

def pegaNumQuadraBanco(id):
    quadra_qry = Cotatotal.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, numero "
        "FROM cadvendas_quadra WHERE id = " + str(id) + " ")

    for p in quadra_qry:
        quadra_numero = (p.numero)

    return quadra_numero


def pegaIdClienteBanco(id):
    venda_qry = Venda.objects.raw(
        "select row_number() OVER (PARTITION by 0)  id, cliente_id "
        "FROM cadvendas_venda WHERE id = " + str(id) + " ")

    for p in venda_qry:
        cliente_id = (p.cliente_id)

    return cliente_id


def pegaMaxPerda():
    perda_qry = Cotatotal.objects.raw(
        'select id, maxperda '
        'from cadvendas_cotatotal ')

    vmaxperda = 0
    for p in perda_qry:
        vmaxperda = (p.maxperda)

    return vmaxperda

def validaCPF(cpf):

    novo_cpf = cpf[:-2]                 # Elimina os dois últimos digitos do CPF
    reverso = 10                        # Contador reverso
    total = 0

    # Loop do CPF
    for index in range(19):
        if index > 8:                   # Primeiro índice vai de 0 a 9,
            index -= 9                  # São os 9 primeiros digitos do CPF

        total += int(novo_cpf[index]) * reverso  # Valor total da multiplicação

        reverso -= 1                    # Decrementa o contador reverso
        if reverso < 2:
            reverso = 11
            d = 11 - (total % 11)

            if d > 9:                   # Se o digito for > que 9 o valor é 0
                d = 0
            total = 0                   # Zera o total
            novo_cpf += str(d)          # Concatena o digito gerado no novo cpf

    # Evita sequencias. Ex.: 11111111111, 00000000000...
    sequencia = novo_cpf == str(novo_cpf[0]) * len(cpf)

    # Descobri que sequências avaliavam como verdadeiro, então também
    # adicionei essa checagem aqui

    if cpf == novo_cpf and not sequencia:
        valor = True ##  print('Válido')
    else:
        valor = False ## print('Inválido')

    return valor

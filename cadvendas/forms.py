from django import forms
from .models import Venda


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = [
            "cliente","corretor","formapagamento","valor",
            "lote","data_venda","obs"
        ]
        error_messagens ={
            "valor":{
                "required":"Preencha o campo valor"

            },
            "obs": {
            "required": "Preencha a observação"
            },
        }




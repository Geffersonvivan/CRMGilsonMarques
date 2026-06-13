from django import forms
from liderancas.models import Regiao, Cidade
from usuarios.models import Usuario
from .models import Tarefa, Comentario, Promessa


class TarefaForm(forms.ModelForm):
    regiao = forms.ModelChoiceField(
        queryset=Regiao.objects.all().order_by('sigla'),
        required=False,
        label='Região',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_regiao'}),
    )

    class Meta:
        model = Tarefa
        fields = [
            'titulo', 'descricao', 'tipo', 'prioridade',
            'responsavel', 'participantes',
            'regiao', 'cidade', 'prazo', 'observacoes',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'prioridade': forms.Select(attrs={'class': 'form-input'}),
            'responsavel': forms.Select(attrs={'class': 'form-input'}),
            'participantes': forms.SelectMultiple(attrs={'class': 'form-input', 'size': 5}),
            'cidade': forms.Select(attrs={'class': 'form-input', 'id': 'id_cidade'}),
            'prazo': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    field_order = [
        'titulo', 'descricao', 'tipo', 'prioridade',
        'responsavel', 'participantes',
        'regiao', 'cidade', 'prazo', 'observacoes',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuarios_sistema = Usuario.objects.exclude(
            vinculo__in=['coordenador', 'cabo', 'replicador']
        ).order_by('first_name')
        self.fields['responsavel'].queryset = usuarios_sistema
        self.fields['participantes'].queryset = usuarios_sistema

        if self.instance.pk and self.instance.cidade_id:
            self.fields['regiao'].initial = self.instance.cidade.regiao_id
            self.fields['cidade'].queryset = Cidade.objects.filter(
                regiao=self.instance.cidade.regiao
            ).order_by('nome')
        else:
            regiao_id = self.data.get('regiao') if self.data else None
            if regiao_id:
                try:
                    self.fields['cidade'].queryset = Cidade.objects.filter(
                        regiao_id=int(regiao_id)
                    ).order_by('nome')
                except (ValueError, TypeError):
                    self.fields['cidade'].queryset = Cidade.objects.none()
            else:
                self.fields['cidade'].queryset = Cidade.objects.none()


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Escreva um comentário...',
            }),
        }


class PromessaForm(forms.ModelForm):
    regiao = forms.ModelChoiceField(
        queryset=Regiao.objects.all().order_by('sigla'),
        label='Região',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_regiao'}),
    )

    field_order = [
        'regiao', 'cidade', 'bairro_linha', 'descricao', 'solicitante',
        'responsavel', 'status', 'data_registro', 'data_entrega', 'observacoes',
    ]

    class Meta:
        model = Promessa
        fields = [
            'cidade', 'bairro_linha', 'descricao', 'solicitante',
            'responsavel', 'status', 'data_registro', 'data_entrega', 'observacoes',
        ]
        widgets = {
            'cidade': forms.Select(attrs={'class': 'form-input', 'id': 'id_cidade'}),
            'bairro_linha': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Bairro ou linha (ex.: Linha Guairapo)'}),
            'descricao': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'O que foi pedido / prometido'}),
            'solicitante': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Quem pediu (liderança, morador...)'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Quem vai entregar'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'data_registro': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}, format='%Y-%m-%d'),
            'data_entrega': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_registro'].input_formats = ['%Y-%m-%d']
        self.fields['data_entrega'].input_formats = ['%Y-%m-%d']
        if self.instance.pk and self.instance.cidade_id:
            self.fields['regiao'].initial = self.instance.cidade.regiao_id
            self.fields['cidade'].queryset = Cidade.objects.filter(
                regiao=self.instance.cidade.regiao
            ).order_by('nome')
        else:
            regiao_id = self.data.get('regiao') if self.data else self.initial.get('regiao')
            if regiao_id:
                try:
                    self.fields['cidade'].queryset = Cidade.objects.filter(regiao_id=int(regiao_id)).order_by('nome')
                except (ValueError, TypeError):
                    self.fields['cidade'].queryset = Cidade.objects.none()
            else:
                self.fields['cidade'].queryset = Cidade.objects.none()

    def clean(self):
        cleaned = super().clean()
        # entregue exige data de entrega (preenche com hoje se faltar)
        if cleaned.get('status') == 'entregue' and not cleaned.get('data_entrega'):
            from django.utils import timezone
            cleaned['data_entrega'] = timezone.localdate()
        return cleaned

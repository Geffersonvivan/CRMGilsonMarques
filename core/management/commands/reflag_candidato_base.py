"""
Re-marca o flag `is_candidato` nos resultados eleitorais já carregados (TSE) para o
candidato da campanha atual (settings.CAMPANHA['TSE_TERMO_BUSCA']) e repopula
`Cidade.votos_referencia_2022` somando os votos dele no cargo-base.

Útil quando os dados do TSE já estão no banco e só é preciso (re)apontar quem é o
candidato — sem rebaixar o pacote do TSE. Idempotente. Roda também depois de
`limpar_dados_campanha` (que zera votos_referencia_2022).

Uso:
    python manage.py reflag_candidato_base
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from liderancas.models import Cidade
from mapa.models import ResultadoCandidato, ResultadoZona


class Command(BaseCommand):
    help = 'Re-marca is_candidato pelo termo de busca e repopula votos_referencia_2022.'

    def handle(self, *args, **options):
        termo = settings.CAMPANHA['TSE_TERMO_BUSCA']
        cargo = settings.CAMPANHA['TSE_CARGO_BASE']
        ano = settings.CAMPANHA['TSE_ANO_BASE']

        with transaction.atomic():
            ResultadoCandidato.objects.filter(is_candidato=True).update(is_candidato=False)
            ResultadoZona.objects.filter(is_candidato=True).update(is_candidato=False)
            rc = ResultadoCandidato.objects.filter(
                candidato_nome__icontains=termo).update(is_candidato=True)
            rz = ResultadoZona.objects.filter(
                candidato_nome__icontains=termo).update(is_candidato=True)

            Cidade.objects.update(votos_referencia_2022=0)
            por_cidade = (
                ResultadoCandidato.objects
                .filter(eleicao__ano=ano, eleicao__turno=1,
                        eleicao__tipo=cargo, is_candidato=True)
                .values('cidade_id').annotate(total=Sum('votos'))
            )
            cidades = 0
            for item in por_cidade:
                cidades += Cidade.objects.filter(id=item['cidade_id']).update(
                    votos_referencia_2022=item['total'])

        total = (ResultadoCandidato.objects
                 .filter(eleicao__ano=ano, eleicao__tipo=cargo, is_candidato=True)
                 .aggregate(s=Sum('votos'))['s'] or 0)
        self.stdout.write(self.style.SUCCESS(
            f'is_candidato re-marcado por "{termo}": {rc} candidato / {rz} zona. '
            f'votos_referencia_2022 em {cidades} cidades ({total} votos, cargo {cargo} {ano}).'))

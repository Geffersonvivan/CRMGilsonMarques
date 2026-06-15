"""
Importa o nº REAL de MEIs (optantes SIMEI) por município e SETA meis_ativos.
Substitui a estimativa derivada do PIB.

A fonte (Receita/SINAC "Optantes por UF e Município - Simei") é um portal ASP.NET
sem API; os dados são extraídos manualmente para um arquivo e injetados aqui:

  - JSON: lista de pares [nome_municipio, total]  (ex.: o dump do scraping)
  - CSV : duas colunas  nome;total  (separador ; ou ,)

    python manage.py import_mei_real --arquivo /caminho/mei_sc.json [--dry-run]

O casamento é por NOME normalizado (maiúsculas, sem acento), pois o SINAC não
traz o código IBGE.
"""
import csv
import json
import unicodedata
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from liderancas.models import Cidade
from mapa.models import IndicadorMunicipal

ANO = 2022


_CONECTIVOS = {'DE', 'DA', 'DO', 'DAS', 'DOS'}


def _norm(s):
    s = unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().upper()
    s = ''.join(ch if ch.isalnum() else ' ' for ch in s)  # hífen/pontuação -> espaço
    return ' '.join(w for w in s.split() if w not in _CONECTIVOS)


def _num(v):
    return int(str(v).replace('.', '').replace(',', '').strip() or 0)


class Command(BaseCommand):
    help = 'Importa MEIs reais (optantes SIMEI) por município de um arquivo JSON/CSV'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', required=True, help='JSON [[nome,total],...] ou CSV nome;total')
        parser.add_argument('--dry-run', action='store_true')

    def _ler(self, path):
        raw = Path(path).read_text(encoding='utf-8')
        pares = []
        if path.endswith('.json'):
            for row in json.loads(raw):
                if isinstance(row, (list, tuple)) and len(row) >= 2:
                    pares.append((row[0], row[1]))
        else:
            sep = ';' if ';' in raw.splitlines()[0] else ','
            for row in csv.reader(raw.splitlines(), delimiter=sep):
                if len(row) >= 2:
                    pares.append((row[0], row[1]))
        return pares

    def handle(self, *args, **opts):
        path = opts['arquivo']
        if not Path(path).exists():
            raise CommandError(f'Arquivo não encontrado: {path}')
        dry = opts['dry_run']

        # nome normalizado -> contagem (ignora cabeçalho/linhas não numéricas)
        fonte = {}
        for nome, total in self._ler(path):
            n = _norm(nome)
            if not n or n in ('MUNICIPIO', 'TOTAL', 'TOTAL GERAL'):
                continue
            try:
                fonte[n] = _num(total)
            except ValueError:
                continue
        self.stdout.write(f'Arquivo: {len(fonte)} municípios com valor.')

        ind_by_cid = {i.cidade_id: i for i in IndicadorMunicipal.objects.filter(ano_referencia=ANO)}
        mud, sem_match, amostra = 0, [], []
        to_update = []
        usados = set()
        for c in Cidade.objects.all():
            val = fonte.get(_norm(c.nome))
            if val is None:
                sem_match.append(c.nome)
                continue
            usados.add(_norm(c.nome))
            ind = ind_by_cid.get(c.id)
            if not ind:
                continue
            if ind.meis_ativos != val:
                if len(amostra) < 5:
                    amostra.append(f'{c.nome}: {ind.meis_ativos} -> {val}')
                ind.meis_ativos = val
                to_update.append(ind)
                mud += 1
        if not dry and to_update:
            IndicadorMunicipal.objects.bulk_update(to_update, ['meis_ativos'])

        for a in amostra:
            self.stdout.write('   ' + a)
        if sem_match:
            self.stdout.write(self.style.WARNING(
                f'  Sem correspondência ({len(sem_match)}): ' + ', '.join(sem_match[:10])))
        nao_usados = [k for k in fonte if k not in usados]
        if nao_usados:
            self.stdout.write(self.style.WARNING(
                f'  No arquivo mas não casaram ({len(nao_usados)}): ' + ', '.join(nao_usados[:10])))
        verbo = 'mudariam' if dry else 'atualizados'
        self.stdout.write(self.style.SUCCESS(f'{mud} indicadores {verbo} com MEI REAL (SINAC).'))

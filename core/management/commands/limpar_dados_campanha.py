"""
Zera os dados da REDE DA CAMPANHA para começar a base de uma nova candidatura,
PRESERVANDO os dados territoriais/eleitorais de Santa Catarina (cidades, regiões,
IBGE, resultados TSE) — que são fatos do estado e independem do candidato.

APAGA (rede / PII / operacional):
    Lideranca, Voluntario, InteracaoLog,
    Tarefa (+ Comentario, AnexoComentario, TarefaHistorico),
    Compromisso, Roteiro (+ RoteiroPonto), Evento, Oportunidade,
    Notificacao, AliadoChapa (chapa de 2026 da campanha anterior).
    Também zera as colunas partido-específicas de Cidade
    (presidente_diretorio, num_vereadores_partido, controle, votos_referencia_2022).

MANTÉM:
    MacroRegiao, Regiao, Cidade (territorial), Bairro, ZonaEleitoral,
    Eleicao, ResultadoCandidato/ResultadoZona (TSE), IndicadorMunicipal (IBGE),
    core.Configuracao, e os usuários (Usuario) — incluindo superusuários.

Uso:
    python manage.py limpar_dados_campanha            # dry-run (só conta o que apagaria)
    python manage.py limpar_dados_campanha --sim      # executa de fato

⚠ Destrutivo. Faça backup antes (o comando copia db.sqlite3 automaticamente em dev).
  Em produção (Postgres), rode só com backup + OK explícito (CLAUDE.md §9.4).
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from liderancas.models import (
    Cidade, Lideranca, Voluntario, InteracaoLog,
)
from tarefas.models import Tarefa, Comentario, AnexoComentario, TarefaHistorico
from agenda.models import Compromisso, Roteiro, RoteiroPonto, Evento
from oportunidades.models import Oportunidade
from mapa.models import AliadoChapa
from notificacoes.models import Notificacao


class Command(BaseCommand):
    help = 'Zera a rede da campanha preservando o mapa territorial/eleitoral de SC.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sim', action='store_true',
            help='Executa de fato (sem isso, apenas mostra o que seria apagado).',
        )

    def handle(self, *args, **options):
        executar = options['sim']

        # Dependentes primeiro (FKs PROTECT em registros de pessoa/rede).
        # Modelos com soft-delete usam all_objects p/ apagar inclusive os ocultos.
        etapas = [
            ('Logs de interação', InteracaoLog.objects.all()),
            ('Anexos de comentário', AnexoComentario.objects.all()),
            ('Comentários', Comentario.objects.all()),
            ('Histórico de tarefas', TarefaHistorico.objects.all()),
            ('Tarefas', Tarefa.objects.all()),
            ('Pontos de roteiro', RoteiroPonto.objects.all()),
            ('Roteiros', Roteiro.objects.all()),
            ('Compromissos', Compromisso.objects.all()),
            ('Eventos', Evento.objects.all()),
            ('Oportunidades', Oportunidade.objects.all()),
            ('Notificações', Notificacao.objects.all()),
            ('Apoiadores/cabos/coordenadores', Lideranca.all_objects.all()),
            ('Voluntários', Voluntario.all_objects.all()),
            ('Aliados de chapa', AliadoChapa.objects.all()),
        ]

        self.stdout.write(self.style.MIGRATE_HEADING(
            'Limpeza da rede da campanha (mapa de SC é preservado)'))
        for rotulo, qs in etapas:
            self.stdout.write(f'  {qs.count():>7}  {rotulo}')

        cidades_afetadas = Cidade.objects.exclude(
            presidente_diretorio='', num_vereadores_partido=0,
            controle='', votos_referencia_2022=0,
        ).count()
        self.stdout.write(f'  {cidades_afetadas:>7}  Cidades a ter colunas de partido zeradas')

        if not executar:
            self.stdout.write(self.style.WARNING(
                '\nDRY-RUN: nada foi apagado. Rode com --sim para executar.'))
            return

        # Backup do sqlite (dev). Em Postgres isso não se aplica.
        db = settings.DATABASES['default']
        if 'sqlite' in db.get('ENGINE', ''):
            origem = Path(db['NAME'])
            if origem.exists():
                destino = origem.with_name(origem.name + '.bak-limpeza')
                shutil.copy2(origem, destino)
                self.stdout.write(self.style.SUCCESS(f'Backup do banco: {destino}'))

        with transaction.atomic():
            for rotulo, qs in etapas:
                n, _ = qs.delete()
                self.stdout.write(f'  apagado: {rotulo} ({n} linhas)')

            atualizadas = Cidade.objects.update(
                presidente_diretorio='', num_vereadores_partido=0,
                controle='', controle_manual=False,
                adversario_nome='', adversario_partido='',
                votos_referencia_2022=0,
            )
            self.stdout.write(f'  colunas de partido zeradas em {atualizadas} cidades')

        self.stdout.write(self.style.SUCCESS(
            '\nConcluído. Rode import_tse para repopular a base eleitoral da nova candidatura.'))

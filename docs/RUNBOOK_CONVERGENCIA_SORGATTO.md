# Runbook — convergir a produção do Sorgatto para o código unificado

> Contexto: `origin/main` (CRM_Leandro_Sorgatto) tem **auto-deploy no Railway**
> (produção ativa, Postgres + volume). A linha dele divergiu do unificado em 8
> commits (auditados em 05/07/2026 — o unificado é superset; ver Seção 3).
> **Nada aqui é executado sem backup + OK explícito (CLAUDE.md §9.4).**

## 1. O único conflito real: migrações renomeadas

A linha do Sorgatto tem `agenda/0008_eventoanexo` **aplicada** no Postgres.
No unificado o mesmo conteúdo é `agenda/0009_eventoanexo` (o `0008` unificado é
`alter_compromisso_tipo`). Um `migrate` cego tentaria recriar a tabela
`agenda_eventoanexo` → crash. As demais divergências (`liderancas/0018`,
`tarefas/0010`) são só de grafo/dependências — as operações são as mesmas e já
estão aplicadas lá; não afetam banco migrado.

## 2. Procedimento (testar ANTES num dump local)

1. **Backup** do Postgres no Railway (dump + snapshot do volume de media).
2. **Ensaio local**: restaurar o dump num Postgres local e rodar:
   ```
   MARCA=sorgatto DATABASE_URL=<dump-local> python manage.py migrate agenda 0007 --fake
   MARCA=sorgatto DATABASE_URL=<dump-local> python manage.py migrate agenda 0008 --fake   # alter_compromisso_tipo: só choices, sem DDL
   MARCA=sorgatto DATABASE_URL=<dump-local> python manage.py migrate agenda 0009 --fake   # eventoanexo: tabela JÁ existe (era a 0008 deles)
   MARCA=sorgatto DATABASE_URL=<dump-local> python manage.py migrate
   python manage.py check && python manage.py test
   ```
   Obs.: o registro `agenda.0008_eventoanexo` antigo fica órfão em
   `django_migrations` — inofensivo (Django ignora aplicadas sem arquivo).
3. **Sanidade no ensaio**: `auditar_indicadores`, contagens de Lideranca por
   aprovação, mapa com `TSE_CARGO_2026=deputado_estadual` e base federal
   (`reflag_candidato_base` se necessário), smoke E2E (`/tmp/e2e_crm.py`).
4. **Env do serviço Railway**: adicionar `MARCA=sorgatto` (+ conferir
   `MEDIA_ROOT` para o volume). Segredos existentes permanecem.
5. **Janela de deploy**: com OK explícito, push do unificado para
   `origin/main`. O Procfile roda `migrate` no boot — as etapas `--fake` do
   passo 2 precisam ser executadas ANTES via `railway run` (ou um release
   command temporário), senão o boot crasha.
6. **Pós-deploy**: smoke nas rotas principais, conferir mapa/concorrência
   (rivais a estadual), moderação e PWA. Rollback = redeploy do commit
   anterior (`d7be41a`) + restore do dump se alguma migração nova rodou.

## 3. Decisões de produto a confirmar com a campanha Sorgatto

- **Doações**: o unificado REMOVEU o módulo (a Isadora não usa). Se o Sorgatto
  usa Doações em produção, é preciso decidir antes: portar o app de volta como
  feature por config, ou exportar os dados e aposentar. As tabelas dele não
  são apagadas pelas migrações unificadas (ficam órfãs, dados preservados).
- **Promessas (tarefas)**: idem — `0011_delete_promessa` DROPA a tabela no
  `migrate`. Conferir se há dados de Promessa em produção antes (o ensaio do
  passo 2 mostra a contagem).
- Colunas de Lideranças e paleta PL definitiva (`configs/sorgatto.py`).

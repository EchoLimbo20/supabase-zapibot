# Enviador de Mensagens — Z-API + Supabase

Script em Python que lê contatos cadastrados no Supabase e envia, via
WhatsApp (Z-API), a mensagem personalizada:

> Olá, **\<nome_contato>** tudo bem com você?

O envio é limitado a **no máximo 3 contatos por execução** — o script
busca apenas os contatos com `mensagem_enviada = False` e aplica
`limit(3)` na consulta ao Supabase.

## Stack

- Python 3.10+
- [Supabase](https://supabase.com/) (plano gratuito) — banco de contatos
- [Z-API](https://www.z-api.io/) (plano gratuito) — envio de WhatsApp

## Setup da tabela no Supabase

A tabela `contatos` precisa existir com (pelo menos) estas colunas:

| coluna             | tipo        | observação                          |
|---------------------|-------------|---------------------------------------|
| `id`                | int8 / uuid | chave primária                       |
| `nome`              | text        | nome usado na personalização da msg  |
| `telefone`          | text        | formato aceito pela Z-API (ex: `5511999999999`) |
| `mensagem_enviada`  | bool        | default `false`                      |

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha com suas credenciais:

```bash
cp .env.example .env
```

```dotenv
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_API_KEY=sua_anon_key_aqui

ZAPI_INSTANCE_ID=sua_instance_id_aqui
ZAPI_CLIENT_TOKEN=seu_client_token_aqui
```

> ⚠️ O `.env` nunca deve ser commitado — ele já está no `.gitignore`.
> Use sempre a **anon key** do Supabase (não a `service_role`), e
> configure as RLS Policies da tabela `contatos` conforme necessário.

## Como rodar

```bash
# 1. Criar e ativar um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar o .env (ver seção acima)

# 4. Rodar o script
python main.py
```

## O que o script faz

1. Busca no Supabase até 3 contatos com `mensagem_enviada = False`.
2. Para cada contato, envia a mensagem via Z-API (`send-text`).
3. Verifica se o envio deu certo checando se a resposta da Z-API
   contém `messageId` ou `zaapId` (a Z-API não retorna um campo
   "sucesso" explícito).
4. Se o envio deu certo, marca o contato como `mensagem_enviada = True`
   no Supabase, para não reenviar numa próxima execução.
5. Exibe um resumo no terminal com total de enviados e falhas.

## Tratamento de erros

- Timeout ou erro de conexão com a Z-API → contato é contado como
  falha e o script segue para o próximo, sem travar a execução.
- Resposta inesperada da Z-API (não-JSON) → tratado como falha.
- Falha ao atualizar o Supabase após um envio bem-sucedido → o script
  avisa explicitamente no terminal, pois esse contato pode ser
  reenviado numa próxima execução.

## Observação sobre o limite de envios

O limite de 3 é aplicado **por execução** (via `.limit(3)` na query).
Como o script só busca contatos com `mensagem_enviada = False`, depois
de enviar para os 3 primeiros eles deixam de aparecer em execuções
futuras — então, na prática, rodar o script repetidamente não excede
o limite total combinado no desafio, desde que a tabela não receba
novos contatos pendentes além dos 3 originais.
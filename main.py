"""
Enviador de mensagens via WhatsApp (Z-API) para contatos cadastrados no Supabase.
O que o código faz:
- Busca no Supabase os contatos que ainda não receberam mensagem
- Envia uma mensagem de WhatsApp pra cada um, usando a API da Z-API
- Se o envio der certo, marca o contato como 'mensagem_enviada' = True
- Retorna resumo no terminal
"""
import os
import requests

from supabase import create_client
from dotenv import load_dotenv
from colorama import init, Fore, Style
import logging

#Configurar logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_sender.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

init(autoreset=True)
load_dotenv()

#Credenciais
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
token = os.getenv("ZAPI_CLIENT_TOKEN")
instance = os.getenv("ZAPI_INSTANCE_ID")

#Buscar contatos pendentes
#Filtra só quem não recebeu a mensagem e limita 3
contatos = sb.table("contatos").select("*").eq("mensagem_enviada", False).limit(3).execute().data

#Contadores para resumo final de mensagens enviadas e falhas
enviados = 0
falhas = 0

#Enviar
for i, c in enumerate(contatos, start=1):
    msg = f"Olá, {c['nome']} tudo bem com você?"
    logger.info(f"[{i}/{len(contatos)}] Enviando para {c['nome']}...")
    #Faz a chamada pra API da Z-API pra enviar a mensagem de texto e tratamento de erros
    try:
        r = requests.post(
            f"https://api.z-api.io/instances/{instance}/token/{token}/send-text",
            json={"phone": c["telefone"], "message": msg},
            timeout=15
        )
        resposta = r.json()
        
    except requests.exceptions.RequestException as erro:
        logger.error(f"Erro de conexão para {c['nome']}: {erro}")
        falhas += 1
        continue
    
    except ValueError:
        logger.error(f"Resposta inválida da Z-API para {c['nome']}")
        falhas += 1
        continue
    
    if resposta.get("messageId") or resposta.get("zaapId"):
        try:
            sb.table("contatos").update({"mensagem_enviada": True}).eq("id", c["id"]).execute()
            logger.info(f"✓ {c['nome']} marcado como enviado (ID: {resposta.get('messageId')})")
            enviados += 1
            
        except Exception as erro:
            logger.error(f"✗ Falha ao enviar para {c['nome']}")
            enviados += 1
            
    else:
        logger.error(f"✗ Falha ao enviar para {c['nome']}")
        falhas += 1
        
print(f"\n{Fore.CYAN}{Style.BRIGHT}-----------------------------------------------------")
print(f"ENVIADOR DE MENSAGENS - Z-API+SUPABASE")
print(f"{Fore.CYAN}{Style.BRIGHT}-----------------------------------------------------")
print(f"{Fore.YELLOW}→ {len(contatos)} contato(s) pendente(s)\n")
print(f" RESUMO")
print(f"---------------------")
print(f"{Fore.GREEN}Enviados: {enviados}")
print(f"{Fore.RED}Falhas:   {falhas}")
print(f"---------------------\n")
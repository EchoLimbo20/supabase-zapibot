"""
Enviador de mensagens via WhatsApp (Z-API) para contatos cadastrados no Supabase.
O que o código faz:
- Busca no Supabase os contatos que ainda não receberam mensagem
- Envia uma mensagem de WhatsApp pra cada um, usando a API da Z-API
- Se o envio der certo, marca o contato como 'mensagem_enviada' = True
- Retorna resumo no terminal
"""

import requests
from supabase import create_client
import os
from dotenv import load_dotenv
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

#Credenciais
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))
token = os.getenv("ZAPI_CLIENT_TOKEN")
instance = os.getenv("ZAPI_INSTANCE_ID")

#Buscar contatos pendentes
#Filtra só quem não recebeu a mensagem e limita 3
contatos = sb.table("contatos").select("*").eq("mensagem_enviada", False).limit(3).execute().data

print(f"\n{Fore.CYAN}{Style.BRIGHT}-----------------------------------------------------")
print(f"ENVIADOR DE MENSAGENS - Z-API+SUPABASE")
print(f"{Fore.CYAN}{Style.BRIGHT}-----------------------------------------------------{Style.RESET_ALL}")
print(f"{Fore.YELLOW}→ {len(contatos)} contato(s) pendente(s)\n{Style.RESET_ALL}")

#Contadores para resumo final de mensagens enviadas e falhas
enviados = 0
falhas = 0

#Enviar
for i, c in enumerate(contatos, start=1):
    msg = f"Olá, {c['nome']} tudo bem com você?"

    print(f"{Fore.BLUE}[{i}/{len(contatos)}]{Style.RESET_ALL} Enviando para {Fore.WHITE}{Style.BRIGHT}{c['nome']}{Style.RESET_ALL}...", end=" ")

    #Faz a chamada pra API da Z-API pra enviar a mensagem de texto e tratamento de erros
    try:
        r = requests.post(
            f"https://api.z-api.io/instances/{instance}/token/{token}/send-text",
            json={"phone": c["telefone"], "message": msg},
            timeout=15
        )
        resposta = r.json()
        
    except requests.exceptions.RequestException as erro:
        print(f"ERRO (erro de conexão: {erro})")
        falhas += 1
        continue
    
    except ValueError:
        print(f"ERRO (resposta inválida da Z-API)")
        falhas += 1
        continue
    
    if resposta.get("messageId") or resposta.get("zaapId"):
        try:
            sb.table("contatos").update({"mensagem_enviada": True}).eq("id", c["id"]).execute()
            print(f"{Fore.GREEN}Enviado{Style.RESET_ALL}")
            enviados += 1
            
        except Exception as erro:
            print(f"Enviado, mas FALHA ao atualizar Supabase ({erro})")
            enviados += 1
            
    else:
        print(f"Falhou")
        falhas += 1

print(f" RESUMO")
print(f"___________________________{Style.RESET_ALL}")
print(f"{Fore.GREEN}Enviados: {enviados}{Style.RESET_ALL}")
print(f"{Fore.RED}Falhas:   {falhas}{Style.RESET_ALL}")
print(f"___________________________{Style.RESET_ALL}\n")
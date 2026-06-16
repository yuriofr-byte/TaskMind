import json
import os
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

API_KEY = os.environ.get("GEMINI_API_KEY", "")
FICHEIRO_TAREFAS = "tarefas.json"
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")

def carregar_tarefas():
    if os.path.exists(FICHEIRO_TAREFAS):
        with open(FICHEIRO_TAREFAS, "r") as f:
            return json.load(f)
    return []

def guardar_tarefas(tarefas):
    with open(FICHEIRO_TAREFAS, "w") as f:
        json.dump(tarefas, f, indent=2)

def adicionar_tarefa(titulo, descricao, prazo):
    tarefas = carregar_tarefas()
    tarefa = {
        "id": len(tarefas) + 1,
        "titulo": titulo,
        "descricao": descricao,
        "prazo": prazo,
        "concluida": False,
        "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    tarefas.append(tarefa)
    guardar_tarefas(tarefas)
    print(f"Tarefa '{titulo}' adicionada com sucesso!")

def priorizar_com_ia(tarefas):
    if not tarefas:
        print("Nao tens tarefas para priorizar!")
        return
    lista = ""
    for t in tarefas:
        if not t["concluida"]:
            lista += f"- ID {t['id']}: {t['titulo']} | Prazo: {t['prazo']} | {t['descricao']}\n"
    prompt = f"""
Es um assistente de produtividade.
Hoje e {datetime.now().strftime("%d/%m/%Y")}.
Analisa estas tarefas e ordena por prioridade para hoje:
{lista}
Para cada tarefa indica:
1. Prioridade (Alta/Media/Baixa)
2. Motivo
3. Ordem sugerida para executar
Responde em portugues de forma clara e objetiva.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    resposta = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    resultado = resposta.json()
    texto = resultado["candidates"][0]["content"]["parts"][0]["text"]
    print("\nTASKMIND - PLANO DO TEU DIA:")
    print("-" * 40)
    print(texto)
    print("-" * 40)

def concluir_tarefa(id_tarefa):
    tarefas = carregar_tarefas()
    for t in tarefas:
        if t["id"] == id_tarefa:
            t["concluida"] = True
            guardar_tarefas(tarefas)
            print(f"Tarefa '{t['titulo']}' marcada como concluida!")
            return
    print("Tarefa nao encontrada!")

def listar_tarefas():
    tarefas = carregar_tarefas()
    if not tarefas:
        print("Nao tens tarefas!")
        return
    print("\nLISTA DE TAREFAS:")
    print("-" * 40)
    for t in tarefas:
        status = "FEITA" if t["concluida"] else "PENDENTE"
        print(f"[{status}] ID {t['id']} - {t['titulo']} | Prazo: {t['prazo']}")
    print("-" * 40)

def enviar_resumo_email():
    tarefas = carregar_tarefas()
    if not tarefas:
        print("Nao tens tarefas para enviar!")
        return
    pendentes = [t for t in tarefas if not t["concluida"]]
    concluidas = [t for t in tarefas if t["concluida"]]
    corpo = f"""
TASKMIND - RESUMO DO DIA
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}

TAREFAS PENDENTES ({len(pendentes)}):
"""
    for t in pendentes:
        corpo += f"- {t['titulo']} | Prazo: {t['prazo']}\n"
    corpo += f"\nTAREFAS CONCLUIDAS ({len(concluidas)}):\n"
    for t in concluidas:
        corpo += f"- {t['titulo']}\n"
    try:
        mensagem = MIMEMultipart()
        mensagem["From"] = EMAIL_REMETENTE
        mensagem["To"] = EMAIL_DESTINO
        mensagem["Subject"] = f"TaskMind - Resumo do dia {datetime.now().strftime('%d/%m/%Y')}"
        mensagem.attach(MIMEText(corpo, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, mensagem.as_string())
            print("Resumo enviado por email com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def menu():
    print("\n" + "=" * 40)
    print("   TASKMIND - ASSISTENTE DE TAREFAS")
    print("=" * 40)
    print("1. Adicionar tarefa")
    print("2. Ver plano do dia com IA")
    print("3. Listar tarefas")
    print("4. Concluir tarefa")
    print("5. Enviar resumo por email")
    print("6. Sair")
    print("=" * 40)
    opcao = input("Escolhe uma opcao: ")
    if opcao == "1":
        titulo = input("Titulo da tarefa: ")
        descricao = input("Descricao: ")
        prazo = input("Prazo (ex: Hoje 14h / Amanha): ")
        adicionar_tarefa(titulo, descricao, prazo)
    elif opcao == "2":
        tarefas = carregar_tarefas()
        priorizar_com_ia(tarefas)
    elif opcao == "3":
        listar_tarefas()
    elif opcao == "4":
        listar_tarefas()
        id_tarefa = int(input("ID da tarefa a concluir: "))
        concluir_tarefa(id_tarefa)
    elif opcao == "5":
        enviar_resumo_email()
    elif opcao == "6":
        print("Ate logo!")
        return False
    return True

while menu():
    pass
FIM
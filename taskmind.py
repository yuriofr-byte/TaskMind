"""TaskMind - Assistente de Tarefas com IA"""
import json
import os
import smtplib
from typing import List, Dict, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY", "")
FICHEIRO_TAREFAS = os.environ.get("FICHEIRO_TAREFAS", "tarefas.json")
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")

# Constants
ENCODING = "utf-8"
MAX_TENTATIVAS_EMAIL = 3

def carregar_tarefas() -> List[Dict]:
    """Carrega as tarefas do arquivo JSON.
    
    Returns:
        List[Dict]: Lista de tarefas. Retorna lista vazia se arquivo não existe ou está inválido.
    """
    if not os.path.exists(FICHEIRO_TAREFAS):
        return []
    
    try:
        with open(FICHEIRO_TAREFAS, "r", encoding=ENCODING) as f:
            conteudo = f.read().strip()
            if not conteudo:
                return []
            return json.loads(conteudo)
    except json.JSONDecodeError:
        print(f"Erro: Arquivo '{FICHEIRO_TAREFAS}' contém JSON inválido. Iniciando com lista vazia.")
        return []
    except IOError as e:
        print(f"Erro ao ler arquivo: {e}")
        return []

def guardar_tarefas(tarefas: List[Dict]) -> bool:
    """Salva as tarefas em arquivo JSON.
    
    Args:
        tarefas: Lista de tarefas a salvar.
        
    Returns:
        bool: True se salvo com sucesso, False caso contrário.
    """
    try:
        with open(FICHEIRO_TAREFAS, "w", encoding=ENCODING) as f:
            json.dump(tarefas, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Erro ao salvar arquivo: {e}")
        return False

def adicionar_tarefa(titulo: str, descricao: str, prazo: str) -> bool:
    """Adiciona uma nova tarefa.
    
    Args:
        titulo: Título da tarefa.
        descricao: Descrição da tarefa.
        prazo: Prazo para completar a tarefa.
        
    Returns:
        bool: True se tarefa foi adicionada com sucesso.
        
    Raises:
        ValueError: Se titulo estiver vazio.
    """
    if not titulo or not titulo.strip():
        raise ValueError("Título da tarefa não pode estar vazio!")
    
    tarefas = carregar_tarefas()
    
    # Calcula o próximo ID
    proximo_id = max([t["id"] for t in tarefas], default=0) + 1
    
    tarefa = {
        "id": proximo_id,
        "titulo": titulo.strip(),
        "descricao": descricao.strip(),
        "prazo": prazo.strip(),
        "concluida": False,
        "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    tarefas.append(tarefa)
    
    if guardar_tarefas(tarefas):
        print(f"Tarefa '{titulo}' adicionada com sucesso!")
        return True
    return False

def priorizar_com_ia(tarefas: List[Dict]) -> Optional[str]:
    """Prioriza tarefas com base em regras heurísticas (sem dependência de API).
    
    Nota: Implementação local sem chamadas à API. Para usar IA real, 
    adicione implementação com requests e configure GEMINI_API_KEY.
    
    Args:
        tarefas: Lista de tarefas a priorizar.
        
    Returns:
        str: Texto com priorização ou None se não houver tarefas.
    """
    if not tarefas:
        print("Não tens tarefas para priorizar!")
        return None
    
    pendentes = [t for t in tarefas if not t["concluida"]]
    if not pendentes:
        print("Todas as tarefas estão concluídas!")
        return None
    
    # Ordenação simples por prazo (heurística)
    ordem_prazos = {"hoje": 0, "agora": 0, "urgente": 0, "amanha": 1, "semana": 2, "mes": 3}
    
    def prioridade(tarefa):
        prazo_lower = tarefa["prazo"].lower()
        for chave, valor in ordem_prazos.items():
            if chave in prazo_lower:
                return valor
        return 999
    
    pendentes_ordenados = sorted(pendentes, key=prioridade)
    
    resultado = "\nTASKMIND - PLANO DO TEU DIA:\n"
    resultado += "-" * 40 + "\n"
    
    for i, t in enumerate(pendentes_ordenados, 1):
        prioridade_str = "ALTA" if i == 1 else "MÉDIA" if i <= len(pendentes_ordenados) // 2 else "BAIXA"
        resultado += f"{i}. [{prioridade_str}] {t['titulo']}\n"
        resultado += f"   Prazo: {t['prazo']}\n"
        resultado += f"   Descrição: {t['descricao']}\n"
    
    resultado += "-" * 40
    print(resultado)
    return resultado

def concluir_tarefa(id_tarefa: int) -> bool:
    """Marca uma tarefa como concluída.
    
    Args:
        id_tarefa: ID da tarefa a concluir.
        
    Returns:
        bool: True se tarefa foi marcada como concluída, False se não foi encontrada.
    """
    if not isinstance(id_tarefa, int) or id_tarefa <= 0:
        print("ID da tarefa inválido!")
        return False
    
    tarefas = carregar_tarefas()
    for t in tarefas:
        if t["id"] == id_tarefa:
            t["concluida"] = True
            guardar_tarefas(tarefas)
            print(f"Tarefa '{t['titulo']}' marcada como concluída!")
            return True
    
    print("Tarefa não encontrada!")
    return False

def listar_tarefas() -> List[Dict]:
    """Lista todas as tarefas.
    
    Returns:
        List[Dict]: Lista de tarefas.
    """
    tarefas = carregar_tarefas()
    if not tarefas:
        print("Não tens tarefas!")
        return []
    
    print("\nLISTA DE TAREFAS:")
    print("-" * 50)
    for t in tarefas:
        status = "✓ CONCLUÍDA" if t["concluida"] else "○ PENDENTE"
        print(f"[{status}] ID {t['id']:2d} - {t['titulo']}")
        print(f"         Prazo: {t['prazo']} | Criada: {t['data_criacao']}")
    print("-" * 50)
    
    return tarefas

def enviar_resumo_email() -> bool:
    """Envia resumo de tarefas por email.
    
    Returns:
        bool: True se email foi enviado com sucesso.
    """
    if not EMAIL_REMETENTE or not EMAIL_SENHA or not EMAIL_DESTINO:
        print("Erro: Variáveis de ambiente de email não configuradas!")
        print("Configure: EMAIL_REMETENTE, EMAIL_SENHA, EMAIL_DESTINO")
        return False
    
    tarefas = carregar_tarefas()
    if not tarefas:
        print("Não tens tarefas para enviar!")
        return False
    
    pendentes = [t for t in tarefas if not t["concluida"]]
    concluidas = [t for t in tarefas if t["concluida"]]
    
    corpo = f"""
TASKMIND - RESUMO DO DIA
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}

TAREFAS PENDENTES ({len(pendentes)}):
"""
    for t in pendentes:
        corpo += f"- {t['titulo']} | Prazo: {t['prazo']}\n"
    
    corpo += f"\nTAREFAS CONCLUÍDAS ({len(concluidas)}):\n"
    for t in concluidas:
        corpo += f"- {t['titulo']}\n"
    
    try:
        mensagem = MIMEMultipart()
        mensagem["From"] = EMAIL_REMETENTE
        mensagem["To"] = EMAIL_DESTINO
        mensagem["Subject"] = f"TaskMind - Resumo do dia {datetime.now().strftime('%d/%m/%Y')}"
        mensagem.attach(MIMEText(corpo, "plain", _charset="utf-8"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, mensagem.as_string())
        
        print("Resumo enviado por email com sucesso!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("Erro: Email ou senha incorretos!")
        return False
    except smtplib.SMTPException as e:
        print(f"Erro ao enviar email: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

def menu() -> bool:
    """Menu interativo para o TaskMind.
    
    Returns:
        bool: False se usuário escolher sair, True caso contrário.
    """
    print("\n" + "=" * 50)
    print("   TASKMIND - ASSISTENTE DE TAREFAS")
    print("=" * 50)
    print("1. Adicionar tarefa")
    print("2. Ver plano do dia com IA")
    print("3. Listar tarefas")
    print("4. Concluir tarefa")
    print("5. Enviar resumo por email")
    print("6. Sair")
    print("=" * 50)
    
    opcao = input("Escolhe uma opção: ").strip()
    
    try:
        if opcao == "1":
            titulo = input("Título da tarefa: ").strip()
            if not titulo:
                print("Título não pode estar vazio!")
                return True
            descricao = input("Descrição: ").strip()
            prazo = input("Prazo (ex: Hoje 14h / Amanhã): ").strip()
            adicionar_tarefa(titulo, descricao, prazo)
        
        elif opcao == "2":
            tarefas = carregar_tarefas()
            priorizar_com_ia(tarefas)
        
        elif opcao == "3":
            listar_tarefas()
        
        elif opcao == "4":
            tarefas = listar_tarefas()
            if tarefas:
                try:
                    id_tarefa = int(input("ID da tarefa a concluir: "))
                    concluir_tarefa(id_tarefa)
                except ValueError:
                    print("ID inválido! Digite um número inteiro.")
        
        elif opcao == "5":
            enviar_resumo_email()
        
        elif opcao == "6":
            print("Até logo! 👋")
            return False
        
        else:
            print("Opção inválida! Digite 1-6.")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return True

if __name__ == "__main__":
    try:
        while menu():
            pass
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido.")

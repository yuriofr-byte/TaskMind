import json
import os
import tempfile
import pytest
from taskmind import carregar_tarefas, guardar_tarefas, adicionar_tarefa, concluir_tarefa

# Use a temporary file for testing
@pytest.fixture
def temp_tasks_file(monkeypatch):
    """Create a temporary tasks file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
        json.dump([], f)
    
    # Monkeypatch the FICHEIRO_TAREFAS to use the temp file
    import taskmind
    monkeypatch.setattr(taskmind, 'FICHEIRO_TAREFAS', temp_path)
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_carregar_tarefas_empty(temp_tasks_file):
    """Test loading an empty task file"""
    tarefas = carregar_tarefas()
    assert isinstance(tarefas, list)
    assert len(tarefas) == 0


def test_guardar_tarefas(temp_tasks_file):
    """Test saving tasks"""
    tarefas = [
        {
            "id": 1,
            "titulo": "Teste",
            "descricao": "Descricao teste",
            "prazo": "Hoje",
            "concluida": False,
            "data_criacao": "01/01/2025 10:00"
        }
    ]
    guardar_tarefas(tarefas)
    
    # Verify tasks were saved
    loaded = carregar_tarefas()
    assert len(loaded) == 1
    assert loaded[0]["titulo"] == "Teste"


def test_adicionar_tarefa(temp_tasks_file, capsys):
    """Test adding a task"""
    adicionar_tarefa("Nova Tarefa", "Descricao", "Amanha")
    
    tarefas = carregar_tarefas()
    assert len(tarefas) == 1
    assert tarefas[0]["titulo"] == "Nova Tarefa"
    assert tarefas[0]["descricao"] == "Descricao"
    assert tarefas[0]["prazo"] == "Amanha"
    assert tarefas[0]["concluida"] == False


def test_concluir_tarefa(temp_tasks_file):
    """Test marking a task as complete"""
    adicionar_tarefa("Tarefa para concluir", "Descricao", "Hoje")
    
    # Mark as complete
    concluir_tarefa(1)
    
    tarefas = carregar_tarefas()
    assert len(tarefas) == 1
    assert tarefas[0]["concluida"] == True


def test_concluir_tarefa_not_found(temp_tasks_file, capsys):
    """Test marking a non-existent task as complete"""
    concluir_tarefa(999)
    
    captured = capsys.readouterr()
    assert "não encontrada" in captured.out.lower() or "not found" in captured.out.lower()
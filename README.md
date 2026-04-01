# SOLÉ — Catálogo de Calçados Online

Sistema completo de catálogo digital para loja de sapatos, com painel admin.

## Estrutura
```
sapatos/
├── app.py              ← Backend Flask (API + servidor)
├── requirements.txt    ← Dependências Python
├── db.json             ← Banco de dados (criado automaticamente)
├── templates/
│   ├── index.html      ← Catálogo público
│   └── admin.html      ← Painel administrativo
└── static/
    └── uploads/        ← Imagens dos produtos
```

## Como rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o servidor
```bash
python app.py
```

### 3. Acessar
- **Catálogo público:** http://localhost:5000
- **Painel admin:**     http://localhost:5000/admin

## Login padrão
| Campo  | Valor    |
|--------|----------|
| Usuário | `admin`  |
| Senha   | `admin123` |

> ⚠️ Troque a senha em produção editando a variável `app.secret_key` no `app.py`
> e atualizando o hash da senha no `db.json`.

## Funcionalidades
- ✅ Catálogo público com filtro por categoria e busca
- ✅ Modal de detalhes do produto
- ✅ Painel admin com login seguro (sessão)
- ✅ Adicionar produtos com upload de imagem (base64)
- ✅ Editar produtos existentes
- ✅ Excluir produtos
- ✅ Persistência em JSON (sem banco de dados externo)
- ✅ Design elegante e responsivo

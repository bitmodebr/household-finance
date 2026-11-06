# FinanceMode

FinanceMode é uma aplicação web para organizar despesas compartilhadas. O projeto
usa Django e Postgres, com interface em português e horário padrão de
`America/Sao_Paulo`.

## Ideias básicas

- Cadastro e autenticação de usuários por e-mail.
- Dashboard e páginas restritas a usuários autenticados.
- Registro de pagamentos em nome de um usuário, com identificação de
  quem criou o gasto.
- Seleção de compartilhantes para dividir cada pagamento.
- Cálculo mensal por período de calendário, com divisão em centavos.
- Desativação lógica de gastos: o registro permanece no sistema e deixa de
  participar dos cálculos.
- Área administrativa do Django para gerenciamento de usuários e gastos.

## Requisitos

- Python 3.12 ou compatível com as dependências do projeto.
- `pip`.

## Começar a rodar

Execute os comandos abaixo na pasta raiz do repositório.

### 1. Criar e ativar um ambiente virtual

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar o ambiente

O Django carrega as configurações locais do arquivo `.env` e é deixado um `.env.example` como base. Crie-o na raiz do projeto:

```bash
cp .env.example .env
```

Defina pelo menos uma chave secreta em `.env`. Gere uma com:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Exemplo de `.env` para desenvolvimento:

```dotenv
DJANGO_SECRET_KEY=cole-aqui-a-chave-gerada
DJANGO_DEBUG=True
```

Para carregar o Bootstrap hospedado em outro endereço da rede, configure também
as URLs absolutas dos arquivos CSS e JavaScript:

```dotenv
BOOTSTRAP_CSS_URL=http://servidor-local/bootstrap/css/bootstrap.min.css
BOOTSTRAP_JS_URL=http://servidor-local/bootstrap/js/bootstrap.bundle.min.js
```

Essas URLs podem ficar vazias enquanto os arquivos não estiverem disponíveis.

### 4. Aplicar as migrações

```bash
python manage.py migrate
```

### 5. Iniciar o servidor de desenvolvimento

```bash
python manage.py runserver
```

Abra <http://127.0.0.1:8000/> no navegador. Para acessar o painel administrativo,
crie um superusuário:

```bash
python manage.py createsuperuser
```

O admin ficará disponível em <http://127.0.0.1:8000/admin/>.

## Testes e verificações

Com o ambiente virtual ativado:

```bash
python manage.py test
python manage.py check
```

Para executar somente os testes do app financeiro:

```bash
python manage.py test finance
```

## Estrutura do projeto

- `setup/`: configurações e rotas principais do Django.
- `finance/`: modelos, validações, formulários, cálculos, views e testes.
- `templates/`: templates HTML compartilhados e páginas da aplicação.
- `requirements.txt`: dependências Python.

O servidor `runserver` é destinado ao desenvolvimento. Antes de disponibilizar a
aplicação na rede ou na internet, configure um servidor de produção, `DEBUG=False`,
`ALLOWED_HOSTS`, HTTPS e uma chave secreta exclusiva e protegida.
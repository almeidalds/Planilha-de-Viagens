# Planilhas de Viagens | CTM

Sistema em Streamlit para organizar planilhas de chegadas e partidas de missionários, combinando dados de uma planilha de voos com informações da master do CTM.

> **Aviso de uso:** este é um sistema privado e de uso restrito. O uso, cópia, distribuição ou modificação dependem de autorização prévia. Consulte [LICENSE.md](LICENSE.md).

## Funcionalidades

- Seleção entre os fluxos **Chegadas** e **Partidas**.
- Seleção da planilha de voos disponível na pasta configurada.
- Seleção de um período de datas.
- Filtragem dos missionários pela data do voo:
  - `Partida` para o fluxo de partidas.
  - `Chegada` para o fluxo de chegadas.
- Uso da planilha de voos como fonte principal da lista final.
- Complementação dos dados pela master:
  - `Type` -> `Tipo`.
  - `Msny ID` -> `ID`.
  - `Country Home Unit` -> `Países`.
- Cálculo automático da quantidade de veículos necessária.
- Exibição do resultado na interface.
- Exportação de uma planilha Excel formatada.
- Logo exibido no menu lateral.

## Requisitos

- Python 3.10 ou superior.
- Acesso à internet para ler a master hospedada no SharePoint.
- Acesso à pasta local onde ficam as planilhas de voos.

## Instalação

No terminal, dentro da pasta do projeto, execute:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit pandas requests openpyxl
```

Caso o PowerShell bloqueie a ativação do ambiente virtual, execute apenas nesta sessão:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

## Execução

Com o ambiente virtual ativado:

```powershell
python -m streamlit run app.py
```

Depois, abra o endereço exibido pelo Streamlit, normalmente:

```text
http://localhost:8501
```

## Como usar

1. Selecione `Chegadas` ou `Partidas` no menu lateral.
2. Escolha a planilha de voos.
3. Informe o período desejado.
4. Clique em **Processar Dados**.
5. Confira a tabela gerada.
6. Clique em **Exportar Planilha Oficial (Formatada)** para salvar o Excel.

O processamento só começa depois que o botão **Processar Dados** é pressionado.

## Regra dos dados

A planilha de voos controla quais missionários aparecem no resultado final. A master não adiciona missionários que não estejam na planilha de voos selecionada.

A master é usada para complementar os dados encontrados pelo nome do missionário. O sistema normaliza acentos, espaços e nomes nos formatos `Nome Sobrenome` e `Sobrenome, Nome` para tentar fazer a correspondência entre as planilhas.

Se um missionário estiver na planilha de voos, mas não for encontrado na master, os dados disponíveis na planilha de voos continuam sendo exibidos e os campos complementares da master ficam vazios.

## Arquivos de entrada

### Planilha de voos

A planilha deve conter uma coluna de nome do missionário e informações de voo. O sistema reconhece nomes como:

- `Missionary Name`
- `Nome do Missionário`
- `Nome do Passageiro`
- `Nome Completo`
- `Missionários`

Para filtrar o período, a planilha precisa fornecer os dados de data que resultam nas colunas `Partida` e `Chegada`.

### Master online

O endereço da master está configurado na constante `LINK_MASTER`, em `app.py`.

O sistema procura a aba chamada `Master`, ignorando diferenças de espaços e maiúsculas/minúsculas. As colunas esperadas são:

| Coluna na master | Coluna no sistema |
| --- | --- |
| `Missionary Name` | `Missionários` |
| `Msny ID` | `ID` |
| `Type` | `Tipo` |
| `Country Home Unit` | `Países` |
| `Mission Assigned` | `Missões` |

## Configuração local

Os caminhos principais estão no início de `app.py`:

- `PASTA_BASE`: pasta principal de trabalho.
- `PASTA_VOOS`: pasta que contém os arquivos de voo.
- `LINK_MASTER`: endereço da master online.
- `LOGO_PATH`: arquivo `logo.png` usado no menu lateral.

Por padrão, o sistema procura as planilhas em:

```text
C:\Users\Almeidalds\OneDrive - Church of Jesus Christ\Paulo Cezar Sousa's files - Planilha de Viagens - (PYTHON, NÃO MEXE AMIGA)\voo_semanais
```

Se o projeto for usado em outro computador, ajuste `PASTA_BASE` em `app.py`.

Para trocar o logo, substitua o arquivo `logo.png` na mesma pasta de `app.py`.

## Estrutura do projeto

```text
viagens/
├── app.py          # Interface Streamlit e fluxo principal
├── modelos.py      # Layout das tabelas e exportação para Excel
├── logistica.py    # Regras de cálculo de transporte
├── logo.png        # Logo exibido no menu lateral
└── README.md       # Documentação do sistema
```

## Transporte

O sistema calcula o transporte para os missionários que possuem voo confirmado, considerando bagagem. As faixas atuais estão implementadas em `logistica.py` e incluem carro, van, micro e ônibus.

## Validação local

Para verificar se os arquivos Python estão compilando corretamente:

```powershell
python -m py_compile app.py logistica.py modelos.py
```

Para verificar espaços em branco inválidos no diff:

```powershell
git diff --check
```

<h1 align="center">Leilão Online em Tempo Real com Sockets TCP</h1>

<p align="center">Leonardo Ferreira Cabral</p>

## 📝 Sumário

- [📖 Sobre](#sobre)
- [🏁 Primeiros Passos](#primeiros_passos)
- [📱 Uso](#uso)
- [⛏️ Tecnologias Utilizadas](#tecnologias)

## 📖 Sobre <a name = "sobre"></a>

Sistema distribuído cliente-servidor que gerencia um leilão online em tempo real para um item específico. O servidor mantém conexões TCP persistentes com todos os usuarios e controla o estado do leilão: lance atual (valor e ID do proponente) e tempo restante. Cada cliente pode enviar lances com BID <valor> e consultar o estado com STATUS.

O servidor atende cada cliente em uma thread própria. A validação e o registro de um lance acontecem dentro do mesmo threading.Lock, então lances concorrentes são registrados de forma atômica: dois lances simultâneos nunca comparam com o mesmo "lance atual". Sempre que um novo lance válido é registrado, o servidor notifica na hora todos os outros clientes conectados pela conexão TCP persistente, ainda dentro da seção crítica, para que as notificações cheguem na mesma ordem em que os lances foram registrados.

## 🏁 Primeiros Passos <a name = "primeiros_passos"></a>

As instruções abaixo permitem executar o projeto na sua máquina local.

### Pré-requisitos

O projeto usa apenas a biblioteca padrão do Python, então basta ter o Python 3.8 ou superior instalado.

```bash
# Verifique a versão do Python instalada
python --version
```

### Instalação

Não há dependências externas. Basta clonar o repositório:

```bash
# Clone o repositório e entre na pasta
git clone https://github.com/LeofCabral/leilao-aps.git
cd leilao-aps
```

## 📱 Uso <a name = "uso"></a>

Inicie primeiro o servidor e, em seguida, um ou mais clientes, cada um em um terminal diferente.

### Executando o Servidor

```bash
# Abre o leilão na porta 5000, com lance mínimo de 100 e duração de 120 segundos
python servidor.py --porta 5000 --item Relogio-Antigo --minimo 100 --duracao 120
```

### Executando o Cliente

```bash
# Conecta um concorrente ao servidor (abra um terminal para cada concorrente)
python cliente.py --host 127.0.0.1 --porta 5000
```

Comandos disponíveis no cliente:

```bash
BID 150    # envia um lance de 150
STATUS     # mostra o lance atual, o proponente e o tempo restante
QUIT       # desconecta do leilão
```

### Teste de Concorrência

```bash
# Sobe um servidor próprio e simula 20 concorrentes enviando 25 lances cada, ao mesmo tempo
python teste_concorrencia.py
```

O teste verifica se o lance final é o maior lance aceito, se os lances aceitos formam uma sequência crescente e se um cliente observador recebeu um `NEW_BID` para cada lance aceito, na ordem correta. Ao final, deve exibir `OK: registro atômico e notificações consistentes.`

## ⛏️ Tecnologias Utilizadas <a name = "tecnologias"></a>

- [Python3](https://www.python.org/) - Linguagem de programação
- [socket](https://docs.python.org/3/library/socket.html) - Comunicação TCP entre cliente e servidor
- [threading](https://docs.python.org/3/library/threading.html) - Atendimento concorrente dos clientes e sincronização com `Lock`

---

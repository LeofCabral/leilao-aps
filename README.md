# Leilão online Leonardo Ferreira Cabral

Requer Python 3.8+ (somente biblioteca padrão).

## Como executar

```bash
python servidor.py --porta 5000 --item Relogio-Antigo --minimo 100 --duracao 120
```

Em outros terminais (um por licitante):

```bash
python cliente.py --host 127.0.0.1 --porta 5000
```

Comandos do cliente: `BID <valor>`, `STATUS`, `QUIT`.

Teste automático de concorrência (20 clientes × 25 lances simultâneos):

```bash
python teste_concorrencia.py
```

## Protocolo (texto, uma mensagem por linha)

| Direção | Mensagem | Significado |
|---|---|---|
| C → S | `BID <valor>` | envia lance |
| C → S | `STATUS` | consulta o estado |
| C → S | `QUIT` | desconecta |
| S → C | `WELCOME <id> <item>` | boas-vindas, com o ID do licitante |
| S → C | `OK <valor>` | lance aceito |
| S → C | `ERRO <motivo>` | lance/comando inválido |
| S → C | `STATUS <item> <valor> <id> <segundos>` | estado atual |
| S → C | `NEW_BID <valor> <id>` | **push**: novo lance máximo (para os outros clientes) |
| S → C | `END <valor> <id>` | fim do leilão e vencedor |

## Decisões de projeto

- **Conexão persistente**: cada cliente aceito ganha uma thread no servidor que lê seus comandos; o socket fica aberto até o fim do leilão, e é por ele que chegam as notificações.
- **Atomicidade**: `Leilao.dar_lance` faz a verificação (`valor > lance_atual`) e a atualização (valor + proponente) dentro do mesmo `threading.Lock`. Dois lances simultâneos nunca leem o mesmo "lance atual"; um deles sempre vence e o outro é comparado ao novo valor.
- **Notificação imediata**: o broadcast `NEW_BID` acontece ainda dentro da seção crítica, para que todos recebam as notificações na mesma ordem em que os lances foram registrados.
- **Escrita segura no socket**: cada cliente tem um lock de envio, porque sua própria thread (respostas) e a thread de outro licitante (notificações) podem escrever nele ao mesmo tempo.
- **Valores**: `Decimal` com 2 casas, para evitar erros de ponto flutuante com dinheiro.
- **Tempo**: uma thread cronômetro encerra o leilão, envia `END` a todos e fecha o servidor.
- **Cliente**: uma thread fica lendo o socket o tempo todo, então as notificações aparecem na hora, mesmo enquanto o usuário digita.

"""
Servidor online em tempo real.

Cliente -> Servidor:
    BID <valor>     envia um lance
    STATUS          consulta o estado atual do leilão
    QUIT            desconecta

Servidor -> Cliente:
    WELCOME <id> <item>                 enviado ao conectar
    OK <valor>                          lance aceito
    ERRO <motivo>                       comando/lance inválido
    STATUS <item> <valor> <id> <seg>    estado atual (id = '-' se não houver lance)
    NEW_BID <valor> <id>                notificação push de novo lance máximo
    END <valor> <id>                    leilão encerrado (id = '-' se ninguém deu lance)
"""

import argparse
import socket
import threading
import time
from decimal import Decimal, InvalidOperation


class Cliente:

    def __init__(self, conn, addr, cid):
        self.conn = conn
        self.addr = addr
        self.id = cid

        self._send_lock = threading.Lock()

    def enviar(self, msg):
        try:
            with self._send_lock:
                self.conn.sendall((msg + "\n").encode("utf-8"))
        except OSError:
            pass 


class Leilao:
    def __init__(self, item, lance_minimo, duracao):
        self.item = item
        self.lance_atual = lance_minimo
        self.proponente = None
        self.fim = time.monotonic() + duracao
        self.encerrado = False
        self.clientes = {}
        
        self.lock = threading.Lock()

    def restante(self):
        return max(0, int(self.fim - time.monotonic()))

    def adicionar(self, cliente):
        with self.lock:
            self.clientes[cliente.id] = cliente

    def remover(self, cliente):
        with self.lock:
            self.clientes.pop(cliente.id, None)

    def status(self):
        with self.lock:
            return (f"STATUS {self.item} {self.lance_atual:.2f} "
                    f"{self.proponente or '-'} {self.restante()}")

    def dar_lance(self, cliente, valor):
        """Valida e registra o lance de forma atômica. Retorna a resposta ao autor."""
        with self.lock:
            if self.encerrado or time.monotonic() >= self.fim:
                return "ERRO leilao encerrado"
            if valor <= self.lance_atual:
                return f"ERRO lance deve ser maior que {self.lance_atual:.2f}"

            self.lance_atual = valor
            self.proponente = cliente.id
            print(f"[LANCE] {cliente.id} -> {valor:.2f}")

            aviso = f"NEW_BID {valor:.2f} {cliente.id}"
            for outro in self.clientes.values():
                if outro is not cliente:
                    outro.enviar(aviso)
            return f"OK {valor:.2f}"

    def encerrar(self):
        with self.lock:
            self.encerrado = True
            msg = f"END {self.lance_atual:.2f} {self.proponente or '-'}"
            clientes = list(self.clientes.values())
        print(f"[FIM] {msg}")
        for c in clientes:
            c.enviar(msg)
            try:
                c.conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            c.conn.close()


def parse_valor(texto):
    try:
        valor = Decimal(texto.replace(",", "."))
    except InvalidOperation:
        return None
    if not valor.is_finite() or valor <= 0:
        return None
    return valor.quantize(Decimal("0.01"))


def atender(leilao, cliente):
    print(f"[CONEXAO] {cliente.id} {cliente.addr}")
    leilao.adicionar(cliente)
    cliente.enviar(f"WELCOME {cliente.id} {leilao.item}")
    try:
        with cliente.conn.makefile("r", encoding="utf-8") as entrada:
            for linha in entrada:
                partes = linha.strip().split()
                if not partes:
                    continue
                cmd = partes[0].upper()
                if cmd == "BID":
                    valor = parse_valor(partes[1]) if len(partes) == 2 else None
                    if valor is None:
                        cliente.enviar("ERRO uso: BID <valor positivo>")
                    else:
                        cliente.enviar(leilao.dar_lance(cliente, valor))
                elif cmd == "STATUS":
                    cliente.enviar(leilao.status())
                elif cmd == "QUIT":
                    break
                else:
                    cliente.enviar("ERRO comando desconhecido (use BID <valor>, STATUS ou QUIT)")
    except (OSError, UnicodeDecodeError):
        pass
    finally:
        leilao.remover(cliente)
        try:
            cliente.conn.close()
        except OSError:
            pass
        print(f"[DESCONEXAO] {cliente.id}")


def main():
    p = argparse.ArgumentParser(description="Servidor de leilão TCP")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--porta", type=int, default=5000)
    p.add_argument("--item", default="Relogio-Antigo")
    p.add_argument("--minimo", default="100", help="lance inicial (lances precisam superá-lo)")
    p.add_argument("--duracao", type=int, default=120, help="duração do leilão em segundos")
    args = p.parse_args()

    leilao = Leilao(args.item.replace(" ", "-"), parse_valor(args.minimo) or Decimal("0.00"), args.duracao)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.porta))
    srv.listen()

    def cronometro():
        time.sleep(args.duracao)
        leilao.encerrar()
        srv.close()

    threading.Thread(target=cronometro, daemon=True).start()
    print(f"Leilão de '{leilao.item}' aberto em {args.host}:{args.porta} "
          f"(mínimo {leilao.lance_atual:.2f}, {args.duracao}s)")

    contador = 0
    try:
        while True:
            try:
                conn, addr = srv.accept()
            except OSError:
                break
            if leilao.encerrado:
                conn.close()
                continue
            contador += 1
            cliente = Cliente(conn, addr, f"licitante-{contador}")
            threading.Thread(target=atender, args=(leilao, cliente), daemon=True).start()
    except KeyboardInterrupt:
        leilao.encerrar()
    finally:
        srv.close()


if __name__ == "__main__":
    main()

"""
Cliente do leilao online (Leonardo Ferreira Cabral),
fiz sozinho pois estava sem grupo.)
"""

import argparse
import os
import socket
import threading


def formatar(linha):
    partes = linha.split()
    tipo = partes[0] if partes else ""
    if tipo == "WELCOME":
        return f"Conectado como {partes[1]} no leilão de '{partes[2]}'."
    if tipo == "OK":
        return f"Seu lance de {partes[1]} foi registrado. Você está vencendo!"
    if tipo == "NEW_BID":
        return f"*** NOVO LANCE MÁXIMO: {partes[1]} por {partes[2]} ***"
    if tipo == "STATUS":
        _, item, valor, quem, seg = partes
        quem = "nenhum lance ainda" if quem == "-" else quem
        return f"Item: {item} | Lance atual: {valor} ({quem}) | Restam {seg}s"
    if tipo == "END":
        quem = "sem vencedor" if partes[2] == "-" else f"vencedor {partes[2]}"
        return f"=== LEILÃO ENCERRADO: {quem}, valor {partes[1]} ==="
    if tipo == "ERRO":
        return "Erro: " + linha[5:]
    return linha


def receber(sock):
    try:
        with sock.makefile("r", encoding="utf-8") as entrada:
            for linha in entrada:
                linha = linha.strip()
                try:
                    texto = formatar(linha)
                except (IndexError, ValueError):
                    texto = linha 
                print("\n" + texto, flush=True)
                print("> ", end="", flush=True)
    except OSError:
        pass
    print("\nConexão encerrada pelo servidor.")
    os._exit(0)  


def main():
    p = argparse.ArgumentParser(description="Cliente de leilão TCP")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=5000)
    args = p.parse_args()

    sock = socket.create_connection((args.host, args.porta))
    threading.Thread(target=receber, args=(sock,), daemon=True).start()

    print("Comandos: BID <valor> | STATUS | QUIT")
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            sock.sendall((cmd + "\n").encode("utf-8"))
            if cmd.upper() == "QUIT":
                break
    except (EOFError, KeyboardInterrupt, OSError):
        pass
    sock.close()


if __name__ == "__main__":
    main()

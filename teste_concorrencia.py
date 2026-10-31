"""
Teste automático: sobe o servidor, conecta vários licitantes que disparam
lances ao mesmo tempo e verifica que
  1. o lance final é o maior lance aceito
  2. um observador recebeu um NEW_BID para cada lance aceito, na mesma ordem.
"""

import random
import socket
import subprocess
import sys
import threading
import time

PORTA = 5055
N_CLIENTES = 20
LANCES_POR_CLIENTE = 25


def conectar():
    for _ in range(50):
        try:
            s = socket.create_connection(("127.0.0.1", PORTA))
            return s, s.makefile("r", encoding="utf-8")
        except ConnectionRefusedError:
            time.sleep(0.1)
    raise RuntimeError("servidor não subiu")


def main():
    servidor = subprocess.Popen(
        [sys.executable, "servidor.py", "--porta", str(PORTA), "--duracao", "8", "--minimo", "100"],
        stdout=subprocess.DEVNULL)
    try:
        obs, obs_in = conectar()
        obs_in.readline() 
        notificacoes = []

        def observar():
            for linha in obs_in:
                if linha.startswith("NEW_BID"):
                    notificacoes.append(linha.split()[1])

        threading.Thread(target=observar, daemon=True).start()

        aceitos = []
        aceitos_lock = threading.Lock()
        largada = threading.Barrier(N_CLIENTES)

        def licitante():
            s, entrada = conectar()
            entrada.readline()
            largada.wait()  
            for _ in range(LANCES_POR_CLIENTE):
                s.sendall(f"BID {random.randint(101, 5000)}\n".encode())
                while True:  
                    resp = entrada.readline().split()
                    if resp[0] in ("OK", "ERRO"):
                        break
                if resp[0] == "OK":
                    with aceitos_lock:
                        aceitos.append(resp[1])
            s.close()

        threads = [threading.Thread(target=licitante) for _ in range(N_CLIENTES)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        time.sleep(0.5)

        s, entrada = conectar()
        entrada.readline()
        s.sendall(b"STATUS\n")
        status = entrada.readline().split()

        maior = max(aceitos, key=float)
        valores = [float(v) for v in notificacoes]
        print(f"lances enviados: {N_CLIENTES * LANCES_POR_CLIENTE}, aceitos: {len(aceitos)}")
        print(f"STATUS final: {' '.join(status)}")
        assert status[2] == maior, "lance final diferente do maior aceito"
        assert valores == sorted(valores) and len(set(valores)) == len(valores), "sequência não crescente"
        assert sorted(notificacoes, key=float) == sorted(aceitos, key=float), "observador perdeu notificações"
        print("OK: registro atômico e notificações consistentes.")
    finally:
        servidor.terminate()


if __name__ == "__main__":
    main()

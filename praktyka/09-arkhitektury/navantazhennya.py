"""Навантаження — скільки запитів на секунду витримує те, що стоїть за портом.

    python navantazhennya.py --port 50007 --kliyentiv 1
    python navantazhennya.py --port 50000 --kliyentiv 8 --zapytiv 200

Запускає N клієнтів одночасно, кожен надсилає по K записів, і рахує:
пропускну здатність, затримки (медіана й 95-й відсоток), скільки запитів
обслужив кожен вузол і скільки було помилок.

Наприкінці питає «стан» **у кожного** вузла зі списку `--vuzly` окремо —
щоб було видно, чи журнал один, чи їх кілька.
"""

import argparse
import json
import socket
import statistics
import threading
import time
import uuid

HOST = "127.0.0.1"


def odyn_zapyt(port, zapyt, taimaut):
    s = socket.create_connection((HOST, port), timeout=taimaut)
    try:
        s.settimeout(taimaut)
        f = s.makefile("rwb")
        f.write((json.dumps(zapyt, ensure_ascii=False) + "\n").encode())
        f.flush()
        ryadok = f.readline()
        if not ryadok:
            raise ConnectionError("з'єднання закрито без відповіді")
        return json.loads(ryadok.decode())
    finally:
        s.close()


class VidpovidPomylka(Exception):
    """Вузол відповів, але не "ok" (наприклад, сховище недоступне)."""


def kliyent(nomer, port, zapytiv, taimaut, kliuch, chasy, vuzly_lich, pomylky, zamok,
            povtoriv=0, povtory_lich=None):
    for i in range(zapytiv):
        zapyt = {"dia": "dodaty", "zapys": {"kliyent": nomer, "nomer": i}}
        if kliuch:
            # ключ створюється ОДИН раз на запис і не змінюється між повторами —
            # саме так сховище впізнає повтор і не запише дублікат
            zapyt["kliuch"] = str(uuid.uuid4())
        t0 = time.perf_counter()
        for sproba in range(povtoriv + 1):
            try:
                vidpovid = odyn_zapyt(port, zapyt, taimaut)
                if vidpovid.get("status") != "ok":
                    raise VidpovidPomylka(vidpovid.get("chomu", ""))
                dt = (time.perf_counter() - t0) * 1000
                with zamok:
                    chasy.append(dt)
                    v = vidpovid.get("vuzol", "?")
                    vuzly_lich[v] = vuzly_lich.get(v, 0) + 1
                    if sproba and povtory_lich is not None:
                        povtory_lich["uspishni_povtory"] += 1
                break
            except (OSError, ConnectionError, ValueError, VidpovidPomylka) as e:
                if sproba < povtoriv:
                    # балансувальник роздає по черзі — наступне з'єднання
                    # піде на інший вузол; коротка пауза дає перевірці живості
                    # шанс виключити мертвий
                    with zamok:
                        if povtory_lich is not None:
                            povtory_lich["sprob_povtoru"] += 1
                    time.sleep(0.05 * (sproba + 1))
                    continue
                with zamok:
                    pomylky.append(type(e).__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=50007,
                   help="куди стукати: 50007 — просто в службу, 50000 — у балансувальник")
    p.add_argument("--kliyentiv", type=int, default=1)
    p.add_argument("--zapytiv", type=int, default=100, help="запитів на кожного клієнта")
    p.add_argument("--taimaut", type=float, default=5.0)
    p.add_argument("--kliuch", action="store_true", help="додавати ключ ідемпотентності")
    p.add_argument("--povtoriv", type=int, default=0,
                   help="скільки разів повторити запит при помилці (⭐4); з --kliuch без дублікатів")
    p.add_argument("--vuzly", type=int, nargs="*", default=[50007, 50008],
                   help="у кого наприкінці питати стан")
    args = p.parse_args()

    chasy, pomylky, vuzly_lich = [], [], {}
    povtory_lich = {"sprob_povtoru": 0, "uspishni_povtory": 0}
    zamok = threading.Lock()
    potoky = [threading.Thread(target=kliyent,
                               args=(n, args.port, args.zapytiv, args.taimaut,
                                     args.kliuch, chasy, vuzly_lich, pomylky, zamok,
                                     args.povtoriv, povtory_lich))
              for n in range(args.kliyentiv)]

    t0 = time.perf_counter()
    for t in potoky:
        t.start()
    for t in potoky:
        t.join()
    tryvalist = time.perf_counter() - t0

    vsogo = args.kliyentiv * args.zapytiv
    uspishnyh = len(chasy)
    print(f"\nклієнтів {args.kliyentiv} · запитів {vsogo} · порт {args.port}")
    print(f"успішних {uspishnyh} · помилок {len(pomylky)} · разом {tryvalist:.2f} с")
    if uspishnyh:
        print(f"пропускна здатність: {uspishnyh / tryvalist:8.0f} запитів/с")
        print(f"затримка: медіана {statistics.median(chasy):.2f} мс · "
              f"95-й відсоток {statistics.quantiles(chasy, n=20)[18]:.2f} мс · "
              f"максимум {max(chasy):.2f} мс")
    if vuzly_lich:
        print("обслужили: " + " · ".join(f"{k}: {v}" for k, v in sorted(vuzly_lich.items())))
    if args.povtoriv:
        print(f"повтори: спроб {povtory_lich['sprob_povtoru']} · "
              f"запитів, урятованих повтором {povtory_lich['uspishni_povtory']}")
    if pomylky:
        vydy = {}
        for e in pomylky:
            vydy[e] = vydy.get(e, 0) + 1
        print("помилки: " + " · ".join(f"{k} ×{v}" for k, v in vydy.items()))

    print("\nстан у кожного вузла окремо:")
    for port in args.vuzly:
        try:
            st = odyn_zapyt(port, {"dia": "stan"}, 3)
            print(f"  :{port} ({st.get('vuzol', '?')}) — записів {st.get('vsogo')}"
                  + (f" · звернень до сховища {st['zvernen_do_shovyshcha']}"
                     if "zvernen_do_shovyshcha" in st else ""))
        except OSError as e:
            print(f"  :{port} — недоступний ({type(e).__name__})")


if __name__ == "__main__":
    main()

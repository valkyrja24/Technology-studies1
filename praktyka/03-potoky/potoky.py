import json
import os
import platform
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter, process_time

W, H = 1000, 750
MAX_ITER = 400
X0, X1, Y0, Y1 = -2.0, 1.0, -1.2, 1.2
DX = (X1 - X0) / W
DY = (Y1 - Y0) / H


def ryadok(y):
    ci = Y0 + y * DY
    res = []
    for px in range(W):
        cr = X0 + px * DX
        x = yy = 0.0
        n = MAX_ITER
        for i in range(MAX_ITER):
            x2, y2 = x * x, yy * yy
            if x2 + y2 > 4.0:
                n = i
                break
            yy = 2.0 * x * yy + ci
            x = x2 - y2 + cr
        res.append(n)
    return res


def poslidovno():
    return [ryadok(y) for y in range(H)]


def zamir(fn, prohoniv=3, *a):
    chasy, rez = [], None
    for _ in range(prohoniv):
        t0 = perf_counter()
        rez = fn(*a)
        chasy.append(perf_counter() - t0)
    return min(chasy), chasy, rez


def potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H)))


def navantazhennya(fn, *a):
    c0, t0 = process_time(), perf_counter()
    fn(*a)
    return (process_time() - c0) / (perf_counter() - t0)


def zapyt(nomer):
    time.sleep(0.5)
    return nomer


def ochikuvannya_poslidovno():
    return [zapyt(i) for i in range(32)]


def ochikuvannya_potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(zapyt, range(32)))


np = None


def blok_np(y_start, y_end):
    ys = np.arange(y_start, y_end, dtype=np.float64)
    xs = np.arange(W, dtype=np.float64)
    ci = (Y0 + ys * DY)[:, None] * np.ones((1, W))
    cr = np.ones((y_end - y_start, 1)) * (X0 + xs * DX)[None, :]
    x = np.zeros_like(cr)
    yy = np.zeros_like(cr)
    zhyva = np.ones(cr.shape, dtype=bool)
    lich = np.zeros(cr.shape, dtype=np.int64)
    with np.errstate(over="ignore", invalid="ignore"):
        for _ in range(MAX_ITER):
            x2 = x * x
            y2 = yy * yy
            zhyva &= (x2 + y2) <= 4.0
            lich += zhyva
            yy = 2.0 * x * yy + ci
            x = x2 - y2 + cr
    return lich


def mezhi(chastyn):
    krok = -(-H // chastyn)
    return [(s, min(s + krok, H)) for s in range(0, H, krok)]


def numpy_poslidovno():
    return blok_np(0, H).tolist()


def numpy_potokamy(n):
    shmatky = mezhi(n)
    with ThreadPoolExecutor(max_workers=n) as ex:
        chastyny = list(ex.map(lambda m: blok_np(*m), shmatky))
    return np.concatenate(chastyny).tolist()


def gil_status():
    f = getattr(sys, "_is_gil_enabled", None)
    return "увімкнено (Python < 3.13)" if f is None else ("увімкнено" if f() else "ВИМКНЕНО")


if __name__ == "__main__":
    potoky = sorted({2, 4, 8, os.cpu_count()})
    vyhid = {
        "mashyna": {
            "cpu_count": os.cpu_count(),
            "procesor": platform.processor() or platform.machine(),
            "systema": platform.platform(),
            "python": platform.python_version(),
            "gil": gil_status(),
        },
        "zadacha": {"W": W, "H": H, "MAX_ITER": MAX_ITER},
    }
    print("машина:", vyhid["mashyna"])

    t_base, chasy, base = zamir(poslidovno, 3)
    print("послідовно", [round(c, 2) for c in chasy], "мінімум", round(t_base, 2))
    obch = [{"n": 1, "chasy": chasy, "min": t_base, "pryskorennya": 1.0}]
    for n in potoky:
        t, chasy, r = zamir(potokamy, 3, n)
        assert r == base, "результат розійшовся з послідовним"
        print("потоків", n, [round(c, 2) for c in chasy],
              "мінімум", round(t, 2), "прискорення", round(t_base / t, 2))
        obch.append({"n": n, "chasy": chasy, "min": t, "pryskorennya": t_base / t})
    vyhid["obchyslennya"] = obch

    nav = navantazhennya(potokamy, 8)
    print("процесорний / настінний, 8 потоків:", round(nav, 2))
    vyhid["proc_nast_8"] = nav

    t0 = perf_counter()
    base_o = ochikuvannya_poslidovno()
    t_base_o = perf_counter() - t0
    print("очікування послідовно", round(t_base_o, 2))
    och = [{"n": 1, "chasy": [t_base_o], "min": t_base_o, "pryskorennya": 1.0}]
    for n in (2, 4, 8, 16, 32):
        t, chasy, r = zamir(ochikuvannya_potokamy, 3, n)
        assert r == base_o
        print("очікування, потоків", n, [round(c, 2) for c in chasy],
              "прискорення", round(t_base_o / t, 1))
        och.append({"n": n, "chasy": chasy, "min": t, "pryskorennya": t_base_o / t})
    vyhid["ochikuvannya"] = och
    vyhid["proc_nast_ochikuvannya_16"] = navantazhennya(ochikuvannya_potokamy, 16)

    if np is not None:
        t_np, chasy, base_np = zamir(numpy_poslidovno, 3)
        assert base_np == base, "NumPy-версія розійшлася з чистим Python"
        print("numpy послідовно", [round(c, 2) for c in chasy], "мінімум", round(t_np, 3))
        nump = [{"n": 1, "chasy": chasy, "min": t_np, "pryskorennya": 1.0}]
        for n in potoky:
            t, chasy, r = zamir(numpy_potokamy, 3, n)
            assert r == base, "NumPy-потоки розійшлися з послідовним"
            print("numpy потоків", n, [round(c, 3) for c in chasy],
                  "мінімум", round(t, 3), "прискорення", round(t_np / t, 2))
            nump.append({"n": n, "chasy": chasy, "min": t, "pryskorennya": t_np / t})
        vyhid["numpy"] = nump
        vyhid["proc_nast_numpy"] = navantazhennya(numpy_potokamy, os.cpu_count())
        print("процесорний / настінний, numpy", os.cpu_count(), "потоків:",
              round(vyhid["proc_nast_numpy"], 2))
    else:
        print("numpy не встановлено — ⭐ пропущено (pip install numpy)")

    shlyakh = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rezultaty.json")
    with open(shlyakh, "w", encoding="utf-8") as f:
        json.dump(vyhid, f, ensure_ascii=False, indent=2)
    print("збережено", shlyakh)

    najkrashche = max(obch[1:], key=lambda d: d["n"])
    och16 = next(d for d in och if d["n"] == 16)
    print(f"\nрядок у чат:\nядер {os.cpu_count()} · база {t_base:.1f} с · "
          f"потоків {najkrashche['n']}: ×{najkrashche['pryskorennya']:.2f} · "
          f"проц/наст {nav:.2f} · очікування 16 потоків: ×{och16['pryskorennya']:.0f}")

"""Будує 2-potoky/grafik.png і таблиці для zamiry.md з rezultaty.json.

Запуск (після potoky.py):   python 2-potoky/grafik.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TUT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(TUT, "rezultaty.json"), encoding="utf-8") as f:
    R = json.load(f)
m = R["mashyna"]

# ─────────────────────────────── графік ───────────────────────────────
SYNII, POMARANCH, BIRYUZA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1f1f1f", "#6b6b6b", "#e6e6e6"

fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
maks_n = max(d["n"] for d in R["ochikuvannya"])

kryvi = [("ochikuvannya", "Очікування (32 × sleep 0,5 с)", POMARANCH),
         ("obchyslennya", "Обчислення, чистий Python", SYNII)]
if "numpy" in R:
    kryvi.append(("numpy", "Обчислення, NumPy", BIRYUZA))

for kl, nazva, kolir in kryvi:
    d = R[kl]
    xs = [p["n"] for p in d]
    ys = [p["pryskorennya"] for p in d]
    ax.plot(xs, ys, marker="o", ms=6, lw=2, color=kolir, label=nazva, zorder=3,
            markeredgecolor="white", markeredgewidth=1.2)
    ax.annotate(f"×{ys[-1]:.2f}" if ys[-1] < 10 else f"×{ys[-1]:.0f}",
                (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=9, color=INK)

ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)
ticks = sorted({1, 2, 4, 8, 16, 32, m["cpu_count"]})
ax.set_xticks(ticks)
ax.set_xticklabels([str(t) for t in ticks])
yt = [0.5, 1, 2, 4, 8, 16, 32]
ax.set_yticks(yt)
ax.set_yticklabels(["0,5", "1", "2", "4", "8", "16", "32"])
ax.set_ylim(0.4, 45)
ax.set_xlabel("Кількість потоків", color=MUTED)
ax.set_ylabel("Прискорення (t послідовно / t потоками)", color=MUTED)
ax.set_title(f"Потоки й GIL: {m['cpu_count']} логічних ядер, Python {m['python']}",
             loc="left", color=INK, fontsize=12)
ax.grid(True, which="major", color=GRID, lw=0.8)
ax.minorticks_off()
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#c8c8c8")
ax.tick_params(colors=MUTED)
ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK)
fig.tight_layout()
fig.savefig(os.path.join(TUT, "grafik.png"))
print("збережено grafik.png")

# ─────────────────────────────── таблиці ───────────────────────────────
def tablytsya(zag, dani, znakiv=2):
    ryadky = [f"### {zag}", "",
              "| Потоків | Прогін 1 | Прогін 2 | Прогін 3 | Мінімум | Прискорення |",
              "|---|---|---|---|---|---|"]
    for p in dani:
        ch = [f"{c:.{znakiv}f}" for c in p["chasy"]] + ["—"] * (3 - len(p["chasy"]))
        n = "1 (послідовно)" if p["n"] == 1 else str(p["n"])
        ryadky.append(f"| {n} | {' | '.join(ch)} | {p['min']:.{znakiv}f} | "
                      f"×{p['pryskorennya']:.2f} |")
    return "\n".join(ryadky) + "\n"


z = R["zadacha"]
tekst = [
    "## Практична 03. Потоки і GIL\n",
    f"Машина: {m['procesor']}, логічних ядер: {m['cpu_count']} · {m['systema']} · "
    f"Python {m['python']}, GIL {m['gil']}\n",
    f"Задача: Мандельброт {z['W']}×{z['H']}, MAX_ITER={z['MAX_ITER']}. Час у секундах.\n",
    tablytsya("Обчислення: чистий Python", R["obchyslennya"]),
    f"Процесорний / настінний час, 8 потоків: **{R['proc_nast_8']:.2f}**\n",
    tablytsya("Очікування: 32 × 0,5 с", R["ochikuvannya"]),
    f"Процесорний / настінний час, очікування 16 потоків: "
    f"**{R['proc_nast_ochikuvannya_16']:.3f}**\n",
]
if "numpy" in R:
    tekst += [tablytsya("⭐ Обчислення: NumPy", R["numpy"], 3),
              f"Процесорний / настінний час, NumPy {m['cpu_count']} потоків: "
              f"**{R['proc_nast_numpy']:.2f}**\n"]
# zamiry.md лежить у корені репозиторію (поруч із 1-poslidovno/ і 2-potoky/).
# Скрипт НЕ чіпає таблиці тижня 2: він вставляє або оновлює лише розділ
# між мітками нижче, тож його можна перезапускати скільки завгодно.
POCH, KIN = "<!-- практична-03: початок -->", "<!-- практична-03: кінець -->"
rozdil = POCH + "\n" + "\n".join(tekst) + KIN + "\n"
shlyakh = os.path.join(os.path.dirname(TUT), "zamiry.md")
if os.path.exists(shlyakh):
    with open(shlyakh, encoding="utf-8") as f:
        staryi = f.read()
    if POCH in staryi and KIN in staryi:
        novyi = staryi[:staryi.index(POCH)] + rozdil + staryi[staryi.index(KIN) + len(KIN):].lstrip("\n")
    else:
        novyi = staryi.rstrip("\n") + "\n\n" + rozdil
else:
    novyi = rozdil
with open(shlyakh, "w", encoding="utf-8") as f:
    f.write(novyi)
print("оновлено", shlyakh)

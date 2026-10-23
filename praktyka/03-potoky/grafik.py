import os
import numpy as np
import matplotlib.pyplot as plt

x_potoky_obch = [1, 2, 4, 8, 12]
x_potoky_ochik = [1, 2, 4, 8, 16, 32]

y_obchyslennya = [1.0, 1.03, 0.97, 0.97, 0.97]
y_ochikuvannya = [1.0, 2.0, 4.0, 8.0, 15.9, 31.6]


def plavno(xs, ys, krokiv=300):
    x, y = np.log2(xs), np.log2(ys)
    h = np.diff(x)
    d = np.diff(y) / h
    m = np.zeros_like(y)
    for i in range(1, len(x) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0], m[-1] = d[0], d[-1]
    xn = np.linspace(x[0], x[-1], krokiv)
    i = np.clip(np.searchsorted(x, xn) - 1, 0, len(h) - 1)
    t = (xn - x[i]) / h[i]
    yn = ((2*t**3 - 3*t**2 + 1) * y[i] + (t**3 - 2*t**2 + t) * h[i] * m[i]
          + (-2*t**3 + 3*t**2) * y[i + 1] + (t**3 - t**2) * h[i] * m[i + 1])
    return 2 ** xn, 2 ** yn


plt.figure(figsize=(9, 6))
plt.plot(*plavno(x_potoky_ochik, y_ochikuvannya), "-", color="#e6b800", linewidth=2.5)
plt.plot(x_potoky_ochik, y_ochikuvannya, "D", color="#e6b800", markersize=9)
plt.plot(*plavno(x_potoky_obch, y_obchyslennya), "-", color="#7b2cbf", linewidth=2.5)
plt.plot(x_potoky_obch, y_obchyslennya, "o", color="#7b2cbf", markersize=9)

plt.plot([], [], "D-", color="#e6b800", linewidth=2.5, markersize=9, label="Очікування")
plt.plot([], [], "o-", color="#7b2cbf", linewidth=2.5, markersize=9, label="Обчислення")

plt.xscale("log", base=2)
plt.yscale("log", base=2)
ticks = [1, 2, 4, 8, 12, 16, 32]
plt.xticks(ticks, [str(t) for t in ticks], fontsize=12)
plt.yticks([0.5, 1, 2, 4, 8, 16, 32], ["0,5", "1", "2", "4", "8", "16", "32"], fontsize=12)
plt.minorticks_off()
plt.ylim(0.5, 40)

plt.xlabel("Кількість потоків", fontsize=13)
plt.ylabel("Прискорення, разів", fontsize=13)
plt.legend(loc="upper left", fontsize=13)
plt.grid(True, alpha=0.3)
plt.tight_layout()

tut = os.path.dirname(os.path.abspath(__file__))
plt.savefig(os.path.join(tut, "grafik.png"), dpi=150)

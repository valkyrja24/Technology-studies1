import os
import matplotlib.pyplot as plt

x_potoky_obch = [1, 2, 4, 8, 12]
x_potoky_ochik = [1, 2, 4, 8, 16, 32]

y_obchyslennya = [1.0, 1.03, 0.97, 0.97, 0.97]
y_ochikuvannya = [1.0, 2.0, 4.0, 8.0, 15.9, 31.6]

plt.plot(x_potoky_obch, y_obchyslennya, "o-", label="Обчислення")
plt.plot(x_potoky_ochik, y_ochikuvannya, "s-", label="Очікування")
plt.title("Прискорення потоками: обчислення й очікування")
plt.xlabel("Кількість потоків")
plt.ylabel("Прискорення, разів")
plt.legend()
plt.grid(True)

tut = os.path.dirname(os.path.abspath(__file__))
plt.savefig(os.path.join(tut, "grafik.png"), dpi=120)

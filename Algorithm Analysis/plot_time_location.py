##plot_time_location.py##
#used to analyze execution time by location in the geodata
#(used in figure 38 in thesis)

import matplotlib.pyplot as plt

#insert data
cities = ['Nydalen, Oslo', 'Manhattan, New York', 'Rome, Italy']
times_seconds = [17280.712, 10389.311, 5479.678]
times_labels = [f"{int(t // 3600)}h {int((t % 3600) // 60)}m " for t in times_seconds]

#plot
plt.figure(figsize=(6, 4))
bars = plt.bar(cities, times_seconds, color='skyblue', width=0.4)

for bar, label in zip(bars, times_labels):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height + 200, label,
             ha='center', va='bottom', fontsize=17)

plt.title("Execution Time by Location", fontsize=18)
plt.ylabel("Time (seconds)", fontsize=16)
plt.xticks(fontsize=16)
plt.yticks(fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()






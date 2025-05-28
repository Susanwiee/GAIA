###plot_fitness_evolution.py####
#this codes plot the fitness across generations
#(used to produce figure 28 and 36 in thesis)


import matplotlib.pyplot as plt
import re

#load the fitness report text
with open("(insert pat).......GAIA/fitness_per_generationtid.txt", "r") as f:
    lines = f.readlines()

#initialize list
generations = []
total_fitness = []
gfa = []
shadow_nature = []
walkability = []
cycleability = []
serviceability = []
shadow_buildings = []

for i, line in enumerate(lines):
    if line.startswith("Generation"):
        generations.append(int(re.findall(r'\d+', line)[0]))
        total_fitness.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 1])[0]))
        gfa.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 2])[0]))
        shadow_nature.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 3])[0]))
        walkability.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 4])[0]))
        cycleability.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 5])[0]))
        serviceability.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 6])[0]))
        shadow_buildings.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", lines[i + 7])[0]))

#plotting fitness scores
plt.figure(figsize=(12, 6))
plt.plot(generations, gfa, label="GFA")
plt.plot(generations, shadow_nature, label="Shadow Nature")
plt.plot(generations, walkability, label="Walkability")
plt.plot(generations, cycleability, label="Cycleability")
plt.plot(generations, serviceability, label="Serviceability")
plt.plot(generations, shadow_buildings, label="Shadow Buildings")
plt.plot(generations, total_fitness, label="Total Fitness", linewidth=3, color='black')

plt.xlabel("Generation", fontsize=16)
plt.ylabel("Fitness Score", fontsize=16)
plt.title("Fitness Evolution per Generation", fontsize=16)
plt.legend(
    loc='upper left',
    bbox_to_anchor=(1.01, 1),
    fontsize=15,
    borderaxespad=0.
)
plt.grid(True)
plt.tight_layout()
plt.show()


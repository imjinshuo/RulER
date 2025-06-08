import os.path

methods = ['BatFix', 'RulER', 'LLM']
model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
langs = ['Java', 'Python']

info = {'RulER':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'LLM':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'BatFix':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}}}
sameinfo = {'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}}
S_pass_java = {'BatFix':[], 'LLM':[], 'RulER':[]}
S_pass_python = {'BatFix':[], 'LLM':[], 'RulER':[]}

N_totals = {'TransCoder': {'Java': 24, 'Python': 131}, 'TransCoderST': {'Java': 30, 'Python': 197}, 'Codex': {'Java': 20, 'Python': 44}, 'Qwen2.5-Coder-32B-Instruct': {'Java': 16, 'Python': 91}}
for method in methods:
    for model in model_names:
        for lang in langs:
            if method == 'BatFix' and model == 'Qwen2.5-Coder-32B-Instruct':
                continue
            print(f'{method}-{model}-{lang}-to-C++:')
            IDs = []
            for round_id in range(1, 6):
                file1 = f'{method}/round{round_id}-info/info/{model}-{lang}-C++-fixinfo.txt'
                file2 = f'{method}/round{round_id}-info/info/{model}-{lang}-C++-fixinfo-uncompare.txt'
                lines = []
                if os.path.exists(file1):
                    f1_lines = open(file1).readlines()
                    lines.extend(f1_lines)
                if os.path.exists(file2):
                    f2_lines = open(file2).readlines()
                    lines.extend(f2_lines)
                for line in lines:
                    items = line.strip().split('\t')
                    ID = items[0]
                    ori_same = int(items[1])
                    new_same = int(items[2])
                    if new_same:
                        if ID not in IDs:
                            IDs.append(ID)
                        else:
                            print('')
                print(f'{round_id}: {len(IDs)}')
            info[method][model][lang] = IDs[:]
            S_pass = round(len(IDs)/N_totals[model][lang], 4)
            print(f'{method}-{model}-{lang}-to-C++:')
            print(f'N_pass: {len(IDs)}')
            print(f'N_total: {N_totals[model][lang]}')
            print(f'S_pass: {S_pass}')
            print('')
            if lang == 'Java':
                S_pass_java[method].append(S_pass)
            elif lang == 'Python':
                S_pass_python[method].append(S_pass)

print('Java')
for method in methods:
    print(f'{method} average S_pass: {sum(S_pass_java[method]) / len(S_pass_java[method])}')
print('Python')
for method in methods:
    print(f'{method} average S_pass: {sum(S_pass_python[method]) / len(S_pass_python[method])}')

for model in model_names:
    for lang in langs:
        IDs1 = info['RulER'][model][lang]
        IDs2 = info['LLM'][model][lang]
        same_IDs = [item for item in IDs1 if item in IDs2]
        sameinfo[model][lang] = same_IDs[:]

java_same = 0
# print('Java')
for model in model_names:
    lang = 'Java'
    java_same += len(sameinfo[model][lang])
# print(java_same)
python_same = 0
# print('Python')
for model in model_names:
    lang = 'Python'
    python_same += len(sameinfo[model][lang])
# print(python_same)

for method in methods:
    # print(method)
    more = 0
    for model in model_names:
        lang = 'Java'
        more += len(info[method][model][lang]) - len(sameinfo[model][lang])
        # print(len(info[method][model][lang]) - len(sameinfo[model][lang]))
    # print('more:', more)

for method in methods:
    # print(method)
    more = 0
    for model in model_names:
        lang = 'Python'
        more += len(info[method][model][lang]) - len(sameinfo[model][lang])
        # print(len(info[method][model][lang]) - len(sameinfo[model][lang]))
    # print('more:', more)

import matplotlib.pyplot as plt
from matplotlib_venn import venn2

RulER_set_Java = []
for model in model_names:
    lang = 'Java'
    for item in info['RulER'][model][lang]:
        RulER_set_Java.append(model+item)
RulER_set_Java = set(RulER_set_Java)
RulER_set_Python = []
for model in model_names:
    lang = 'Python'
    for item in info['RulER'][model][lang]:
        RulER_set_Python.append(model+item)
RulER_set_Python = set(RulER_set_Python)
LLM_set_Java = []
for model in model_names:
    lang = 'Java'
    for item in info['LLM'][model][lang]:
        LLM_set_Java.append(model+item)
LLM_set_Java = set(LLM_set_Java)
LLM_set_Python = []
for model in model_names:
    lang = 'Python'
    for item in info['LLM'][model][lang]:
        LLM_set_Python.append(model+item)
LLM_set_Python = set(LLM_set_Python)

default_colors = [
    # r, g, b, a
    [92, 192, 98, 0.5],
    [90, 155, 212, 0.5],
    [246, 236, 86, 0.6],
    [241, 90, 96, 0.4],
    [255, 117, 0, 0.3],
    [82, 82, 190, 0.2],
]

default_colors = [
    [i[0] / 255.0, i[1] / 255.0, i[2] / 255.0, i[3]]
    for i in default_colors
]

v1 = venn2([LLM_set_Java, RulER_set_Java], ('Qwen2.5 Fixed Programs', 'RulER Fixed Programs'), set_colors=(default_colors[1], default_colors[0]), alpha=0.4)
overlap = v1.get_patch_by_id('A')
overlap.set_edgecolor(default_colors[1])
overlap.set_lw(1.5)
overlap = v1.get_patch_by_id('B')
overlap.set_edgecolor(default_colors[0])
overlap.set_lw(1.5)
overlap = v1.get_patch_by_id('C')
overlap.set_lw(1.5)

plt.show()

v2 = venn2([LLM_set_Python, RulER_set_Python], ('Qwen2.5 Fixed Programs', 'RulER Fixed Programs'), set_colors=(default_colors[1], default_colors[0]), alpha=0.4)
overlap = v2.get_patch_by_id('A')
overlap.set_edgecolor(default_colors[1])
overlap.set_lw(1.5)
overlap = v2.get_patch_by_id('B')
overlap.set_edgecolor(default_colors[0])
overlap.set_lw(1.5)
overlap = v2.get_patch_by_id('C')
overlap.set_lw(1.5)

plt.show()









import os.path
from openpyxl import Workbook


def list_to_excel(data_list, filename):
    wb = Workbook()
    ws = wb.active
    for index, item in enumerate(data_list, start=1):
        ws.cell(row=index, column=1, value=item)
    wb.save(filename)

methods = ['BatFix', 'TransAgent', 'LLM-Test-Aware', 'LLM-Value-Aware', 'RulER', 'RulER(vsBatFix)']
model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
langs = ['Java', 'Python']

info = {'RulER':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'TransAgent':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'LLM-Test-Aware':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'LLM-Value-Aware':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'BatFix':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}},
        'RulER(vsBatFix)':{'TransCoder':{'Java':[], 'Python':[]}, 'TransCoderST':{'Java':[], 'Python':[]}, 'Codex':{'Java':[], 'Python':[]}, 'Qwen2.5-Coder-32B-Instruct':{'Java':[], 'Python':[]}}}
S_pass_java = {'BatFix':[],
               'TransAgent':[],
               'LLM-Test-Aware':[],
               'LLM-Value-Aware':[],
               'RulER':[],
               'RulER(vsBatFix)':[]}
S_pass_sum_java = {'BatFix':0,
                   'TransAgent':0,
                   'LLM-Test-Aware':0,
                   'LLM-Value-Aware':0,
                   'RulER(vsBatFix)':0,
                   'RulER':0}
S_total_sum_java = {'BatFix':0,
                    'TransAgent':0,
                   'LLM-Test-Aware':0,
                   'LLM-Value-Aware':0,
                   'RulER(vsBatFix)':0,
                    'RulER':0}
S_pass_python = {'BatFix':[],
                 'TransAgent':[],
                 'LLM-Test-Aware':[],
                 'LLM-Value-Aware':[],
                 'RulER(vsBatFix)':[],
                 'RulER':[]}
S_pass_sum_python = {'BatFix':0,
                     'TransAgent':0,
                   'LLM-Test-Aware':0,
                   'LLM-Value-Aware':0,
                   'RulER(vsBatFix)':0,
                     'RulER':0}
S_total_sum_python = {'BatFix':0,
                      'TransAgent':0,
                   'LLM-Test-Aware':0,
                   'LLM-Value-Aware':0,
                   'RulER(vsBatFix)':0,
                      'RulER':0}

dataset = None
N_totals_BatFix = {'TransCoder': {'Java': 0, 'Python': 0}, 'TransCoderST': {'Java': 0, 'Python': 0}, 'Codex': {'Java': 0, 'Python': 0}}
N_totals = {'TransCoder': {'Java': 0, 'Python': 0}, 'TransCoderST': {'Java': 0, 'Python': 0}, 'Codex': {'Java': 0, 'Python': 0}, 'Qwen2.5-Coder-32B-Instruct': {'Java': 0, 'Python': 0}}

if dataset == 'LeetCode':
    for sut in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for lang in ['Java', 'Python']:
            files = os.listdir(f'/home/ubuntu/RulER/DATABASE/DATA/CODE/{sut}-data/{lang}')
            for file in files:
                ID = file.split('.')[0]
                if ID.isdigit():
                    N_totals[sut][lang] += 1
                    if ID.isdigit() or ID.startswith('CTCI') or sut == 'Qwen2.5-Coder-32B-Instruct':
                        continue
                    N_totals_BatFix[sut][lang] += 1
elif dataset == 'CTCI':
    for sut in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for lang in ['Java', 'Python']:
            files = os.listdir(f'/home/ubuntu/RulER/DATABASE/DATA/CODE/{sut}-data/{lang}')
            for file in files:
                ID = file.split('.')[0]
                if ID.startswith('CTCI'):
                    N_totals[sut][lang] += 1
                    if ID.isdigit() or ID.startswith('CTCI') or sut == 'Qwen2.5-Coder-32B-Instruct':
                        continue
                    N_totals_BatFix[sut][lang] += 1
elif dataset == 'GeeksforGeeks':
    for sut in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for lang in ['Java', 'Python']:
            files = os.listdir(f'/home/ubuntu/RulER/DATABASE/DATA/CODE/{sut}-data/{lang}')
            for file in files:
                ID = file.split('.')[0]
                if ID.isdigit() or ID.startswith('CTCI'):
                    continue
                N_totals[sut][lang] += 1
                if ID.isdigit() or ID.startswith('CTCI') or sut == 'Qwen2.5-Coder-32B-Instruct':
                    continue
                N_totals_BatFix[sut][lang] += 1
else:
    for sut in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for lang in ['Java', 'Python']:
            files = os.listdir(f'/home/ubuntu/RulER/DATABASE/DATA/CODE/{sut}-data/{lang}')
            for file in files:
                ID = file.split('.')[0]
                N_totals[sut][lang] += 1
                if ID.isdigit() or ID.startswith('CTCI') or sut == 'Qwen2.5-Coder-32B-Instruct':
                    continue
                N_totals_BatFix[sut][lang] += 1

TransAgent_IDs = []
RulER_IDs = []
RulERvsBatFix_IDs = []
BatFix_IDs = []
LLM_value_IDs = []
LLM_test_IDs = []
for method in methods:
    for lang in langs:
        for model in model_names:
            if method in ['BatFix', 'RulER(vsBatFix)'] and model == 'Qwen2.5-Coder-32B-Instruct':
                continue
            print(f'{method}-{model}-{lang}-to-C++:')
            IDs = []
            max_round = 6
            repaired_ids_each_round = []
            if method == 'TransAgent':
                if os.path.exists(f'{method}/info/{model}-{lang}-C++'):
                    files = os.listdir(f'{method}/info/{model}-{lang}-C++')
                else:
                    files = []
                for file in files:
                    ID = file.split('.')[0]
                    lines = open(f'{method}/info/{model}-{lang}-C++/{file}').readlines()
                    same = 0
                    for line in lines:
                        if line.strip():
                            this_same = int(line.split('\t')[0])
                            if this_same > same:
                                same = this_same
                    if same == 10:
                        if ID not in IDs:
                            IDs.append(ID)
                repaired_ids_each_round.append(f'{round_id}: {len(IDs)}')
            elif method == 'RulER(vsBatFix)':
                for round_id in range(1, max_round):
                    if os.path.exists(f'RulER/round{round_id}-info/info/{model}-{lang}-C++'):
                        files = os.listdir(f'RulER/round{round_id}-info/info/{model}-{lang}-C++')
                    else:
                        files = []
                    for file in files:
                        ID = file.split('.')[0]
                        if not ID.isdigit() and not ID.startswith('CTCI'):
                            lines = open(f'RulER/round{round_id}-info/info/{model}-{lang}-C++/{file}').readlines()
                            same = 0
                            for line in lines:
                                if line.strip():
                                    this_same = int(line.split('\t')[0])
                                    if this_same > same:
                                        same = this_same
                            if same == 10:
                                if ID not in IDs:
                                    IDs.append(ID)
                    repaired_ids_each_round.append(f'{round_id}: {len(IDs)}')
            else:
                for round_id in range(1, max_round):
                    if os.path.exists(f'{method}/round{round_id}-info/info/{model}-{lang}-C++'):
                        files = os.listdir(f'{method}/round{round_id}-info/info/{model}-{lang}-C++')
                    else:
                        files = []
                    for file in files:
                        ID = file.split('.')[0]
                        lines = open(f'{method}/round{round_id}-info/info/{model}-{lang}-C++/{file}').readlines()
                        same = 0
                        for line in lines:
                            if line.strip():
                                this_same = int(line.split('\t')[0])
                                if this_same > same:
                                    same = this_same
                        if same == 10:
                            if ID not in IDs:
                                IDs.append(ID)
                    repaired_ids_each_round.append(f'{round_id}: {len(IDs)}')
            if dataset == 'LeetCode':
                IDs = [ID for ID in IDs if ID.isdigit()]
            elif dataset == 'CTCI':
                IDs = [ID for ID in IDs if ID.startswith('CTCI_')]
            elif dataset == 'GeeksforGeeks':
                IDs = [ID for ID in IDs if not (ID.isdigit() or ID.startswith('CTCI_'))]
            print(' '.join(repaired_ids_each_round))
            info[method][model][lang] = IDs[:]
            S_pass = 0
            out_S_pass = 0
            if method in ['BatFix', 'RulER(vsBatFix)']:
                if N_totals_BatFix[model][lang]:
                    S_pass = round(len(IDs)/N_totals_BatFix[model][lang], 3)
                    out_S_pass = round((len(IDs)/N_totals_BatFix[model][lang])*100, 1)
            else:
                if N_totals[model][lang]:
                    S_pass = round(len(IDs)/N_totals[model][lang], 3)
                    out_S_pass = round((len(IDs)/N_totals[model][lang])*100, 1)
            if method in ['BatFix', 'RulER(vsBatFix)']:
                print(f'{N_totals_BatFix[model][lang]} & {len(IDs)} & {out_S_pass}\\%')
            else:
                print(f'{N_totals[model][lang]} & {len(IDs)} & {out_S_pass}\\%')
            if lang == 'Java':
                S_pass_java[method].extend(IDs)
                S_pass_sum_java[method] += len(IDs)
                if method in ['BatFix', 'RulER(vsBatFix)']:
                    S_total_sum_java[method] += N_totals_BatFix[model][lang]
                else:
                    S_total_sum_java[method] += N_totals[model][lang]
            elif lang == 'Python':
                S_pass_python[method].extend(IDs)
                S_pass_sum_python[method] += len(IDs)
                if method in ['BatFix', 'RulER(vsBatFix)']:
                    S_total_sum_python[method] += N_totals_BatFix[model][lang]
                else:
                    S_total_sum_python[method] += N_totals[model][lang]
            IDs.sort()
            for ID in IDs:
                if method in ['TransAgent']:
                    TransAgent_IDs.append(f'{model}-{lang}-{ID}')
                elif method in ['RulER']:
                    RulER_IDs.append(f'{model}-{lang}-{ID}')
                elif method in ['RulER(vsBatFix)']:
                    if 'Qwen2.5-Coder-32B-Instruct' not in ID and not ID.split('-')[-1].isdigit() and not ID.split('-')[-1].startswith('CTCI'):
                        RulERvsBatFix_IDs.append(f'{model}-{lang}-{ID}')
                elif method in ['BatFix']:
                    BatFix_IDs.append(f'{model}-{lang}-{ID}')
                elif method in ['LLM-Test-Aware']:
                    LLM_test_IDs.append(f'{model}-{lang}-{ID}')
                elif method in ['LLM-Value-Aware']:
                    LLM_value_IDs.append(f'{model}-{lang}-{ID}')

sum_N_totals_BatFix = 0
for lang in langs:
    for model in model_names:
        if model in N_totals_BatFix:
            sum_N_totals_BatFix += N_totals_BatFix[model][lang]
sum_N_totals = 0
for lang in langs:
    for model in model_names:
        sum_N_totals += N_totals[model][lang]

print('\n')

if dataset is not None:
    print(f'Results on {dataset}:')
else:
    print(f'Results on All datasets:')

if BatFix_IDs:
    print(f"RulER than BatFix: {round((len(RulERvsBatFix_IDs)-len(BatFix_IDs))/len(BatFix_IDs), 3)}")
print(f"RulER than TransAgent: {round((len(RulER_IDs)-len(TransAgent_IDs))/len(TransAgent_IDs), 3)}")
print(f"RulER than LLM_Test: {round((len(RulER_IDs)-len(LLM_test_IDs))/len(LLM_test_IDs), 3)}")
print(f"RulER than LLM_Value: {round((len(RulER_IDs)-len(LLM_value_IDs))/len(LLM_value_IDs), 3)}")

if sum_N_totals_BatFix:
    print(f"\nBatFix average repair succ: {round(len(BatFix_IDs)/sum_N_totals_BatFix, 3)}")
print(f"TransAGENT average repair succ: {round(len(TransAgent_IDs)/sum_N_totals, 3)}")
print(f"LLM_Test average repair succ: {round(len(LLM_test_IDs)/sum_N_totals, 3)}")
print(f"LLM_Value average repair succ: {round(len(LLM_value_IDs)/sum_N_totals, 3)}")
print(f"RulER average repair succ: {round(len(RulER_IDs)/sum_N_totals, 3)}")
combine_IDs = set(TransAgent_IDs+RulER_IDs)
print(f"TransAGENT+RulER average repair succ: {round(len(combine_IDs)/sum_N_totals, 3)}")
print(f"Delta: {round(round(len(combine_IDs)/sum_N_totals, 3)-round(len(TransAgent_IDs)/sum_N_totals, 3), 3)}")


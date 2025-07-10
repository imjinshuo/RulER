import os
import copy
import nltk
import argparse
from strsimpy.levenshtein import Levenshtein
from strsimpy.longest_common_subsequence import LongestCommonSubsequence
from strsimpy.normalized_levenshtein import NormalizedLevenshtein
levenshtein = Levenshtein()
lcs = LongestCommonSubsequence()
normalized_levenshtein = NormalizedLevenshtein()


def loadMap(path):
    files = os.listdir(path)
    map = {}
    for file in files:
        f = open(f'{path}/{file}')
        lines = f.readlines()
        f.close()
        ID = file.split('.')[0]
        map[ID] = []
        for line in lines:
            if line.strip():
                map[ID].append([line.strip().split(';')[0], line.strip().split(';')[1]])
    return map


def read_code(file_path, lang):
    f = open(file_path)
    lines = f.readlines()
    filter_lines = []
    if lang == 'Java':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if line.strip().endswith(';') and line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line.replace(';', ') ;')
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            filter_lines.append(this_line)
    elif lang == 'Python':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line + ' )'
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            if line.strip().startswith('if (') and line.strip().endswith(') :'):
                this_line = this_line.replace('if (', 'if')
                this_line = this_line.replace(') :', ':')
            if line.strip().startswith('while (') and line.strip().endswith(') :'):
                this_line = this_line.replace('while (', 'while')
                this_line = this_line.replace(') :', ':')
            filter_lines.append(this_line)
    elif lang == 'C++':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if 'std :: ' in line:
                this_line = this_line.replace('std :: ', '')
            if line.strip().endswith(';') and line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line.replace(';', ') ;')
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            if line.strip().startswith('while ( ( ') and line.strip().endswith(' ) ) {') and line.count('(') == 2:
                this_line = this_line.replace('while ( ( ', 'while ( ')
                this_line = this_line.replace(' ) ) {', ' ) {')
            if line.strip().startswith('if ( ( ') and line.strip().endswith(' ) ) {') and line.count('(') == 2:
                this_line = this_line.replace('if ( ( ', 'if ( ')
                this_line = this_line.replace(' ) ) {', ' ) {')
            filter_lines.append(this_line)
    wholecode = ''.join(lines)
    f.close()
    return wholecode, filter_lines


def run(path, target_model_name, source_lang, target_lang):
    gt_map = loadMap(f'{path_to_DATABASE}/DATA/MAP/{target_model_name}-{source_lang}-{target_lang}-GT-mapping')
    generated_map = loadMap(path)
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    ID2label = {}
    f_IDlabel = open(f'{path_to_DATABASE}/DATA/BUG/{target_model_name}-{source_lang}-{target_lang}.txt')
    lines = f_IDlabel.readlines()
    for line in lines:
        items = line.split('|')
        ID2label[items[0]] = []
        for item in items[1:]:
            ID2label[items[0]].append(int(item))
    script_dir = f'{path_to_DATABASE}/DATA/CODE/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
    code_files = os.listdir(script_dir)
    code_dir = f'{path_to_DATABASE}/DATA/CODE/{target_model_name}-data/{source_lang}'
    transcode_dir = f'{path_to_DATABASE}/DATA/CODE/{target_model_name}-data/{source_lang}-{target_lang}'
    IDs = [code_file.split('.')[0] for code_file in code_files if code_file.split('.')[0] in ID2label]
    IDs.sort()
    total = 0
    total_gt = 0
    right = 0
    wrong = 0
    correct_sim_list = []
    wrong_sim_list = []
    for ID in IDs:
        _, source_lines = read_code(f'{code_dir}/{ID}.{source_ext}', source_lang)
        _, trans_lines = read_code(f'{transcode_dir}/{ID}.{target_ext}', target_lang)
        for pair in gt_map[ID]:
            total_gt += 1
        if ID in generated_map:
            this_wrong = []
            for pair in generated_map[ID]:
                if int(pair[0]) < len(source_lines) and source_lines[int(pair[0])].strip() in ['{', '}'] \
                        and int(pair[1]) < len(trans_lines) and trans_lines[int(pair[1])].strip() == source_lines[int(pair[0])].strip():
                    continue
                total += 1
                if pair not in gt_map[ID]:
                    try:
                        score = nltk.translate.bleu_score.sentence_bleu([source_lines[int(pair[0])].strip()], trans_lines[int(pair[1])].strip(), weights=(0.5, 0.5))
                        wrong_sim_list.append(score)
                    except:
                        None
                    wrong += 1
                    this_wrong.append(pair)
                else:
                    try:
                        score = nltk.translate.bleu_score.sentence_bleu([source_lines[int(pair[0])].strip()], trans_lines[int(pair[1])].strip(), weights=(0.5, 0.5))
                        correct_sim_list.append(score)
                    except:
                        None
                    right += 1
    precision = round(right/(right + wrong), 3)
    recall = round(right/total_gt, 3)
    f1 = round((2 * precision * recall) / (precision + recall), 3)

    print(f'{target_model_name}-{source_lang}-{target_lang}')
    print('N_gen:', total)
    print('TP:', right)
    print('FP:', wrong)
    print('TP+FN:', total_gt)
    print('Precision:', precision)
    print('Recall:', recall)
    print('F1:', f1)
    print('')
    return correct_sim_list, wrong_sim_list, precision, recall, f1, right, wrong, total_gt


def calculate(all_sim, k):
    nums = [round(i*(1/k), 2) for i in range(k)]
    nums.append(1.0)

    count = [0 for _ in range(len(nums)-1)]
    for item in all_sim['correct_map']:
        for val_id, val in enumerate(nums[:-1]):
            if val_id == 0:
                if val <= item and item <= nums[val_id+1]:
                    count[val_id] += 1
                    break
            else:
                if val < item and item <= nums[val_id+1]:
                    count[val_id] += 1
                    break

    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_DATABASE",
        default='/DATABASE',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    path_to_DATABASE = args.path_to_DATABASE

    data_collect = []
    methods = ['BatFix', 'TransMap', 'RulER', 'GT']
    target_model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
    TPs = {'BatFix':0, 'TransMap':0, 'RulER':0, 'GT':0}
    FPs = {'BatFix':0, 'TransMap':0, 'RulER':0, 'GT':0}
    TP_FNs = {'BatFix':0, 'TransMap':0, 'RulER':0, 'GT':0}
    precisions = {'BatFix':[], 'TransMap':[], 'RulER':[], 'GT':[]}
    recalls = {'BatFix':[], 'TransMap':[], 'RulER':[], 'GT':[]}
    f1s = {'BatFix':[], 'TransMap':[], 'RulER':[], 'GT':[]}
    source_langs = ['Java']
    target_lang = 'C++'
    all_sim_java = {'BatFix': {'correct_map': [], 'wrong_map': []}, 'TransMap': {'correct_map': [], 'wrong_map': []}, 'RulER': {'correct_map': [], 'wrong_map': []}, 'GT': {'correct_map': [], 'wrong_map': []}}
    for target_model_name in target_model_names:
        for source_lang in source_langs:
            for method_id, path in enumerate([f'BatFix_map/{target_model_name}-{source_lang}-{target_lang}-Batfix-mapping',
                                              f'TransMap_map/{target_model_name}/{source_lang}-{target_lang}',
                                              f'RulER_map/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping',
                                              f'{path_to_DATABASE}/DATA/MAP/{target_model_name}-{source_lang}-{target_lang}-GT-mapping']):
                print(f'{methods[method_id]}-{source_lang}-{target_lang}')
                correct_sim_list, wrong_sim_list, precision, recall, f1, TP, FP, TP_FN = run(path, target_model_name, source_lang, target_lang)
                TPs[methods[method_id]] += TP
                FPs[methods[method_id]] += FP
                TP_FNs[methods[method_id]] += TP_FN
                precisions[methods[method_id]].append(precision)
                f1s[methods[method_id]].append(f1)
                recalls[methods[method_id]].append(recall)
                all_sim_java[methods[method_id]]['correct_map'].extend(correct_sim_list)
                all_sim_java[methods[method_id]]['wrong_map'].extend(wrong_sim_list)

    # precisions = {'BatFix':[], 'TransMap':[], 'RulER':[], 'GT':[]}
    # recalls = {'BatFix':[], 'TransMap':[], 'RulER':[], 'GT':[]}
    source_langs = ['Python']
    target_lang = 'C++'
    all_sim_py = {'BatFix': {'correct_map': [], 'wrong_map': []}, 'TransMap': {'correct_map': [], 'wrong_map': []}, 'RulER': {'correct_map': [], 'wrong_map': []}, 'GT': {'correct_map': [], 'wrong_map': []}}
    for target_model_name in target_model_names:
        for source_lang in source_langs:
            for method_id, path in enumerate([f'BatFix_map/{target_model_name}-{source_lang}-{target_lang}-Batfix-mapping',
                                              f'TransMap_map/{target_model_name}/{source_lang}-{target_lang}',
                                              f'RulER_map/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping',
                                              f'{path_to_DATABASE}/DATA/MAP/{target_model_name}-{source_lang}-{target_lang}-GT-mapping']):
                print(f'{methods[method_id]}-{source_lang}-{target_lang}')
                correct_sim_list, wrong_sim_list, precision, recall, f1, TP, FP, TP_FN = run(path, target_model_name, source_lang, target_lang)
                TPs[methods[method_id]] += TP
                FPs[methods[method_id]] += FP
                TP_FNs[methods[method_id]] += TP_FN
                precisions[methods[method_id]].append(precision)
                recalls[methods[method_id]].append(recall)
                f1s[methods[method_id]].append(f1)
                all_sim_py[methods[method_id]]['correct_map'].extend(correct_sim_list)
                all_sim_py[methods[method_id]]['wrong_map'].extend(wrong_sim_list)

    BatFix_ave_r = 0
    TransMap_ave_r = 0
    RulER_ave_r = 0
    for method in methods:
        TP = TPs[method]
        FP = FPs[method]
        TP_FN = TP_FNs[method]
        precision = round(TP / (TP + FP), 3)
        recall = round(TP / TP_FN, 3)
        f1 = round((2 * precision * recall) / (precision + recall), 3)
        print(f'{method} average Precision: {precision}')
        print(f'{method} average Recall: {recall}')
        print(f'{method} average F1: {f1}')
        if method == 'BatFix':
            BatFix_ave_r = f1
        if method == 'TransMap':
            TransMap_ave_r = f1
        if method == 'RulER':
            RulER_ave_r = f1

    print(f'\nRulER than BatFix in average F1: {round((RulER_ave_r - BatFix_ave_r) / BatFix_ave_r, 2)}')
    print(f'RulER than TransMap in average F1: {round((RulER_ave_r - TransMap_ave_r) / TransMap_ave_r, 2)}')
    print('')

    print('Java-to-C++:')
    print('\t'.join(['[0, 0.1]', '(0.1, 0.2]', '(0.2, 0.3]', '(0.3, 0.4]', '(0.4, 0.5]', '(0.5, 0.6]', '(0.6, 0.7]', '(0.7, 0.8]', '(0.8, 0.9]', '(0.9, 1]']))
    count1 = calculate(all_sim_java['GT'], 10)
    count = calculate(all_sim_java['BatFix'], 10)
    print('BatFix', '\t'.join([str(round(item/item1, 2)) for item1, item in zip(count1, count)]))
    count = calculate(all_sim_java['TransMap'], 10)
    print('TransMap', '\t'.join([str(round(item/item1, 2)) for item1, item in zip(count1, count)]))
    count = calculate(all_sim_java['RulER'], 10)
    print('RulER', '\t'.join([str(round(item/item1, 2)) for item1, item in zip(count1, count)]))
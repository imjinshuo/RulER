import os
import copy
import nltk
import argparse
from utils import *


def run(path, target_model_name, source_lang, target_lang, dataset=None):
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
    all_sim_list = []

    if dataset == 'LeetCode':
        IDs = [ID for ID in IDs if ID.isdigit()]
    elif dataset == 'CTCI':
        IDs = [ID for ID in IDs if ID.startswith('CTCI_')]
    elif dataset == 'GeeksforGeeks':
        IDs = [ID for ID in IDs if not(ID.isdigit() or ID.startswith('CTCI_'))]

    for ID in IDs:
        if 'BatFix' in path:
            if ID.isdigit() or ID.startswith('CTCI_'):
                continue
        _, source_lines = read_code(f'{code_dir}/{ID}.{source_ext}', source_lang)
        _, trans_lines = read_code(f'{transcode_dir}/{ID}.{target_ext}', target_lang)
        for pair in gt_map[ID]:
            score = nltk.translate.bleu_score.sentence_bleu([source_lines[int(pair[0])].strip()], trans_lines[int(pair[1])].strip(), weights=(0.5, 0.5))
            all_sim_list.append(score)
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
    if right + wrong:
        precision = round(right/(right + wrong), 3)
        recall = round(right/total_gt, 3)
        f1 = round((2 * precision * recall) / (precision + recall), 3)

        out_precision = round((right/(right + wrong))*100, 1)
        out_recall = round((right/total_gt)*100, 1)
        out_f1 = round(((2 * precision * recall) / (precision + recall))*100, 1)
        print(f'{out_precision}\\% & {out_recall}\\% & {out_f1}\\%')
        return correct_sim_list, wrong_sim_list, all_sim_list, precision, recall, f1, right, wrong, total_gt
    else:
        precision = 0
        recall = 0
        f1 = 0

        out_precision = 0
        out_recall = 0
        out_f1 = 0
        print(f'{out_precision}\\% & {out_recall}\\% & {out_f1}\\%')
        return correct_sim_list, wrong_sim_list, all_sim_list, precision, recall, f1, right, wrong, total_gt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_DATABASE",
        default='/home/ubuntu/RulER/DATABASE',
        type=str,
        required=True,
        help=""
    )
    args = parser.parse_args()
    path_to_DATABASE = args.path_to_DATABASE

    data_collect = []
    target_model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
    methods = ['BatFix', 'TransAgent', 'TransMapGPT', 'TransMapQwen', 'RulER', 'GT']
    TPs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0, 'GT':0}
    FPs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0, 'GT':0}
    TP_FNs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0, 'GT':0}
    precisions = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[], 'GT':[]}
    recalls = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[], 'GT':[]}
    f1s = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[], 'GT':[]}
    target_lang = 'C++'
    all_sim = {'BatFix': {'correct_map': [], 'wrong_map': [], 'all': []}, 'TransAgent': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapGPT': {'correct_map': [], 'wrong_map': [], 'all': []}, 'RulER': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapQwen': {'correct_map': [], 'wrong_map': [], 'all': []},
               'GT': {'correct_map': [], 'wrong_map': [], 'all': []}}
    all_sim_java = {'BatFix': {'correct_map': [], 'wrong_map': [], 'all': []}, 'TransAgent': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapGPT': {'correct_map': [], 'wrong_map': [], 'all': []}, 'RulER': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapQwen': {'correct_map': [], 'wrong_map': [], 'all': []},
               'GT': {'correct_map': [], 'wrong_map': [], 'all': []}}
    all_sim_py = {'BatFix': {'correct_map': [], 'wrong_map': [], 'all': []}, 'TransAgent': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapGPT': {'correct_map': [], 'wrong_map': [], 'all': []}, 'RulER': {'correct_map': [], 'wrong_map': [], 'all': []},
               'TransMapQwen': {'correct_map': [], 'wrong_map': [], 'all': []},
               'GT': {'correct_map': [], 'wrong_map': [], 'all': []}}
    for target_model_name in target_model_names:
        for source_lang in ['Java', 'Python']:
            print(f'{target_model_name}-{source_lang}-{target_lang}')
            print('Precision', 'Recall', 'F1')
            for method_id, path in enumerate([f'BatFix_map/{target_model_name}-{source_lang}-{target_lang}-Batfix-mapping',
                                              f'TransAgent_map/{target_model_name}-{source_lang}-{target_lang}-TransAgent-mapping',
                                              f'TransMapGPT_map/{target_model_name}-{source_lang}-{target_lang}-TransMap-mapping',
                                              f'TransMapQwen_map/{target_model_name}-{source_lang}-{target_lang}-TransMap-mapping',
                                              f'RulER_map/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping',
                                              f'{path_to_DATABASE}/DATA/MAP/{target_model_name}-{source_lang}-{target_lang}-GT-mapping']):
                correct_sim_list, wrong_sim_list, all_sim_list, precision, recall, f1, TP, FP, TP_FN = run(path, target_model_name, source_lang, target_lang, dataset=None)
                TPs[methods[method_id]] += TP
                FPs[methods[method_id]] += FP
                TP_FNs[methods[method_id]] += TP_FN
                precisions[methods[method_id]].append(precision)
                f1s[methods[method_id]].append(f1)
                recalls[methods[method_id]].append(recall)
                if source_lang == 'Java':
                    all_sim_java[methods[method_id]]['correct_map'].extend(correct_sim_list)
                    all_sim_java[methods[method_id]]['wrong_map'].extend(wrong_sim_list)
                    all_sim_java[methods[method_id]]['all'].extend(all_sim_list)
                elif source_lang == 'Python':
                    all_sim_py[methods[method_id]]['correct_map'].extend(correct_sim_list)
                    all_sim_py[methods[method_id]]['wrong_map'].extend(wrong_sim_list)
                    all_sim_py[methods[method_id]]['all'].extend(all_sim_list)
                all_sim[methods[method_id]]['correct_map'].extend(correct_sim_list)
                all_sim[methods[method_id]]['wrong_map'].extend(wrong_sim_list)
                all_sim[methods[method_id]]['all'].extend(all_sim_list)

    BatFix_ave_r = 0
    TransMapGPT_ave_r = 0
    TransMapQwen_ave_r = 0
    TransAgent_ave_r = 0
    RulER_ave_r = 0
    for method in methods:
        if TPs[method] and FPs[method]:
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
            if method == 'TransMapGPT':
                TransMapGPT_ave_r = f1
            if method == 'TransMapQwen':
                TransMapQwen_ave_r = f1
            if method == 'TransAgent':
                TransAgent_ave_r = f1
            if method == 'RulER':
                RulER_ave_r = f1

    print(f'\nRulER than BatFix in average F1: {round((RulER_ave_r - BatFix_ave_r) / BatFix_ave_r, 2)}')
    print(f'RulER than TransMapGPT in average F1: {round((RulER_ave_r - TransMapGPT_ave_r) / TransMapGPT_ave_r, 2)}')
    print(f'RulER than TransMapQwen in average F1: {round((RulER_ave_r - TransMapQwen_ave_r) / TransMapQwen_ave_r, 2)}')
    print(f'RulER than TransAgent in average F1: {round((RulER_ave_r - TransAgent_ave_r) / TransAgent_ave_r, 2)}')

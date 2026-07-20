import argparse
import os.path


def run(method_name, path_to_DATABASE, target_model_name, source_lang, target_lang, dataset=None):
    if method_name in ['BatFix']:
        save_FL_dir = f'{method_name}_FL/{target_model_name}-{source_lang}-{target_lang}-FL'
    else:
        save_FL_dir = f'{method_name}_FL/{target_model_name}/{source_lang}-{target_lang}'

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

    TP = 0
    FP = 0
    FN = 0

    for k, v in ID2label.items():
        ID = k
        if dataset == 'LeetCode':
            if not ID.isdigit():
                continue
        elif dataset == 'CTCI':
            if not ID.startswith('CTCI_'):
                continue
        elif dataset == 'GeeksforGeeks':
            if ID.isdigit() or ID.startswith('CTCI_'):
                continue
        if method_name in ['BatFix'] and (ID.isdigit() or ID.startswith('CTCI_')):
            continue
        report_ids = []
        if os.path.exists(f'{save_FL_dir}/{ID}.txt'):
            report_line = open(f'{save_FL_dir}/{ID}.txt').readlines()[0]
            report_ids = [int(item) for item in report_line.strip().split('|') if item.strip()]
            for report_id in report_ids:
                if report_id in ID2label[ID]:
                    TP += 1
                else:
                    FP += 1
        for label_id in ID2label[ID]:
            if label_id not in report_ids:
                FN += 1
    if TP and FP:
        precision = round((TP/(TP+FP)), 3)
        recall = round((TP/(TP+FN)), 3)
        F1 = round((2*precision*recall)/(precision+recall), 3)
        out_precision = round((TP/(TP+FP))*100, 1)
        out_recall = round((TP/(TP+FN))*100, 1)
        out_F1 = round(((2*precision*recall)/(precision+recall))*100, 1)
        print(f'{out_precision}\% & {out_recall}\% & {out_F1}\%')
        return precision, recall, F1, TP, FP, FN
    else:
        precision = 0
        recall = 0
        F1 = 0
        out_precision = 0
        out_recall = 0
        out_F1 = 0
        print(f'{out_precision}\% & {out_recall}\% & {out_F1}\%')
        return precision, recall, F1, TP, FP, FN


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
    method_names = ['BatFix', 'TransAgent', 'TransMapGPT', 'TransMapQwen', 'RulER']
    precisions = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[]}
    recalls = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[]}
    F1s = {'BatFix':[], 'TransMapGPT':[], 'TransMapQwen':[], 'TransAgent':[], 'RulER':[]}

    TPs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0}
    FPs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0}
    FNs = {'BatFix':0, 'TransMapGPT':0, 'TransMapQwen':0, 'TransAgent':0, 'RulER':0}
    target_model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
    source_langs = ['Java', 'Python']
    target_lang = 'C++'
    for target_model_name in target_model_names:
        for source_lang in source_langs:
            print(f'{target_model_name}-{source_lang}-{target_lang}')
            print('Precision', 'Recall', 'F1')
            for method_name in method_names:
                precision, recall, F1, TP, FP, FN = run(method_name, path_to_DATABASE, target_model_name, source_lang, target_lang, dataset=None)
                precisions[method_name].append(precision)
                recalls[method_name].append(recall)
                F1s[method_name].append(F1)
                TPs[method_name] += TP
                FPs[method_name] += FP
                FNs[method_name] += FN

    BatFix_ave_f = 0
    TransMapGPT_ave_f = 0
    TransMapQwen_ave_f = 0
    TransAgent_ave_f = 0
    RulER_ave_f = 0
    for method_name in method_names:
        if TPs[method_name] and FPs[method_name]:
            all_P = round(TPs[method_name]/(TPs[method_name]+FPs[method_name]), 3)
            all_R = round(TPs[method_name]/(TPs[method_name]+FNs[method_name]), 3)
            all_F = round((2*all_P*all_R)/(all_P+all_R), 3)
            print(f'{method_name} Total P: {all_P}')
            print(f'{method_name} Total R: {all_R}')
            print(f'{method_name} Total F: {all_F}')
            if method_name == 'BatFix':
                BatFix_ave_f = all_F
            if method_name == 'TransMapGPT':
                TransMapGPT_ave_f = all_F
            if method_name == 'TransMapQwen':
                TransMapQwen_ave_f = all_F
            if method_name == 'TransAgent':
                TransAgent_ave_f = all_F
            if method_name == 'RulER':
                RulER_ave_f = all_F
    if BatFix_ave_f:
        print(f'\nRulER than BatFix in average F1: {round((RulER_ave_f - BatFix_ave_f) / BatFix_ave_f, 2)}')
    if TransMapGPT_ave_f:
        print(f'RulER than TransMapGPT in average F1: {round((RulER_ave_f - TransMapGPT_ave_f) / TransMapGPT_ave_f, 2)}')
    if TransMapQwen_ave_f:
        print(f'RulER than TransMapQwen in average F1: {round((RulER_ave_f - TransMapQwen_ave_f) / TransMapQwen_ave_f, 2)}')
    if TransAgent_ave_f:
        print(f'RulER than TransAgent in average F1: {round((RulER_ave_f - TransAgent_ave_f) / TransAgent_ave_f, 2)}')

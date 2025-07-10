import argparse
import os.path


def run(method_name, path_to_DATABASE, target_model_name, source_lang, target_lang):
    save_FL_dir = f'{method_name}_FL/{target_model_name}-{source_lang}-{target_lang}-FL'

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

    Correct_FL = 0
    all_FL_case_count = 0

    for k, v in ID2label.items():
        ID = k
        all_FL_case_count += 1
        if os.path.exists(f'{save_FL_dir}/{ID}.txt'):
            report_id = int(open(f'{save_FL_dir}/{ID}.txt').readlines()[0].strip())
            if report_id in ID2label[ID]:
                Correct_FL += 1
    S_locate = round(Correct_FL/all_FL_case_count, 3)
    print('')
    print(f'{method_name}-{target_model_name}-{source_lang}-{target_lang}')
    print('N_locate: ', Correct_FL)
    print('N_total: ', all_FL_case_count)
    print('S_locate', S_locate)
    return S_locate, Correct_FL, all_FL_case_count


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
    method_names = ['BatFix', 'TransMap', 'RulER']
    S_locates = {'BatFix':[], 'TransMap':[], 'RulER':[]}
    sum_FL_case_count = {'BatFix':0, 'TransMap':0, 'RulER':0}
    sum_correct_FL = {'BatFix':0, 'TransMap':0, 'RulER':0}
    target_model_names = ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']
    source_langs = ['Java', 'Python']
    target_lang = 'C++'
    for method_name in method_names:
        for target_model_name in target_model_names:
            for source_lang in source_langs:
                S_locate, this_correct_FL, this_FL_case_count = run(method_name, path_to_DATABASE, target_model_name, source_lang, target_lang)
                S_locates[method_name].append(S_locate)
                sum_correct_FL[method_name] += this_correct_FL
                sum_FL_case_count[method_name] += this_FL_case_count
    BatFix_ave_r = 0
    TransMap_ave_r = 0
    RulER_ave_r = 0
    for method_name in method_names:
        print(f'{method_name} average S_locate: {round(sum_correct_FL[method_name]/sum_FL_case_count[method_name], 3)}')
        if method_name == 'BatFix':
            BatFix_ave_r = round(sum_correct_FL[method_name]/sum_FL_case_count[method_name], 3)
        if method_name == 'TransMap':
            TransMap_ave_r = round(sum_correct_FL[method_name]/sum_FL_case_count[method_name], 3)
        if method_name == 'RulER':
            RulER_ave_r = round(sum_correct_FL[method_name]/sum_FL_case_count[method_name], 3)

    print(f'\nRulER than BatFix in average S_pass: {round((RulER_ave_r - BatFix_ave_r) / BatFix_ave_r, 2)}')
    print(f'RulER than TransMap in average S_pass: {round((RulER_ave_r - TransMap_ave_r) / TransMap_ave_r, 2)}')

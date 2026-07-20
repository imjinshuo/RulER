import os
import shutil
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_DATABASE",
        default='/home/ubuntu/DATABASE',
        type=str,
        required=True,
        help=""
    )
    args = parser.parse_args()
    path_to_DATABASE = args.path_to_DATABASE

    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for source_lang in ['Java', 'Python']:
            target_lang = 'C++'
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[source_lang]
            target_ext = extensions[target_lang]
            if not os.path.exists(f'info/{model_name}-{source_lang}-{target_lang}'):
                continue
            info_files = os.listdir(f'info/{model_name}-{source_lang}-{target_lang}')
            ori_source_script_for_trace_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
            fix_IDs = []
            fix_IDs_CODE = []
            fix_IDs_LeetCode = []
            fix_IDs_CTCI = []
            notfix_IDs = []
            notfix_IDs_CODE = []
            notfix_IDs_LeetCode = []
            notfix_IDs_CTCI = []
            for info_file in info_files:
                ID = info_file.split('.')[0]
                info_lines = open(f'info/{model_name}-{source_lang}-{target_lang}/{info_file}').readlines()
                info_lines = [line.strip() for line in info_lines if line.strip()]
                info = []
                for info_line in info_lines:
                    val = int(info_line.split('\t')[0])
                    if '|' in info_line:
                        ids = info_line.split('\t')[1].split('|')
                    else:
                        ids = [info_line.split('\t')[1]]
                    ids = [int(item) for item in ids]
                    ids.sort()
                    info.append([val, ids])
                info.sort(reverse=True)
                if info and info[0][0] == 10:
                    fix_IDs.append(ID)
                    if ID.startswith('CTCI_'):
                        fix_IDs_CTCI.append(ID)
                    elif ID.isdigit():
                        fix_IDs_LeetCode.append(ID)
                    else:
                        fix_IDs_CODE.append(ID)
                else:
                    notfix_IDs.append(ID)
                    if ID.startswith('CTCI_'):
                        notfix_IDs_CTCI.append(ID)
                    elif ID.isdigit():
                        notfix_IDs_LeetCode.append(ID)
                    else:
                        notfix_IDs_CODE.append(ID)
            print(model_name, source_lang)
            if len(fix_IDs) and len(fix_IDs) + len(notfix_IDs):
                print('ALL:', len(fix_IDs), len(fix_IDs) + len(notfix_IDs), round(len(fix_IDs) / (len(fix_IDs) + len(notfix_IDs)), 3))
                if len(fix_IDs_CODE) + len(notfix_IDs_CODE):
                    print('CODE:', len(fix_IDs_CODE), len(fix_IDs_CODE) + len(notfix_IDs_CODE), round(len(fix_IDs_CODE) / (len(fix_IDs_CODE) + len(notfix_IDs_CODE)), 3))
                if len(fix_IDs_LeetCode) + len(notfix_IDs_LeetCode):
                    print('LEET:', len(fix_IDs_LeetCode), len(fix_IDs_LeetCode) + len(notfix_IDs_LeetCode), round(len(fix_IDs_LeetCode) / (len(fix_IDs_LeetCode) + len(notfix_IDs_LeetCode)), 3))
                if len(fix_IDs_CTCI) + len(notfix_IDs_CTCI):
                    print('CTCI:', len(fix_IDs_CTCI), len(fix_IDs_CTCI) + len(notfix_IDs_CTCI), round(len(fix_IDs_CTCI) / (len(fix_IDs_CTCI) + len(notfix_IDs_CTCI)), 3))
                print('')
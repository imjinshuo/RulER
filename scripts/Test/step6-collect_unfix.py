import os
import shutil
import argparse


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

    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for source_lang in ['Java', 'Python']:
            target_lang = 'C++'
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[source_lang]
            target_ext = extensions[target_lang]
            info_file = f'info/{model_name}-{source_lang}-{target_lang}-fixinfo.txt'
            info_uncompare_file = f'info/{model_name}-{source_lang}-{target_lang}-fixinfo-uncompare.txt'
            info_lines = open(info_file).readlines()
            if os.path.exists(info_uncompare_file):
                info_uncompare_lines = open(info_uncompare_file).readlines()
            else:
                info_uncompare_lines = []
            lines = []
            lines.extend(info_lines)
            lines.extend(info_uncompare_lines)
            uncompared = []
            f_uncompared = open(f'{model_name}-{source_lang}-{target_lang}-uncompared.txt')
            uncompared_lines = f_uncompared.readlines()
            for line in uncompared_lines:
                if line.strip():
                    uncompared.append(line.strip())
            f_uncompared.close()
            os.makedirs(f'CODE-round2/{model_name}-data/{source_lang}', exist_ok=True)
            os.makedirs(f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}', exist_ok=True)
            os.makedirs(f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace', exist_ok=True)
            os.makedirs(f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace', exist_ok=True)
            os.makedirs(f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace', exist_ok=True)
            ori_source_script_for_trace_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
            fix_count = 0
            notfix_count = 0
            all_count = 0
            for line in lines:
                all_count += 1
                items = line.strip().split('\t')
                ID = items[0]
                ori_same = int(items[1])
                new_same = int(items[2])
                if '|' in items[3]:
                    ids = items[3].split('|')
                else:
                    ids = [items[3]]
                ids = [int(item) for item in ids]
                ids.sort()
                if new_same:
                    fix_count += 1
                else:
                    notfix_count += 1
                    if ID in uncompared:
                        shutil.copy(f'{model_name}-data/{source_lang}/{ID}.{source_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}/{ID}.{source_ext}')
                        shutil.copy(f'Fix_Code/{model_name}-{source_lang}-{target_lang}/{ID}/{ids[0]}.{target_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}/{ID}.{target_ext}')
                        shutil.copy(f'{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                        shutil.copy(f'{ori_source_script_for_trace_dir}/{ID}.{source_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}')
                        shutil.copy(f'{model_name}-data-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{ids[0]}.{target_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}')
                    else:
                        shutil.copy(f'{model_name}-data/{source_lang}/{ID}.{source_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}/{ID}.{source_ext}')
                        shutil.copy(f'Fix_Code/{model_name}-{source_lang}-{target_lang}/{ID}/{ids[0]}.{target_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}/{ID}.{target_ext}')
                        shutil.copy(f'{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                        shutil.copy(f'{ori_source_script_for_trace_dir}/{ID}.{source_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}')
                        shutil.copy(f'{model_name}-data-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{ids[0]}.{target_ext}',
                                    f'CODE-round2/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}')
            print(model_name, source_lang)
            print(fix_count, notfix_count, all_count)
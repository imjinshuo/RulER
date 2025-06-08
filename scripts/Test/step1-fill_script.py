import argparse
import os
import shutil


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_fixcode",
        default='Fix_Code',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_DATABASE",
        default='/DATABASE',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    path_to_FixCode = args.path_to_FixCode
    path_to_DATABASE = args.path_to_DATABASE

    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for source_lang in ['Java', 'Python']:
            target_lang = 'C++'
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[source_lang]
            target_ext = extensions[target_lang]
            target_func_dir = f'{path_to_FixCode}/{model_name}-{source_lang}-{target_lang}'
            target_func_files = os.listdir(target_func_dir)
            IDs = os.listdir(target_func_dir)
            ori_source_func_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}'
            ori_target_func_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}'
            ori_source_args_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace'
            ori_source_script_for_trace_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
            ori_target_script_for_trace_dir = f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
            save_dir = f'{model_name}-data'
            os.makedirs(save_dir, exist_ok=True)
            os.makedirs(f'{save_dir}/{source_lang}', exist_ok=True)
            os.makedirs(f'{save_dir}/{source_lang}-{target_lang}-{source_lang}-script-for-trace', exist_ok=True)
            os.makedirs(f'{save_dir}/{source_lang}-{target_lang}-{target_lang}-args-for-trace', exist_ok=True)
            count1 = 0
            count2 = 0
            for ID in IDs:
                print(ID)
                ID_files = os.listdir(f'{target_func_dir}/{ID}')
                for ID_file in ID_files:
                    os.makedirs(f'{save_dir}/{source_lang}-{target_lang}/{ID}', exist_ok=True)
                    os.makedirs(f'{save_dir}/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}', exist_ok=True)
                    this_id = ID_file.split('.')[0]
                    f = open(f'{target_func_dir}/{ID}/{ID_file}')
                    func_lines = f.readlines()
                    f.close()
                    shutil.copy(f'{target_func_dir}/{ID}/{ID_file}', f'{save_dir}/{source_lang}-{target_lang}/{ID}/{ID_file}')
                    f = open(f'{ori_target_script_for_trace_dir}/{ID}.{target_ext}')
                    script_lines = f.readlines()
                    f.close()
                    new_script_lines = []
                    if_start = 0
                    for line in script_lines:
                        if line == '#include <iostream>\n':
                            if_start = 1
                        if if_start == 1:
                            new_script_lines.append(line)
                            if line == 'using namespace std;\n':
                                new_script_lines.append('\n')
                            elif 'f_filled' in line:
                                new_script_lines = new_script_lines[:-1]
                                new_script_lines.extend(func_lines)
                                new_script_lines.append('\n')
                                if_start = 0
                        elif if_start == 2:
                            new_script_lines.append(line)
                        elif 'public static void main(String args[]) {' in line or 'int main() {' in line or "if __name__ == '__main__':" in line:
                            new_script_lines.append(line)
                            if_start = 2
                    f = open(f'{save_dir}/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{ID_file}', 'w')
                    print(''.join(new_script_lines), file=f)
                    f.close()
                    shutil.copy(f'{ori_source_args_dir}/{ID}.args', f'{save_dir}/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                    shutil.copy(f'{ori_source_script_for_trace_dir}/{ID}.{source_ext}', f'{save_dir}/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}')
                    shutil.copy(f'{ori_source_func_dir}/{ID}.{source_ext}', f'{save_dir}/{source_lang}/{ID}.{source_ext}')
            print(len(IDs))
            print(count1)
            print(count2)
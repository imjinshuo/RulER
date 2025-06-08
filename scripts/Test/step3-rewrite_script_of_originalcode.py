import argparse
import os


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
        for src_lang in ['Java', 'Python']:
            ori_dir = f'{model_name}-data'
            tar_lang = 'C++'
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[src_lang]
            target_ext = extensions[tar_lang]
            save_dir = f'{ori_dir}-new/ori-{src_lang}-{tar_lang}-{tar_lang}-script-for-trace'
            os.makedirs(save_dir, exist_ok=True)
            ori_file_dir = f'{path_to_DATABASE}/DATA/CODE/{ori_dir}/{src_lang}-{tar_lang}-{tar_lang}-script-for-trace'
            files = os.listdir(ori_file_dir)
            uncompared = []
            f_uncompared = open(f'{model_name}-{src_lang}-{tar_lang}-uncompared.txt')
            uncompared_lines = f_uncompared.readlines()
            for line in uncompared_lines:
                if line.strip():
                    uncompared.append(line.strip())
            f_uncompared.close()
            for file in files:
                if tar_lang == 'C++':
                    ID = file.split('.')[0]
                    f_i = open(f'{ori_file_dir}/{file}')
                    ori_input_lines = f_i.readlines()
                    input_lines = []
                    for line in ori_input_lines:
                        if line.endswith('\n'):
                            input_lines.append(line[:-1])
                        else:
                            input_lines.append(line)
                    f_i.close()
                    compare_line_id = -1
                    for line_id, line in enumerate(input_lines):
                        if 'f_filled' in line and 'f_gold' in line:
                            compare_line_id = line_id
                    print(input_lines[compare_line_id])
                    if ID in uncompared:
                        f_o = open(f'{save_dir}/{file}', 'w')
                        for i in input_lines:
                            print(i, file=f_o)
                        f_o.close()
                        continue
                    elif 'if(f_filled(' in input_lines[compare_line_id]:
                        output_lines = input_lines[:compare_line_id]
                        new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
                    else:
                        continue
                    print(new_line)
                    output_lines.append(f'        cout << {new_line} << endl;')
                    output_lines.append('    }')
                    output_lines.append('    return 0;')
                    output_lines.append('}')
                    f_o = open(f'{save_dir}/{file}', 'w')
                    for i in output_lines:
                        print(i, file=f_o)
                    f_o.close()
import os
import argparse


if __name__ == "__main__":
    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for src_lang in ['Java', 'Python']:
            ori_dir = f'{model_name}-data'
            tar_lang = 'C++'
            uncompared = []
            if not os.path.exists(f'{model_name}-{src_lang}-{tar_lang}-uncompared.txt'):
                continue
            f_uncompared = open(f'{model_name}-{src_lang}-{tar_lang}-uncompared.txt')
            uncompared_lines = f_uncompared.readlines()
            for line in uncompared_lines:
                if line.strip():
                    uncompared.append(line.strip())
            for lang in [src_lang, tar_lang]:
                source_code_dir = f'{ori_dir}/{src_lang}'
                source_script_dir = f'{ori_dir}/{src_lang}-{tar_lang}-{lang}-script-for-trace'
                if os.path.exists(source_script_dir):
                    source_script_files = os.listdir(source_script_dir)
                else:
                    source_script_files = []
                source_script_files.sort()
                os.makedirs(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace', exist_ok=True)
                for file in source_script_files:
                    if lang == 'C++':
                        ID = file.split('.')[0]
                        if ID not in uncompared:
                            continue
                        ID_files = os.listdir(f'{source_script_dir}/{ID}')
                        os.makedirs(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                        os.makedirs(f'{ori_dir}-trace/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                        for this_file in ID_files:
                            f_i = open(f'{source_script_dir}/{ID}/{this_file}')
                            input_lines = f_i.readlines()
                            f_i.close()
                            new_target_code = []
                            if_in_main = False
                            for test_line in input_lines:
                                if 'main(' in test_line:
                                    if_in_main = True
                                if test_line == '            n_success+=1;\n' and if_in_main:
                                    new_target_code.append('            std::cout << \"Pass_test_id-\" << i << std::endl;\n')
                                    new_target_code.append(test_line)
                                else:
                                    new_target_code.append(test_line)
                            if 'mpz_class' in ''.join(new_target_code):
                                if '#include <gmpxx.h>' not in new_target_code[7]:
                                    new_target_code.insert(7, '#include <gmpxx.h>')
                            f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}/{this_file}', 'w')
                            print(''.join(new_target_code), file=f_o)
                            f_o.close()

                    if lang == 'Java':
                        ID = file.split('.')[0]
                        if ID not in uncompared:
                            continue
                        f_i = open(f'{source_script_dir}/{file}')
                        input_lines = f_i.readlines()
                        f_i.close()
                        new_target_code = []
                        if_in_main = False
                        for test_line in input_lines:
                            if 'main(' in test_line:
                                if_in_main = True
                            if test_line == '            n_success+=1;\n' and if_in_main:
                                new_target_code.append('            System.out.println(\"Pass_test_id-\"+i);\n')
                                new_target_code.append(test_line)
                            else:
                                new_target_code.append(test_line)
                        f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}', 'w')
                        print(''.join(new_target_code), file=f_o)
                        f_o.close()
                    if lang == 'Python':
                        ID = file.split('.')[0]
                        if ID not in uncompared:
                            continue
                        f_i = open(f'{source_script_dir}/{file}')
                        input_lines = f_i.readlines()
                        f_i.close()
                        new_target_code = []
                        if_in_main = False
                        for test_line in input_lines:
                            if "if __name__ == '__main__'" in test_line:
                                if_in_main = True
                            if test_line == '            n_success+=1\n' and if_in_main:
                                new_target_code.append('            print(\"Pass_test_id-\"+str(i))\n')
                                new_target_code.append(test_line)
                            else:
                                new_target_code.append(test_line)
                        f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}', 'w')
                        print(''.join(new_target_code), file=f_o)
                        f_o.close()
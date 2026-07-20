import os
import shutil

if __name__ == "__main__":
    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for src_lang in ['Java', 'Python']:
            ori_dir = f'{model_name}-data'
            tar_lang = 'C++'
            uncompared = []
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
                        if file.startswith('CTCI_') or file.isdigit():
                            ID = file.split('.')[0]
                            ID_files = os.listdir(f'{source_script_dir}/{ID}')
                            os.makedirs(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                            os.makedirs(f'{ori_dir}-trace/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                            ID_files.sort()
                            for this_file in ID_files:
                                f_i = open(f'{source_script_dir}/{ID}/{this_file}')
                                ori_input_lines = f_i.readlines()
                                ori_input_lines_str = ''.join(ori_input_lines)
                                input_lines = []
                                patch_line_lines = ''
                                for line_id, line in enumerate(ori_input_lines):
                                    if '// Patch' in line:
                                        patch_line_lines += line
                                if 'sort' in patch_line_lines or '.size()' in patch_line_lines or '.begin()' in patch_line_lines or '.end()' in patch_line_lines:
                                    for line_id, line in enumerate(ori_input_lines):
                                        if 'cout << f_filled(' in line:
                                            this_line = line
                                            for num in range(10):
                                                if f'&param{num}[i].front()' in this_line:
                                                    this_line = this_line.replace(f'&param{num}[i].front()',
                                                                                f'param{num}[i]')
                                            ori_input_lines[line_id] = this_line
                                for line in ori_input_lines:
                                    if line.endswith('\n'):
                                        input_lines.append(line[:-1])
                                    else:
                                        input_lines.append(line)
                                f_i.close()
                                compare_line_id = -1
                                for line_id, line in enumerate(input_lines):
                                    if 'cout << f_filled(' in line:
                                        compare_line_id = line_id
                                print(input_lines[compare_line_id])
                                output_lines = input_lines[:compare_line_id]
                                new_line = input_lines[compare_line_id].strip().split('<<')[1].strip()
                                print(new_line)
                                if '__int128' in patch_line_lines:
                                    output_lines.append(f'        print_int128({new_line});')
                                    output_lines.append(f'        cout << endl;')
                                    print_128_codes = ["void print_int128(__int128 n) {\n",
                                                       "    if(n < 0) {\n",
                                                       "        std::cout << '-';\n",
                                                       "        n = -n;\n",
                                                       "    }\n",
                                                       "    if(n > 9) {\n",
                                                       "        print_int128(n / 10);", "    }\n",
                                                       "    std::cout << char('0' + n % 10);\n",
                                                       "}\n"]
                                    output_lines.insert(8, ''.join(print_128_codes))
                                else:
                                    output_lines.append(f'        cout << {new_line} << endl;')
                                if 'mpz_class' in ori_input_lines_str:
                                    if '#include <gmpxx.h>' not in output_lines[7]:
                                        output_lines.insert(7, '#include <gmpxx.h>')
                                output_lines.append('    }')
                                output_lines.append('    return 0;')
                                output_lines.append('}')
                                f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}/{this_file}', 'w')
                                for i in output_lines:
                                    print(i, file=f_o)
                                f_o.close()
                        else:
                            ID = file.split('.')[0]
                            ID_files = os.listdir(f'{source_script_dir}/{ID}')
                            os.makedirs(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                            os.makedirs(f'{ori_dir}-trace/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}', exist_ok=True)
                            ID_files.sort()
                            for this_file in ID_files:
                                f_i = open(f'{source_script_dir}/{ID}/{this_file}')
                                ori_input_lines = f_i.readlines()
                                ori_input_lines_str = ''.join(ori_input_lines)
                                input_lines = []
                                patch_line_lines = ''
                                for line_id, line in enumerate(ori_input_lines):
                                    if '// Patch' in line:
                                        patch_line_lines += line
                                if 'sort' in patch_line_lines or '.size()' in patch_line_lines:
                                    for line_id, line in enumerate(ori_input_lines):
                                        if 'f_filled' in line and 'f_gold' in line:
                                            items = line.split('==')
                                            if 'f_filled' in items[0]:
                                                for num in range(10):
                                                    if f'&param{num}[i].front()' in items[0]:
                                                        items[0] = items[0].replace(f'&param{num}[i].front()', f'param{num}[i]')
                                                ori_input_lines[line_id] = '=='.join(items)
                                            elif 'f_filled' in items[1]:
                                                for num in range(10):
                                                    if f'&param{num}[i].front()' in items[1]:
                                                        items[1] = items[1].replace(f'&param{num}[i].front()', f'param{num}[i]')
                                                ori_input_lines[line_id] = '=='.join(items)
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
                                if compare_line_id != -1 and 'if(f_filled(' in input_lines[compare_line_id]:
                                    output_lines = input_lines[:compare_line_id]
                                    new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
                                else:
                                    if ID not in uncompared:
                                        uncompared.append(ID)
                                    continue
                                print(new_line)
                                output_lines.append('        cout << "OUTPUT-OF-" << i << ":" << endl;')
                                if '__int128' in patch_line_lines:
                                    output_lines.append(f'        print_int128({new_line});')
                                    output_lines.append(f'        cout << endl;')
                                    print_128_codes = ["void print_int128(__int128 n) {\n",
                                                       "    if(n < 0) {\n",
                                                       "        std::cout << '-';\n",
                                                       "        n = -n;\n",
                                                       "    }\n",
                                                       "    if(n > 9) {\n",
                                                       "        print_int128(n / 10);", "    }\n",
                                                       "    std::cout << char('0' + n % 10);\n",
                                                       "}\n"]
                                    output_lines.insert(8, ''.join(print_128_codes))
                                else:
                                    output_lines.append(f'        cout << {new_line} << endl;')
                                if 'mpz_class' in ori_input_lines_str:
                                    if '#include <gmpxx.h>' not in output_lines[7]:
                                        output_lines.insert(7, '#include <gmpxx.h>')
                                output_lines.append('    }')
                                output_lines.append('    return 0;')
                                output_lines.append('}')
                                f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{ID}/{this_file}', 'w')
                                for i in output_lines:
                                    print(i, file=f_o)
                                f_o.close()
                    if lang == 'Java':
                        ID = file.split('.')[0]
                        if ID.startswith('CTCI_'):
                            shutil.copy(f'{source_script_dir}/{file}', f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}')
                        elif ID.isdigit():
                            shutil.copy(f'{source_script_dir}/{file}', f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}')
                        else:
                            f_i = open(f'{source_script_dir}/{file}')
                            ori_input_lines = f_i.readlines()
                            input_lines = []
                            for line in ori_input_lines:
                                if line.endswith('\n'):
                                    input_lines.append(line[:-1])
                                else:
                                    input_lines.append(line)
                            f_i.close()
                            f_i = open(f"{source_code_dir}/{file.split('.')[0]}.java")
                            func_lines = f_i.readlines()
                            f_i.close()
                            compare_line_id = -1
                            for line_id, line in enumerate(input_lines):
                                if 'f_filled' in line and 'f_gold' in line:
                                    compare_line_id = line_id
                            print(input_lines[compare_line_id])
                            if compare_line_id != -1 and 'if(f_filled(' in input_lines[compare_line_id] and '.equals' not in input_lines[compare_line_id]:
                                output_lines = input_lines[:compare_line_id]
                                new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
                            else:
                                if file.split('.')[0] not in uncompared:
                                    uncompared.append(file.split('.')[0])
                                continue
                            print(new_line)
                            output_lines.append('        System.out.println("OUTPUT-OF-"+i+":");')
                            output_lines.append(f'        System.out.println({new_line});')
                            output_lines.append('    }')
                            output_lines.append('}')
                            output_lines.append('}')
                            f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}', 'w')
                            for i in output_lines:
                                print(i, file=f_o)
                            f_o.close()
                    if lang == 'Python':
                        ID = file.split('.')[0]
                        if ID.startswith('CTCI_'):
                            shutil.copy(f'{source_script_dir}/{file}', f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}')
                        elif ID.isdigit():
                            shutil.copy(f'{source_script_dir}/{file}', f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}')
                        else:
                            f_i = open(f'{source_script_dir}/{file}')
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
                            if compare_line_id != -1 and 'if f_filled(' in input_lines[compare_line_id]:
                                output_lines = input_lines[:compare_line_id]
                                new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
                            else:
                                if file.split('.')[0] not in uncompared:
                                    uncompared.append(file.split('.')[0])
                                continue
                            print(new_line)
                            output_lines.append('        print(f"OUTPUT-OF-{i}:")')
                            output_lines.append(f'        print({new_line})')
                            f_o = open(f'{ori_dir}-new/{src_lang}-{tar_lang}-{lang}-script-for-trace/{file}', 'w')
                            for i in output_lines:
                                print(i, file=f_o)
                            f_o.close()
            f = open(f'{model_name}-{src_lang}-{tar_lang}-uncompared.txt', 'w')
            for i in uncompared:
                print(i, file=f)
            f.close()
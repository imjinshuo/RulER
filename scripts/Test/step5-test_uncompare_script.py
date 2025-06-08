import re
import os
from subprocess import Popen, PIPE
import shutil
from tqdm import tqdm
import argparse


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def run(file_path, lang, tmp_dir):
    if lang == "Python":
        try:
            p = Popen(['python3', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            output = stdout.decode().strip()
            if 'False' in output:
                output = output.replace('False', 'false')
            if 'True' in output:
                output = output.replace('True', 'true')
            return 'success', output
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "Java":
        try:
            p = Popen(['java', '--module-path', '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
                       '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE,
                      stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "C++":
        try:
            p = Popen(['g++', '-o', f'{tmp_dir}/output', file_path], cwd=os.getcwd(), stdout=PIPE,
                      stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if not os.path.isfile(f'{tmp_dir}/output'):
                return 'compile_failed', ''
        except:
            p.kill()
            return 'compile_failed', ''
        try:
            p = Popen([f'{tmp_dir}/output'], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''


def find_same(output_info, output):
    same = 0
    if output_info != 'success':
        same = 0
    else:
        match1 = re.search(r'Results:\s*(\d+),\s*\d+', output)
        if match1:
            same = int(match1.group(1))
    return same


def update_list(same, ID, id, s_val, val):
    if_contain = False
    new_same = [item[:] for item in same]
    for index, item in enumerate(same):
        this_ID, this_s_val, this_val, this_ids = item
        if this_ID == ID:
            if_contain = True
            if val < s_val:
                continue
            elif this_val == s_val and val == s_val:
                new_same[index][3].append(id)
            elif this_val == s_val and val > s_val:
                new_same[index] = [ID, s_val, val, [id]]
            elif this_val > s_val and val > this_val:
                new_same[index] = [ID, s_val, val, [id]]
    if not if_contain and val >= s_val:
        new_same.append([ID, s_val, val, [id]])
    return new_same


def main(model_name, tmp_dir, source_lang, target_lang):
    ori_dir = f'{model_name}-data'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    uncompared = []
    f_uncompared = open(f'{model_name}-{source_lang}-{target_lang}-uncompared.txt')
    uncompared_lines = f_uncompared.readlines()
    for line in uncompared_lines:
        if line.strip():
            uncompared.append(line.strip())
    f_uncompared.close()
    script_dir = f'{ori_dir}/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
    script_files = os.listdir(script_dir)
    script_files.sort()
    passinfo_lines = open(f'{model_name}-{source_lang}-{target_lang}-passInfo.txt').readlines()
    passinfo_ID2info = {}
    for line in passinfo_lines:
        ID, this_info = line.strip().split('####')
        this_info_list = this_info.split('\t')
        passinfo_ID2info[ID] = this_info_list
    if_advance = []
    count = -1
    for file in tqdm(script_files):
        count += 1
        ID = file.split(".")[0]
        os.makedirs(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace', exist_ok=True)
        if ID in uncompared:
            if os.path.exists(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}'):
                exist_files = os.listdir(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}')
                for exist_file in exist_files:
                    if os.path.isdir(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{exist_file}'):
                        shutil.rmtree(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{exist_file}')
                    else:
                        os.remove(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{exist_file}')
            else:
                os.makedirs(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}', exist_ok=True)
            source_script = f'{ori_dir}/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}'
            source_trans_script = f'{ori_dir}-new/ori-{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}'
            target_script_dir = f'{ori_dir}/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}'
            f_i = open(source_trans_script)
            ori_input_lines = f_i.readlines()
            input_lines = []
            patch_line_ids = []
            patch_line_lines = ''
            for line_id, line in enumerate(ori_input_lines):
                if ' // Patch' in line:
                    patch_label = line[line.index(' // Patch ') + len(' // Patch '):]
                    if ' ' in patch_label:
                        patch_label = int(patch_label.split(' ')[0])
                    else:
                        patch_label = int(patch_label.strip())
                    patch_line_ids.append([line_id, patch_label])
                    patch_line_lines += ori_input_lines[line_id]
            if 'sort' in patch_line_lines:
                for line_id, line in enumerate(ori_input_lines):
                    if 'f_filled' in line and 'f_gold' in line and '==' in line:
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
            output_lines = input_lines[:compare_line_id]
            new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
            last_output_line = output_lines[-1]
            this_pass_info = passinfo_ID2info[ID]
            last_output_line_items = last_output_line[11:-11].split('||')
            last_output_line_items = [item.strip()[5:] for item in last_output_line_items]
            last_output_line_items_target = []
            for item in last_output_line_items:
                if item not in this_pass_info:
                    last_output_line_items_target.append(item)
            if last_output_line_items_target:
                if_condition = f'i == {last_output_line_items_target[0]}'
                for i in last_output_line_items_target[1:]:
                    if_condition = if_condition + f' || i == {i}'
                replace_last_line = '        if(' + if_condition + ') continue;'
            else:
                replace_last_line = '        '
            output_lines[-1] = replace_last_line
            output_lines.extend(input_lines[compare_line_id:])
            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')
            f_o = open(f'{tmp_dir}/{ID}.{target_ext}', 'w')
            for i in output_lines:
                print(i, file=f_o)
            f_o.close()
            source_trans_info, source_trans_output = run(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)
            source_same_len = find_same(source_trans_info, source_trans_output)
            trans_files = os.listdir(target_script_dir)
            trans_files_IDs = [int(file.split('.')[0]) for file in trans_files]
            trans_files_IDs.sort()
            for this_id in trans_files_IDs:
                trans_file = f'{this_id}.cpp'
                target_script = f'{target_script_dir}/{trans_file}'
                f_i = open(target_script)
                ori_input_lines = f_i.readlines()
                input_lines = []
                patch_line_ids = []
                patch_line_lines = ''
                for line_id, line in enumerate(ori_input_lines):
                    if ' // Patch' in line:
                        patch_label = line[line.index(' // Patch ') + len(' // Patch '):]
                        if ' ' in patch_label:
                            patch_label = int(patch_label.split(' ')[0])
                        else:
                            patch_label = int(patch_label.strip())
                        patch_line_ids.append([line_id, patch_label])
                        patch_line_lines += ori_input_lines[line_id]
                if 'sort' in patch_line_lines:
                    for line_id, line in enumerate(ori_input_lines):
                        if 'f_filled' in line and 'f_gold' in line and '==' in line:
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
                output_lines = input_lines[:compare_line_id]
                new_line = input_lines[compare_line_id].strip().split(' == ')[0][3:]
                trace_output_lines = output_lines[:]
                last_output_line = output_lines[-1]
                this_pass_info = passinfo_ID2info[ID]
                last_output_line_items = last_output_line[11:-11].split('||')
                last_output_line_items = [item.strip()[5:] for item in last_output_line_items]
                last_output_line_items_target = []
                for item in last_output_line_items:
                    if item not in this_pass_info:
                        last_output_line_items_target.append(item)
                if last_output_line_items_target:
                    if_condition = f'i == {last_output_line_items_target[0]}'
                    for i in last_output_line_items_target[1:]:
                        if_condition = if_condition + f' || i == {i}'
                    replace_last_line = '        if(' + if_condition + ') continue;'
                else:
                    replace_last_line = '        '
                output_lines[-1] = replace_last_line
                output_lines.extend(input_lines[compare_line_id:])
                trace_output_lines.extend(input_lines[compare_line_id:])
                exist_files = os.listdir(f'{tmp_dir}/')
                for exist_file in exist_files:
                    if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                        shutil.rmtree(f'{tmp_dir}/{exist_file}')
                    else:
                        os.remove(f'{tmp_dir}/{exist_file}')
                f_o = open(f'{tmp_dir}/{ID}.{target_ext}', 'w')
                for i in output_lines:
                    print(i, file=f_o)
                f_o.close()
                f_o = open(f'{ori_dir}-trace/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{trans_file}', 'w')
                for i in trace_output_lines:
                    print(i, file=f_o)
                f_o.close()
                target_info, target_output = run(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)
                this_source_same_len = find_same(target_info, target_output)
                if this_source_same_len == 1:
                    if_advance = update_list(if_advance, ID, this_id, source_same_len, this_source_same_len)
                    print(if_advance)
                    print(len([item for item in if_advance if item[2] > item[1]]), count)
                    break
                else:
                    if_advance = update_list(if_advance, ID, this_id, source_same_len, this_source_same_len)
                print(if_advance)
                print(len([item for item in if_advance if item[2] > item[1]]), count)
    os.makedirs('info', exist_ok=True)
    info_save_file = f'info/{model_name}-{source_lang}-{target_lang}-fixinfo-uncompare.txt'
    f1 = open(info_save_file, 'w')
    for item in if_advance:
        print(f'{item[0]}\t{item[1]}\t{item[2]}\t{"|".join([str(this_item) for this_item in item[3]])}', file=f1)
    f1.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source_lang",
        default='Python',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--target_lang",
        default='C++',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--target_model_name",
        default='TransCoder',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--tmp_dir",
        default='tmp',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()

    target_model_name = args.target_model_name
    source_lang = args.source_lang
    target_lang = args.target_lang
    tmp_dir = args.tmp_dir
    main(target_model_name, tmp_dir, source_lang, target_lang)
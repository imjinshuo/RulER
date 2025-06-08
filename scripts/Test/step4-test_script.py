import os
from subprocess import Popen, PIPE
import shutil
from tqdm import tqdm
import time
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


def compare(output1, output2):
    output1_strip = output1.strip()
    output2_strip = output2.strip()
    if output1_strip == output2_strip:
        return 1
    else:
        if ('true' in output1 or 'false' in output1) and ('1' in output2 or '0' in output2):
            output1 = output1.replace('true', '1')
            output1 = output1.replace('false', '0')
            output1_strip = output1.strip()
            output2_strip = output2.strip()
        if output1_strip == output2_strip:
            return 1
        return 0


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
    os.makedirs(tmp_dir, exist_ok=True)
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
    script_dir = f'{ori_dir}-new/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
    script_files = os.listdir(script_dir)
    script_files.sort()
    if_advance = []
    count = -1
    for file in tqdm(script_files[:]):
        count += 1
        ID = file.split(".")[0]
        if ID in uncompared:
            continue
        source_script = f'{ori_dir}-new/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}'
        source_trans_script = f'{ori_dir}-new/ori-{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}'
        target_script_dir = f'{ori_dir}-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}'

        exist_files = os.listdir(f'{tmp_dir}/')
        for exist_file in exist_files:
            if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                shutil.rmtree(f'{tmp_dir}/{exist_file}')
            else:
                os.remove(f'{tmp_dir}/{exist_file}')
        time.sleep(1)
        shutil.copyfile(source_script, f'{tmp_dir}/{ID}.{source_ext}')
        source_info, source_output = run(f'{tmp_dir}/{ID}.{source_ext}', source_lang, tmp_dir)
        shutil.copyfile(source_trans_script, f'{tmp_dir}/{ID}.{target_ext}')
        source_trans_info, source_trans_output = run(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)
        if source_trans_info == 'success':
            source_same_len = compare(source_output, source_trans_output)
        else:
            source_same_len = 0
        trans_files = os.listdir(target_script_dir)
        trans_files_IDs = [int(file.split('.')[0]) for file in trans_files]
        trans_files_IDs.sort()
        for this_id in trans_files_IDs:
            trans_file = f'{this_id}.cpp'
            if os.path.exists(f'{tmp_dir}/output'):
                os.remove(f'{tmp_dir}/output')
            target_script = f'{target_script_dir}/{trans_file}'
            shutil.copyfile(target_script, f'{tmp_dir}/{ID}.{target_ext}')
            target_info, target_output = run(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)
            if target_info == 'success':
                this_source_same_len = compare(source_output, target_output)
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
    info_save_file = f'info/{model_name}-{source_lang}-{target_lang}-fixinfo.txt'
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
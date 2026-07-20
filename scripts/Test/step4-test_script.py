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
            if stdout.decode().strip().count('OUTPUT-OF') == 0 and stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            output = stdout.decode().strip()
            if 'False' in output:
                output = output.replace('False', 'false')
            if 'True' in output:
                output = output.replace('True', 'true')
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
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
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "C++":
        lines = open(file_path).readlines()
        if '#include <gmpxx.h>' in ''.join(lines):
            try:
                p = Popen(['g++', '-o', f'{tmp_dir}/output', file_path, '-lgmp', '-lgmpxx'], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
                stdout, stderr_data = p.communicate(timeout=5)
                p.kill()
                if not os.path.isfile(f'{tmp_dir}/output'):
                    return 'compile_failed', ''
            except:
                p.kill()
                return 'compile_failed', ''
        else:
            try:
                p = Popen(['g++', '-o', f'{tmp_dir}/output', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
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
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''


def compare_uncompare(output):
    output_strip = output.strip()
    if '#Results:' not in output_strip:
        return []
    ori_output2_strip_list = [int(item.strip()) for item in output_strip.split('#Results:')[0].split('Pass_test_id-') if item != '']
    return ori_output2_strip_list


def compare(output1, output2):
    output1_strip = output1.strip()
    output2_strip = output2.strip()
    ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
    ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
    if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
        ori_output1_strip_list = ori_output1_strip_list[1:]
    if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
        ori_output2_strip_list = ori_output2_strip_list[1:]
    output1_strip_list = []
    output1_strip_dict = {}
    for i in range(10):
        for item in ori_output1_strip_list:
            if item.startswith(f'{i}:\n'):
                if item.endswith('.0\n'):
                    output1_strip_list.append(item[len(f'{i}:\n'):-len('.0\n')]+'\n')
                    output1_strip_dict[i] = item[len(f'{i}:\n'):-len('.0\n')]+'\n'
                elif item.endswith('.0'):
                    output1_strip_list.append(item[len(f'{i}:\n'):-len('.0')])
                    output1_strip_dict[i] = item[len(f'{i}:\n'):-len('.0')]
                else:
                    output1_strip_list.append(item[len(f'{i}:\n'):])
                    output1_strip_dict[i] = item[len(f'{i}:\n'):]
    output2_strip_list = []
    output2_strip_dict = {}
    for i in range(10):
        for item in ori_output2_strip_list:
            if item.startswith(f'{i}:\n'):
                if item.endswith('.0\n'):
                    output2_strip_list.append(item[len(f'{i}:\n'):-len('.0\n')]+'\n')
                    output2_strip_dict[i] = item[len(f'{i}:\n'):-len('.0\n')]+'\n'
                elif item.endswith('.0'):
                    output2_strip_list.append(item[len(f'{i}:\n'):-len('.0')])
                    output2_strip_dict[i] = item[len(f'{i}:\n'):-len('.0')]
                else:
                    output2_strip_list.append(item[len(f'{i}:\n'):])
                    output2_strip_dict[i] = item[len(f'{i}:\n'):]
    if output1_strip_list == output2_strip_list:
        return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    else:
        if ('true' in output1 or 'false' in output1) and ('1' in output2 or '0' in output2):
            output1_strip = output1_strip.replace('true', '1')
            output1_strip = output1_strip.replace('false', '0')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif ('True' in output1 or 'False' in output1) and ('1' in output2 or '0' in output2):
            output1_strip = output1_strip.replace('True', '1')
            output1_strip = output1_strip.replace('False', '0')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif ('True' in output1 or 'False' in output1) and ('true' in output2 or 'false' in output2):
            output1_strip = output1_strip.replace('True', 'true')
            output1_strip = output1_strip.replace('False', 'false')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif '.' in output1 and 'e' in output1 and '.' in output2 and 'e' in output2:
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        if '.' in item and 'e' in item:
                            output1_strip_list.append(item[len(f'{i}:\n'):].split('e')[0][0])
                            output1_strip_dict[i] = item[len(f'{i}:\n'):].split('e')[0][0]
                        else:
                            output1_strip_list.append(item[len(f'{i}:\n'):][0])
                            output1_strip_dict[i] = item[len(f'{i}:\n'):][0]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        if '.' in item and 'e' in item:
                            output2_strip_list.append(item[len(f'{i}:\n'):].split('e')[0][0])
                            output2_strip_dict[i] = item[len(f'{i}:\n'):].split('e')[0][0]
                        else:
                            output2_strip_list.append(item[len(f'{i}:\n'):][0])
                            output2_strip_dict[i] = item[len(f'{i}:\n'):][0]
        if output1_strip_list == output2_strip_list:
            return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        same = []
        for id in range(10):
            if id in output1_strip_dict and id in output2_strip_dict:
                if output1_strip_dict[id] == output2_strip_dict[id]:
                    same.append(id)
            elif id not in output1_strip_dict and id not in output2_strip_dict:
                    same.append(id)
        return same


def update_list(info, id, val):
    if val in info:
        info[val].append(id)
    else:
        info[val] = [id]
    return info


def main(model_name, tmp_dir, source_lang, target_lang, start_id, end_id):
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
    os.makedirs(f'info/{model_name}-{source_lang}-{target_lang}', exist_ok=True)
    count = -1
    for file in tqdm(script_files[start_id:end_id]):
        info = {}
        count += 1
        ID = file.split(".")[0]
        if ID in uncompared:
            target_script_dir = f'{ori_dir}-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}'

            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')
            time.sleep(0.3)
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
                    this_source_same_ids = compare_uncompare(target_output)
                    info = update_list(info, this_id, len(this_source_same_ids))
                    if len(this_source_same_ids) == 10:
                        break
            info_save_file = f'info/{model_name}-{source_lang}-{target_lang}/{ID}.txt'
            f1 = open(info_save_file, 'w')
            if info:
                for k, v in info.items():
                    print(f'{k}\t{"|".join([str(this_item) for this_item in v])}', file=f1)
            f1.close()
        else:
            source_script = f'{ori_dir}-new/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}'
            target_script_dir = f'{ori_dir}-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}'

            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')
            time.sleep(0.3)
            shutil.copyfile(source_script, f'{tmp_dir}/{ID}.{source_ext}')
            source_info, source_output = run(f'{tmp_dir}/{ID}.{source_ext}', source_lang, tmp_dir)
            trans_files = os.listdir(target_script_dir)
            trans_files_IDs = [int(file.split('.')[0]) for file in trans_files]
            trans_files_IDs.sort()
            for this_id in trans_files_IDs:
                trans_file = f'{this_id}.cpp'
                if os.path.exists(f'{tmp_dir}/output'):
                    os.remove(f'{tmp_dir}/output')
                    time.sleep(0.3)
                target_script = f'{target_script_dir}/{trans_file}'
                shutil.copyfile(target_script, f'{tmp_dir}/{ID}.{target_ext}')
                target_info, target_output = run(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)
                if target_info == 'success':
                    this_source_same_ids = compare(source_output, target_output)
                    info = update_list(info, this_id, len(this_source_same_ids), )
                    if len(this_source_same_ids) == 10:
                        break
            info_save_file = f'info/{model_name}-{source_lang}-{target_lang}/{ID}.txt'
            f1 = open(info_save_file, 'w')
            if info:
                for k, v in info.items():
                    print(f'{k}\t{"|".join([str(this_item) for this_item in v])}', file=f1)
            f1.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source_lang",
        default='Java',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--target_lang",
        default='C++',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--target_model_name",
        default='TransCoder',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--tmp_dir",
        default='tmp',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--start_id",
        default=0,
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--end_id",
        default=1000,
        type=str,
        required=True,
        help=""
    )
    args = parser.parse_args()

    target_model_name = args.target_model_name
    source_lang = args.source_lang
    target_lang = args.target_lang
    tmp_dir = args.tmp_dir
    start_id = int(args.start_id)
    end_id = int(args.end_id)
    main(target_model_name, tmp_dir, source_lang, target_lang, start_id, end_id)
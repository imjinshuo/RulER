import os
from tqdm import tqdm
from subprocess import Popen, PIPE
import shutil
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


def run(file_path, run_input_file, lang, tmp_dir):
    if lang == "Python":
        try:
            with open(run_input_file, 'r') as f:
                f_in = f.read()
            p = Popen(['python3', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(input=f_in.encode(), timeout=5)
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
            with open(run_input_file, 'r') as f:
                f_in = f.read()
            p = Popen(['java', '--module-path', '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
                 '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(input=f_in.encode(), timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "C++":
        try:
            p = Popen(['g++', '-o', f'{tmp_dir}/output', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)  # g++ -o output -std=c++11
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if not os.path.isfile(f'{tmp_dir}/output'):
                return 'compile_failed', ''
        except:
            p.kill()
            return 'compile_failed', ''
        try:
            with open(run_input_file, 'r') as f:
                f_in = f.read()
            p = Popen([f'{tmp_dir}/output'], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(input=f_in.encode(), timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''


def main(model_name, source_lang, target_lang, CodeNet_test_input_path, tmp_dir, dataset_name):
    dataset_folder = f'CodeNet_sourcefiles'
    trans_dataset_dir = f'{dataset_name}/OUTPUT_{model_name}'
    extensions = { 'Python': 'py', 'C++': 'cpp','Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    trans_ids = [id.split('.')[0] for id in os.listdir(f'{trans_dataset_dir}/{source_lang}-{target_lang}')]

    os.makedirs(tmp_dir, exist_ok=True)
    test_passed = []

    for file_ID in tqdm(trans_ids):
        file_group = file_ID.split('-')[0]
        run_input_file = f'{CodeNet_test_input_path}/{file_group}/input.txt'

        source_file = f'{dataset_folder}/{source_lang}-{target_lang}/{file_ID}.{source_ext}'
        trans_file = f'{trans_dataset_dir}/{source_lang}-{target_lang}/{file_ID}.{target_ext}'

        exist_files = os.listdir(f'{tmp_dir}/')
        for exist_file in exist_files:
            if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                shutil.rmtree(f'{tmp_dir}/{exist_file}')
            else:
                os.remove(f'{tmp_dir}/{exist_file}')

        shutil.copyfile(source_file, f'{tmp_dir}/{file_ID}.{source_ext}')
        source_info, source_output = run(f'{tmp_dir}/{file_ID}.{source_ext}', run_input_file, source_lang, tmp_dir)
        if source_info != 'success' or source_output.strip() == '':
            print(f"{color.BOLD}{color.RED}Fail--{file_ID}.{source_ext}{color.END}")
            continue

        exist_files = os.listdir(f'{tmp_dir}/')
        for exist_file in exist_files:
            if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                shutil.rmtree(f'{tmp_dir}/{exist_file}')
            else:
                os.remove(f'{tmp_dir}/{exist_file}')

        shutil.copyfile(trans_file, f'{tmp_dir}/{file_ID}.{target_ext}')
        trans_info, trans_output = run(f'{tmp_dir}/{file_ID}.{target_ext}', run_input_file, target_lang, tmp_dir)
        if trans_info != 'success' or trans_output.strip() == '':
            print(f"{color.BOLD}{color.RED}Fail--{file_ID}.{target_ext}{color.END}")
            continue

        if source_output == trans_output:
            test_passed.append(file_ID)
        else:
            print(f"{color.BOLD}{color.RED}Diff--{file_ID}{color.END}")
            print(source_output)
            print('-----------------------------')
            print(trans_output)
        print(len(test_passed))
    f_test_pass = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-testpass.txt', 'w')
    for id in test_passed:
        print(id, file=f_test_pass)
    f_test_pass.close()


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
        "--CodeNet_test_input_path",
        default='Project_CodeNet/derived/input_output/data',
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
    parser.add_argument(
        "--model_name",
        default='qwen2.5-coder-32b-instruct',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    source_lang = args.source_lang
    target_lang = args.target_lang
    CodeNet_test_input_path = args.CodeNet_test_input_path
    tmp_dir = args.tmp_dir
    model_name = args.model_name
    dataset_name = 'CodeNet'
    main(model_name, source_lang, target_lang, CodeNet_test_input_path, tmp_dir, dataset_name)

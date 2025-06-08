import os
from openai import OpenAI
import argparse
import json
from subprocess import Popen, PIPE
import shutil
from tqdm import tqdm


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


def filter_return_str(gen_str, lang, model_name):
    if lang == 'C++':
        if model_name == 'qwen2.5-coder-32b-instruct':
            ori_gen_lines = gen_str.split('\n')
            gen_lines = []
            if_record = False
            for line in ori_gen_lines:
                if line.strip() == '```cpp':
                    if_record = True
                if line.strip() == '```':
                    break
                if if_record and line.strip() != '```cpp':
                    gen_lines.append(line)
            pre_lines = ['#include <iostream>', '#include <cstdlib>', '#include <string>', '#include <vector>', '#include <fstream>', '#include <iomanip>', '#include <bits/stdc++.h>', 'using namespace std;']
            fol_lines = []
            filter_lines = []
            if_record = False
            for line in gen_lines:
                if line.startswith('int main'):
                    if_record = True
                if if_record:
                    filter_lines.append(line)
                if line == '}\n' or line == '}':
                    break
            return pre_lines, filter_lines, fol_lines
        else:
            gen_lines = gen_str.split('\n')
            pre_lines = ['#include <iostream>', '#include <cstdlib>', '#include <string>', '#include <vector>', '#include <fstream>', '#include <iomanip>', '#include <bits/stdc++.h>', 'using namespace std;']
            fol_lines = []
            filter_lines = []
            if_record = False
            for line in gen_lines:
                if line.startswith('int main'):
                    if_record = True
                if if_record:
                    filter_lines.append(line)
                if line == '}\n' or line == '}':
                    break
            return pre_lines, filter_lines, fol_lines
    elif lang == 'Python':
        if model_name in ['TransCoder', 'TransCoderST']:
            gen_lines = gen_str.split('\n')
            pre_lines = []
            for line in gen_lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    pre_lines.append(line.strip())
            pre_lines.append('def main():')
            fol_lines = ['main()']
            if '\ndef ' in gen_str:
                return pre_lines, [], fol_lines
            if "if __name__ == '__main__':" in gen_lines:
                filter_lines = []
                if_record = False
                for line in gen_lines:
                    if line == ("if __name__ == '__main__':"):
                        if_record = True
                    if if_record and line.startswith('    '):
                        filter_lines.append(line)
                return pre_lines, filter_lines, fol_lines
            else:
                if_in_comment = False
                filter_lines = []
                for line in gen_lines:
                    if line.strip() == '"""':
                        if not if_in_comment:
                            if_in_comment = True
                        else:
                            if_in_comment = False
                    if if_in_comment:
                        continue
                    if line == '' or line.strip() == '"""' or line.strip().startswith('import ') or line.strip().startswith('from ') or line.strip().startswith('#') or line.strip().startswith('def '):
                        continue
                    filter_lines.append(line)
                return pre_lines, filter_lines, fol_lines
        elif model_name == 'qwen2.5-coder-32b-instruct':
            ori_gen_lines = gen_str.split('\n')
            gen_lines = []
            if_record = False
            for line in ori_gen_lines:
                if line.strip() == '```python':
                    if_record = True
                if line.strip() == '```' or line.strip() == 'if __name__ == "__main__":':
                    break
                if if_record and line.strip() not in ['```python', 'def main():']:
                    gen_lines.append(line)
            if_start_with_space = True
            for line in gen_lines:
                if line.strip() and not line.startswith('    '):
                    if_start_with_space = False
            if if_start_with_space:
                for line_id, line in enumerate(gen_lines):
                    if line.strip():
                        gen_lines[line_id] = line[len('    '):]
            fol_lines = ['main()']
            pre_lines = []
            for line_id, line in enumerate(gen_lines):
                if line.startswith('import ') or line.startswith('from '):
                    pre_lines.append(line)
            pre_lines.append('def main():')
            filter_lines = []
            for line in gen_lines:
                if line.startswith('import ') or line.startswith('from ') or line.startswith('#'):
                    continue
                filter_lines.append('    ' + line)
            return pre_lines, filter_lines, fol_lines
        else:
            gen_lines = gen_str.split('\n')
            pre_lines = []
            for line in gen_lines:
                if line.startswith('import ') or line.startswith('from '):
                    pre_lines.append(line)
            pre_lines.append('def main():')
            fol_lines = ['main()']
            if '\ndef ' in gen_str:
                return pre_lines, [], fol_lines
            if "if __name__ == '__main__':" in gen_lines:
                filter_lines = []
                if_record = False
                for line in gen_lines:
                    if line == ("if __name__ == '__main__':"):
                        if_record = True
                    if if_record and line.startswith('    '):
                        filter_lines.append(line)
                return pre_lines, filter_lines, fol_lines
            else:
                filter_lines = []
                for line in gen_lines:
                    if line == '' or line.startswith('import ') or line.startswith('from ') or line.startswith('#'):
                        continue
                    filter_lines.append('    '+line)
                return pre_lines, filter_lines, fol_lines
    elif lang == 'Java':
        if model_name in ['TransCoder', 'TransCoderST']:
            gen_lines = gen_str.split('\n')
            pre_lines = ['import java.util.*;', 'import java.util.stream.*;', 'import java.lang.*;', 'import javafx.util.Pair;', 'public class Main {']
            fol_lines = ['}']
            filter_lines = []
            if_record = False
            for line in gen_lines:
                if ' public static void main ( ' in line:
                    if_record = True
                if if_record:
                    if ' public static void main ( ' in line:
                        filter_lines.append('  '+line[line.index('public static void main ( '):])
                    else:
                        filter_lines.append('  '+line)
                if line == '}':
                    break
            return pre_lines, filter_lines, fol_lines
        elif model_name == 'qwen2.5-coder-32b-instruct':
            ori_gen_lines = gen_str.split('\n')
            gen_lines = []
            if_record = False
            for line in ori_gen_lines:
                if line.strip() == '```java':
                    if_record = True
                if line.strip() == '```':
                    break
                if if_record and line.strip() != '```java':
                    gen_lines.append(line)
            pre_lines = ['import java.util.*;', 'import java.util.stream.*;', 'import java.lang.*;', 'import javafx.util.Pair;', 'public class Main {']
            fol_lines = ['}']
            filter_lines = []
            if_record = False
            for line in gen_lines:
                if line.startswith('    public static void main('):
                    if_record = True
                if if_record:
                    filter_lines.append(line)
                if line == '    }\n' or line == '    }':
                    break
            return pre_lines, filter_lines, fol_lines
        else:
            gen_lines = gen_str.split('\n')
            pre_lines = ['import java.util.*;', 'import java.util.stream.*;', 'import java.lang.*;', 'import javafx.util.Pair;', 'public class Main {']
            fol_lines = ['}']
            filter_lines = []
            if_record = False
            for line in gen_lines:
                if line.startswith('    public static void main('):
                    if_record = True
                if if_record:
                    filter_lines.append(line)
                if line == '    }\n' or line == '    }':
                    break
            return pre_lines, filter_lines, fol_lines


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
        "--tmp_dir",
        default='tmp',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--CodeNet_data_path",
        default='Project_CodeNet/data',
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
    parser.add_argument(
        "--CodeNet_test_input_path",
        default='Project_CodeNet/derived/input_output/data',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_save_source_code",
        default='CodeNet_sourcefiles',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--api_key",
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()

    source_lang = args.source_lang
    target_lang = args.target_lang
    tmp_dir = args.tmp_dir
    dataset_folder = args.CodeNet_data_path
    model_name = args.model_name
    run_input_output_folder = args.CodeNet_test_input_path
    api_key = args.api_key
    save_source_code_dir = f'{args.path_to_save_source_code}/{source_lang}-{target_lang}'

    os.makedirs(save_source_code_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)

    dataset_name = 'CodeNet'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    ext = extensions[target_lang]

    file_name_f = open(f'CodeNet_filenames/CodeNet_{source_lang}.txt')
    file_name_lines = file_name_f.readlines()
    file_name_f.close()
    files_path_ID = []
    for file_name_line in file_name_lines[:10]:
        if file_name_line.strip():
            files_path_ID.append(file_name_line.strip())
    del file_name_lines

    if model_name == 'qwen2.5-coder-32b-instruct':

        output_dir = f'{dataset_name}/OUTPUT_{model_name}/{source_lang}-{target_lang}'
        os.makedirs(output_dir, exist_ok=True)

        for file_path in tqdm(files_path_ID):
            file_group = file_path.split('/')[0]
            file_name = file_path.split('/')[-1]

            run_input_file = f'{run_input_output_folder}/{file_group}/input.txt'
            if not os.path.isfile(run_input_file):
                print(f"{color.BOLD}{color.RED}No Test Input--{file_path}{color.END}")
                continue

            file_ID = file_path.split('/')[-1].split('.')[0]
            source_file = ''
            if source_lang == 'Java':
                source_file = f'{dataset_folder}/{file_group}/Java/{file_ID}.{source_ext}'
            elif source_lang == 'Python':
                source_file = f'{dataset_folder}/{file_group}/Python/{file_ID}.{source_ext}'
            elif source_lang == 'C++':
                source_file = f'{dataset_folder}/{file_group}/C++/{file_ID}.{source_ext}'
            f = open(source_file)
            source_code_lines = f.readlines()
            f.close()
            if len(source_code_lines) > 100:
                print(f"{color.BOLD}{color.RED}Too Long--{file_path}{color.END}")
                continue

            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')

            if source_lang == 'Python':
                source_code = ''.join(source_code_lines)
                if 'def ' in source_code:
                    continue
                new_source_code_lines = []
                for source_code_line in source_code_lines:
                    if source_code_line.startswith('import') or source_code_line.startswith('from '):
                        new_source_code_lines.append(source_code_line)
                new_source_code_lines.append('def main():\n')
                if_main = False
                for source_code_line in source_code_lines:
                    if source_code_line.strip() == '' or source_code_line.startswith('import') or source_code_line.startswith('from '):
                        continue
                    else:
                        if_main = True
                    if if_main:
                        this_source_code_line = '    ' + source_code_line
                        new_source_code_lines.append(this_source_code_line)
                if new_source_code_lines[-1].endswith('\n'):
                    new_source_code_lines.append('main()')
                else:
                    new_source_code_lines.append('\nmain()')
                new_source_code_lines = [new_source_code_line for new_source_code_line in new_source_code_lines if new_source_code_line.strip()]
                f_save_new_source_code = open(f'{tmp_dir}/{file_ID}.{source_ext}', 'w')
                print(''.join(new_source_code_lines).strip(), file=f_save_new_source_code)
                f_save_new_source_code.close()
            elif source_lang == 'Java':
                source_code = ''.join(source_code_lines)
                head1 = 'public class Main {\n\n    public static void main('
                head2 = 'public class Main {\n	public static void main('
                if head1 not in source_code and head2 not in source_code:
                    continue
                if source_code.count('\n    {') > 1 or source_code.count('public ') != 2 or source_code.count('class ') != 1 or source_code.count('private ') != 0 or source_code.count('static ') != 1:
                    continue
                new_source_code_lines = ['import java.util.*;\n', 'import java.util.stream.*;\n', 'import java.lang.*;\n', 'import javafx.util.Pair;\n']
                if head1 in source_code:
                    left_code = source_code[source_code.index(head1):]
                    left_code_lines = left_code.split('\n')
                    for left_code_line in left_code_lines:
                        if left_code_line.strip():
                            new_source_code_lines.append(left_code_line + '\n')
                elif head2 in source_code:
                    left_code = source_code[source_code.index(head2):]
                    left_code_lines = left_code.split('\n')
                    for left_code_line in left_code_lines:
                        if left_code_line.strip():
                            new_source_code_lines.append(left_code_line + '\n')
                f_save_new_source_code = open(f'{tmp_dir}/{file_ID}.{source_ext}', 'w')
                print(''.join(new_source_code_lines).strip(), file=f_save_new_source_code)
                f_save_new_source_code.close()
            elif source_lang == 'C++':
                new_source_code_lines = ['#include <iostream>\n', '#include <cstdlib>\n', '#include <string>\n', '#include <vector>\n', '#include <fstream>\n', '#include <iomanip>\n', '#include <bits/stdc++.h>\n', 'using namespace std;\n']
                if_start_record = False
                for line in source_code_lines:
                    if line.strip() == '':
                        continue
                    if line.endswith('main() {\n') or line.endswith('main(){\n') or line.endswith('main()\n'):
                        if_start_record = True
                    elif line == '}\n':
                        new_source_code_lines.append(line)
                        if_start_record = False
                        break
                    if if_start_record:
                        new_source_code_lines.append(line)
                if len(new_source_code_lines) <= 8:
                    continue
                f_save_new_source_code = open(f'{tmp_dir}/{file_ID}.{source_ext}', 'w')
                print(''.join(new_source_code_lines).strip(), file=f_save_new_source_code)
                f_save_new_source_code.close()

            source_info, source_output = run(f'{tmp_dir}/{file_ID}.{source_ext}', run_input_file, source_lang, tmp_dir)
            if source_info != 'success' or source_output.strip() == '':
                print(f"{color.BOLD}{color.RED}Fail--{file_path}{color.END}")
                continue
            print(f"{color.BOLD}{color.GREEN}Success--{file_path}{color.END}")

            code_file = open(f'{dataset_folder}/{file_path}')
            code_lines = code_file.readlines()
            prompt = f"{source_lang} Code:\n\n" + "".join(
                code_lines) + f'\n\nTranslate the above {source_lang} code to {target_lang}.\n\n{target_lang} Code:\n\n'

            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            completion = client.chat.completions.create(
                model="qwen2.5-coder-32b-instruct",
                temperature=0,
                messages=[
                    {
                            "role": "user",
                            "content": prompt
                    }],
            )

            source_API_result = json.loads(completion.model_dump_json())
            source_translation = source_API_result['choices'][0]['message']['content']

            pre_lines, filter_lines, fol_lines = filter_return_str(source_translation, target_lang, model_name)
            if not filter_lines:
                continue

            return_lines = []
            return_lines.extend(pre_lines)
            return_lines.extend(filter_lines)
            return_lines.extend(fol_lines)

            return_str = '\n'.join(return_lines).strip()
            out_file = f'{output_dir}/{file_group}-{file_name.split(".")[0]}.{ext}'
            with open(out_file, 'w') as fot:
                fot.write(return_str)
            shutil.copyfile(f'{tmp_dir}/{file_ID}.{source_ext}', f'{save_source_code_dir}/{file_group}-{file_name.split(".")[0]}.{source_ext}')

import os
from openai import OpenAI
import json
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
        "--model_name",
        default='qwen2.5-coder-32b-instruct',
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

    model_name = args.model_name
    source_lang = args.source_lang
    target_lang = args.target_lang
    api_key = args.api_key

    dataset_name = 'CodeNet'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    ext = extensions[target_lang]

    output_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans'
    os.makedirs(output_dir, exist_ok=True)
    dataset_folder = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass'
    source_deleteinfopass_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo-pass'
    dirs = os.listdir(dataset_folder)
    dirs.sort()
    if model_name == 'qwen2.5-coder-32b-instruct':
        for ID in tqdm(dirs):
            f_info = open(f'{source_deleteinfopass_dir}/{ID}.txt')
            info_lines = f_info.readlines()
            f_info.close()
            files = os.listdir(f'{dataset_folder}/{ID}')
            files.sort()
            for file in files:
                if file.split('.')[0] == '0':
                    os.makedirs(f'{output_dir}/{ID}', exist_ok=True)
                    shutil.copyfile(f'{dataset_name}/OUTPUT_{model_name}/{source_lang}-{target_lang}/{ID}.{ext}', f'{output_dir}/{ID}/{file.split(".")[0]}.{ext}')
                else:
                    input_file = f'{dataset_folder}/{ID}/{file}'
                    print(file)
                    code_file = open(input_file)
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
                    os.makedirs(f'{output_dir}/{ID}', exist_ok=True)
                    out_file = f'{output_dir}/{ID}/{file.split(".")[0]}.{ext}'
                    with open(out_file, 'w') as fot:
                        fot.write(return_str)
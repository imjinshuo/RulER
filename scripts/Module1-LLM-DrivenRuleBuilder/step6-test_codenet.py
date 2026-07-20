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

import ast, copy
def compare_value(s_val, t_val):
    if s_val == t_val:
        return True
    else:
        if '.' in s_val and '.' in t_val:
            this_s_val = ast.literal_eval(s_val)
            this_t_val = ast.literal_eval(t_val)
            if isinstance(this_s_val, float) and isinstance(this_t_val, float) and round(this_s_val, 2) == round(this_t_val, 2):
                return True
        try:
            if ':' in s_val and ':' in t_val:
                this_s_val = ast.literal_eval(s_val)
                this_t_val = ast.literal_eval(t_val)
                if this_s_val == this_t_val:
                    return True
        except:
            None
        if s_val in ['[]', '""', "''", '{}'] and t_val in ['[]', '""', "''", '{}']:
            return True
        if s_val.startswith("['") and s_val.endswith("']") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace("', '", '')
            s_val_str = s_val_str.replace("['", '')
            s_val_str = s_val_str.replace("']", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("{'") and s_val.endswith("'}") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace("', '", '')
            s_val_str = s_val_str.replace("{'", '')
            s_val_str = s_val_str.replace("'}", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("[") and s_val.endswith("]") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace(", ", '')
            s_val_str = s_val_str.replace("[", '')
            s_val_str = s_val_str.replace("]", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("{") and s_val.endswith("}") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace(", ", '')
            s_val_str = s_val_str.replace("{", '')
            s_val_str = s_val_str.replace("}", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if '(int *)' in s_val or '(int *)' in t_val:
            return True
        if '(int &)' in s_val or '(int &)' in t_val:
            return True
        if s_val in ['False'] and t_val in ['false']:
            return True
        if s_val in ['True'] and t_val in ['true']:
            return True
        if s_val in ['False'] and t_val in ['0']:
            return True
        if s_val in ['True'] and t_val in ['1']:
            return True
        if s_val in ['false'] and t_val in ['0']:
            return True
        if s_val in ['true'] and t_val in ['1']:
            return True
        if s_val in ['{}', '[]'] and t_val in ['{}', '[]']:
            return True
        if s_val in ['None', '-1'] and t_val in ['None', '-1']:
            return True
        if '\'' in s_val:
            s_val = s_val.replace('\'', '')
        if '"' in s_val:
            s_val = s_val.replace('"', '')
        if '\'' in t_val:
            t_val = t_val.replace('\'', '')
        if '"' in t_val:
            t_val = t_val.replace('"', '')
        if s_val == t_val:
            return True
        if '.0' in s_val and '.0' not in t_val:
            this_s_val = copy.deepcopy(s_val)
            this_s_val = this_s_val.replace('.0', '')
            if this_s_val == t_val:
                return True
        if '.0' in t_val and '.0' not in s_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace('.0', '')
            if this_t_val == s_val:
                return True
        if '.' in s_val and 'e' in s_val and '.' in t_val and 'e' in t_val:
            if s_val[0] == t_val[0]:
                return True
        if '[' in s_val and '{' in t_val:
            this_t_val = t_val.replace('{', '[')
            this_t_val = this_t_val.replace('}', ']')
            if s_val == this_t_val:
                return True
        if '{' in s_val and '[' in t_val:
            this_s_val = s_val.replace('{', '[')
            this_s_val = this_s_val.replace('}', ']')
            if t_val == this_s_val:
                return True
        if s_val.startswith('{') and ': ' in s_val and t_val.startswith('[[') and ' = ' in t_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace(', [', ', ')
            this_t_val = this_t_val.replace('] = ', ': ')
            this_t_val = this_t_val.replace(']', '}')
            this_t_val = this_t_val.replace('[', '{')
            this_t_val = this_t_val.replace('{{', '{')
            try:
                this_s_val = ast.literal_eval(s_val)
                this_t_val = ast.literal_eval(this_t_val)
                if this_s_val == this_t_val:
                    return True
            except:
                return False
        if s_val.startswith('[') and '[[' not in s_val and t_val.startswith('[[') and ' = ' in t_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace(', [', ', ')
            this_t_val = this_t_val.replace('] = ', ': ')
            this_t_val = this_t_val.replace('[[', '{')
            this_t_val = this_t_val.replace(']', '}')
            this_s_val = copy.deepcopy(s_val)
            this_s_val = this_s_val.replace('[', '{')
            this_s_val = this_s_val.replace(']', '}')
            try:
                this_s_val = ast.literal_eval(this_s_val)
                this_t_val = ast.literal_eval(this_t_val)
                this_t_val = set([v for k, v in this_t_val.items()])
                if this_s_val == this_t_val:
                    return True
            except:
                return False
        return False


def run(file_path, run_input_file, lang, tmp_dir):
    if lang == "Python":
        try:
            with open(run_input_file, 'r') as f:
                f_in = f.read()
            p = Popen(['python3', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(input=f_in.encode(), timeout=5)
            p.kill()
            real_error = []
            for line in stderr_data.splitlines():
                if b"Connected to:" in line or b"socket.socket" in line:
                    continue
                real_error.append(line)

            real_error = b"\n".join(real_error).strip()
            if real_error.decode() != '':
                return 'runtime_failed', str(real_error.decode()).strip()
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
            code_lines = open(file_path).readlines()
            for idx in range(len(code_lines) - 1, -1, -1):
                if code_lines[idx].strip() == '}':
                    code_lines[idx] = """
    public static void print(Object... args) {
        System.out.println(
            Arrays.stream(args)
                .map(Main::format)
                .collect(Collectors.joining("||||"))
        );
    }

    private static String format(Object obj) {
        if (obj == null) {
            return "null";
        }

        if (!obj.getClass().isArray()) {
            return String.valueOf(obj);
        }

        if (obj instanceof Object[]) {
            return Arrays.deepToString((Object[]) obj);
        }

        if (obj instanceof int[]) {
            return Arrays.toString((int[]) obj);
        }

        if (obj instanceof long[]) {
            return Arrays.toString((long[]) obj);
        }

        if (obj instanceof double[]) {
            return Arrays.toString((double[]) obj);
        }

        if (obj instanceof float[]) {
            return Arrays.toString((float[]) obj);
        }

        if (obj instanceof boolean[]) {
            return Arrays.toString((boolean[]) obj);
        }

        if (obj instanceof byte[]) {
            return Arrays.toString((byte[]) obj);
        }

        if (obj instanceof short[]) {
            return Arrays.toString((short[]) obj);
        }

        if (obj instanceof char[]) {
            return Arrays.toString((char[]) obj);
        }

        return String.valueOf(obj);
    }
}"""
                    break
            f = open(file_path, 'w')
            print(''.join(code_lines), file=f)
            f.close()
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
        code_lines = open(file_path).readlines()
        for idx in range(len(code_lines)):
            if code_lines[idx].strip() == 'using namespace std;':
                code_lines[idx] = """
using namespace std;
template<typename T, typename = void>
struct IsStreamable : false_type {};

template<typename T>
struct IsStreamable<
    T,
    void_t<
        decltype(
            declval<ostream&>() << declval<const T&>()
        )
    >
> : true_type {};

template<typename T>
inline constexpr bool IsStreamableV = IsStreamable<T>::value;

template<typename T, typename = void>
struct IsIterable : false_type {};

template<typename T>
struct IsIterable<
    T,
    void_t<
        decltype(begin(declval<const T&>())),
        decltype(end(declval<const T&>()))
    >
> : true_type {};

template<typename T>
inline constexpr bool IsIterableV = IsIterable<T>::value;

template<typename T>
struct IsPair : false_type {};

template<typename First, typename Second>
struct IsPair<pair<First, Second>> : true_type {};

template<typename T>
inline constexpr bool IsPairV =
    IsPair<remove_cv_t<remove_reference_t<T>>>::value;

template<typename T>
struct IsCharPointer : false_type {};

template<typename T>
struct IsCharPointer<T*>
    : bool_constant<
          is_same_v<remove_cv_t<T>, char>
      > {};

template<typename T>
inline constexpr bool IsCharPointerV =
    IsCharPointer<
        remove_cv_t<remove_reference_t<T>>
    >::value;

template<typename T>
void outputValue(ostream& os, const T& value);

template<typename T>
void outputSequence(ostream& os, const T& values) {
    os << "[";
    bool first = true;
    for (const auto& item : values) {
        if (!first) {
            os << ", ";
        }

        first = false;
        outputValue(os, item);
    }
    os << "]";
}

template<typename T>
void outputValue(ostream& os, const T& value) {
    using U = remove_cv_t<remove_reference_t<T>>;
    if constexpr (IsCharPointerV<U>) {
        if (value != nullptr) {
            os << value;
        } else {
            os << "No-Support";
        }
    }
    else if constexpr (
        is_same_v<U, string> ||
        is_same_v<U, string_view>
    ) {
        os << value;
    }
    else if constexpr (is_same_v<U, bool>) {
        os << (value ? "true" : "false");
    }
    else if constexpr (IsPairV<U>) {
        os << "(";
        outputValue(os, value.first);
        os << ", ";
        outputValue(os, value.second);
        os << ")";
    }
    else if constexpr (is_array_v<U>) {
        os << "[";
        constexpr size_t N = extent_v<U>;
        for (size_t i = 0; i < N; ++i) {
            if (i > 0) {
                os << ", ";
            }
            outputValue(os, value[i]);
        }
        os << "]";
    }
    else if constexpr (IsIterableV<U>) {
        outputSequence(os, value);
    }
    else if constexpr (is_pointer_v<U>) {
        os << "No-Support";
    }
    else if constexpr (IsStreamableV<U>) {
        os << value;
    }
    else {
        os << "No-Support";
    }
}

template<typename... Args>
void print(Args... args) {
    bool first = true;

    auto printOne = [&](const auto& value) {
        if (!first) {
            cout << "||||";
        }

        first = false;

        outputValue(cout, value);
    };

    (printOne(args), ...);

    cout << '\\n';
}

"""
        f = open(file_path, 'w')
        print(''.join(code_lines), file=f)
        f.close()
        try:
            p = Popen(['g++', '-o', f'{tmp_dir}/output', '-std=c++17', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
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


def save_file(str, path):
    f = open(path, 'w')
    print(str, file=f)
    f.close()


def main(model_name, source_lang, target_lang, tmp_dir, dataset_name):
    source_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass'
    trans_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans'
    trans_pass_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans-pass'
    run_input_output_folder = '/home/ubuntu/CodeNet/Project_CodeNet/derived/input_output/data'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    file_IDs = [this_id for this_id in os.listdir(source_dataset_dir)]
    file_IDs.sort()

    os.makedirs(tmp_dir, exist_ok=True)
    test_passed = []
    test_failed = []

    for ID in tqdm(file_IDs):
        file_group = ID.split('-')[0]
        run_input_file = f'{run_input_output_folder}/{file_group}/input.txt'
        source_file_ID = [this_ID.split('.')[0] for this_ID in os.listdir(f'{source_dataset_dir}/{ID}')]
        source_file_ID.sort()
        for file_ID in source_file_ID:
            if not os.path.isfile(f'{trans_dataset_dir}/{ID}/{file_ID}.{target_ext}'):
                continue

            source_file = f'{file_ID}.{source_ext}'
            trans_file = f'{file_ID}.{target_ext}'

            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')

            source_lines = open(f'{source_dataset_dir}/{ID}/{file_ID}.{source_ext}', 'r').readlines()
            print_line = ''
            print_line_source_idx = 0
            for line_idx, line in enumerate(source_lines):
                if '\"RulEROUTPUT:\"' in line:
                    print_line = line.split('\"RulEROUTPUT:\"')[1].strip()
                    print_line_source_idx = line_idx
            if print_line == '':
                continue
            if target_lang == 'Python':
                print_line = print_line.replace(', ', ', "||||", ')
            if source_lang == 'Python':
                source_lines[print_line_source_idx] = source_lines[print_line_source_idx].replace('\"RulEROUTPUT:\", ', '\"RulEROUTPUT:\", \"||||\", ')
                print_line = print_line + ';'
            trans_lines = open(f'{trans_dataset_dir}/{ID}/{file_ID}.{target_ext}', 'r').readlines()
            if_change = False
            for line_idx, line in enumerate(trans_lines):
                if '\"RulEROUTPUT' in line and 'print' in line:
                    this_trans_line = line.split('\"RulEROUTPUT')[0]
                    trans_lines[line_idx] = this_trans_line + '\"RulEROUTPUT:\"' + print_line +'\n'
                    if_change = True
                elif '\'RulEROUTPUT' in line and 'print' in line:
                    this_trans_line = line.split('\'RulEROUTPUT')[0]
                    trans_lines[line_idx] = this_trans_line + '\"RulEROUTPUT:\"' + print_line +'\n'
                    if_change = True
                elif 'RulEROUTPUT' in line and 'print' in line:
                    this_trans_line = line.split('RulEROUTPUT')[0]
                    trans_lines[line_idx] = this_trans_line + '\"RulEROUTPUT:\"' + print_line +'\n'
                    if_change = True

            save_file(''.join(source_lines), f'{tmp_dir}/{file_ID}.{source_ext}')
            source_info, source_output = run(f'{tmp_dir}/{file_ID}.{source_ext}', run_input_file, source_lang, tmp_dir)
            if source_info != 'success' or source_output.strip() == '':
                print(f"{color.BOLD}{color.RED}Fail--{file_ID}.{source_ext}{color.END}")
                continue
            save_file(''.join(trans_lines), f'{tmp_dir}/{file_ID}.{target_ext}')
            trans_info, trans_output = run(f'{tmp_dir}/{file_ID}.{target_ext}', run_input_file, target_lang, tmp_dir)
            if trans_info != 'success' or trans_output.strip() == '':
                print(f"{color.BOLD}{color.RED}Fail--{file_ID}.{target_ext}{color.END}")
                continue

            if source_output == trans_output or source_output.replace(' ', '') == trans_output.replace(' ', ''):
                print(f"{color.BOLD}{color.GREEN}Success--{file_ID}{color.END}")
                os.makedirs(f'{trans_pass_dataset_dir}/{ID}/', exist_ok=True)
                save_file(''.join(trans_lines), f'{trans_pass_dataset_dir}/{ID}/{trans_file}')
                test_passed.append(f"{trans_file.split('.')[0]}")
            elif source_output.replace(' ', '').replace('(', '[').replace(')', ']') == trans_output.replace(' ', '').replace('(', '[').replace(')', ']'):
                print(f"{color.BOLD}{color.GREEN}Success--{file_ID}{color.END}")
                os.makedirs(f'{trans_pass_dataset_dir}/{ID}/', exist_ok=True)
                save_file(''.join(trans_lines), f'{trans_pass_dataset_dir}/{ID}/{trans_file}')
                test_passed.append(f"{trans_file.split('.')[0]}")
            else:
                source_output_list = source_output.split('RulEROUTPUT:')
                source_output_list_list = []
                for item in source_output_list:
                    this_source_output_list = item.split('||||')
                    source_output_list_list.extend(this_source_output_list)
                trans_output_list = trans_output.split('RulEROUTPUT:')
                trans_output_list_list = []
                for item in trans_output_list:
                    this_trans_output_list = item.split('||||')
                    trans_output_list_list.extend(this_trans_output_list)
                source_output_list_list = [item for item in source_output_list_list if item.strip()]
                trans_output_list_list = [item for item in trans_output_list_list if item.strip()]
                if len(source_output_list_list) == len(trans_output_list_list):
                    if_diff = False
                    same = 0
                    for item1, item2 in zip(source_output_list_list, trans_output_list_list):
                        if item1.strip() == 'No-Support' or item2.strip() == 'No-Support':
                            continue
                        if item1.strip() == '' and item2.strip() == '':
                            continue
                        if not compare_value(item1.strip(), item2.strip()):
                            if_diff = True
                        else:
                            same += 1
                    if if_diff == True or same == 0:
                        print(f"{color.BOLD}{color.RED}Diff--{file_ID}{color.END}")
                        test_failed.append(f"{trans_file.split('.')[0]}")
                    else:
                        print(f"{color.BOLD}{color.GREEN}Success--{file_ID}{color.END}")
                        os.makedirs(f'{trans_pass_dataset_dir}/{ID}/', exist_ok=True)
                        save_file(''.join(trans_lines), f'{trans_pass_dataset_dir}/{ID}/{trans_file}')
                        test_passed.append(f"{trans_file.split('.')[0]}")
                else:
                    print(f"{color.BOLD}{color.RED}Diff--{file_ID}{color.END}")
                    test_failed.append(f"{trans_file.split('.')[0]}")


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
        "--model_name",
        default='qwen2.5-coder-32b-instruct',
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
    args = parser.parse_args()

    model_name = args.model_name
    source_lang = args.source_lang
    target_lang = args.target_lang
    tmp_dir = args.tmp_dir

    dataset_name = 'CodeNet'
    main(model_name, source_lang, target_lang, tmp_dir, dataset_name)

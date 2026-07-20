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


def main(model_name, source_lang, target_lang, tmp_dir, dataset_name):
    run_input_output_folder = '/home/ubuntu/CodeNet/Project_CodeNet/derived/input_output/data'
    source_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted'
    info_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo'
    source_pass_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted-pass'
    info_pass_dataset_dir = f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo-pass'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]

    file_IDs = [this_id for this_id in os.listdir(source_dataset_dir)]
    file_IDs.sort()

    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(info_pass_dataset_dir, exist_ok=True)


    for ID in tqdm(file_IDs):
        print(ID)
        file_group = ID.split('-')[0]
        run_input_file = f'{run_input_output_folder}/{file_group}/input.txt'
        test_passed = []
        test_failed = []

        source_file_ID = [this_ID.split('.')[0] for this_ID in os.listdir(f'{source_dataset_dir}/{ID}')]
        source_file_ID.sort()
        for file_ID in tqdm(source_file_ID):
            exist_files = os.listdir(f'{tmp_dir}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                    shutil.rmtree(f'{tmp_dir}/{exist_file}')
                else:
                    os.remove(f'{tmp_dir}/{exist_file}')

            shutil.copyfile(f'{source_dataset_dir}/{ID}/{file_ID}.{source_ext}', f'{tmp_dir}/{file_ID}.{source_ext}')
            source_info, source_output = run(f'{tmp_dir}/{file_ID}.{source_ext}', run_input_file, source_lang, tmp_dir)
            if source_info == 'success' and source_output.strip() != '':
                print(f"{color.BOLD}{color.GREEN}Success{color.END}")
                test_passed.append(f"{file_ID}")
            else:
                print(f"{color.BOLD}{color.RED}Fail{color.END}")
                test_failed.append(f"{file_ID}")

        f_info = open(f'{info_dataset_dir}/{ID}.txt')
        info_lines = f_info.readlines()
        infos = []
        for line in info_lines:
            this_info = line.strip().split('\t')
            try:
                infos.append([this_info[1].split('.')[0], this_info[2].split('.')[0]])
            except:
                continue
        print(infos)
        print(test_passed)
        info_list = []
        for line in info_lines:
            this_info = line.strip().split('\t')
            try:
                source_delete_path = this_info[0]
                code1_id = this_info[1].split('.')[0]
                code2_id = this_info[2].split('.')[0]
                tree_id = this_info[3].split('.')[0]
            except:
                continue
            if code1_id in test_passed and code2_id in test_passed:
                os.makedirs(f'{source_pass_dataset_dir}/{ID}/', exist_ok=True)
                shutil.copyfile(f'{source_dataset_dir}/{ID}/{code1_id}.{source_ext}', f'{source_pass_dataset_dir}/{ID}/{code1_id}.{source_ext}')
                shutil.copyfile(f'{source_dataset_dir}/{ID}/{code2_id}.{source_ext}', f'{source_pass_dataset_dir}/{ID}/{code2_id}.{source_ext}')
                info_list.append(f'{source_delete_path}\t{code1_id}.{source_ext}\t{code2_id}.{source_ext}\t{tree_id}.pkl')
        if info_list:
            f_map = open(f'{info_pass_dataset_dir}/{ID}.txt', 'w')
            for this_info_list in info_list:
                print(this_info_list.strip(), file=f_map)
            f_map.close()


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

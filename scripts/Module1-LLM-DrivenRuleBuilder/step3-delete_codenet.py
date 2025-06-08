from utils import *
from tqdm import tqdm
import time
import pickle
import argparse


def delete_func(source_lang, target_lang, source_lines, source_ext, file_ID, dataset_name, model_name):
    pre_lines = []
    source_delete_code_dict = []
    if source_lang == 'Java':
        source_delete_code_dict = delete(source_lang, source_lines[5:-1])
    elif source_lang == 'Python':
        start_line_id = -1
        for line_id, line in enumerate(source_lines):
            if line == 'def main():\n':
                start_line_id = line_id
                break
            else:
                pre_lines.append(line)
        source_delete_code_dict = delete(source_lang, source_lines[start_line_id:-1])
    elif source_lang == 'C++':
        source_delete_code_dict = delete(source_lang, source_lines[8:])
    code_list = []

    for source_delete_path, source_delete_path_codelines_pair in source_delete_code_dict.items():
        for code_pair in source_delete_path_codelines_pair:
            code1 = code_pair[0]
            code2 = code_pair[1]
            if code1 not in code_list:
                code_list.append(code1)
            if code2 not in code_list:
                code_list.append(code2)
    for code_id, code in enumerate(code_list):
        this_new_deleted_code_lines = []
        if source_lang == 'Python':
            this_new_deleted_code_lines = pre_lines[:]
            for this_line in code:
                if this_line.strip() and this_line.strip() != ';':
                    this_new_deleted_code_lines.append(this_line)
            this_new_deleted_code_lines.append('\nmain()')
        elif source_lang == 'Java':
            this_new_deleted_code_lines = ['import java.util. *;\n', 'import java.util.stream.*;\n', 'import java.lang.*;\n', 'import javafx.util.Pair;\n', 'public class Main {\n']
            for this_line in code:
                if this_line.strip():
                    this_new_deleted_code_lines.append(this_line)
            this_new_deleted_code_lines.append('}\n')
        elif source_lang == 'C++':
            this_new_deleted_code_lines = ['#include <iostream>\n', '#include <cstdlib>\n', '#include <string>\n', '#include <vector>\n', '#include <fstream>\n', '#include <iomanip>\n', '#include <bits/stdc++.h>\n', 'using namespace std;\n']
            for this_line in code:
                if this_line.strip():
                    this_new_deleted_code_lines.append(this_line)
        f_delete = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted/{file_ID}/{code_id}.{source_ext}', 'w')
        f_delete.write(''.join(this_new_deleted_code_lines).strip())
        f_delete.close()
    path_id = 0
    info_list = []
    for source_delete_path, source_delete_path_codelines_pair in source_delete_code_dict.items():
        for code_pair in source_delete_path_codelines_pair:
            code1 = code_pair[0]
            code2 = code_pair[1]
            code_path_tree = code_pair[2][0]
            count1 = code_list.index(code1)
            count2 = code_list.index(code2)
            if [source_delete_path, count1, count2] not in info_list:
                f_map = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo/{file_ID}.txt', 'a')
                print(f'{source_delete_path}\t{count1}.{source_ext}\t{count2}.{source_ext}\t{path_id}', file=f_map)
                f_map.close()
                outp = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedtree/{file_ID}/{path_id}.pkl', 'wb')
                pickle.dump(code_path_tree, outp, pickle.HIGHEST_PROTOCOL)
                outp.close()
                path_id += 1
                info_list.append([source_delete_path, count1, count2])


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
        "--path_to_save_source_code",
        default='CodeNet_sourcefiles',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()

    model_name = args.model_name
    source_lang = args.source_lang
    target_lang = args.target_lang
    source_dataset_dir = args.path_to_save_source_code

    dataset_name = 'CodeNet'
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    IDs = []
    f_pass = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-testpass.txt')
    ID_lines = f_pass.readlines()
    f_pass.close()
    for line in ID_lines:
        if line.strip():
            IDs.append(line.strip())
    os.makedirs(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted/', exist_ok=True)
    os.makedirs(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo/', exist_ok=True)
    os.makedirs(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedtree/', exist_ok=True)
    IDs.sort()
    for file_ID in tqdm(IDs):
        print(file_ID)
        start = time.time()
        f_map = open(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedinfo/{file_ID}.txt', 'w')
        f_map.close()
        os.makedirs(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deleted/{file_ID}/', exist_ok=True)
        os.makedirs(f'{dataset_name}/{model_name}-{source_lang}-{target_lang}-deletedtree/{file_ID}/', exist_ok=True)
        f_source = open(f'{source_dataset_dir}/{source_lang}-{target_lang}/{file_ID}.{source_ext}')
        source_lines = f_source.readlines()
        f_source.close()
        delete_func(source_lang, target_lang, source_lines, source_ext, file_ID, dataset_name, model_name)

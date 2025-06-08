from utils import *
import argparse


def logout(task_name, source_lang, target_lang, new_maps_count, this_new_map, source_path, trans_path, text1, text2, text3, text4, loop_time, source_path2, target_path2, source_tree2_text, target_tree2_text):
    f = open(f'{task_name}/exp-{source_lang}-{target_lang}-expression-update-{loop_time+1}/{new_maps_count}.cpp', 'w')
    print(source_path, file=f)
    print('\n' + text1, file=f)
    print('\n' + this_new_map[0], file=f)
    print('\n' + text3 + '\n', file=f)
    print('\n' + trans_path, file=f)
    print('\n' + text2, file=f)
    print('\n' + this_new_map[1][0], file=f)
    print('\n' + text4, file=f)
    print('\n' + '--------------------------', file=f)
    print('\n' + source_path2, file=f)
    print('\n' + source_tree2_text, file=f)
    print('\n' + target_path2, file=f)
    print('\n' + target_tree2_text, file=f)
    f.close()


def run(path_to_map, path_to_save_FL, path_to_label, path_to_code, path_to_DATABASE, target_model_name, source_lang, target_lang, model_name):
    generated_map = loadMap(f'{path_to_map}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')
    save_FL_dir = f'{path_to_save_FL}/{target_model_name}-{source_lang}-{target_lang}-FL'
    os.makedirs(save_FL_dir, exist_ok=True)
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    ID2label = {}
    f_IDlabel = open(f'{path_to_label}/{target_model_name}-{source_lang}-{target_lang}.txt')
    lines = f_IDlabel.readlines()
    for line in lines:
        items = line.split('|')
        ID2label[items[0]] = []
        for item in items[1:]:
            ID2label[items[0]].append(int(item))

    model_names_for_mining = [model_name]
    datasets = ['CodeNet']
    task1_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-{"_".join(datasets)}-{source_lang}-{target_lang}'
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1]) for file in os.listdir(f'{task1_name}/') if
                                  file.startswith(
                                      f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-')
                                  and file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)
    print(f"{color.BOLD}{color.GREEN}{max_loop}{color.END}")

    maps2trees = load_maps2trees(task1_name)
    maps = load_map_for_locate(
        f'{task1_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{max_loop}.txt')
    path2pair = load_path2pair(task1_name, source_lang, target_lang, max_loop)
    source_path2tree = {}
    trans_path2tree = {}
    for k, v_lists in maps.items():
        for v_list in v_lists:
            this_map_trees = maps2trees[k + '>>>>' + '####'.join(v_list)]
            k_tree = this_map_trees[0]
            v_trees = this_map_trees[1]
            if k_tree not in source_path2tree:
                source_path2tree[k] = k_tree
            for v, v_tree in zip(v_list, v_trees):
                if v not in trans_path2tree:
                    trans_path2tree[v] = v_tree
    root_node2map = {}
    for k, v in path2pair.items():
        if '||||' in k:
            this_k = k.split('||||')[0]
        else:
            this_k = k
        if this_k not in root_node2map:
            root_node2map[this_k] = v[:]
        else:
            root_node2map[this_k].extend(v)

    code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}'
    transcode_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}'
    script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
    script_files = os.listdir(script_dir)

    IDs = [file.split('.')[0] for file in script_files if file.split('.')[0] in ID2label]
    IDs.sort()
    sum = 0
    Correct_FL = 0
    Wrong_FL = 0
    miss_FL = 0
    all_FL_case_count = 0
    for ID in IDs:
        all_FL_case_count += 1
        sum += 1

        if ID not in generated_map:
            Wrong_FL += 1
            miss_FL += 1
            continue
        _, source_lines = read_code(f'{code_dir}/{ID}.{source_ext}', source_lang)
        _, trans_lines = read_code(f'{transcode_dir}/{ID}.{target_ext}', target_lang)

        source_tree, source_varilable_names = code_parse_for_map(source_lang, source_lines)
        trans_tree, trans_varilable_names = code_parse_for_map(target_lang, trans_lines)
        source_stmt_list = []
        source_stmt_list_pos = []
        trans_stmt_list = []
        trans_stmt_list_pos = []
        if source_lang == 'Java':
            this_source_lines = copy.deepcopy(source_lines)
            this_source_lines.insert(0, 'public class ClassName{\n')
            this_source_lines.append('}\n')
            ori_source_stmt_info_lists = traverse_tree(source_tree, source_lang, this_source_lines,
                                                       source_varilable_names, only_block=False,
                                                       exclude_last_child=False, only_path=True, fun_block=0)
            ori_source_stmt_info_lists = reduce_pos_of_java_tree(ori_source_stmt_info_lists)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_source_stmt_info_lists)
        elif source_lang == 'Python':
            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines,
                                                       source_varilable_names, only_block=False,
                                                       exclude_last_child=False, only_path=True, fun_block=0)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_source_stmt_info_lists)
        elif source_lang == 'C++':
            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines,
                                                       source_varilable_names, only_block=False,
                                                       exclude_last_child=False, only_path=True, fun_block=0)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_source_stmt_info_lists)

        if target_lang == 'Java':
            this_trans_lines = copy.deepcopy(trans_lines)
            this_trans_lines.insert(0, 'public class ClassName{\n')
            this_trans_lines.append('}\n')
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, this_trans_lines,
                                                      trans_varilable_names, only_block=False, exclude_last_child=False,
                                                      only_path=True, fun_block=0)
            ori_trans_stmt_info_lists = reduce_pos_of_java_tree(ori_trans_stmt_info_lists)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_trans_stmt_info_lists)
        elif target_lang == 'Python':
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                      trans_varilable_names, only_block=False, exclude_last_child=False,
                                                      only_path=True, fun_block=0)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_trans_stmt_info_lists)
        elif target_lang == 'C++':
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                      trans_varilable_names, only_block=False, exclude_last_child=False,
                                                      only_path=True, fun_block=0)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                ori_trans_stmt_info_lists)

        source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos = rephrase_stmt_trees(source_lang, source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, source_lines)
        trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos = rephrase_stmt_trees(target_lang, trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, trans_lines)

        line_M = {}
        for s_id in range(len(source_lines)):
            for t_id in range(len(trans_lines)):
                line_M[f'{s_id}-{t_id}'] = False
        for pair in generated_map[ID]:
            line_M[f'{pair[0]}-{pair[1]}'] = True

        transline2stmt = line2stmt(trans_stmt_list_pos)

        source_predecessors, source_successors, source_stmt_use_consts, source_stmt_def_variables, source_stmt_use_variables, source_line_def_variables = parse_vari_dep(
            source_stmt_list, source_lines, source_stmt_list_pos, source_lang, this_source_trees)
        trans_predecessors, trans_successors, trans_stmt_use_consts, trans_stmt_def_variables, trans_stmt_use_variables, trans_line_def_variables = parse_vari_dep(
            trans_stmt_list, trans_lines, trans_stmt_list_pos, target_lang, this_trans_trees)

        source_traces = load_trace(
            f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt',
            source_lines, source_lang, target_lang, source_lang, ID)
        trans_traces = load_trace(
            f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt',
            trans_lines, source_lang, target_lang, target_lang, ID)
        report_id = compare_stepbystep(source_traces, trans_traces, source_lang, target_lang, line_M, len(source_lines), len(trans_lines), source_lines, trans_lines, trans_line_def_variables)

        f_fl = open(f'{save_FL_dir}/{ID}.txt', 'w')
        print(report_id, file=f_fl)
        f_fl.close()

        if report_id in ID2label[ID]:
            Correct_FL += 1
        else:
            Wrong_FL += 1

    print(f'{target_model_name}-{source_lang}-{target_lang}')
    print('ALL: ', all_FL_case_count)
    print('Correct_FL: ', Correct_FL)
    print('S_FL', round(Correct_FL/(Correct_FL+Wrong_FL), 3))
    print('')
    return None, None, None, None


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
        "--model_name",
        default='qwen2.5-coder-32b-instruct',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_map",
        default='Ours_map',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_save_FL",
        default='Ours_FL',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_label",
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_code",
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_DATABASE",
        default='/DATABASE',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    source_lang = args.source_lang
    target_lang = args.target_lang
    target_model_name = args.target_model_name
    model_name = args.model_name
    path_to_map = args.path_to_map
    path_to_save_FL = args.path_to_save_FL
    path_to_label = args.path_to_label
    path_to_code = args.path_to_code
    path_to_DATABASE = args.path_to_DATABASE
    count_right, count_wrong, count_right_B, count_wrong_B = run(path_to_map, path_to_save_FL, path_to_label, path_to_code, path_to_DATABASE, target_model_name, source_lang, target_lang, model_name)

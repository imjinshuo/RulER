from utils import *
from tqdm import tqdm
import time
import argparse


def run(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir, path_to_save_map_for_line, path_to_save_map_for_statement):
    save_mapping_dir = f'{path_to_save_map_for_line}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping'
    os.makedirs(save_mapping_dir, exist_ok=True)
    save_stmtmapping_dir = f'{path_to_save_map_for_statement}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping'
    os.makedirs(save_stmtmapping_dir, exist_ok=True)
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    code_files = os.listdir(transcode_script_dir)

    IDs = [code_file.split('.')[0] for code_file in code_files]
    IDs.sort()

    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1])
                                  for file in os.listdir(f'{task1_name}/')
                                  if file.startswith(f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-')
                                  and file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)
    print(f"{color.BOLD}{color.GREEN}{max_loop}{color.END}")
    maps2trees = load_maps2trees(task1_name)
    maps = load_map_for_locate(f'{task1_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{max_loop}.txt')
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


    inverse_existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1])
                                          for file in os.listdir(f'{task2_name}/')
                                          if file.startswith(f'{"_".join(model_names_for_mining)}-{target_lang}-{source_lang}-maps-')
                                          and file.split('.')[-1] == 'txt']
    inverse_max_loop = max(inverse_existing_maps_files_number)
    print(f"{color.BOLD}{color.GREEN}{inverse_max_loop}{color.END}")

    inverse_maps2trees = load_maps2trees(task2_name)
    inverse_maps = load_map_for_locate(f'{task2_name}/{"_".join(model_names_for_mining)}-{target_lang}-{source_lang}-maps-{inverse_max_loop}.txt')
    inverse_path2pair = load_path2pair(task2_name, target_lang, source_lang, inverse_max_loop)
    inverse_source_path2tree = {}
    inverse_trans_path2tree = {}
    for k, v_lists in inverse_maps.items():
        for v_list in v_lists:
            this_map_trees = inverse_maps2trees[k + '>>>>' + '####'.join(v_list)]
            k_tree = this_map_trees[0]
            v_trees = this_map_trees[1]
            if k_tree not in inverse_source_path2tree:
                inverse_source_path2tree[k] = k_tree
            for v, v_tree in zip(v_list, v_trees):
                if v not in inverse_trans_path2tree:
                    inverse_trans_path2tree[v] = v_tree

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

    inverse_root_node2map = {}
    for k, v in inverse_path2pair.items():
        if '||||' in k:
            this_k = k.split('||||')[0]
        else:
            this_k = k
        if this_k not in inverse_root_node2map:
            inverse_root_node2map[this_k] = v[:]
        else:
            inverse_root_node2map[this_k].extend(v)

    sum = 0
    count1 = 0
    count2 = 0
    count3 = 0
    count4 = 0
    for ID in IDs[:]:
        sum += 1
        print(f"{color.BOLD}{color.GREEN}\n{sum}--{ID}{color.END}")
        _, source_lines = read_code(f'{code_dir}/{ID}.{source_ext}', source_lang)
        _, trans_lines = read_code(f'{transcode_dir}/{ID}.{target_ext}', target_lang)
        source_tree, source_varilable_names = code_parse_for_map(source_lang, source_lines)
        trans_tree, trans_varilable_names = code_parse_for_map(target_lang, trans_lines)
        source_stmt_list = []
        this_source_path2tree = {}
        source_stmt_list_pos = []
        trans_stmt_list = []
        this_trans_path2tree = {}
        trans_stmt_list_pos = []
        if source_lang == 'Java':
            this_source_lines = copy.deepcopy(source_lines)
            this_source_lines.insert(0, 'public class ClassName{\n')
            this_source_lines.append('}\n')
            ori_source_stmt_info_lists = traverse_tree(source_tree, source_lang, this_source_lines, source_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=False)
            ori_source_stmt_info_lists = reduce_pos_of_java_tree(ori_source_stmt_info_lists)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)
        elif source_lang == 'Python':
            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines, source_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=True)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)
        elif source_lang == 'C++':
            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines, source_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=False)
            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)

        if target_lang == 'Java':
            this_trans_lines = copy.deepcopy(trans_lines)
            this_trans_lines.insert(0, 'public class ClassName{\n')
            this_trans_lines.append('}\n')
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, this_trans_lines, trans_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=False)
            ori_trans_stmt_info_lists = reduce_pos_of_java_tree(ori_trans_stmt_info_lists)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)
        elif target_lang == 'Python':
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines, trans_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=True)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)
        elif target_lang == 'C++':
            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines, trans_varilable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0, mine=False)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)

        source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos = rephrase_stmt_trees(source_lang, source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, source_lines)
        trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos = rephrase_stmt_trees(target_lang, trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, trans_lines)

        sourceline2stmt = line2stmt(source_stmt_list_pos)
        transline2stmt = line2stmt(trans_stmt_list_pos)
        source_stmt2mapping = {}
        for ori_id, ori_path in tqdm(enumerate(source_stmt_list)):
            if ori_id == 0:
                continue
            ori_code = this_source_trees[ori_id].text
            depth = 0
            max_depth = 1000000000
            max_possible_choices = 1000000000
            time_limit = 60
            start_time = time.time()
            possible_maps_list = match(this_source_path2tree[ori_path], [], source_lang, target_lang, maps, trans_path2tree)
            if not possible_maps_list:
                search, search_result = check_new_rule(f'{task1_name}-new', ori_path)
                if search:
                    possible_maps_force_list = search_result
                else:
                    possible_maps_force_list, _ = match_force(this_source_path2tree[ori_path], [], root_node2map,
                                                                    source_lang, target_lang,
                                                                    maps, source_path2tree, trans_path2tree, depth,
                                                                    max_depth,
                                                                    max_possible_choices, start_time, time_limit, False)
                    save_new_rule(f'{task1_name}-new', ori_path, possible_maps_force_list)
                possible_maps_list.extend(possible_maps_force_list)
            if possible_maps_list:
                count1 += 1
                source_stmt2mapping[ori_path] = possible_maps_list
            else:
                count2 += 1
                source_stmt2mapping[ori_path] = []
                print(f"{color.BOLD}{color.GREEN}CODE w.o. R: {ori_code}{color.END}")

        trans_stmt2mapping = {}
        for ori_id, ori_path in tqdm(enumerate(trans_stmt_list)):
            if ori_id == 0:
                continue
            ori_code = this_trans_trees[ori_id].text
            depth = 0
            max_depth = 1000000000
            max_possible_choices = 1000000000
            time_limit = 60
            start_time = time.time()
            possible_maps_list = match(this_trans_path2tree[ori_path], [], target_lang, source_lang, inverse_maps, source_path2tree)
            if not possible_maps_list:
                search, search_result = check_new_rule(f'{task2_name}-new', ori_path)
                if search:
                    possible_maps_force_list = search_result
                else:
                    possible_maps_force_list, _ = match_force(this_trans_path2tree[ori_path], [], inverse_root_node2map,
                                                                    target_lang, source_lang,
                                                                    inverse_maps, trans_path2tree, source_path2tree, depth,
                                                                    max_depth,
                                                                    max_possible_choices, start_time, time_limit, False)
                    save_new_rule(f'{task2_name}-new', ori_path, possible_maps_force_list)
                possible_maps_list.extend(possible_maps_force_list)
            if possible_maps_list:
                count3 += 1
                trans_stmt2mapping[ori_path] = possible_maps_list
            else:
                count4 += 1
                trans_stmt2mapping[ori_path] = []
                print(f"{color.BOLD}{color.GREEN}CODE w.o. R: {ori_code}{color.END}")

        M = {}
        for s_id in range(len(source_stmt_list)):
            for t_id in range(len(trans_stmt_list)):
                M[f'{s_id}-{t_id}'] = False
        M[f'{0}-{0}'] = True

        for s_id, s_path in enumerate(source_stmt_list):
            if s_path not in source_stmt2mapping:
                continue
            templates = source_stmt2mapping[s_path]
            for template_list_id, template_list in enumerate(templates):
                for trans_id in range(len(trans_stmt_list)-len(template_list)+1):
                    if_matched = True
                    for this_id in range(len(template_list)):
                        this_diff = compare_MyTree(template_list[this_id], this_trans_trees[trans_id+this_id], target_lang)
                        if this_diff:
                            if_matched = False
                            break
                    if if_matched:
                        for this_id in range(len(template_list)):
                            M[f'{s_id}-{trans_id+this_id}'] = True

        for t_id, t_path in enumerate(trans_stmt_list):
            if t_path not in trans_stmt2mapping:
                continue
            templates = trans_stmt2mapping[t_path]
            for template_list_id, template_list in enumerate(templates):
                for source_id in range(len(source_stmt_list)-len(template_list)+1):
                    if_matched = True
                    for this_id in range(len(template_list)):
                        this_diff = compare_MyTree(template_list[this_id], this_source_trees[source_id+this_id], source_lang)
                        if this_diff:
                            if_matched = False
                            break
                    if if_matched:
                        for this_id in range(len(template_list)):
                            M[f'{source_id+this_id}-{t_id}'] = True

        source_predecessors, source_successors, source_stmt_use_consts, source_stmt_def_variables, source_stmt_use_variables, source_line_def_variables = parse_vari_dep(source_stmt_list, source_lines, source_stmt_list_pos, source_lang, this_source_trees)
        trans_predecessors, trans_successors, trans_stmt_use_consts, trans_stmt_def_variables, trans_stmt_use_variables, trans_line_def_variables = parse_vari_dep(trans_stmt_list, trans_lines, trans_stmt_list_pos, target_lang, this_trans_trees)


        ori_updated_M = {}
        new_updated_M = copy.deepcopy(M)
        while ori_updated_M != new_updated_M:
            ori_updated_M = copy.deepcopy(new_updated_M)
            new_updated_M = verify_maps(copy.deepcopy(ori_updated_M), source_stmt_list, trans_stmt_list, source_predecessors, source_successors, trans_predecessors, trans_successors, source_stmt_use_consts, trans_stmt_use_consts)

        new_new_updated_M = extend_maps(new_updated_M, this_source_trees, this_trans_trees, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, source_stmt_list, trans_stmt_list)
        line_M = M2lines(new_new_updated_M, source_stmt_list_pos, trans_stmt_list_pos, source_lines, trans_lines, source_stmt_list, trans_stmt_list, sourceline2stmt, transline2stmt)

        f_map = open(f'{save_mapping_dir}/{ID}.txt', 'w')
        for k, v in line_M.items():
            if v and k != '0-0':
                this_mapping = k.split('-')
                print(f'{this_mapping[0]};{this_mapping[1]}', file=f_map)
        f_map.close()

        f_map = open(f'{save_stmtmapping_dir}/{ID}.txt', 'w')
        for k, v in new_new_updated_M.items():
            if v and k != '0-0':
                this_mapping = k.split('-')
                print(f'{this_mapping[0]};{this_mapping[1]}', file=f_map)
        f_map.close()

        print(f"{color.BOLD}{color.BLUE}\ncount1--{count1}{color.END}")
        print(f"{color.BOLD}{color.BLUE}count2--{count2}{color.END}")
        print(f"{color.BOLD}{color.BLUE}rate--{round(count1 / (count1 + count2), 4)}{color.END}")
        print(f"{color.BOLD}{color.BLUE}\ncount3--{count3}{color.END}")
        print(f"{color.BOLD}{color.BLUE}count4--{count4}{color.END}")
        print(f"{color.BOLD}{color.BLUE}rate--{round(count3 / (count3 + count4), 4)}{color.END}")
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
        "--path_to_code",
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_save_map_for_line",
        default='RulER_map',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_save_map_for_statement",
        default='RulER_map',
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
    model_names_for_mining = [args.model_name]
    path_to_code = args.path_to_code
    path_to_save_map_for_line = args.path_to_save_map_for_line
    path_to_save_map_for_statement = args.path_to_save_map_for_statement
    path_to_DATABASE = args.path_to_DATABASE

    task1_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-CodeNet-{source_lang}-{target_lang}'
    task2_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-CodeNet-{target_lang}-{source_lang}'
    code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}'
    transcode_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}'
    transcode_script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
    count_right, count_wrong, count_right_B, count_wrong_B = run(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir, path_to_save_map_for_line, path_to_save_map_for_statement)
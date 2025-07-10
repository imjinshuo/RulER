from utils import *
import time
import argparse


def run_wo_rule_synthesis(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir):
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

        source_stmt2mapping = {}
        for ori_id, ori_path in enumerate(source_stmt_list):
            if ori_id == 0:
                continue
            ori_code = this_source_trees[ori_id].text
            possible_maps_list = match(this_source_path2tree[ori_path], [], source_lang, target_lang, maps, trans_path2tree)
            if possible_maps_list:
                count1 += 1
                source_stmt2mapping[ori_path] = possible_maps_list
            else:
                count2 += 1
                source_stmt2mapping[ori_path] = []

        trans_stmt2mapping = {}
        for ori_id, ori_path in enumerate(trans_stmt_list):
            if ori_id == 0:
                continue
            ori_code = this_trans_trees[ori_id].text
            possible_maps_list = match(this_trans_path2tree[ori_path], [], target_lang, source_lang, inverse_maps, source_path2tree)
            if possible_maps_list:
                count3 += 1
                trans_stmt2mapping[ori_path] = possible_maps_list
            else:
                count4 += 1
                trans_stmt2mapping[ori_path] = []

    return count1, count2, round(count1 / (count1 + count2), 4), count3, count4, round(count3 / (count3 + count4), 4)


def run_w_rule_synthesis(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir):
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
        
        source_stmt2mapping = {}
        for ori_id, ori_path in enumerate(source_stmt_list):
            if ori_id == 0:
                continue
            ori_code = this_source_trees[ori_id].text
            possible_maps_list = match(this_source_path2tree[ori_path], [], source_lang, target_lang, maps, trans_path2tree)
            if not possible_maps_list:
                search, search_result = check_new_rule(f'{task1_name}-new', ori_path)
                possible_maps_list.extend(search_result)
            if possible_maps_list:
                count1 += 1
                source_stmt2mapping[ori_path] = possible_maps_list
            else:
                count2 += 1
                source_stmt2mapping[ori_path] = []

        trans_stmt2mapping = {}
        for ori_id, ori_path in enumerate(trans_stmt_list):
            if ori_id == 0:
                continue
            ori_code = this_trans_trees[ori_id].text
            possible_maps_list = match(this_trans_path2tree[ori_path], [], target_lang, source_lang, inverse_maps, source_path2tree)
            if not possible_maps_list:
                search, search_result = check_new_rule(f'{task2_name}-new', ori_path)
                possible_maps_list.extend(search_result)
            if possible_maps_list:
                count3 += 1
                trans_stmt2mapping[ori_path] = possible_maps_list
            else:
                count4 += 1
                trans_stmt2mapping[ori_path] = []

    return count1, count2, round(count1 / (count1 + count2), 4), count3, count4, round(count3 / (count3 + count4), 4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_code",
        default='DATABASE/DATA/CODE',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--path_to_DATABASE",
        default='DATABASE',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    target_lang ='C++'
    model_names_for_mining = ['qwen2.5-coder-32b-instruct']
    path_to_code = args.path_to_code
    path_to_DATABASE = args.path_to_DATABASE

    all_count1_w = 0
    all_count2_w = 0
    all_count1_wo = 0
    all_count2_wo = 0
    for source_lang in ['Java', 'Python']:
        count1_w = 0
        count2_w = 0
        count3_w = 0
        count4_w = 0
        count1_wo = 0
        count2_wo = 0
        count3_wo = 0
        count4_wo = 0
        for target_model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
            task1_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-CodeNet-{source_lang}-{target_lang}'
            task2_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-CodeNet-{target_lang}-{source_lang}'
            code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}'
            transcode_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}'
            transcode_script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
            w_count1, w_count2, w_count_rate_s_t, w_count3, w_count4, w_count_rate_t_s = run_w_rule_synthesis(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir)
            wo_count1, wo_count2, wo_count_rate_s_t, wo_count3, wo_count4, wo_count_rate_t_s = run_wo_rule_synthesis(model_names_for_mining, target_model_name, source_lang, target_lang, task1_name, task2_name, code_dir, transcode_dir, transcode_script_dir)
            count1_w += w_count1
            count2_w += w_count2
            count3_w += w_count3
            count4_w += w_count4
            count1_wo += wo_count1
            count2_wo += wo_count2
            count3_wo += wo_count3
            count4_wo += wo_count4

        all_count1_w += count1_w
        all_count1_w += count3_w
        all_count2_w += count2_w
        all_count2_w += count4_w
        all_count1_wo += count1_wo
        all_count1_wo += count3_wo
        all_count2_wo += count2_wo
        all_count2_wo += count4_wo
        print(f"\nC_stmt of RulER on {source_lang}-{target_lang} w.o. rule synthesis:{round(count1_wo / (count1_wo + count2_wo), 4)}")
        print(f"C_stmt of RulER on {target_lang}-{source_lang} w.o. rule synthesis:{round(count3_wo / (count3_wo + count4_wo), 4)}")
        print(f"C_stmt of RulER on {source_lang}-{target_lang} w. rule synthesis:{round(count1_w / (count1_w + count2_w), 4)}")
        print(f"C_stmt of RulER on {target_lang}-{source_lang} w. rule synthesis:{round(count3_w / (count3_w + count4_w), 4)}")
    print(f"\nAverage C_stmt of RulER on Java-{target_lang} w. rule synthesis:{round(all_count1_w / (all_count1_w + all_count2_w), 4)}")
    print(f"Average C_stmt of RulER on Python-{target_lang} w.o. rule synthesis:{round(all_count1_wo / (all_count1_wo + all_count2_wo), 4)}")


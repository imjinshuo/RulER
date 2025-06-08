from tqdm import tqdm
from utils import *
from tqdm import trange


def build_statement_mapping(model_names_for_mining, source_lang, target_lang, task_name, datasets, number1, invalid_stmt):
    f_invalid_stmt = open(invalid_stmt)
    invalid_stmt_lines = [line.strip() for line in f_invalid_stmt.readlines()]
    f_invalid_stmt.close()
    invalid_stmt_maps = []
    for line in invalid_stmt_lines:
        this_map = line.split('\t')
        if '####' not in this_map[1]:
            invalid_stmt_maps.append([this_map[0], [this_map[1]]])
        else:
            invalid_stmt_maps.append([this_map[0], this_map[1].split('####')])

    maps = {}
    ori_path2tree = {}
    path2tree = {}
    for dataset in datasets:
        for model_name in model_names_for_mining:
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[source_lang]
            target_ext = extensions[target_lang]
            source_tree_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deletedtree'
            source_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted'
            source_deletepass_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted-pass'
            source_deleteinfopass_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deletedinfo-pass'
            trans_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans-pass'
            os.makedirs(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}', exist_ok=True)
            exist_files = os.listdir(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}')
            for exist_file in exist_files:
                if os.path.isdir(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{exist_file}'):
                    shutil.rmtree(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{exist_file}')
                else:
                    os.remove(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{exist_file}')

            IDs = os.listdir(source_delete_dir)
            IDs.sort()
            IDs = IDs[:number1]
            pass_IDs = os.listdir(source_deletepass_dir)

            count = 0
            for ID in tqdm(IDs):
                if ID not in pass_IDs:
                    continue
                f_info = open(f'{source_deleteinfopass_dir}/{ID}.txt')
                info_lines = f_info.readlines()
                f_info.close()
                for info_line in info_lines:
                    if info_line.strip():
                        info = info_line.strip().split('\t')
                        original_path = info[0]
                        file1_name = info[1].split('.')[0]
                        file2_name = info[2].split('.')[0]
                        tree_file = info[3].split('.')[0]
                        if os.path.isfile(f'{source_tree_dir}/{ID}/{tree_file}.pkl'):
                            with open(f'{source_tree_dir}/{ID}/{tree_file}.pkl', 'rb') as f:
                                source_tree = pickle.load(f)
                                if original_path not in ori_path2tree:
                                    ori_path2tree[original_path] = source_tree

                        if not os.path.isfile(f'{source_deletepass_dir}/{ID}/{file1_name}.{source_ext}') or not os.path.isfile(f'{source_deletepass_dir}/{ID}/{file2_name}.{source_ext}'):
                            continue
                        source_wholecode1, source_code_lines1 = read_code(f'{source_deletepass_dir}/{ID}/{file1_name}.{source_ext}', source_lang)
                        source_wholecode2, source_code_lines2 = read_code(f'{source_deletepass_dir}/{ID}/{file2_name}.{source_ext}', source_lang)
                        if dataset == 'CodeNet':
                            if source_lang == 'C++':
                                source_code_lines1 = source_code_lines1[8:]
                                source_code_lines2 = source_code_lines2[8:]
                            elif source_lang == 'Python':
                                source_code_lines1 = source_code_lines1[source_code_lines1.index('def main():\n'):-1]
                                source_code_lines2 = source_code_lines2[source_code_lines2.index('def main():\n'):-1]
                            elif source_lang == 'Java':
                                source_code_lines1 = source_code_lines1[5:-1]
                                source_code_lines2 = source_code_lines2[5:-1]
                        elif dataset == 'GeeksforGeeks':
                            source_code_lines1 = preprocess_funclines(source_code_lines1, source_lang)
                            source_code_lines2 = preprocess_funclines(source_code_lines2, source_lang)

                        source_tree1, source_variable_names1 = code_parse_for_map(source_lang, ''.join(source_code_lines1))
                        source_tree2, source_variable_names2 = code_parse_for_map(source_lang, ''.join(source_code_lines2))
                        source_stmt_list1 = []
                        source_stmt_list_depth1 = []
                        this_source_trees1 = []
                        this_source_path2tree1 = {}
                        source_stmt_list2 = []
                        source_stmt_list_depth2 = []
                        this_source_trees2 = []
                        this_source_path2tree2 = {}
                        if source_lang == 'Java':
                            this_source_lines1 = copy.deepcopy(source_code_lines1)
                            this_source_lines1.insert(0, 'public class ClassName{\n')
                            this_source_lines1.append('}\n')
                            ori_source_stmt_info_lists1 = traverse_tree(source_tree1, source_lang, this_source_lines1,
                                                                       source_variable_names1, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            ori_source_stmt_info_lists1 = reduce_pos_of_java_tree(ori_source_stmt_info_lists1)
                            source_func_stmt1 = ori_source_stmt_info_lists1[0]
                            ori_source_stmt_info_lists1 = ori_source_stmt_info_lists1[1:]
                            source_stmt_list1, source_stmt_list_depth1, this_source_trees1, this_source_path2tree1, source_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists1)
                            this_source_lines2 = copy.deepcopy(source_code_lines2)
                            this_source_lines2.insert(0, 'public class ClassName{\n')
                            this_source_lines2.append('}\n')
                            ori_source_stmt_info_lists2 = traverse_tree(source_tree2, source_lang, this_source_lines2,
                                                                       source_variable_names2, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            ori_source_stmt_info_lists2 = reduce_pos_of_java_tree(ori_source_stmt_info_lists2)
                            source_func_stmt2 = ori_source_stmt_info_lists2[0]
                            ori_source_stmt_info_lists2 = ori_source_stmt_info_lists2[1:]
                            source_stmt_list2, source_stmt_list_depth2, this_source_trees2, this_source_path2tree2, source_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists2)
                            del this_source_lines1
                            del this_source_lines2
                        elif source_lang == 'Python':
                            ori_source_stmt_info_lists1 = traverse_tree(source_tree1.root_node, source_lang, source_code_lines1,
                                                                       source_variable_names1, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt1 = ori_source_stmt_info_lists1[0]
                            ori_source_stmt_info_lists1 = ori_source_stmt_info_lists1[1:]
                            source_stmt_list1, source_stmt_list_depth1, this_source_trees1, this_source_path2tree1, source_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists1)
                            ori_source_stmt_info_lists2 = traverse_tree(source_tree2.root_node, source_lang, source_code_lines2,
                                                                       source_variable_names2, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt2 = ori_source_stmt_info_lists2[0]
                            ori_source_stmt_info_lists2 = ori_source_stmt_info_lists2[1:]
                            source_stmt_list2, source_stmt_list_depth2, this_source_trees2, this_source_path2tree2, source_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists2)
                        elif source_lang == 'C++':
                            ori_source_stmt_info_lists1 = traverse_tree(source_tree1.root_node, source_lang, source_code_lines1,
                                                                       source_variable_names1, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt1 = ori_source_stmt_info_lists1[0]
                            ori_source_stmt_info_lists1 = ori_source_stmt_info_lists1[1:]
                            source_stmt_list1, source_stmt_list_depth1, this_source_trees1, this_source_path2tree1, source_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists1)
                            ori_source_stmt_info_lists2 = traverse_tree(source_tree2.root_node, source_lang, source_code_lines2,
                                                                       source_variable_names2, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt2 = ori_source_stmt_info_lists2[0]
                            ori_source_stmt_info_lists2 = ori_source_stmt_info_lists2[1:]
                            source_stmt_list2, source_stmt_list_depth2, this_source_trees2, this_source_path2tree2, source_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists2)

                        if not os.path.isfile(f'{trans_delete_dir}/{ID}/{file1_name}.{target_ext}') or not os.path.isfile(f'{trans_delete_dir}/{ID}/{file2_name}.{target_ext}'):
                            continue
                        trans_wholecode1, trans_code_lines1 = read_code(f'{trans_delete_dir}/{ID}/{file1_name}.{target_ext}', target_lang)
                        trans_wholecode2, trans_code_lines2 = read_code(f'{trans_delete_dir}/{ID}/{file2_name}.{target_ext}', target_lang)
                        if dataset == 'CodeNet':
                            if target_lang == 'C++':
                                trans_code_lines1 = trans_code_lines1[8:]
                                trans_code_lines2 = trans_code_lines2[8:]
                            elif target_lang == 'Python':
                                trans_code_lines1 = trans_code_lines1[trans_code_lines1.index('def main():\n'):-1]
                                trans_code_lines2 = trans_code_lines2[trans_code_lines2.index('def main():\n'):-1]
                            elif target_lang == 'Java':
                                trans_code_lines1 = trans_code_lines1[5:-1]
                                trans_code_lines2 = trans_code_lines2[5:-1]
                        elif dataset == 'GeeksforGeeks':
                            trans_code_lines1 = preprocess_funclines(trans_code_lines1, target_lang)
                            trans_code_lines2 = preprocess_funclines(trans_code_lines2, target_lang)

                        trans_tree1, trans_variable_names1 = code_parse_for_map(target_lang, ''.join(trans_code_lines1))
                        trans_tree2, trans_variable_names2 = code_parse_for_map(target_lang, ''.join(trans_code_lines2))
                        trans_stmt_list1 = []
                        trans_stmt_list_depth1 = []
                        this_trans_trees1 = []
                        this_trans_path2tree1 = {}
                        trans_stmt_list2 = []
                        trans_stmt_list_depth2 = []
                        this_trans_trees2 = []
                        this_trans_path2tree2 = {}
                        if target_lang == 'Java':
                            this_trans_lines1 = copy.deepcopy(trans_code_lines1)
                            this_trans_lines1.insert(0, 'public class ClassName{\n')
                            this_trans_lines1.append('}\n')
                            ori_trans_stmt_info_lists1 = traverse_tree(trans_tree1, target_lang, this_trans_lines1,
                                                                      trans_variable_names1, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            ori_trans_stmt_info_lists1 = reduce_pos_of_java_tree(ori_trans_stmt_info_lists1)
                            trans_func_stmt1 = ori_trans_stmt_info_lists1[0]
                            ori_trans_stmt_info_lists1 = ori_trans_stmt_info_lists1[1:]
                            trans_stmt_list1, trans_stmt_list_depth1, this_trans_trees1, this_trans_path2tree1, trans_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists1)
                            this_trans_lines2 = copy.deepcopy(trans_code_lines2)
                            this_trans_lines2.insert(0, 'public class ClassName{\n')
                            this_trans_lines2.append('}\n')
                            ori_trans_stmt_info_lists2 = traverse_tree(trans_tree2, target_lang, this_trans_lines2,
                                                                      trans_variable_names2, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            ori_trans_stmt_info_lists2 = reduce_pos_of_java_tree(ori_trans_stmt_info_lists2)
                            trans_func_stmt2 = ori_trans_stmt_info_lists2[0]
                            ori_trans_stmt_info_lists2 = ori_trans_stmt_info_lists2[1:]
                            trans_stmt_list2, trans_stmt_list_depth2, this_trans_trees2, this_trans_path2tree2, trans_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists2)
                            del this_trans_lines1
                            del this_trans_lines2
                        elif target_lang == 'Python':
                            ori_trans_stmt_info_lists1 = traverse_tree(trans_tree1.root_node, target_lang, trans_code_lines1,
                                                                      trans_variable_names1, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt1 = ori_trans_stmt_info_lists1[0]
                            ori_trans_stmt_info_lists1 = ori_trans_stmt_info_lists1[1:]
                            trans_stmt_list1, trans_stmt_list_depth1, this_trans_trees1, this_trans_path2tree1, trans_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists1)
                            ori_trans_stmt_info_lists2 = traverse_tree(trans_tree2.root_node, target_lang, trans_code_lines2,
                                                                      trans_variable_names2, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt2 = ori_trans_stmt_info_lists2[0]
                            ori_trans_stmt_info_lists2 = ori_trans_stmt_info_lists2[1:]
                            trans_stmt_list2, trans_stmt_list_depth2, this_trans_trees2, this_trans_path2tree2, trans_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists2)
                        if target_lang == 'C++':
                            ori_trans_stmt_info_lists1 = traverse_tree(trans_tree1.root_node, target_lang, trans_code_lines1,
                                                                      trans_variable_names1, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt1 = ori_trans_stmt_info_lists1[0]
                            ori_trans_stmt_info_lists1 = ori_trans_stmt_info_lists1[1:]
                            trans_stmt_list1, trans_stmt_list_depth1, this_trans_trees1, this_trans_path2tree1, trans_stmt_list_pos1, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists1)
                            ori_trans_stmt_info_lists2 = traverse_tree(trans_tree2.root_node, target_lang, trans_code_lines2,
                                                                      trans_variable_names2, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt2 = ori_trans_stmt_info_lists2[0]
                            ori_trans_stmt_info_lists2 = ori_trans_stmt_info_lists2[1:]
                            trans_stmt_list2, trans_stmt_list_depth2, this_trans_trees2, this_trans_path2tree2, trans_stmt_list_pos2, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists2)

                        source_path_depth1 = [[this_path, this_depth] for this_path, this_depth in zip(source_stmt_list1, source_stmt_list_depth1)]
                        source_path_depth2 = [[this_path, this_depth] for this_path, this_depth in zip(source_stmt_list2, source_stmt_list_depth2)]

                        source_more_stmt = []
                        source_more_depth = []
                        source_less_stmt = []
                        delete_paths = copy.deepcopy(source_path_depth2)
                        for this_id, this_i_path_depth in enumerate(source_path_depth1):
                            if this_i_path_depth not in delete_paths:
                                source_more_stmt.append([this_i_path_depth[0], this_id])
                                source_more_depth.append(this_i_path_depth[1])
                            else:
                                delete_paths.remove(this_i_path_depth)
                        delete_paths = copy.deepcopy(source_path_depth1)
                        for this_j_path_depth in source_path_depth2:
                            if this_j_path_depth not in delete_paths:
                                source_less_stmt.append(this_j_path_depth[0])
                            else:
                                delete_paths.remove(this_j_path_depth)
                        min_depth_ids = [id for id, depth in enumerate(source_more_depth) if depth == min(source_more_depth)]
                        source_more_stmt_filt = [source_more_stmt[id] for id in min_depth_ids]

                        trans_path_depth1 = [[this_path, this_depth] for this_path, this_depth in zip(trans_stmt_list1, trans_stmt_list_depth1)]
                        trans_path_depth2 = [[this_path, this_depth] for this_path, this_depth in zip(trans_stmt_list2, trans_stmt_list_depth2)]

                        trans_more_stmt = []
                        trans_more_depth = []
                        trans_less_stmt = []
                        delete_paths = copy.deepcopy(trans_path_depth2)
                        for this_id, this_i_path_depth in enumerate(trans_path_depth1):
                            if this_i_path_depth not in delete_paths:
                                trans_more_stmt.append([this_i_path_depth[0], this_id])
                                trans_more_depth.append(this_i_path_depth[1])
                            else:
                                delete_paths.remove(this_i_path_depth)
                        delete_paths = copy.deepcopy(trans_path_depth1)
                        for this_j_path_depth in trans_path_depth2:
                            if this_j_path_depth not in delete_paths:
                                trans_less_stmt.append(this_j_path_depth[0])
                            else:
                                delete_paths.remove(this_j_path_depth)
                        min_depth_ids = [id for id, depth in enumerate(trans_more_depth) if depth == min(trans_more_depth)]
                        trans_more_stmt_filt = [trans_more_stmt[id] for id in min_depth_ids]

                        for stmt, tree in zip(source_stmt_list1, this_source_trees1):
                            path2tree[stmt] = tree
                        for stmt, tree in zip(source_stmt_list2, this_source_trees2):
                            path2tree[stmt] = tree
                        for stmt, tree in zip(trans_stmt_list1, this_trans_trees1):
                            path2tree[stmt] = tree
                        for stmt, tree in zip(trans_stmt_list2, this_trans_trees2):
                            path2tree[stmt] = tree
                        if source_more_stmt_filt == []:
                            continue
                        if original_path.startswith('return'):
                            this_source_filter_more = [item[0] for item in source_more_stmt_filt if item[0].startswith('return')]
                            this_source_filter_more_id = [item[1] for item in source_more_stmt_filt if item[0].startswith('return')]
                            if 'comment' not in original_path and len(this_source_filter_more) != 1:
                                continue
                            this_trans_filter_more = [item[0] for item in trans_more_stmt_filt if item[0].startswith('return')]
                            this_trans_filter_more_id = [item[1] for item in trans_more_stmt_filt if item[0].startswith('return')]
                            if not this_trans_filter_more_id:
                                continue
                            if 'comment' not in original_path:
                                if_verified_new_mapping = verify_build_mapping(this_source_trees1[this_source_filter_more_id[0]],
                                                                               [this_trans_trees1[this_trans_filter_more_id[0]]],
                                                                               source_variable_names1, trans_variable_names1, source_lang, target_lang)
                                if not if_verified_new_mapping:
                                    continue
                            if not check_ERROR_map([original_path, [this_trans_filter_more[0]]]):
                                continue
                            if [original_path, [this_trans_filter_more[0]]] in invalid_stmt_maps:
                                continue
                            if len(this_trans_filter_more) == 1:
                                if original_path not in maps:
                                    count += 1
                                    print(count)
                                    f = open(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{count}.cpp', 'w')
                                    print(ID, file=f)
                                    print(file1_name, file2_name, file=f)
                                    print('------------------------------------------', file=f)
                                    print(original_path+'\t'+this_trans_filter_more[0], file=f)
                                    print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                    this_source_code_str = mytree2text(this_source_trees1[this_source_filter_more_id[0]], '')
                                    print(this_source_code_str, file=f)
                                    print('==========================================', file=f)
                                    this_trans_code_str = mytree2text(this_trans_trees1[this_trans_filter_more_id[0]], '')
                                    print(this_trans_code_str, file=f)
                                    f.close()
                                    maps[original_path] = [[this_trans_filter_more[0]]]
                                    save_maps2trees(task_name, original_path+'>>>>'+this_trans_filter_more[0], [this_source_trees1[this_source_filter_more_id[0]], [this_trans_trees1[this_trans_filter_more_id[0]]]])
                                else:
                                    if [this_trans_filter_more[0]] not in maps[original_path]:
                                        count += 1
                                        print(count)
                                        f = open(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{count}.cpp', 'w')
                                        print(ID, file=f)
                                        print(file1_name, file2_name, file=f)
                                        print('------------------------------------------', file=f)
                                        print(original_path+'\t'+this_trans_filter_more[0], file=f)
                                        print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                        this_source_code_str = mytree2text(this_source_trees1[this_source_filter_more_id[0]], '')
                                        print(this_source_code_str, file=f)
                                        print('==========================================', file=f)
                                        this_trans_code_str = mytree2text(this_trans_trees1[this_trans_filter_more_id[0]], '')
                                        print(this_trans_code_str, file=f)
                                        f.close()
                                        maps[original_path].append([this_trans_filter_more[0]])
                                        save_maps2trees(task_name, original_path+'>>>>'+this_trans_filter_more[0], [this_source_trees1[this_source_filter_more_id[0]], [this_trans_trees1[this_trans_filter_more_id[0]]]])
                            else:
                                continue
                        else:
                            this_source_filter_more = [item[0] for item in source_more_stmt_filt if not item[0].startswith('return')]
                            this_source_filter_more_id = [item[1] for item in source_more_stmt_filt if not item[0].startswith('return')]
                            if 'comment' not in original_path and len(this_source_filter_more) != 1:
                                continue
                            if 'comment' not in original_path:
                                this_trans_filter_more = [item[0] for item in trans_more_stmt_filt if not (item[0].startswith('return') or item[0].startswith('comment'))]
                                this_trans_filter_more_id = [item[1] for item in trans_more_stmt_filt if not (item[0].startswith('return') or item[0].startswith('comment'))]
                                this_trans_filter_less = [item for item in trans_less_stmt if not (item.startswith('return') or item.startswith('comment'))]
                            else:
                                this_trans_filter_more = [item[0] for item in trans_more_stmt_filt if not item[0].startswith('return')]
                                this_trans_filter_more_id = [item[1] for item in trans_more_stmt_filt if not item[0].startswith('return')]
                                this_trans_filter_less = [item for item in trans_less_stmt if not item.startswith('return')]
                            if not this_trans_filter_more_id:
                                continue
                            if this_trans_filter_less:
                                continue
                            if [original_path, this_trans_filter_more] in invalid_stmt_maps:
                                continue
                            if this_trans_filter_more:
                                if len(this_trans_filter_more) == 1:
                                    if not validate_map([original_path, this_trans_filter_more], source_lang, target_lang, invalid_stmt_maps):
                                        continue
                                if not check_ERROR_map([original_path, this_trans_filter_more]):
                                    continue
                                if 'comment' not in original_path:
                                    if_verified_new_mapping = verify_build_mapping(this_source_trees1[this_source_filter_more_id[0]],
                                                                               [this_trans_trees1[item] for item in this_trans_filter_more_id],
                                                                               source_variable_names1, trans_variable_names1, source_lang, target_lang)
                                    if not if_verified_new_mapping:
                                        continue
                                if original_path not in maps:
                                    maps[original_path] = [this_trans_filter_more]
                                    save_maps2trees(task_name, original_path+'>>>>'+'####'.join(this_trans_filter_more), [this_source_trees1[this_source_filter_more_id[0]], [this_trans_trees1[this_filter_more_item] for this_filter_more_item in this_trans_filter_more_id]])
                                    count += 1
                                    print(count)
                                    f = open(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{count}.cpp', 'w')
                                    print(ID, file=f)
                                    print(file1_name, file2_name, file=f)
                                    print('------------------------------------------', file=f)
                                    print(original_path+'\t'+'####'.join(this_trans_filter_more), file=f)
                                    print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                    this_source_code_str = mytree2text(this_source_trees1[this_source_filter_more_id[0]], '')
                                    print(this_source_code_str, file=f)
                                    print('==========================================', file=f)
                                    for this_filter_more_item in this_trans_filter_more_id:
                                        this_trans_code_str = mytree2text(this_trans_trees1[this_filter_more_item], '')
                                        print(this_trans_code_str, file=f)
                                    f.close()
                                else:
                                    if this_trans_filter_more not in maps[original_path]:
                                        maps[original_path].append(this_trans_filter_more)
                                        save_maps2trees(task_name, original_path+'>>>>'+'####'.join(this_trans_filter_more), [this_source_trees1[this_source_filter_more_id[0]], [this_trans_trees1[this_filter_more_item] for this_filter_more_item in this_trans_filter_more_id]])
                                        count += 1
                                        f = open(f'{task_name}/example-{dataset}-{model_name}-{source_lang}-{target_lang}/{count}.cpp', 'w')
                                        print(ID, file=f)
                                        print(file1_name, file2_name, file=f)
                                        print('------------------------------------------', file=f)
                                        print(original_path+'\t'+'####'.join(this_trans_filter_more), file=f)
                                        print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                        this_source_code_str = mytree2text(this_source_trees1[this_source_filter_more_id[0]], '')
                                        print(this_source_code_str, file=f)
                                        print('==========================================', file=f)
                                        for this_filter_more_item in this_trans_filter_more_id:
                                            this_trans_code_str = mytree2text(this_trans_trees1[this_filter_more_item], '')
                                            print(this_trans_code_str, file=f)
                                        f.close()
                        del delete_paths

    f_out = open(f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-0.txt', 'w')
    source_path2tree = {}
    trans_path2tree = {}
    maps_count = 0
    for k, v in maps.items():
        for val in v:
            if k not in source_path2tree:
                source_path2tree[k] = ori_path2tree[k]
            for this_val in val:
                if this_val not in trans_path2tree:
                    trans_path2tree[this_val] = path2tree[this_val]
            print(f'{k}\t{"####".join(val)}', file=f_out)
            maps_count += 1
    del maps
    del source_path2tree
    del trans_path2tree
    return maps_count


def contains(small, big):
    if small and big:
        matched_pos = []
        for i in range(1 + len(big) - len(small)):
            if small == big[i:i+len(small)]:
                matched_pos.append([id for id in range(i, i + len(small))])
        return matched_pos
    else:
        return []


def logout(task_name, s_stmt_id, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, source_tree, trans_tree, loop_time, file_ID):
    f = open(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{new_maps_count}.txt', 'w')
    print(file_ID, file=f)
    print('------------------------------------------', file=f)
    print(this_new_map[0]+'\t'+'####'.join(this_new_map[1]), file=f)
    print('++++++++++++++++++++++++++++++++++++++++++', file=f)
    this_source_code_str = mytree2text(source_tree, '')
    print(this_source_code_str, file=f)
    print('==========================================', file=f)
    this_trans_code_str = mytree2text(trans_tree, '')
    print(this_trans_code_str, file=f)
    f.close()


def extend_mapping1(model_names_for_mining, source_lang, target_lang, task_name, datasets, loop_limit, number1, invalid_stmt):
    f_invalid_stmt = open(invalid_stmt)
    invalid_stmt_lines = [line.strip() for line in f_invalid_stmt.readlines()]
    f_invalid_stmt.close()
    invalid_stmt_maps = []
    for line in invalid_stmt_lines:
        this_map = line.split('\t')
        if '####' not in this_map[1]:
            invalid_stmt_maps.append([this_map[0], [this_map[1]]])
        else:
            invalid_stmt_maps.append([this_map[0], this_map[1].split('####')])

    max_loop = -1
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1]) for file in os.listdir(f'{task_name}/') if file.startswith(
                                      f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-') and
                                  file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)

    fail_IDs_Geeks = []

    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    maps_count = 0

    for loop_time in range(max_loop, loop_limit):
        new_maps_count = 0
        maps = {}
        f_map = open(f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time}.txt')
        map_lines = f_map.readlines()
        f_map.close()
        for map_line in map_lines:
            if not map_line.strip():
                continue
            info = map_line.strip().split('\t')
            if len(info) == 1:
                continue
            source_path = info[0]
            mapped_paths = info[1]
            if '####' in mapped_paths:
                mapped_paths = mapped_paths.split('####')
            else:
                mapped_paths = [mapped_paths]
            if source_path not in maps:
                maps[source_path] = [mapped_paths]
            else:
                maps[source_path].append(mapped_paths)

        update_maps = copy.deepcopy(maps)

        os.makedirs(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}', exist_ok=True)
        exist_files = os.listdir(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}')
        for exist_file in exist_files:
            if os.path.isdir(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}'):
                shutil.rmtree(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}')
            else:
                os.remove(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}')

        for dataset in datasets:
            this_model_names_for_mining = model_names_for_mining[:]
            source_dataset_dir = ''
            fail_IDs = []
            if dataset == 'GeeksforGeeks':
                source_dataset_dir = f'GeeksforGeeks_sourcefiles'
                fail_IDs = copy.deepcopy(fail_IDs_Geeks)
            elif dataset == 'CodeNet':
                source_dataset_dir = f'CodeNet_sourcefiles'
                fail_IDs = []

            for model_name in this_model_names_for_mining:
                trans_dataset_dir = f'{dataset}/OUTPUT_{model_name}'
                source_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted'
                trans_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans-pass'
                IDs = os.listdir(source_delete_dir)
                IDs.sort()
                IDs = IDs[:number1]
                for file_ID in tqdm(IDs):
                    if file_ID in fail_IDs:
                        continue
                    _, source_lines = read_code(f'{source_dataset_dir}/{source_lang}-{target_lang}/{file_ID}.{source_ext}', source_lang)
                    _, trans_lines = read_code(f'{trans_dataset_dir}/{source_lang}-{target_lang}/{file_ID}.{target_ext}', target_lang)
                    if dataset == 'CodeNet':
                        if source_lang == 'Java':
                            source_lines = source_lines[5:-1]
                        elif source_lang == 'Python':
                            source_lines = source_lines[source_lines.index('def main():\n'):-1]
                        elif source_lang == 'C++':
                            source_lines = source_lines[8:]
                        if target_lang == 'Java':
                            trans_lines = trans_lines[5:-1]
                        elif target_lang == 'Python':
                            trans_lines = trans_lines[trans_lines.index('def main():\n'):-1]
                        elif target_lang == 'C++':
                            trans_lines = trans_lines[8:]
                    elif dataset == 'GeeksforGeeks':
                        source_lines = preprocess_funclines(source_lines, source_lang)
                        trans_lines = preprocess_funclines(trans_lines, target_lang)

                    source_tree, source_variable_names = code_parse_for_map(source_lang, ''.join(source_lines))
                    source_stmt_list = []
                    this_source_trees = []
                    source_stmt_list_pos = []
                    this_source_path2tree = {}
                    source_func_stmt = []
                    if source_lang == 'Java':
                        this_source_lines = copy.deepcopy(source_lines)
                        this_source_lines.insert(0, 'public class ClassName{\n')
                        this_source_lines.append('}\n')
                        ori_source_stmt_info_lists = traverse_tree(source_tree, source_lang, this_source_lines, source_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        ori_source_stmt_info_lists = reduce_pos_of_java_tree(ori_source_stmt_info_lists)
                        source_func_stmt = ori_source_stmt_info_lists[0]
                        ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                        source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)
                        del this_source_lines
                    elif source_lang == 'Python':
                        ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines, source_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        source_func_stmt = ori_source_stmt_info_lists[0]
                        ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                        source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)
                    elif source_lang == 'C++':
                        ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines, source_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        source_func_stmt = ori_source_stmt_info_lists[0]
                        ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                        source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(ori_source_stmt_info_lists)

                    trans_tree, trans_variable_names = code_parse_for_map(target_lang, ''.join(trans_lines))
                    trans_stmt_list = []
                    this_trans_trees = []
                    trans_stmt_list_pos = []
                    this_trans_path2tree = {}
                    trans_func_stmt = []
                    if target_lang == 'Java':
                        this_trans_lines = copy.deepcopy(trans_lines)
                        this_trans_lines.insert(0, 'public class ClassName{\n')
                        this_trans_lines.append('}\n')
                        ori_trans_stmt_info_lists = traverse_tree(trans_tree, target_lang, this_trans_lines, trans_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        ori_trans_stmt_info_lists = reduce_pos_of_java_tree(ori_trans_stmt_info_lists)
                        trans_func_stmt = ori_trans_stmt_info_lists[0]
                        ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                        trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)
                        del this_trans_lines
                    elif target_lang == 'Python':
                        ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines, trans_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        trans_func_stmt = ori_trans_stmt_info_lists[0]
                        ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                        trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)
                    if target_lang == 'C++':
                        ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines, trans_variable_names, only_block=False, exclude_last_child=False, only_path=True, fun_block=0)
                        trans_func_stmt = ori_trans_stmt_info_lists[0]
                        ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                        trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(ori_trans_stmt_info_lists)

                    trans2source_stmtMap= {}
                    mapped_s_stmt_id_list = []
                    for s_stmt_id, s_stmt in enumerate(source_stmt_list):
                        if s_stmt in maps:
                            s_map_choice_lists = maps[s_stmt]
                            for choice_list in s_map_choice_lists:
                                match_result = contains(choice_list, trans_stmt_list)
                                for this_trans_pos_list in match_result:
                                    for this_trans_id in this_trans_pos_list:
                                        mapped_s_stmt_id_list.append(s_stmt_id)
                                        if this_trans_id not in trans2source_stmtMap:
                                            trans2source_stmtMap[this_trans_id] = [s_stmt_id]
                                        else:
                                            trans2source_stmtMap[this_trans_id].append(s_stmt_id)
                    not_mapped_s_stmt_id_list = [s_stmt_id for s_stmt_id in range(len(source_stmt_list)) if s_stmt_id not in mapped_s_stmt_id_list]

                    source2trans_stmtMap = {}
                    for t_k, s_v in trans2source_stmtMap.items():
                        for this_s in s_v:
                            if this_s not in source2trans_stmtMap:
                                source2trans_stmtMap[this_s] = [t_k]
                            else:
                                source2trans_stmtMap[this_s].append(t_k)

                    source_predecessors, source_successors, source_stmt_use_consts, source_stmt_def_variables, source_stmt_use_variables, source_line_def_variables = parse_vari_dep(
                        source_stmt_list, source_lines, source_stmt_list_pos, source_lang, this_source_trees)
                    trans_predecessors, trans_successors, trans_stmt_use_consts, trans_stmt_def_variables, trans_stmt_use_variables, trans_line_def_variables = parse_vari_dep(
                        trans_stmt_list, trans_lines, trans_stmt_list_pos, target_lang, this_trans_trees)

                    if dataset in ['GeeksforGeeks']:
                        this_new_map = [source_func_stmt[0], [trans_func_stmt[0]]]
                        if not check_ERROR_map(this_new_map):
                            continue
                        if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                            continue
                        if this_new_map[0] not in update_maps:
                            new_maps_count += 1
                            f = open(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}/{new_maps_count}.txt', 'w')
                            print(file_ID, file=f)
                            print('------------------------------------------', file=f)
                            print(this_new_map[0]+'\t'+'####'.join(this_new_map[1]), file=f)
                            print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                            this_source_code_str = mytree2text(source_func_stmt[1], '')
                            print(this_source_code_str, file=f)
                            print('==========================================', file=f)
                            this_trans_code_str = mytree2text(trans_func_stmt[1], '')
                            print(this_trans_code_str, file=f)
                            f.close()
                            update_maps[this_new_map[0]] = [this_new_map[1]]
                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [source_func_stmt[1], [trans_func_stmt[1]]])
                        elif this_new_map[1] not in update_maps[this_new_map[0]]:
                            new_maps_count += 1
                            f = open(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}/{new_maps_count}.txt', 'w')
                            print(file_ID, file=f)
                            print('------------------------------------------', file=f)
                            print(this_new_map[0]+'\t'+'####'.join(this_new_map[1]), file=f)
                            print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                            this_source_code_str = mytree2text(source_func_stmt[1], '')
                            print(this_source_code_str, file=f)
                            print('==========================================', file=f)
                            this_trans_code_str = mytree2text(trans_func_stmt[1], '')
                            print(this_trans_code_str, file=f)
                            f.close()
                            update_maps[this_new_map[0]].append(this_new_map[1])
                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [source_func_stmt[1], [trans_func_stmt[1]]])


                    if len(source_stmt_list) == 1 and len(trans_stmt_list) == 1:
                        this_new_map = [source_stmt_list[0], [trans_stmt_list[0]]]
                        if not check_ERROR_map(this_new_map):
                            continue
                        if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                            continue
                        if this_new_map[0] not in update_maps:
                            new_maps_count += 1
                            logout(task_name, 0, 0, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                            update_maps[this_new_map[0]] = [this_new_map[1]]
                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                        elif this_new_map[1] not in update_maps[this_new_map[0]]:
                            new_maps_count += 1
                            logout(task_name, 0, 0, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                            update_maps[this_new_map[0]].append(this_new_map[1])
                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])

                    for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
                        if t_stmt_id in trans2source_stmtMap:
                            continue
                        if t_stmt_id == 0 and 1 in trans2source_stmtMap and 0 in not_mapped_s_stmt_id_list and 1 not in not_mapped_s_stmt_id_list:

                            if_verified_new_mapping = verify_build_mapping(this_source_trees[0], [this_trans_trees[0]],
                                                                           source_variable_names, trans_variable_names,
                                                                           source_lang, target_lang)
                            if not if_verified_new_mapping:
                                continue
                            this_new_map = [source_stmt_list[0], [trans_stmt_list[0]]]
                            if not check_ERROR_map(this_new_map):
                                continue
                            if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                continue
                            if this_new_map[0] not in update_maps:
                                new_maps_count += 1
                                logout(task_name, 0, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                                update_maps[this_new_map[0]] = [this_new_map[1]]
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                            elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                new_maps_count += 1
                                logout(task_name, 0, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                                update_maps[this_new_map[0]].append(this_new_map[1])
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                        elif t_stmt_id:
                            if t_stmt_id == len(trans_stmt_list)-1 and t_stmt_id-1 in trans2source_stmtMap:
                                pre_mapped_s_id = trans2source_stmtMap[t_stmt_id-1]
                                pre_mapped_s_id.sort()
                                possible_mapped_s_id_list = [this_stmt_id for this_stmt_id in range(len(source_stmt_list)) if this_stmt_id > pre_mapped_s_id[-1]]
                                if len(possible_mapped_s_id_list) == 1:
                                    if_verified_new_mapping = verify_build_mapping(this_source_trees[possible_mapped_s_id_list[0]],
                                                                                   [this_trans_trees[t_stmt_id]],
                                                                                   source_variable_names,
                                                                                   trans_variable_names,
                                                                                   source_lang, target_lang)
                                    if not if_verified_new_mapping:
                                        continue
                                    this_new_map = [source_stmt_list[possible_mapped_s_id_list[0]], [trans_stmt_list[t_stmt_id]]]
                                    if not check_ERROR_map(this_new_map):
                                        continue
                                    if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                            elif t_stmt_id-1 in trans2source_stmtMap and t_stmt_id+1 in trans2source_stmtMap:
                                possible_mapped_s_id_list = []
                                pre_mapped_s_id = trans2source_stmtMap[t_stmt_id-1]
                                fol_mapped_s_id = trans2source_stmtMap[t_stmt_id+1]
                                pre_mapped_s_id.sort()
                                fol_mapped_s_id.sort()
                                last_pre_mapped_s_id = pre_mapped_s_id[-1]
                                first_fol_mapped_s_id = fol_mapped_s_id[0]
                                if last_pre_mapped_s_id + 1 == first_fol_mapped_s_id:
                                    continue
                                for pre_id in pre_mapped_s_id:
                                    for fol_id in fol_mapped_s_id:
                                        if fol_id == pre_id + 2:
                                            possible_mapped_s_id_list.append(pre_id+1)
                                if len(possible_mapped_s_id_list) == 1:
                                    if_verified_new_mapping = verify_build_mapping(
                                                                        this_source_trees[possible_mapped_s_id_list[0]],
                                                                        [this_trans_trees[t_stmt_id]],
                                                                        source_variable_names,
                                                                        trans_variable_names,
                                                                        source_lang, target_lang)
                                    if not if_verified_new_mapping:
                                        continue
                                    this_new_map = [source_stmt_list[possible_mapped_s_id_list[0]], [trans_stmt_list[t_stmt_id]]]
                                    if not check_ERROR_map(this_new_map):
                                        continue
                                    if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                    for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
                        if t_stmt_id in trans2source_stmtMap:
                            continue
                        if t_stmt_id-1 not in trans2source_stmtMap and t_stmt_id+1 in trans2source_stmtMap:
                            next_mapped_s_id = trans2source_stmtMap[t_stmt_id+1]
                            next_mapped_s_id.sort()
                            possible_mapped_s_id = next_mapped_s_id[0] - 1
                            t_def_vars = set(trans_stmt_def_variables[t_stmt_id]) if t_stmt_id in trans_stmt_def_variables else set([])
                            t_use_vars = set(trans_stmt_use_variables[t_stmt_id]) if t_stmt_id in trans_stmt_use_variables else set([])
                            s_def_vars = set(source_stmt_def_variables[possible_mapped_s_id]) if possible_mapped_s_id in source_stmt_def_variables else set([])
                            s_use_vars = set(source_stmt_use_variables[possible_mapped_s_id]) if possible_mapped_s_id in source_stmt_use_variables else set([])
                            if t_def_vars and s_def_vars and t_def_vars == s_def_vars and t_use_vars == s_use_vars:
                                this_new_map = [source_stmt_list[possible_mapped_s_id], [trans_stmt_list[t_stmt_id]]]
                                if not check_ERROR_map(this_new_map):
                                    continue
                                if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    logout(task_name, possible_mapped_s_id, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id], [this_trans_trees[t_stmt_id]]])
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    logout(task_name, possible_mapped_s_id, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id], [this_trans_trees[t_stmt_id]]])
                        elif t_stmt_id-1 in trans2source_stmtMap and t_stmt_id+1 not in trans2source_stmtMap:
                            pre_mapped_s_id = trans2source_stmtMap[t_stmt_id-1]
                            pre_mapped_s_id.sort()
                            possible_mapped_s_id = pre_mapped_s_id[-1] - 1
                            t_def_vars = set(trans_stmt_def_variables[t_stmt_id]) if t_stmt_id in trans_stmt_def_variables else set([])
                            t_use_vars = set(trans_stmt_use_variables[t_stmt_id]) if t_stmt_id in trans_stmt_use_variables else set([])
                            s_def_vars = set(source_stmt_def_variables[possible_mapped_s_id]) if possible_mapped_s_id in source_stmt_def_variables else set([])
                            s_use_vars = set(source_stmt_use_variables[possible_mapped_s_id]) if possible_mapped_s_id in source_stmt_use_variables else set([])
                            if t_def_vars and s_def_vars and t_def_vars == s_def_vars and t_use_vars == s_use_vars:
                                this_new_map = [source_stmt_list[possible_mapped_s_id], [trans_stmt_list[t_stmt_id]]]
                                if not check_ERROR_map(this_new_map):
                                    continue
                                if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    logout(task_name, possible_mapped_s_id, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id], [this_trans_trees[t_stmt_id]]])
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    logout(task_name, possible_mapped_s_id, t_stmt_id, source_lang, target_lang, new_maps_count, this_new_map, source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[possible_mapped_s_id], this_trans_trees[t_stmt_id], loop_time, file_ID)
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id], [this_trans_trees[t_stmt_id]]])
                print(f'{dataset}\t{model_name}\t{new_maps_count}')
        print(f'Final: {new_maps_count}')
        if new_maps_count == 0:
            shutil.rmtree(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}')
            break
        f_out = open(f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time+1}.txt', 'w')
        max_loop = loop_time + 1
        maps_count = 0
        for k, v in update_maps.items():
            for val in v:
                this_v_list = '####'.join(val)
                print(f'{k}\t{this_v_list}', file=f_out)
                maps_count += 1
        f_out.close()
        del update_maps
        del maps
    return maps_count, max_loop


def extend_mapping2(model_names_for_mining, source_lang, target_lang, task_name, datasets, loop_limit, number1, invalid_stmt):
    f_invalid_stmt = open(invalid_stmt)
    invalid_stmt_lines = [line.strip() for line in f_invalid_stmt.readlines()]
    f_invalid_stmt.close()
    invalid_stmt_maps = []
    for line in invalid_stmt_lines:
        this_map = line.split('\t')
        if '####' not in this_map[1]:
            invalid_stmt_maps.append([this_map[0], [this_map[1]]])
        else:
            invalid_stmt_maps.append([this_map[0], this_map[1].split('####')])

    max_loop = -1
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1]) for file in os.listdir(f'{task_name}/') if
                                  file.startswith(f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-') and
                                  file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)

    fail_IDs_Geeks = []
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]
    maps_count = 0

    for loop_time in range(max_loop, loop_limit):
        new_maps_count = 0
        maps = {}
        f_map = open(f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time}.txt')
        map_lines = f_map.readlines()
        f_map.close()
        for map_line in map_lines:
            if not map_line.strip():
                continue
            info = map_line.strip().split('\t')
            if len(info) == 1:
                continue
            source_path = info[0]
            mapped_paths = info[1]
            if '####' in mapped_paths:
                mapped_paths = mapped_paths.split('####')
            else:
                mapped_paths = [mapped_paths]
            if source_path not in maps:
                maps[source_path] = [mapped_paths]
            else:
                maps[source_path].append(mapped_paths)

        update_maps = copy.deepcopy(maps)

        os.makedirs(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}', exist_ok=True)
        exist_files = os.listdir(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}')
        for exist_file in exist_files:
            if os.path.isdir(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}'):
                shutil.rmtree(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}')
            else:
                os.remove(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time+1}/{exist_file}')

        for dataset in datasets:
            this_model_names_for_mining = model_names_for_mining[:]
            source_dataset_dir = ''
            fail_IDs = []
            if dataset == 'GeeksforGeeks':
                source_dataset_dir = f'GeeksforGeeks_sourcefiles'
                fail_IDs = copy.deepcopy(fail_IDs_Geeks)
            elif dataset == 'CodeNet':
                source_dataset_dir = f'CodeNet_sourcefiles'
                fail_IDs = []

            for model_name in this_model_names_for_mining:
                trans_dataset_dir = f'{dataset}/OUTPUT_{model_name}'
                source_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted'
                trans_delete_dir = f'{dataset}/{model_name}-{source_lang}-{target_lang}-deleted-pass-trans-pass'
                IDs = os.listdir(source_delete_dir)
                IDs.sort()
                IDs = IDs[:number1]

                for ID in tqdm(IDs):
                    file_IDs = [item.split('.')[0] for item in os.listdir(f'{source_delete_dir}/{ID}')]
                    if ID in fail_IDs:
                        continue
                    for file_ID in file_IDs:
                        if not os.path.isfile(f'{source_delete_dir}/{ID}/{file_ID}.{source_ext}') or not os.path.isfile(f'{trans_delete_dir}/{ID}/{file_ID}.{target_ext}'):
                            continue
                        _, source_lines = read_code(f'{source_delete_dir}/{ID}/{file_ID}.{source_ext}', source_lang)
                        _, trans_lines = read_code(f'{trans_delete_dir}/{ID}/{file_ID}.{target_ext}', target_lang)
                        if dataset == 'CodeNet':
                            if source_lang == 'Java':
                                source_lines = source_lines[5:-1]
                            elif source_lang == 'Python':
                                source_lines = source_lines[source_lines.index('def main():\n'):-1]
                            elif source_lang == 'C++':
                                source_lines = source_lines[8:]
                            if target_lang == 'Java':
                                trans_lines = trans_lines[5:-1]
                            elif target_lang == 'Python':
                                trans_lines = trans_lines[trans_lines.index('def main():\n'):-1]
                            elif target_lang == 'C++':
                                trans_lines = trans_lines[8:]
                        elif dataset == 'GeeksforGeeks':
                            source_lines = preprocess_funclines(source_lines, source_lang)
                            trans_lines = preprocess_funclines(trans_lines, target_lang)

                        source_tree, source_variable_names = code_parse_for_map(source_lang, ''.join(source_lines))
                        source_stmt_list = []
                        this_source_trees = []
                        source_stmt_list_pos = []
                        this_source_path2tree = {}
                        source_func_stmt = []
                        if source_lang == 'Java':
                            this_source_lines = copy.deepcopy(source_lines)
                            this_source_lines.insert(0, 'public class ClassName{\n')
                            this_source_lines.append('}\n')
                            ori_source_stmt_info_lists = traverse_tree(source_tree, source_lang, this_source_lines,
                                                                       source_variable_names, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            ori_source_stmt_info_lists = reduce_pos_of_java_tree(ori_source_stmt_info_lists)
                            source_func_stmt = ori_source_stmt_info_lists[0]
                            ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_source_stmt_info_lists)
                            del this_source_lines
                        elif source_lang == 'Python':
                            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines,
                                                                       source_variable_names, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt = ori_source_stmt_info_lists[0]
                            ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_source_stmt_info_lists)
                        elif source_lang == 'C++':
                            ori_source_stmt_info_lists = traverse_tree(source_tree.root_node, source_lang, source_lines,
                                                                       source_variable_names, only_block=False,
                                                                       exclude_last_child=False, only_path=True,
                                                                       fun_block=0)
                            source_func_stmt = ori_source_stmt_info_lists[0]
                            ori_source_stmt_info_lists = ori_source_stmt_info_lists[1:]
                            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_source_stmt_info_lists)

                        trans_tree, trans_variable_names = code_parse_for_map(target_lang, ''.join(trans_lines))
                        trans_stmt_list = []
                        this_trans_trees = []
                        trans_stmt_list_pos = []
                        this_trans_path2tree = {}
                        trans_func_stmt = []
                        if target_lang == 'Java':
                            this_trans_lines = copy.deepcopy(trans_lines)
                            this_trans_lines.insert(0, 'public class ClassName{\n')
                            this_trans_lines.append('}\n')
                            ori_trans_stmt_info_lists = traverse_tree(trans_tree, target_lang, this_trans_lines,
                                                                      trans_variable_names, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            ori_trans_stmt_info_lists = reduce_pos_of_java_tree(ori_trans_stmt_info_lists)
                            trans_func_stmt = ori_trans_stmt_info_lists[0]
                            ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_trans_stmt_info_lists)
                            del this_trans_lines
                        elif target_lang == 'Python':
                            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                                      trans_variable_names, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt = ori_trans_stmt_info_lists[0]
                            ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_trans_stmt_info_lists)
                        if target_lang == 'C++':
                            ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                                      trans_variable_names, only_block=False,
                                                                      exclude_last_child=False, only_path=True,
                                                                      fun_block=0)
                            trans_func_stmt = ori_trans_stmt_info_lists[0]
                            ori_trans_stmt_info_lists = ori_trans_stmt_info_lists[1:]
                            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                                ori_trans_stmt_info_lists)

                        trans2source_stmtMap = {}
                        mapped_s_stmt_id_list = []
                        for s_stmt_id, s_stmt in enumerate(source_stmt_list):
                            if s_stmt in maps:
                                s_map_choice_lists = maps[s_stmt]
                                for choice_list in s_map_choice_lists:
                                    match_result = contains(choice_list, trans_stmt_list)
                                    for this_trans_pos_list in match_result:
                                        for this_trans_id in this_trans_pos_list:
                                            mapped_s_stmt_id_list.append(s_stmt_id)
                                            if this_trans_id not in trans2source_stmtMap:
                                                trans2source_stmtMap[this_trans_id] = [s_stmt_id]
                                            else:
                                                trans2source_stmtMap[this_trans_id].append(s_stmt_id)
                        not_mapped_s_stmt_id_list = [s_stmt_id for s_stmt_id in range(len(source_stmt_list)) if
                                                     s_stmt_id not in mapped_s_stmt_id_list]

                        source2trans_stmtMap = {}
                        for t_k, s_v in trans2source_stmtMap.items():
                            for this_s in s_v:
                                if this_s not in source2trans_stmtMap:
                                    source2trans_stmtMap[this_s] = [t_k]
                                else:
                                    source2trans_stmtMap[this_s].append(t_k)

                        if dataset in ['GeeksforGeeks']:
                            this_new_map = [source_func_stmt[0], [trans_func_stmt[0]]]
                            if not check_ERROR_map(this_new_map):
                                continue
                            if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                continue
                            if this_new_map[0] not in update_maps:
                                new_maps_count += 1
                                f = open(
                                    f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}/{new_maps_count}.txt',
                                    'w')
                                print(file_ID, file=f)
                                print('------------------------------------------', file=f)
                                print(this_new_map[0]+'\t'+'####'.join(this_new_map[1]), file=f)
                                print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                this_source_code_str = mytree2text(source_func_stmt[1], '')
                                print(this_source_code_str, file=f)
                                print('==========================================', file=f)
                                this_trans_code_str = mytree2text(trans_func_stmt[1], '')
                                print(this_trans_code_str, file=f)
                                f.close()
                                update_maps[this_new_map[0]] = [this_new_map[1]]
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [source_func_stmt[1], [trans_func_stmt[1]]])
                            elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                new_maps_count += 1
                                f = open(
                                    f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}/{new_maps_count}.txt',
                                    'w')
                                print(file_ID, file=f)
                                print('------------------------------------------', file=f)
                                print(this_new_map[0]+'\t'+'####'.join(this_new_map[1]), file=f)
                                print('++++++++++++++++++++++++++++++++++++++++++', file=f)
                                this_source_code_str = mytree2text(source_func_stmt[1], '')
                                print(this_source_code_str, file=f)
                                print('==========================================', file=f)
                                this_trans_code_str = mytree2text(trans_func_stmt[1], '')
                                print(this_trans_code_str, file=f)
                                f.close()
                                update_maps[this_new_map[0]].append(this_new_map[1])
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [source_func_stmt[1], [trans_func_stmt[1]]])

                        if len(source_stmt_list) == 1 and len(trans_stmt_list) == 1:
                            this_new_map = [source_stmt_list[0], [trans_stmt_list[0]]]
                            if not check_ERROR_map(this_new_map):
                                continue
                            if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                continue
                            if this_new_map[0] not in update_maps:
                                new_maps_count += 1
                                logout(task_name, 0, 0, source_lang, target_lang, new_maps_count, this_new_map,
                                       source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0],
                                       this_trans_trees[0], loop_time, file_ID)
                                update_maps[this_new_map[0]] = [this_new_map[1]]
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                            elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                new_maps_count += 1
                                logout(task_name, 0, 0, source_lang, target_lang, new_maps_count, this_new_map,
                                       source_stmt_list_pos, trans_stmt_list_pos, this_source_trees[0],
                                       this_trans_trees[0], loop_time, file_ID)
                                update_maps[this_new_map[0]].append(this_new_map[1])
                                save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])

                        for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
                            if t_stmt_id in trans2source_stmtMap:
                                continue
                            if t_stmt_id == 0 and 1 in trans2source_stmtMap and 0 in not_mapped_s_stmt_id_list and 1 not in not_mapped_s_stmt_id_list:

                                if_verified_new_mapping = verify_build_mapping(this_source_trees[0],
                                                                               [this_trans_trees[0]],
                                                                               source_variable_names,
                                                                               trans_variable_names,
                                                                               source_lang, target_lang)
                                if not if_verified_new_mapping:
                                    continue
                                this_new_map = [source_stmt_list[0], [trans_stmt_list[0]]]
                                if not check_ERROR_map(this_new_map):
                                    continue
                                if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    logout(task_name, 0, t_stmt_id, source_lang, target_lang, new_maps_count,
                                           this_new_map, source_stmt_list_pos, trans_stmt_list_pos,
                                           this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    logout(task_name, 0, t_stmt_id, source_lang, target_lang, new_maps_count,
                                           this_new_map, source_stmt_list_pos, trans_stmt_list_pos,
                                           this_source_trees[0], this_trans_trees[0], loop_time, file_ID)
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[0], [this_trans_trees[0]]])
                            elif t_stmt_id:
                                if t_stmt_id == len(trans_stmt_list) - 1 and t_stmt_id - 1 in trans2source_stmtMap:
                                    pre_mapped_s_id = trans2source_stmtMap[t_stmt_id - 1]
                                    pre_mapped_s_id.sort()
                                    possible_mapped_s_id_list = [this_stmt_id for this_stmt_id in
                                                                 range(len(source_stmt_list)) if
                                                                 this_stmt_id > pre_mapped_s_id[-1]]
                                    if len(possible_mapped_s_id_list) == 1:
                                        if_verified_new_mapping = verify_build_mapping(
                                            this_source_trees[possible_mapped_s_id_list[0]],
                                            [this_trans_trees[t_stmt_id]],
                                            source_variable_names,
                                            trans_variable_names,
                                            source_lang, target_lang)
                                        if not if_verified_new_mapping:
                                            continue
                                        this_new_map = [source_stmt_list[possible_mapped_s_id_list[0]],
                                                        [trans_stmt_list[t_stmt_id]]]
                                        if not check_ERROR_map(this_new_map):
                                            continue
                                        if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                            continue
                                        if this_new_map[0] not in update_maps:
                                            new_maps_count += 1
                                            logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang,
                                                   target_lang, new_maps_count, this_new_map, source_stmt_list_pos,
                                                   trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]],
                                                   this_trans_trees[t_stmt_id], loop_time, file_ID)
                                            update_maps[this_new_map[0]] = [this_new_map[1]]
                                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                                        elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                            new_maps_count += 1
                                            logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang,
                                                   target_lang, new_maps_count, this_new_map, source_stmt_list_pos,
                                                   trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]],
                                                   this_trans_trees[t_stmt_id], loop_time, file_ID)
                                            update_maps[this_new_map[0]].append(this_new_map[1])
                                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                                elif t_stmt_id - 1 in trans2source_stmtMap and t_stmt_id + 1 in trans2source_stmtMap:
                                    possible_mapped_s_id_list = []
                                    pre_mapped_s_id = trans2source_stmtMap[t_stmt_id - 1]
                                    fol_mapped_s_id = trans2source_stmtMap[t_stmt_id + 1]
                                    pre_mapped_s_id.sort()
                                    fol_mapped_s_id.sort()
                                    last_pre_mapped_s_id = pre_mapped_s_id[-1]
                                    first_fol_mapped_s_id = fol_mapped_s_id[0]
                                    if last_pre_mapped_s_id + 1 == first_fol_mapped_s_id:
                                        continue
                                    for pre_id in pre_mapped_s_id:
                                        for fol_id in fol_mapped_s_id:
                                            if fol_id == pre_id + 2:
                                                possible_mapped_s_id_list.append(pre_id + 1)
                                    if len(possible_mapped_s_id_list) == 1:
                                        if_verified_new_mapping = verify_build_mapping(
                                            this_source_trees[possible_mapped_s_id_list[0]],
                                            [this_trans_trees[t_stmt_id]],
                                            source_variable_names,
                                            trans_variable_names,
                                            source_lang, target_lang)
                                        if not if_verified_new_mapping:
                                            continue
                                        this_new_map = [source_stmt_list[possible_mapped_s_id_list[0]],
                                                        [trans_stmt_list[t_stmt_id]]]
                                        if not check_ERROR_map(this_new_map):
                                            continue
                                        if not validate_map(this_new_map, source_lang, target_lang, invalid_stmt_maps):
                                            continue
                                        if this_new_map[0] not in update_maps:
                                            new_maps_count += 1
                                            logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang,
                                                   target_lang, new_maps_count, this_new_map, source_stmt_list_pos,
                                                   trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]],
                                                   this_trans_trees[t_stmt_id], loop_time, file_ID)
                                            update_maps[this_new_map[0]] = [this_new_map[1]]
                                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                                        elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                            new_maps_count += 1
                                            logout(task_name, possible_mapped_s_id_list[0], t_stmt_id, source_lang,
                                                   target_lang, new_maps_count, this_new_map, source_stmt_list_pos,
                                                   trans_stmt_list_pos, this_source_trees[possible_mapped_s_id_list[0]],
                                                   this_trans_trees[t_stmt_id], loop_time, file_ID)
                                            update_maps[this_new_map[0]].append(this_new_map[1])
                                            save_maps2trees(task_name, this_new_map[0]+'>>>>'+'####'.join(this_new_map[1]), [this_source_trees[possible_mapped_s_id_list[0]], [this_trans_trees[t_stmt_id]]])
                print(f'{dataset}\t{model_name}\t{new_maps_count}')
        print(f'Final: {new_maps_count}')
        if new_maps_count == 0:
            shutil.rmtree(f'{task_name}/example-{source_lang}-{target_lang}-update-{loop_time + 1}')
            break
        f_out = open(f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time+1}.txt', 'w')
        max_loop = loop_time + 1
        maps_count = 0
        for k, v in update_maps.items():
            for val in v:
                this_v_list = '####'.join(val)
                print(f'{k}\t{this_v_list}', file=f_out)
                maps_count += 1
        f_out.close()
        del update_maps
        del maps
    return maps_count, max_loop


def logout_expression(task_name, source_lang, target_lang, new_maps_count, this_new_map, source_path, trans_path, text1,
                      text2, tree1, tree2, loop_time, source_path2, target_path2, source_tree2_text, target_tree2_text):
    if this_new_map == ['identifier-2', ['primitive_type-0']]:
        print('')
    f = open(f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}/{new_maps_count}.cpp',
             'w')
    print('------------------------------------------', file=f)
    print(this_new_map[0] + '\t' + this_new_map[1][0], file=f)
    print('++++++++++++++++++++++++++++++++++++++++++', file=f)
    this_source_code_str = mytree2text(tree1, '')
    print(this_source_code_str, file=f)
    print('==========================================', file=f)
    this_trans_code_str = mytree2text(tree2, '')
    print(this_trans_code_str, file=f)
    print('******************************************', file=f)
    print(source_path + '\t' + trans_path, file=f)
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$', file=f)
    print(text1, file=f)
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', file=f)
    print(text2, file=f)
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%', file=f)
    print(source_path2 + '\t' + target_path2, file=f)
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', file=f)
    print(source_tree2_text, file=f)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~', file=f)
    print(target_tree2_text, file=f)
    f.close()


def logout_subtree(task_name, source_lang, target_lang, new_maps_count, this_new_map, tree1, tree2, ori_source_path,
                   ori_trans_path, ori_tree_text1, ori_tree_text2, loop_time):
    if this_new_map[0] == 'integer-0' and this_new_map[1][0] in [
        'binary_expression-0||||identifier-0||||--0||||number_literal-0']:
        print('')
    f = open(f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}/{new_maps_count}.cpp',
             'w')
    print('------------------------------------------', file=f)
    print(this_new_map[0] + '\t' + this_new_map[1][0], file=f)
    print('++++++++++++++++++++++++++++++++++++++++++', file=f)
    this_source_code_str = mytree2text(tree1, '')
    print(this_source_code_str, file=f)
    print('==========================================', file=f)
    this_trans_code_str = mytree2text(tree2, '')
    print(this_trans_code_str, file=f)
    print('******************************************', file=f)
    print(ori_source_path + '\t' + ori_trans_path, file=f)
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$', file=f)
    print(ori_tree_text1, file=f)
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', file=f)
    print(ori_tree_text2, file=f)
    f.close()


def get_corres_trans_tree(maps2trees, source_path, trans_paths):
    trees = maps2trees[source_path + '>>>>' + '####'.join(trans_paths)]
    s_tree = trees[0]
    t_trees = trees[1]
    return s_tree, t_trees


def build_expression_mapping(model_names_for_mining, source_lang, target_lang, task_name, invalid_expr):
    f_invalid_expr = open(invalid_expr)
    invalid_expr_lines = [line.strip() for line in f_invalid_expr.readlines()]
    f_invalid_expr.close()
    invalid_expr_maps = []
    for line in invalid_expr_lines:
        this_map = line.split('\t')
        invalid_expr_maps.append([this_map[0], [this_map[1]]])

    max_loop = -1
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1]) for file in os.listdir(f'{task_name}/') if
                                  file.startswith(
                                      f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-') and
                                  file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)
    maps_count = 0
    for loop_time in trange(max_loop, 1000):
        new_maps_count = 0
        new_path2pair_count = 0
        new_anchor_count = 0

        print(f"{color.BOLD}{color.GREEN}{loop_time + 1}{color.END}")

        maps2trees = load_maps2trees(task_name)
        maps = load_map(
            f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time}.txt')
        source_path2pair = load_path2pair(task_name, source_lang, target_lang, loop_time)
        root_node_list = {}
        for k, v in maps.items():
            if '||||' in k:
                this_root_node = k.split('||||')[0]
            else:
                this_root_node = k
            if this_root_node not in root_node_list:
                root_node_list[this_root_node] = [k]
            else:
                root_node_list[this_root_node].append(k)

        source_path2tree = {}
        for k, v_lists in maps.items():
            for v_list in v_lists:
                this_map_trees = maps2trees[k + '>>>>' + '####'.join(v_list)]
                k_tree = this_map_trees[0]
                v_trees = this_map_trees[1]
                if k_tree not in source_path2tree:
                    source_path2tree[k] = k_tree
                if k in source_path2pair:
                    existing_pairs = source_path2pair[k]
                    if_contain_vlist = False
                    for existing_pair in existing_pairs:
                        if existing_pair.target_paths == v_list:
                            if_contain_vlist = True
                    if not if_contain_vlist:
                        source_path2pair[k].append(MyMap(source_lang, target_lang, k, v_list, k_tree, v_trees, []))
                else:
                    source_path2pair[k] = [MyMap(source_lang, target_lang, k, v_list, k_tree, v_trees, [])]

        update_maps = copy.deepcopy(maps)
        update_source_path2pair = copy.deepcopy(source_path2pair)

        os.makedirs(f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}', exist_ok=True)
        exist_files = os.listdir(f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}')
        for exist_file in exist_files:
            if os.path.isdir(
                    f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}/{exist_file}'):
                shutil.rmtree(
                    f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}/{exist_file}')
            else:
                os.remove(
                    f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}/{exist_file}')

        for source_path, pairs in source_path2pair.items():
            for pair_ID, pair in enumerate(pairs):
                source_subtrees = []
                traverse_tree2subtrees(pair.source_tree, [], source_subtrees)
                trans_subtrees = []
                for target_id, trans_tree in enumerate(pair.trans_trees):
                    this_trans_subtrees = []
                    traverse_tree2subtrees(trans_tree, [], this_trans_subtrees)
                    for this_trans_subtree in this_trans_subtrees:
                        trans_subtrees.append([this_trans_subtree, 0])
                filt_source_subtrees = []
                filt_trans_subtrees = []
                for source_subtree in source_subtrees:
                    if_contain = False
                    for anchor_pair in pair.anchors:
                        if source_subtree[0] == anchor_pair[0]:
                            if_contain = True
                    if not if_contain:
                        filt_source_subtrees.append(source_subtree)
                for trans_subtree in trans_subtrees:
                    if_contain = False
                    for anchor_pair in pair.anchors:
                        for this_trans_subtree_path in anchor_pair[1]:
                            if trans_subtree[0][0] == this_trans_subtree_path[0] and trans_subtree[1] == \
                                    this_trans_subtree_path[1]:
                                if_contain = True
                    if not if_contain:
                        filt_trans_subtrees.append(trans_subtree)

                source_path2subtree = {}
                for source_subtree in filt_source_subtrees:
                    this_source_path = '||||'.join(source_subtree[1].getDFS(source_lang))
                    if this_source_path not in source_path2subtree:
                        source_path2subtree[this_source_path] = [source_subtree]
                    else:
                        source_path2subtree[this_source_path].append(source_subtree)

                trans_path2subtree = {}
                for trans_subtree in filt_trans_subtrees:
                    this_trans_path = '||||'.join(trans_subtree[0][1].getDFS(target_lang))
                    if this_trans_path not in trans_path2subtree:
                        trans_path2subtree[this_trans_path] = [trans_subtree]
                    else:
                        trans_path2subtree[this_trans_path].append(trans_subtree)

                s_tokens = [this_subtree[1].text for this_subtree in source_subtrees if this_subtree[1].children == []]
                t_tokens = [this_subtree[0][1].text for this_subtree in trans_subtrees if
                            this_subtree[0][1].children == []]
                s_single_tokens = [token for token in s_tokens if
                                   s_tokens.count(token) == 1 and (token in string.punctuation or token.isnumeric())]
                t_single_tokens = [token for token in t_tokens if
                                   t_tokens.count(token) == 1 and (token in string.punctuation or token.isnumeric())]

                # add anchors of types
                type2source_subtrees = {}
                for s_path_tree in filt_source_subtrees:
                    if len(s_path_tree[1].children) == 1 and '_type' in s_path_tree[1].type:
                        this_type = s_path_tree[1].children[0].text
                        if this_type not in type2source_subtrees:
                            type2source_subtrees[this_type] = [s_path_tree]
                        else:
                            type2source_subtrees[this_type].append(s_path_tree)
                type2trans_subtrees = {}
                for t_path_tree in filt_trans_subtrees:
                    if len(t_path_tree[0][1].children) == 0 and '_type' in t_path_tree[0][1].type:
                        this_type = t_path_tree[0][1].text
                        if this_type not in type2trans_subtrees:
                            type2trans_subtrees[this_type] = [t_path_tree]
                        else:
                            type2trans_subtrees[this_type].append(t_path_tree)

                type_source_trans_subtrees = []
                if len(type2source_subtrees) == 1 and len(type2trans_subtrees) == 1:
                    this_source_subtrees = []
                    for this_k, this_v in type2source_subtrees.items():
                        this_source_subtrees.extend(this_v)
                    this_trans_subtrees = []
                    for this_k, this_v in type2trans_subtrees.items():
                        this_trans_subtrees.extend(this_v)
                    for this_source_subtree in this_source_subtrees:
                        for this_trans_subtree in this_trans_subtrees:
                            type_source_trans_subtrees.append([this_source_subtree, this_trans_subtree])
                else:
                    same_source_types = []
                    diff_source_types = []
                    for this_k, this_v in type2source_subtrees.items():
                        if this_k not in type2trans_subtrees:
                            diff_source_types.append(this_k)
                        else:
                            same_source_types.append(this_k)
                    same_trans_types = []
                    diff_trans_types = []
                    for this_k, this_v in type2trans_subtrees.items():
                        if this_k not in type2source_subtrees:
                            diff_trans_types.append(this_k)
                        else:
                            same_trans_types.append(this_k)
                    if len(diff_source_types) == 1 and len(diff_trans_types) == 1:
                        for same_type in same_source_types:
                            for this_source_subtree in type2source_subtrees[same_type]:
                                for this_trans_subtree in type2trans_subtrees[same_type]:
                                    type_source_trans_subtrees.append([this_source_subtree, this_trans_subtree])
                        for diff_type1, diff_type2 in zip(diff_source_types, diff_trans_types):
                            for this_source_subtree in type2source_subtrees[diff_type1]:
                                for this_trans_subtree in type2trans_subtrees[diff_type2]:
                                    type_source_trans_subtrees.append([this_source_subtree, this_trans_subtree])

                if type_source_trans_subtrees and len(
                        pair.trans_trees) == 1 and source_lang == 'Java' and target_lang == 'C++':
                    for type_source_trans_subtree in type_source_trans_subtrees:
                        s_subtrees = [type_source_trans_subtree[0]]
                        t_subtree = type_source_trans_subtree[1][:]
                        if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                            [s_subtrees[0][0], t_subtree[0][0], t_subtree[1]], if_force=True)
                        if if_add:
                            new_anchor_count += 1
                            if len(pair.target_paths) == 1:
                                source_child_path = '||||'.join(s_subtrees[0][1].getDFS(source_lang))
                                trans_child_path = '||||'.join(t_subtree[0][1].getDFS(target_lang))
                                source_child_tree = s_subtrees[0][1]
                                trans_child_tree = t_subtree[0][1]
                                this_new_map = [source_child_path, [trans_child_path]]
                                if not validate_buildmap(pair.source_path, pair.target_paths[0], this_new_map,
                                                         source_lang,
                                                         target_lang, invalid_expr_maps):
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_child_tree, [trans_child_tree]]
                                    logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                   this_new_map, source_child_tree, trans_child_tree,
                                                   pair.source_path, pair.target_paths[0],
                                                   pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_child_tree, [trans_child_tree]]
                                    logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                   this_new_map, source_child_tree, trans_child_tree,
                                                   pair.source_path, pair.target_paths[0],
                                                   pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                for token in s_single_tokens:
                    if token not in t_single_tokens:
                        continue
                    s_subtrees = []
                    for s_path_tree in filt_source_subtrees:
                        if s_path_tree[1].children == [] and s_path_tree[1].text == token:
                            s_subtrees.append(s_path_tree)
                    t_subtrees = []
                    for t_path_tree in filt_trans_subtrees:
                        if t_path_tree[0][1].children == [] and t_path_tree[0][1].text == token:
                            t_subtrees.append(t_path_tree)
                    if len(s_subtrees) == 1:
                        for t_subtree in t_subtrees:
                            if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                                [s_subtrees[0][0], t_subtree[0][0], t_subtree[1]])
                            if if_add:
                                new_anchor_count += 1
                                if len(pair.target_paths) == 1:
                                    source_child_path = s_subtrees[0][1].getDFS(source_lang)
                                    trans_child_path = t_subtree[0][1].getDFS(target_lang)
                                    source_child_tree = s_subtrees[0][1]
                                    trans_child_tree = t_subtree[0][1]
                                    this_new_map = [source_child_path[0], [trans_child_path[0]]]
                                    if not validate_buildmap(pair.source_path, pair.target_paths[0], this_new_map,
                                                             source_lang, target_lang, invalid_expr_maps):
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_child_tree, [trans_child_tree]]
                                        logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                       this_new_map, source_child_tree, trans_child_tree,
                                                       pair.source_path, pair.target_paths[0],
                                                       pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_child_tree, [trans_child_tree]]
                                        logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                       this_new_map, source_child_tree, trans_child_tree,
                                                       pair.source_path, pair.target_paths[0],
                                                       pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                for var in pair.source_tree.variable_names:
                    s_subtrees = []
                    for s_path_tree in filt_source_subtrees:
                        if s_path_tree[1].children == [] and s_path_tree[1].text == var:
                            s_subtrees.append(s_path_tree)
                    t_subtrees = []
                    for t_path_tree in filt_trans_subtrees:
                        if t_path_tree[0][1].children == [] and t_path_tree[0][1].text == var:
                            t_subtrees.append(t_path_tree)
                    if len(s_subtrees) == 1:
                        for t_subtree in t_subtrees:
                            if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                                [s_subtrees[0][0], t_subtree[0][0], t_subtree[1]])
                            if if_add:
                                new_anchor_count += 1
                                if len(pair.target_paths) == 1:
                                    source_child_path = s_subtrees[0][1].getDFS(source_lang)
                                    trans_child_path = t_subtree[0][1].getDFS(target_lang)
                                    source_child_tree = s_subtrees[0][1]
                                    trans_child_tree = t_subtree[0][1]
                                    this_new_map = [source_child_path[0], [trans_child_path[0]]]
                                    if not validate_buildmap(pair.source_path, pair.target_paths[0], this_new_map,
                                                             source_lang, target_lang, invalid_expr_maps):
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_child_tree, [trans_child_tree]]
                                        logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                       this_new_map, source_child_tree, trans_child_tree,
                                                       pair.source_path, pair.target_paths[0],
                                                       pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_child_tree, [trans_child_tree]]
                                        logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                                       this_new_map, source_child_tree, trans_child_tree,
                                                       pair.source_path, pair.target_paths[0],
                                                       pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                print(f"{color.BOLD}{color.PURPLE}{new_maps_count}{color.END}")
                print(f"{color.BOLD}{color.PURPLE}{new_path2pair_count}{color.END}")
                print(f"{color.BOLD}{color.PURPLE}{new_anchor_count}{color.END}")
        print(f"{color.BOLD}{color.PURPLE}{new_maps_count}{color.END}")
        print(f"{color.BOLD}{color.PURPLE}{new_path2pair_count}{color.END}")
        print(f"{color.BOLD}{color.PURPLE}{new_anchor_count}{color.END}")

        for root_node, tree_paths in root_node_list.items():
            for source_path1 in tree_paths:
                for source_path2 in tree_paths:
                    if not validate_path(source_path1, source_path2, source_lang):
                        continue
                    source_tree1 = source_path2tree[source_path1]
                    source_tree2 = source_path2tree[source_path2]
                    source_diff_paths = compare_MyTree(source_tree1, source_tree2, source_lang)
                    if source_diff_paths and source_diff_paths[0][0] == []:
                        continue
                    if len(source_diff_paths) != 1 and source_path1 in source_path2pair:
                        mapped_pairs = source_path2pair[source_path1]
                        for mapped_pair in mapped_pairs:
                            source_diff1 = [source_diff_path_type[0] for source_diff_path_type in source_diff_paths]
                            source_diff2 = [source_trans_diff_path_type[0] for source_trans_diff_path_type in
                                            mapped_pair.anchors]
                            more_source_diff1 = diff_contain(source_diff1, source_diff2)
                            more_source_diff_type = ''
                            for source_diff_path_type in source_diff_paths:
                                if source_diff_path_type[0] in more_source_diff1:
                                    more_source_diff_type = source_diff_path_type[1]
                            if len(more_source_diff1) == 1:
                                for target_path2_list in maps[source_path2]:
                                    target_path1_list = mapped_pair.target_paths
                                    target_path2_list = target_path2_list
                                    if len(target_path1_list) != len(target_path2_list):
                                        continue
                                    source_tree1 = mapped_pair.source_tree
                                    target_tree1_list = mapped_pair.trans_trees
                                    source_tree2, target_tree2_list = get_corres_trans_tree(maps2trees, source_path2,
                                                                                            target_path2_list)
                                    if_totally_diff = False
                                    this_record_target_diff = []
                                    target_id = -1
                                    for target_path1, target_path2, target_tree1, target_tree2 in zip(target_path1_list,
                                                                                                      target_path2_list,
                                                                                                      target_tree1_list,
                                                                                                      target_tree2_list):
                                        target_id += 1
                                        if not validate_path(target_path1, target_path2, target_lang):
                                            continue
                                        target_diff_paths = compare_MyTree(target_tree1, target_tree2, target_lang)
                                        if target_diff_paths and target_diff_paths[0][0] == []:
                                            if_totally_diff = True
                                            continue
                                        trans_diff1 = [trans_diff_path_type[0] for trans_diff_path_type in
                                                       target_diff_paths]
                                        trans_diff2 = []
                                        for source_trans_diff_path_type in mapped_pair.anchors:
                                            for this_trans_diff_path_type in source_trans_diff_path_type[1]:
                                                if this_trans_diff_path_type[1] == target_id:
                                                    trans_diff2.append(this_trans_diff_path_type[0])
                                        more_trans_diff1 = diff_contain(trans_diff1, trans_diff2)
                                        more_trans_diff_type = ''
                                        for trans_diff_path_type in target_diff_paths:
                                            if trans_diff_path_type[0] in more_trans_diff1:
                                                more_trans_diff_type = trans_diff_path_type[1]
                                        if len(more_trans_diff1) == 1 and more_source_diff_type == more_trans_diff_type:
                                            this_record_target_diff.append(
                                                [target_id, target_path1, target_path2, target_tree1, target_tree2,
                                                 trans_diff1, trans_diff2, more_trans_diff1])
                                    if if_totally_diff:
                                        continue
                                    if len(this_record_target_diff) != 1:
                                        continue
                                    target_id = this_record_target_diff[0][0]
                                    target_path1 = this_record_target_diff[0][1]
                                    target_path2 = this_record_target_diff[0][2]
                                    target_tree1 = this_record_target_diff[0][3]
                                    target_tree2 = this_record_target_diff[0][4]
                                    trans_diff1 = this_record_target_diff[0][5]
                                    trans_diff2 = this_record_target_diff[0][6]
                                    more_trans_diff1 = this_record_target_diff[0][7]

                                    source_diff_child1 = source_tree1.getChild(more_source_diff1[0])
                                    source_diff_child1_path = '||||'.join(
                                        source_diff_child1.getDFS(source_lang))
                                    target_diff_child1 = target_tree1.getChild(more_trans_diff1[0])
                                    target_diff_child1_path = '||||'.join(
                                        target_diff_child1.getDFS(target_lang))

                                    source_diff_child2 = source_tree2.getChild(more_source_diff1[0])
                                    source_diff_child2_path = '||||'.join(
                                        source_diff_child2.getDFS(source_lang))
                                    target_diff_child2 = target_tree2.getChild(more_trans_diff1[0])
                                    target_diff_child2_path = '||||'.join(
                                        target_diff_child2.getDFS(target_lang))

                                    if not check_unnamed_nodes_for_diff(target_tree1, target_tree2, source_tree1,
                                                                        source_tree2, target_diff_child1,
                                                                        target_diff_child2, source_diff_child1,
                                                                        source_diff_child2, source_diff1, trans_diff1):
                                        continue

                                    this_new_map = [source_diff_child1_path, [target_diff_child1_path]]
                                    if not validate_buildmap(source_path1, target_path1, this_new_map,
                                                             source_lang, target_lang, invalid_expr_maps):
                                        continue
                                    if not validate_expr_operator(source_path1, target_path1, this_new_map):
                                        continue
                                    update_anchors = get_anchors(update_source_path2pair, source_path1,
                                                                 target_path1_list)
                                    if_valid = validate_anchor(source_diff_child1, target_diff_child1,
                                                               more_source_diff1[0], more_trans_diff1[0],
                                                               update_anchors)
                                    if not if_valid:
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_diff_child1, [target_diff_child1]]
                                        logout_expression(task_name, source_lang, target_lang, new_maps_count,
                                                          this_new_map,
                                                          source_path1, target_path1, source_tree1.text,
                                                          target_tree1.text,
                                                          source_diff_child1, target_diff_child1, loop_time,
                                                          source_path2,
                                                          target_path2, source_tree2.text, target_tree2.text)
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_diff_child1, [target_diff_child1]]
                                        logout_expression(task_name, source_lang, target_lang, new_maps_count,
                                                          this_new_map,
                                                          source_path1, target_path1, source_tree1.text,
                                                          target_tree1.text,
                                                          source_diff_child1, target_diff_child1, loop_time,
                                                          source_path2,
                                                          target_path2, source_tree2.text, target_tree2.text)
                                    this_new_map = [source_diff_child2_path, [target_diff_child2_path]]
                                    if not validate_buildmap(source_path2, target_path2, this_new_map,
                                                             source_lang, target_lang, invalid_expr_maps):
                                        continue
                                    if not validate_expr_operator(source_path2, target_path2, this_new_map):
                                        continue
                                    if this_new_map[0] not in update_maps:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]] = [this_new_map[1]]
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_diff_child2, [target_diff_child2]]
                                        logout_expression(task_name, source_lang, target_lang, new_maps_count,
                                                          this_new_map,
                                                          source_path2, target_path2, source_tree2.text,
                                                          target_tree2.text,
                                                          source_diff_child2, target_diff_child2, loop_time,
                                                          source_path1,
                                                          target_path1, source_tree1.text, target_tree1.text)
                                    elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                        new_maps_count += 1
                                        update_maps[this_new_map[0]].append(this_new_map[1])
                                        maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                            source_diff_child2, [target_diff_child2]]
                                        logout_expression(task_name, source_lang, target_lang, new_maps_count,
                                                          this_new_map,
                                                          source_path2, target_path2, source_tree2.text,
                                                          target_tree2.text,
                                                          source_diff_child2, target_diff_child2, loop_time,
                                                          source_path1,
                                                          target_path1, source_tree1.text, target_tree1.text)
                                    if source_path1 in update_source_path2pair:
                                        mapped_pairs = update_source_path2pair[source_path1]
                                        if_contained = False
                                        for mapped_pair_id, mapped_pair in enumerate(mapped_pairs):
                                            if mapped_pair.target_paths == [target_path1]:
                                                if_contained = True
                                                if_add = update_source_path2pair[source_path1][
                                                    mapped_pair_id].addAnchor(
                                                    [more_source_diff1[0], more_trans_diff1[0], target_id])
                                                if if_add:
                                                    new_anchor_count += 1
                                        if not if_contained:
                                            new_path2pair_count += 1
                                            update_source_path2pair[source_path1].append(
                                                MyMap(source_lang, target_lang, source_path1, target_path1_list,
                                                      source_tree1, target_tree1_list,
                                                      [[more_source_diff1[0], [[more_trans_diff1[0], target_id]]]]))
                                    else:
                                        new_path2pair_count += 1
                                        update_source_path2pair[source_path1] = [
                                            MyMap(source_lang, target_lang, source_path1, target_path1_list,
                                                  source_tree1, target_tree1_list,
                                                  [[more_source_diff1[0], [[more_trans_diff1[0], target_id]]]])]
                                    if source_path2 in update_source_path2pair:
                                        mapped_pairs = update_source_path2pair[source_path2]
                                        if_contained = False
                                        for mapped_pair_id, mapped_pair in enumerate(mapped_pairs):
                                            if mapped_pair.target_paths == [target_path2]:
                                                if_contained = True
                                                if_add = update_source_path2pair[source_path2][
                                                    mapped_pair_id].addAnchor(
                                                    [more_source_diff1[0], more_trans_diff1[0], target_id])
                                                if if_add:
                                                    new_anchor_count += 1
                                        if not if_contained:
                                            new_path2pair_count += 1
                                            update_source_path2pair[source_path2].append(
                                                MyMap(source_lang, target_lang, source_path2, target_path2_list,
                                                      source_tree2, target_tree2_list,
                                                      [[more_source_diff1[0], [[more_trans_diff1[0], target_id]]]]))
                                    else:
                                        new_path2pair_count += 1
                                        update_source_path2pair[source_path2] = [
                                            MyMap(source_lang, target_lang, source_path2, target_path2_list,
                                                  source_tree2, target_tree2_list,
                                                  [[more_source_diff1[0], [[more_trans_diff1[0], target_id]]]])]

                    if len(source_diff_paths) == 1:
                        source_diff_path_type = source_diff_paths[0]
                        for target_path1_list in maps[source_path1]:
                            for target_path2_list in maps[source_path2]:
                                if len(target_path1_list) != len(target_path2_list):
                                    continue
                                if_totally_diff = False
                                this_record_target_diff = []
                                source_tree1, target_tree1_list = get_corres_trans_tree(maps2trees, source_path1,
                                                                                        target_path1_list)
                                source_tree2, target_tree2_list = get_corres_trans_tree(maps2trees, source_path2,
                                                                                        target_path2_list)
                                target_id = -1
                                for target_path1, target_path2, target_tree1, target_tree2 in zip(target_path1_list,
                                                                                                  target_path2_list,
                                                                                                  target_tree1_list,
                                                                                                  target_tree2_list):
                                    target_id += 1
                                    if not validate_path(target_path1, target_path2, target_lang):
                                        continue
                                    target_diff_paths = compare_MyTree(target_tree1, target_tree2, target_lang)
                                    if target_diff_paths and target_diff_paths[0][0] == []:
                                        if_totally_diff = True
                                        break
                                    for target_diff_path_type in target_diff_paths:
                                        if source_diff_path_type[1] != target_diff_path_type[1]:
                                            continue
                                        this_record_target_diff.append(
                                            [target_id, target_path1, target_path2, target_tree1, target_tree2,
                                             target_diff_path_type])
                                if if_totally_diff:
                                    continue
                                if len(this_record_target_diff) != 1:
                                    continue
                                target_id = this_record_target_diff[0][0]
                                target_path1 = this_record_target_diff[0][1]
                                target_path2 = this_record_target_diff[0][2]
                                target_tree1 = this_record_target_diff[0][3]
                                target_tree2 = this_record_target_diff[0][4]
                                target_diff_path_type = this_record_target_diff[0][5]

                                source_diff_child1 = source_tree1.getChild(source_diff_path_type[0])
                                source_diff_child1_path = '||||'.join(source_diff_child1.getDFS(source_lang))
                                target_diff_child1 = target_tree1.getChild(target_diff_path_type[0])
                                target_diff_child1_path = '||||'.join(target_diff_child1.getDFS(target_lang))

                                source_diff_child2 = source_tree2.getChild(source_diff_path_type[0])
                                source_diff_child2_path = '||||'.join(source_diff_child2.getDFS(source_lang))
                                target_diff_child2 = target_tree2.getChild(target_diff_path_type[0])
                                target_diff_child2_path = '||||'.join(target_diff_child2.getDFS(target_lang))

                                if not check_unnamed_nodes_for_diff(target_tree1, target_tree2, source_tree1,
                                                                    source_tree2, target_diff_child1,
                                                                    target_diff_child2, source_diff_child1,
                                                                    source_diff_child2, [source_diff_path_type],
                                                                    [target_diff_path_type]):
                                    continue

                                this_new_map = [source_diff_child1_path, [target_diff_child1_path]]
                                if not validate_buildmap(source_path1, target_path1, this_new_map, source_lang,
                                                         target_lang, invalid_expr_maps):
                                    continue
                                if not validate_expr_operator(source_path1, target_path1, this_new_map):
                                    continue
                                update_anchors = get_anchors(update_source_path2pair, source_path1, target_path1_list)
                                if_valid = validate_anchor(source_diff_child1, target_diff_child1,
                                                           source_diff_path_type[0], target_diff_path_type[0],
                                                           update_anchors)
                                if not if_valid:
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_diff_child1, [target_diff_child1]]
                                    logout_expression(task_name, source_lang, target_lang, new_maps_count, this_new_map,
                                                      source_path1, target_path1, source_tree1.text, target_tree1.text,
                                                      source_diff_child1, target_diff_child1, loop_time,
                                                      source_path2,
                                                      target_path2, source_tree2.text, target_tree2.text)
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_diff_child1, [target_diff_child1]]
                                    logout_expression(task_name, source_lang, target_lang, new_maps_count, this_new_map,
                                                      source_path1, target_path1, source_tree1.text, target_tree1.text,
                                                      source_diff_child1, target_diff_child1, loop_time,
                                                      source_path2,
                                                      target_path2, source_tree2.text, target_tree2.text)

                                this_new_map = [source_diff_child2_path, [target_diff_child2_path]]
                                if not validate_buildmap(source_path2, target_path2, this_new_map, source_lang,
                                                         target_lang, invalid_expr_maps):
                                    continue
                                if not validate_expr_operator(source_path2, target_path2, this_new_map):
                                    continue
                                if this_new_map[0] not in update_maps:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]] = [this_new_map[1]]
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_diff_child2, [target_diff_child2]]
                                    logout_expression(task_name, source_lang, target_lang, new_maps_count, this_new_map,
                                                      source_path2, target_path2, source_tree2.text, target_tree2.text,
                                                      source_diff_child2, target_diff_child2, loop_time,
                                                      source_path1,
                                                      target_path1, source_tree1.text, target_tree1.text)
                                elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                    new_maps_count += 1
                                    update_maps[this_new_map[0]].append(this_new_map[1])
                                    maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [
                                        source_diff_child2, [target_diff_child2]]
                                    logout_expression(task_name, source_lang, target_lang, new_maps_count, this_new_map,
                                                      source_path2, target_path2, source_tree2.text, target_tree2.text,
                                                      source_diff_child2, target_diff_child2, loop_time,
                                                      source_path1,
                                                      target_path1, source_tree1.text, target_tree1.text)
                                if source_path1 in update_source_path2pair:
                                    mapped_pairs = update_source_path2pair[source_path1]
                                    if_contained = False
                                    for mapped_pair_id, mapped_pair in enumerate(mapped_pairs):
                                        if mapped_pair.target_paths == target_path1_list:
                                            if_contained = True
                                            if_add = update_source_path2pair[source_path1][mapped_pair_id].addAnchor(
                                                [source_diff_path_type[0], target_diff_path_type[0], target_id])
                                            if if_add:
                                                new_anchor_count += 1
                                    if not if_contained:
                                        new_path2pair_count += 1
                                        update_source_path2pair[source_path1].append(
                                            MyMap(source_lang, target_lang, source_path1, target_path1_list,
                                                  source_tree1, target_tree1_list,
                                                  [[source_diff_path_type, [[target_diff_path_type[0], target_id]]]]))
                                else:
                                    new_path2pair_count += 1
                                    update_source_path2pair[source_path1] = [
                                        MyMap(source_lang, target_lang, source_path1, target_path1_list, source_tree1,
                                              target_tree1_list,
                                              [[source_diff_path_type, [[target_diff_path_type[0], target_id]]]])]

                                if source_path2 in update_source_path2pair:
                                    mapped_pairs = update_source_path2pair[source_path2]
                                    if_contained = False
                                    for mapped_pair_id, mapped_pair in enumerate(mapped_pairs):
                                        if mapped_pair.target_paths == target_path2_list:
                                            if_contained = True
                                            if_add = update_source_path2pair[source_path2][mapped_pair_id].addAnchor(
                                                [source_diff_path_type[0], target_diff_path_type[0], target_id])
                                            if if_add:
                                                new_anchor_count += 1
                                    if not if_contained:
                                        new_path2pair_count += 1
                                        update_source_path2pair[source_path2].append(
                                            MyMap(source_lang, target_lang, source_path2, target_path2_list,
                                                  source_tree2, target_tree2_list,
                                                  [[source_diff_path_type, [[target_diff_path_type[0], target_id]]]]))
                                else:
                                    new_path2pair_count += 1
                                    update_source_path2pair[source_path2] = [
                                        MyMap(source_lang, target_lang, source_path2, target_path2_list, source_tree2,
                                              target_tree2_list,
                                              [[source_diff_path_type, [[target_diff_path_type[0], target_id]]]])]
                print(f"{color.BOLD}{color.BLUE}{new_maps_count}{color.END}")
                print(f"{color.BOLD}{color.BLUE}{new_path2pair_count}{color.END}")
                print(f"{color.BOLD}{color.BLUE}{new_anchor_count}{color.END}")
        print(f"{color.BOLD}{color.BLUE}{new_maps_count}{color.END}")
        print(f"{color.BOLD}{color.BLUE}{new_path2pair_count}{color.END}")
        print(f"{color.BOLD}{color.BLUE}{new_anchor_count}{color.END}")

        for source_path, pairs in source_path2pair.items():
            for pair_ID, pair in enumerate(pairs):
                source_subtrees = []
                traverse_tree2subtrees(pair.source_tree, [], source_subtrees)
                trans_subtrees = []
                for target_id, trans_tree in enumerate(pair.trans_trees):
                    this_trans_subtrees = []
                    traverse_tree2subtrees(trans_tree, [], this_trans_subtrees)
                    for this_trans_subtree in this_trans_subtrees:
                        trans_subtrees.append([this_trans_subtree, 0])
                filt_source_subtrees = []
                filt_trans_subtrees = []
                for source_subtree in source_subtrees:
                    if_contain = False
                    for anchor_pair in pair.anchors:
                        if source_subtree[0] == anchor_pair[0]:
                            if_contain = True
                    if not if_contain:
                        filt_source_subtrees.append(source_subtree)
                for trans_subtree in trans_subtrees:
                    if_contain = False
                    for anchor_pair in pair.anchors:
                        for this_trans_subtree_path in anchor_pair[1]:
                            if trans_subtree[0][0] == this_trans_subtree_path[0] and trans_subtree[1] == \
                                    this_trans_subtree_path[1]:
                                if_contain = True
                    if not if_contain:
                        filt_trans_subtrees.append(trans_subtree)

                source_path2subtree = {}
                for source_subtree in filt_source_subtrees:
                    this_source_path = '||||'.join(source_subtree[1].getDFS(source_lang))
                    if this_source_path not in source_path2subtree:
                        source_path2subtree[this_source_path] = [source_subtree]
                    else:
                        source_path2subtree[this_source_path].append(source_subtree)

                trans_path2subtree = {}
                for trans_subtree in filt_trans_subtrees:
                    this_trans_path = '||||'.join(trans_subtree[0][1].getDFS(target_lang))
                    if this_trans_path not in trans_path2subtree:
                        trans_path2subtree[this_trans_path] = [trans_subtree]
                    else:
                        trans_path2subtree[this_trans_path].append(trans_subtree)

                for var in pair.source_tree.variable_names:
                    s_subtrees = []
                    for s_path_tree in filt_source_subtrees:
                        if s_path_tree[1].children == [] and s_path_tree[1].text == var:
                            s_subtrees.append(s_path_tree)
                    t_subtrees = []
                    for t_path_tree in filt_trans_subtrees:
                        if t_path_tree[0][1].children == [] and t_path_tree[0][1].text == var:
                            t_subtrees.append(t_path_tree)
                    if len(s_subtrees) == 1:
                        for t_subtree in t_subtrees:
                            if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                                [s_subtrees[0][0], t_subtree[0][0], t_subtree[1]])
                            if if_add:
                                new_anchor_count += 1

                for s_path, s_subtrees in source_path2subtree.items():
                    record_available_anchors = []
                    for t_path, t_subtrees in trans_path2subtree.items():
                        if s_path in maps and len(s_subtrees) == len(t_subtrees) and [t_path] in maps[s_path]:
                            this_record_available_anchors = []
                            for s_subtree, t_subtree in zip(s_subtrees, t_subtrees):
                                this_record_available_anchors.append([s_subtree[0], t_subtree[0][0], t_subtree[1]])
                            record_available_anchors.append(this_record_available_anchors)
                    if len(record_available_anchors) == 1:
                        for this_record_available_anchor in record_available_anchors[0]:
                            if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                                this_record_available_anchor)
                            if if_add:
                                new_anchor_count += 1

                source_node2subtree = {}
                for source_subtree in filt_source_subtrees:
                    if source_subtree[1].type not in source_node2subtree:
                        source_node2subtree[source_subtree[1].type] = [source_subtree]
                    else:
                        source_node2subtree[source_subtree[1].type].append(source_subtree)

                trans_node2subtree = {}
                for trans_subtree in filt_trans_subtrees:
                    if trans_subtree[0][1].type not in trans_node2subtree:
                        trans_node2subtree[trans_subtree[0][1].type] = [trans_subtree]
                    else:
                        trans_node2subtree[trans_subtree[0][1].type].append(trans_subtree)

                s_len2nodetype = {}
                for node_type, subtrees in source_node2subtree.items():
                    if len(subtrees) not in s_len2nodetype:
                        s_len2nodetype[len(subtrees)] = [node_type]
                    else:
                        s_len2nodetype[len(subtrees)].append(node_type)
                t_len2nodetype = {}
                for node_type, subtrees in trans_node2subtree.items():
                    if len(subtrees) not in t_len2nodetype:
                        t_len2nodetype[len(subtrees)] = [node_type]
                    else:
                        t_len2nodetype[len(subtrees)].append(node_type)

                s_keys_set = set([k for k in s_len2nodetype])
                t_keys_set = set([k for k in t_len2nodetype])
                if s_keys_set != t_keys_set:
                    continue
                for num, s_node_types in s_len2nodetype.items():
                    if num not in t_len2nodetype:
                        continue
                    t_node_types = t_len2nodetype[num]
                    if len(s_node_types) == 1 and len(t_node_types) == 1:
                        s_subtrees = source_node2subtree[s_node_types[0]]
                        t_subtrees = trans_node2subtree[t_node_types[0]]
                        for s_subtree, t_subtree in zip(s_subtrees, t_subtrees):
                            update_anchors = get_anchors(update_source_path2pair, pair.source_path, pair.target_paths)
                            if_valid = validate_anchor(s_subtree[1], t_subtree[0][1], s_subtree[0], t_subtree[0][0],
                                                       update_anchors)
                            if not if_valid:
                                continue
                            suitable_existing_anchors = []
                            for this_anchor in pair.anchors:
                                this_s_anchor_path = this_anchor[0]
                                this_t_anchors = this_anchor[1]
                                new_anchor_s_path = s_subtree[0]
                                new_anchor_t_path = t_subtree[0][0]
                                for this_t_anchor in this_t_anchors:
                                    if len(this_s_anchor_path) >= len(new_anchor_s_path) \
                                            and this_s_anchor_path[:len(new_anchor_s_path)] == new_anchor_s_path \
                                            and len(this_t_anchor[0]) >= len(new_anchor_t_path) \
                                            and this_t_anchor[0][:len(new_anchor_t_path)] == new_anchor_t_path \
                                            and t_subtree[1] == this_t_anchor[1] \
                                            and this_s_anchor_path != new_anchor_s_path and this_t_anchor[
                                        0] != new_anchor_t_path:
                                        suitable_existing_anchors.append([this_s_anchor_path[len(new_anchor_s_path):],
                                                                          this_t_anchor[0][len(new_anchor_t_path):],
                                                                          this_t_anchor[1]])

                            if_add = update_source_path2pair[source_path][pair_ID].addAnchor(
                                [s_subtree[0], t_subtree[0][0], t_subtree[1]])
                            if not if_add:
                                continue
                            new_anchor_count += 1
                            source_anchor_child_path = '||||'.join(s_subtree[1].getDFS(source_lang))
                            trans_anchor_child_path = '||||'.join(t_subtree[0][1].getDFS(target_lang))

                            if len(pair.target_paths) != 1:
                                continue
                            this_new_map = [source_anchor_child_path, [trans_anchor_child_path]]
                            if not validate_buildmap(pair.source_path, pair.target_paths[0], this_new_map, source_lang,
                                                     target_lang, invalid_expr_maps):
                                continue
                            if this_new_map[0] not in update_maps:
                                new_maps_count += 1
                                update_maps[this_new_map[0]] = [this_new_map[1]]
                                maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [s_subtree[1], [
                                    t_subtree[0][1]]]
                                logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                               this_new_map, s_subtree[1], t_subtree[0][1],
                                               pair.source_path, pair.target_paths[0],
                                               pair.source_tree.text, pair.trans_trees[0].text, loop_time)
                            elif this_new_map[1] not in update_maps[this_new_map[0]]:
                                new_maps_count += 1
                                update_maps[this_new_map[0]].append(this_new_map[1])
                                maps2trees[this_new_map[0] + '>>>>' + '####'.join(this_new_map[1])] = [s_subtree[1], [
                                    t_subtree[0][1]]]
                                logout_subtree(task_name, source_lang, target_lang, new_maps_count,
                                               this_new_map, s_subtree[1], t_subtree[0][1],
                                               pair.source_path, pair.target_paths[0],
                                               pair.source_tree.text, pair.trans_trees[0].text, loop_time)

                            if source_anchor_child_path not in update_source_path2pair:
                                new_path2pair_count += 1
                                update_source_path2pair[source_anchor_child_path] = [
                                    MyMap(source_lang, target_lang, source_anchor_child_path, [trans_anchor_child_path],
                                          s_subtree[1], [t_subtree[0][1]], [])]
                                for suitable_existing_anchor in suitable_existing_anchors:
                                    if_add = update_source_path2pair[source_anchor_child_path][0].addAnchor(
                                        suitable_existing_anchor)
                            else:
                                if_contain = False
                                for item_pair in update_source_path2pair[source_anchor_child_path]:
                                    if item_pair.target_paths == [trans_anchor_child_path]:
                                        if_contain = True
                                if not if_contain:
                                    new_path2pair_count += 1
                                    update_source_path2pair[source_anchor_child_path].append(
                                        MyMap(source_lang, target_lang, source_anchor_child_path,
                                              [trans_anchor_child_path], s_subtree[1], [t_subtree[0][1]], []))
                                    for suitable_existing_anchor in suitable_existing_anchors:
                                        if_add = update_source_path2pair[source_anchor_child_path][-1].addAnchor(
                                            suitable_existing_anchor)

                print(f"{color.BOLD}{color.YELLOW}{new_maps_count}{color.END}")
                print(f"{color.BOLD}{color.YELLOW}{new_path2pair_count}{color.END}")
                print(f"{color.BOLD}{color.YELLOW}{new_anchor_count}{color.END}")

        print(f"{color.BOLD}{color.YELLOW}{new_maps_count}{color.END}")
        print(f"{color.BOLD}{color.YELLOW}{new_path2pair_count}{color.END}")
        print(f"{color.BOLD}{color.YELLOW}{new_anchor_count}{color.END}")
        if new_maps_count == 0 and new_path2pair_count == 0 and new_anchor_count == 0:
            shutil.rmtree(f'{task_name}/example-{source_lang}-{target_lang}-expression-update-{loop_time + 1}')
            break
        f_out = open(
            f'{task_name}/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-{loop_time + 1}.txt', 'w')
        max_loop = loop_time + 1
        maps_count = 0
        for k, v in update_maps.items():
            for val in v:
                this_v_list = '####'.join(val)
                print(f'{k}\t{this_v_list}', file=f_out)
                maps_count += 1
        f_out.close()
        update_maps2trees(task_name, maps2trees)
        save_path2pair(task_name, update_source_path2pair, source_lang, target_lang, loop_time + 1)
    return maps_count, max_loop

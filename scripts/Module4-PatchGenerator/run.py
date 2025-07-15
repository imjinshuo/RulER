from utils import *
from tqdm import tqdm
import time
import argparse


def run(path_to_map, path_to_stmtmap, path_to_code, path_to_DATABASE, path_to_fixcode, target_model_name, source_lang, target_lang, model_name):
    save_fixcode_dir = f'{path_to_fixcode}/{target_model_name}-{source_lang}-{target_lang}'
    os.makedirs(save_fixcode_dir, exist_ok=True)

    geenrated_map = loadMap(f'{path_to_map}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')
    geenrated_stmtmap = loadMap(f'{path_to_stmtmap}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    model_names_for_mining = [model_name]
    datasets = ['CodeNet']
    task1_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-{"_".join(datasets)}-{source_lang}-{target_lang}'
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1]) for file in os.listdir(f'{task1_name}/') if file.startswith(
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

    IDs = [file.split('.')[0] for file in script_files if file.split('.')[0]]
    IDs.sort()
    sum = 0
    for ID in tqdm(IDs):
        sum += 1
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
        for pair in geenrated_map[ID]:
            line_M[f'{pair[0]}-{pair[1]}'] = True

        M = {}
        for s_id in range(len(source_stmt_list)):
            for t_id in range(len(trans_stmt_list)):
                M[f'{s_id}-{t_id}'] = False
        for pair in geenrated_stmtmap[ID]:
            M[f'{pair[0]}-{pair[1]}'] = True

        transline2stmt = line2stmt(trans_stmt_list_pos)

        source_predecessors, source_successors, source_stmt_use_consts, source_stmt_def_variables, source_stmt_use_variables, source_line_def_variables = parse_vari_dep(source_stmt_list, source_lines, source_stmt_list_pos, source_lang, this_source_trees)
        trans_predecessors, trans_successors, trans_stmt_use_consts, trans_stmt_def_variables, trans_stmt_use_variables, trans_line_def_variables = parse_vari_dep(trans_stmt_list, trans_lines, trans_stmt_list_pos, target_lang, this_trans_trees)

        source_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt', source_lines, source_lang, target_lang, source_lang, ID)
        trans_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt', trans_lines, source_lang, target_lang, target_lang, ID)
        report_id = compare_stepbystep(source_traces, trans_traces, source_lang, target_lang, line_M, len(source_lines), len(trans_lines), source_lines, trans_lines, trans_line_def_variables)

        indent = ''
        for char in trans_lines[1]:
            if char == ' ':
                indent += ' '
            else:
                break

        if os.path.exists(f'{save_fixcode_dir}/{ID}/'):
            exist_files = os.listdir(f'{save_fixcode_dir}/{ID}/')
            for exist_file in exist_files:
                if os.path.isdir(f'{save_fixcode_dir}/{ID}/{exist_file}'):
                    shutil.rmtree(f'{save_fixcode_dir}/{ID}/{exist_file}')
                else:
                    os.remove(f'{save_fixcode_dir}/{ID}/{exist_file}')
        else:
            os.makedirs(f'{save_fixcode_dir}/{ID}/', exist_ok=True)
        new_code_id = -1
        FL_trans_line_ids = [report_id]
        if report_id == 0:
            print('')
        for this_trans_stmt_id, this_trans_stmt_list, this_trans_stmt_list_depth, this_this_trans_trees, this_trans_stmt_list_pos in zip(
                [stmt_id for stmt_id in range(len(trans_stmt_list))],
                trans_stmt_list, trans_stmt_list_depth, this_trans_trees, trans_stmt_list_pos):
            if_FL_trans_line = False
            for pos in this_trans_stmt_list_pos:
                if pos[0] in FL_trans_line_ids:
                    if_FL_trans_line = True
            if if_FL_trans_line:
                FL_trans_stmt_ids = [this_trans_stmt_id]
                FL_trans_stmts = [this_trans_stmt_list]
                FL_trans_depths = [this_trans_stmt_list_depth]
                FL_trans_trees = [this_this_trans_trees]
                FL_trans_poses = [this_trans_stmt_list_pos]
                FL_source_stmt_ids = [int(k.split('-')[0]) for k, v in M.items() if v and int(k.split('-')[1]) in FL_trans_stmt_ids]
                if len(FL_source_stmt_ids) != 1 and this_trans_stmt_id != 0:
                    continue
                new_fix_code_list = []
                if this_trans_stmt_id == 0:
                    trans_first_line = trans_lines[0].strip()
                    trans_first_line_list = trans_first_line.split(' ')
                    available_idxs = [this_idx for this_idx, this_token in enumerate(trans_first_line_list) if this_token in ['int', 'float', 'double', 'bool']]
                    if available_idxs and available_idxs[0] == 0:
                        available_idxs = available_idxs[1:]
                    this_choices = []
                    for available_idx in available_idxs:
                        if this_choices == []:
                            this_choices = [['double'], ['float'], ['long long']]
                        else:
                            new_this_choices = []
                            for item in this_choices:
                                for this_type in ['long long', 'double', 'float']:
                                    this_item = item[:]
                                    this_item.append(this_type)
                                    new_this_choices.append(this_item)
                            this_choices = new_this_choices[:]
                    for this_choice in this_choices:
                        this_trans_first_line_list = trans_first_line_list[:]
                        for item_idx, item in enumerate(this_choice):
                            this_trans_first_line_list[available_idxs[item_idx]] = item
                        this_fix_code = ' '.join(this_trans_first_line_list)
                        new_fix_code_list.append(this_fix_code)
                else:
                    FL_source_stmts = []
                    FL_source_depths = []
                    FL_source_trees = []
                    this_stmt_id = -1
                    for this_source_stmt_list, this_source_stmt_list_depth, this_this_source_trees, this_source_stmt_list_pos in zip(source_stmt_list, source_stmt_list_depth, this_source_trees, source_stmt_list_pos):
                        this_stmt_id += 1
                        if this_stmt_id in FL_source_stmt_ids:
                            FL_source_stmts.append(this_source_stmt_list)
                            FL_source_depths.append(this_source_stmt_list_depth)
                            FL_source_trees.append(this_this_source_trees)
                    source_FL_codes = []
                    fix_code_choices_lists = []
                    first_depth = 0
                    if FL_source_depths:
                        first_depth = FL_source_depths[0]
                    all_use_variables = []
                    for FL_source_stmt, FL_source_depth, FL_source_tree in zip(FL_source_stmts, FL_source_depths, FL_source_trees):
                        source_FL_code, _ = mytree2code(FL_source_tree, source_lang, '', '')
                        source_FL_codes.append(source_FL_code)
                        depth = 0
                        max_depth = 1000000000
                        max_possible_choices = 1000000000
                        time_limit = 60
                        start_time = time.time()
                        possible_maps_list = match(FL_source_tree, [], source_lang, target_lang, maps, trans_path2tree)
                        if not possible_maps_list:
                            search, search_result = check_new_rule(f'{task1_name}-new', FL_source_stmt)
                            if search:
                                possible_maps_force_list = search_result
                            else:
                                possible_maps_force_list, _ = match_force(FL_source_tree, [],
                                                                                root_node2map,
                                                                                source_lang, target_lang,
                                                                                maps, source_path2tree, trans_path2tree, depth,
                                                                                max_depth,
                                                                                max_possible_choices, start_time, time_limit,
                                                                                False)
                                save_new_rule(f'{task1_name}-new', FL_source_stmt, possible_maps_force_list)
                            possible_maps_list.extend(possible_maps_force_list)
                        elif len(possible_maps_list) == 1:
                            possible_maps_force_list, _ = match_force_begin(FL_source_tree, [],
                                                                      root_node2map,
                                                                      source_lang, target_lang,
                                                                      maps, source_path2tree, trans_path2tree, depth,
                                                                      max_depth,
                                                                      max_possible_choices, start_time, time_limit,
                                                                      False)
                            possible_maps_list.extend(possible_maps_force_list)
                        templates = []
                        if possible_maps_list:
                            for possible_maps in possible_maps_list[:10]:
                                template = []
                                for stmt in possible_maps:
                                    this_template, var_dict, number_dict, string_dict, type_dict, pretoken = mytree2template(stmt, target_lang, '', [], [], [], [], '')
                                    if len(var_dict) > 6 or len(number_dict) > 6 or len(string_dict) > 6:
                                        continue
                                    print('------------------------')
                                    print(stmt.text)
                                    print(this_template)
                                    this_template = change_format(this_template, stmt, indent, FL_source_depth-first_depth, FL_source_stmt, this_trans_stmt_list)
                                    template.append([this_template, var_dict, number_dict, string_dict, type_dict, stmt.type])
                                if template not in templates:
                                    templates.append(template)

                        use_consts = []
                        source_use_consts = []
                        trans_use_consts = []
                        find_use_consts(FL_source_tree, use_consts)
                        find_use_consts(FL_source_tree, source_use_consts)
                        for FL_trans_tree in FL_trans_trees:
                            find_use_consts(FL_trans_tree, use_consts)
                            find_use_consts(FL_trans_tree, trans_use_consts)
                        use_variables = []
                        source_use_variables = []
                        trans_use_variables = []
                        find_use_variable(FL_source_tree, use_variables, source_lang)
                        find_use_variable(FL_source_tree, source_use_variables, source_lang)
                        for FL_trans_tree in FL_trans_trees:
                            find_use_variable(FL_trans_tree, use_variables, target_lang)
                            find_use_variable(FL_trans_tree, trans_use_variables, target_lang)
                        use_strings = []
                        source_use_strings = []
                        trans_use_strings = []
                        find_use_strings(FL_source_tree, use_strings)
                        find_use_strings(FL_source_tree, source_use_strings)
                        for FL_trans_tree in FL_trans_trees:
                            find_use_strings(FL_trans_tree, use_strings)
                            find_use_strings(FL_trans_tree, trans_use_strings)
                        use_types = []
                        source_use_types = []
                        trans_use_types = []
                        find_use_types(FL_source_tree, use_types)
                        find_use_types(FL_source_tree, source_use_types)
                        for FL_trans_tree in FL_trans_trees:
                            find_use_types(FL_trans_tree, use_types)
                            find_use_types(FL_trans_tree, trans_use_types)
                        this_variables = []
                        this_variables.extend(use_variables)
                        this_variables = list(set(this_variables))
                        use_consts = list(set(use_consts))
                        use_strings = list(set(use_strings))
                        all_use_variables.extend(this_variables)
                        filled_templates = []
                        for template in templates:
                            this_filled_template = []
                            for stmt in template:
                                filled_template = fill_template(stmt[0], stmt[1], stmt[2], stmt[3], stmt[4], stmt[5], this_variables, use_consts, use_strings, use_types,
                                                                source_use_variables, trans_use_variables, source_use_consts, trans_use_consts, source_use_strings, trans_use_strings, source_lang)
                                this_filled_template.append(filled_template)
                            if this_filled_template != [[]]:
                                filled_templates.append(this_filled_template)
                        filled_templates_len = 0
                        for filled_template in filled_templates:
                            for item in filled_template:
                                filled_templates_len += len(item)
                        if filled_templates_len > 500:
                            propt = 500 / filled_templates_len
                            average_len = filled_templates_len / len(filled_templates)
                            target_average_len = int(average_len * propt)
                            filled_templates = []
                            for template in templates:
                                this_filled_template = []
                                for stmt in template:
                                    filled_template = fill_template(stmt[0], stmt[1], stmt[2], stmt[3], stmt[4], stmt[5],
                                                                    this_variables, use_consts, use_strings, use_types,
                                                                    source_use_variables, trans_use_variables,
                                                                    source_use_consts, trans_use_consts, source_use_strings,
                                                                    trans_use_strings, source_lang, average_len=target_average_len, source_FL_code=source_FL_code)
                                    this_filled_template.append(filled_template)
                                if this_filled_template != [[]]:
                                    filled_templates.append(this_filled_template)
                        if fix_code_choices_lists == []:
                            fix_code_choices_lists.extend(filled_templates)
                        else:
                            new_fix_code_choices_lists = []
                            for fix_code_choices_list in fix_code_choices_lists:
                                for new_fix_codes_list in filled_templates:
                                    this_fix_code_choices_list = copy.deepcopy(fix_code_choices_list)
                                    this_fix_code_choices_list.extend(new_fix_codes_list)
                                    new_fix_code_choices_lists.append(this_fix_code_choices_list)
                            fix_code_choices_lists = copy.deepcopy(new_fix_code_choices_lists)
                    fix_code_lists = []
                    for fix_code_choices_list in fix_code_choices_lists:
                        fix_code_list = []
                        for stmt_choices in fix_code_choices_list:
                            if fix_code_list == []:
                                for choice in stmt_choices:
                                    fix_code_list.append(choice)
                            else:
                                this_new_fix_code_list = []
                                for item in fix_code_list:
                                    for choice in stmt_choices:
                                        this_item = copy.deepcopy(item)
                                        this_item += '\n' + choice
                                        this_new_fix_code_list.append(this_item)
                                fix_code_list = copy.deepcopy(this_new_fix_code_list)
                        fix_code_lists.extend(fix_code_list)
                    sort_fix_code_lists = []
                    sort_fix_codes = []
                    for fix_code_list in fix_code_lists:
                        if source_lang == 'Python' and source_FL_codes[0].strip().startswith('for '):
                            score = 0
                            trans_FL_code = ''
                            for FL_trans_stmt_id in FL_trans_stmt_ids:
                                for this_pos in trans_stmt_list_pos[FL_trans_stmt_id]:
                                    trans_FL_code += trans_lines[this_pos[0]][this_pos[1]]
                            if '\n' in trans_FL_code:
                                trans_FL_code = trans_FL_code.replace('\n', '')
                            if ' ' in trans_FL_code:
                                trans_FL_code = trans_FL_code.replace(' ', '')
                            trans_FL_code = trans_FL_code.strip()
                            this_fix_code_list = copy.deepcopy(fix_code_list)
                            if ' ' in this_fix_code_list:
                                this_fix_code_list = fix_code_list.replace(' ', '')
                            BLEUscore = nltk.translate.bleu_score.sentence_bleu([trans_FL_code], this_fix_code_list, weights=(0.5, 0.5))
                            del trans_FL_code
                            del this_fix_code_list
                        else:
                            score = 0
                            score += fix_code_list.count('long long')
                            score += fix_code_list.count('__int128') * 2
                            score += fix_code_list.count('{0}')
                            score += fix_code_list.count(', 0)')
                            score += fix_code_list.count('=')
                            this_source_FL_codes = copy.deepcopy(source_FL_codes)
                            if ' ' in this_source_FL_codes:
                                this_source_FL_codes = this_source_FL_codes.replace(' ', '')
                            this_fix_code_list = copy.deepcopy(fix_code_list)
                            if ' ' in this_fix_code_list:
                                this_fix_code_list = fix_code_list.replace(' ', '')
                            BLEUscore = nltk.translate.bleu_score.sentence_bleu(this_source_FL_codes, this_fix_code_list, weights=(0.5, 0.5))
                            del this_source_FL_codes
                            del this_fix_code_list
                        if fix_code_list not in sort_fix_codes:
                            sort_fix_codes.append(fix_code_list)
                            sort_fix_code_lists.append([score, BLEUscore, fix_code_list])
                    sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[2])
                    sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[1], reverse=True)
                    sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[0], reverse=True)
                    new_fix_code_list = [item[2] for item in sort_fix_code_lists]
                for fix_code_str in new_fix_code_list:
                    new_code_id += 1
                    new_code_lines = copy.deepcopy(trans_lines)
                    replace_pos = []
                    this_line2pos = []
                    for pos in FL_trans_poses[0]:
                        if not this_line2pos:
                            this_line2pos.append([pos])
                        else:
                            this_pos_list_idex = -1
                            for this_pos_list_id, this_pos_list in enumerate(this_line2pos):
                                if pos[0] == this_pos_list[0][0]:
                                    this_pos_list_idex = this_pos_list_id
                            if this_pos_list_idex == -1:
                                this_line2pos.append([pos])
                            else:
                                this_line2pos[this_pos_list_idex].append(pos)
                    if len(this_line2pos[-1]) == 1 and new_code_lines[this_line2pos[-1][0][0]][this_line2pos[-1][0][1]] == '}':
                        for this_this_line2pos in this_line2pos[:-1]:
                            for pos in reversed(this_this_line2pos):
                                new_code_lines[pos[0]] = new_code_lines[pos[0]][:pos[1]] + new_code_lines[pos[0]][pos[1]+1:]
                        replace_pos = this_line2pos[-2][0][:]
                    else:
                        for this_this_line2pos in this_line2pos[:]:
                            for pos in reversed(this_this_line2pos):
                                new_code_lines[pos[0]] = new_code_lines[pos[0]][:pos[1]] + new_code_lines[pos[0]][pos[1]+1:]
                        replace_pos = this_line2pos[-1][0][:]
                    if new_code_lines[replace_pos[0]][replace_pos[1]:].strip() != '' and not new_code_lines[replace_pos[0]][replace_pos[1]:].strip().startswith('\\'):
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                    else:
                        if fix_code_str.strip().endswith(';') or fix_code_str.strip().endswith('{'):
                            new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                        else:
                            new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' {' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                    if new_code_lines[replace_pos[0]][-1] == '\n':
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:-1] + ' // Patch 1' + new_code_lines[replace_pos[0]][-1]
                    else:
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]] + ' // Patch 1'
                    if 'sort' in fix_code_str:
                        ori_first_line = new_code_lines[0]
                        first_line = new_code_lines[0]
                        all_use_variables = set(all_use_variables)
                        for this_use_var in all_use_variables:
                            if this_use_var in fix_code_str:
                                if f'int {this_use_var}[]' in first_line:
                                    first_line = first_line.replace(f'int {this_use_var}[]', f'vector<int> {this_use_var}')
                                elif f'int {this_use_var}[ ]' in first_line:
                                    first_line = first_line.replace(f'int {this_use_var}[ ]', f'vector<int> {this_use_var}')
                                elif f'int {this_use_var} [ ]' in first_line:
                                    first_line = first_line.replace(f'int {this_use_var} [ ]', f'vector<int> {this_use_var}')
                                elif f'int * {this_use_var}' in first_line:
                                    first_line = first_line.replace(f'int * {this_use_var}', f'vector<int> {this_use_var}')
                        if ori_first_line != first_line:
                            new_code_lines[0] = first_line
                            f_out = open(f'{save_fixcode_dir}/{ID}/{new_code_id}.{target_ext}', 'w')
                            print(''.join(new_code_lines), file=f_out)
                            f_out.close()
                    else:
                        if 'long long' in fix_code_str:
                            first_line = new_code_lines[0]
                            first_line_items = first_line.split('f_filled')
                            return_type = first_line_items[0].strip()
                            if return_type in ['int']:
                                new_new_code_lines = new_code_lines[:]
                                new_new_code_lines[0] = f'long long f_filled{first_line_items[1]}'
                                f_out = open(f'{save_fixcode_dir}/{ID}/{new_code_id}.{target_ext}', 'w')
                                print(''.join(new_new_code_lines), file=f_out)
                                f_out.close()
                                new_code_id += 1
                        elif '__int128' in fix_code_str:
                            first_line = new_code_lines[0]
                            first_line_items = first_line.split('f_filled')
                            return_type = first_line_items[0].strip()
                            if return_type in ['int', 'long long']:
                                new_new_code_lines = new_code_lines[:]
                                new_new_code_lines[0] = f'__int128 f_filled{first_line_items[1]}'
                                f_out = open(f'{save_fixcode_dir}/{ID}/{new_code_id}.{target_ext}', 'w')
                                print(''.join(new_new_code_lines), file=f_out)
                                f_out.close()
                                new_code_id += 1
                        f_out = open(f'{save_fixcode_dir}/{ID}/{new_code_id}.{target_ext}', 'w')
                        print(''.join(new_code_lines), file=f_out)
                        f_out.close()
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
        "--path_to_stmtmap",
        default='Ours_stmtmap',
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
        "--path_to_fixcode",
        default='Fix_Code',
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
    path_to_stmtmap = args.path_to_stmtmap
    path_to_code = args.path_to_code
    path_to_fixcode = args.path_to_fixcode
    path_to_DATABASE = args.path_to_DATABASE
    count_right, count_wrong, count_right_B, count_wrong_B = run(path_to_map, path_to_stmtmap, path_to_code, path_to_DATABASE, path_to_fixcode, target_model_name, source_lang, target_lang, model_name)

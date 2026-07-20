import copy

from utils import *
from tqdm import tqdm
import time
import argparse


def compare_stepbystep_for_fix(source_traces, trans_traces, source_lang, target_lang, line_M, len_s, len_t, source_lines, trans_lines, trans_line_def_variables, fixed_lines):
    report_id = 0
    diff_info = []
    pre_s_state = [[], [], []]
    pre_t_state = [[], [], []]
    s_state = [[], [], []]
    t_state = [[], [], []]
    if_step = True
    pass_t_ids = []
    pass_vars = []

    s_vals = {}
    t_vals = {}
    for step_id, step in enumerate(source_traces):
        s_var_vals = read_var_val(step[1:])
        for var, val in s_var_vals.items():
            if var not in s_vals:
                s_vals[var] = [[step_id, val]]
            else:
                s_vals[var].append([step_id, val])
    for step_id, step in enumerate(trans_traces):
        t_var_vals = read_var_val(step[1:])
        for var, val in t_var_vals.items():
            if var not in t_vals:
                t_vals[var] = [[step_id, val]]
            else:
                t_vals[var].append([step_id, val])

    if_source_non = False
    if_target_non = False
    while if_step:
        s_state, s_suc = next_s_state(source_traces, s_state, line_M, len_t, source_lang, source_lines)
        t_state, t_suc = next_t_state(trans_traces, t_state, line_M, len_s, target_lang, trans_lines)
        if not s_suc and t_suc:
            if_step = False
            diff_info.append(['diff_path'])
            if_source_non = True
        elif not s_suc or not t_suc:
            if_step = False
            diff_info.append(['diff_path'])
            if_target_non = True
        else:
            s_expect_t = set()
            for t_stmt_id in range(len_t):
                if line_M[f'{s_state[0][-1]}-{t_stmt_id}']:
                    s_expect_t.add(t_stmt_id)
            s_expect_t = list(s_expect_t)
            if len(s_expect_t):
                if t_state[0][-1] not in s_expect_t:
                    try:
                        if source_lang == 'Java' and len(t_state[0]) == 1 and trans_lines[
                            t_state[0][0]].strip().startswith('for') and len(s_expect_t) == 1 and source_lines[
                            s_expect_t[0] - 2].strip().startswith('for'):
                            None
                        else:
                            if_step = False
                            diff_info.append(['diff_path'])
                    except:
                        if_step = False
                        diff_info.append(['diff_path'])
            last_s_var_vals = s_state[1][-1]
            last_t_var_vals = t_state[1][-1]
            for s_var, s_val in last_s_var_vals.items():
                if s_var in last_t_var_vals:
                    t_val = last_t_var_vals[s_var]
                    if not compare_value(s_var, s_val, t_val, s_vals, t_vals, s_state[2], t_state[2]):
                        if source_lang == 'Python' and target_lang == 'C++' and s_var in ['i', 'j', 'k']:
                            try:
                                pre_s_val_int = int(pre_s_state[1][0][s_var])
                                s_val_int = int(s_val)
                                t_val_int = int(t_val)
                                if pre_s_val_int == s_val_int and s_val_int < t_val_int:
                                    break
                            except:
                                None
                            try:
                                next_val = [val_str for val_str in trans_traces[t_state[2][-1] + 1][1:] if
                                            f'{s_var} = ' in val_str]
                                if next_val:
                                    t_val_int = int(next_val[0].strip()[len(f'{s_var} = '):])
                                    if t_val_int == 0:
                                        break
                            except:
                                None
                        if_step = False
                        diff_info.append(['diff_value', s_var, s_val, t_val])
                    else:
                        pass_vars.append(s_var)
            if if_step:
                pass_t_ids.extend(t_state[0])
        if if_step:
            pre_s_state = copy.deepcopy(s_state)
            pre_t_state = copy.deepcopy(t_state)
        else:
            if diff_info[0][0] == 'diff_value':
                report_id = t_state[0][0]
                if report_id in trans_line_def_variables and (check_overflow(diff_info[0], pass_vars) or check_float(diff_info[0], pass_vars)):
                    report_varis = trans_line_def_variables[report_id]
                    for line_id in range(len(trans_lines)):
                        if line_id in trans_line_def_variables:
                            varis = trans_line_def_variables[line_id]
                            if set(report_varis).intersection(set(varis)):
                                report_id = line_id
                                break
            else:
                if if_source_non and len(pre_t_state[0]):
                    report_id = pre_t_state[0]
                elif if_target_non and len(pre_t_state[0]):
                    if pre_t_state[2] and pre_t_state[2][0]-1 >= 0 :
                        report_id = trans_traces[pre_t_state[2][0]-1][0]
                    else:
                        report_id = pre_t_state[0]
                elif t_state and t_state[0] and t_state[0][0]-1 not in pass_t_ids and t_state[0][0]-1 >= 0 and t_state[0][0]-1 < len(trans_lines) and 'int' in trans_lines[t_state[0][0]-1] and 'return' not in trans_lines[t_state[0][0]-1] and '=' not in trans_lines[t_state[0][0]-1]:
                    report_id = t_state[0][0]-1
                elif len(pre_t_state[0]):
                    report_id = pre_t_state[0]
                else:
                    report_id = -1
                if report_id != -1 and isinstance(report_id, int):
                    if trans_lines[report_id].strip().startswith('return '):
                        return_str = trans_lines[report_id].strip()
                        return_str_val = return_str[return_str.index('return ')+len('return '):]
                        if return_str_val.endswith(';'):
                            return_str_val = return_str_val[:-2].strip()
                        if return_str_val in t_vals:
                            for line_id in range(len(trans_lines)):
                                if line_id in trans_line_def_variables:
                                    varis = trans_line_def_variables[line_id]
                                    if return_str_val in varis:
                                        report_id = line_id
                                        break
            if report_id != -1 and isinstance(report_id, int):
                if report_id in fixed_lines:
                    if_have_diff_value = False
                    for item in diff_info:
                        if item[0] == 'diff_value':
                            if_have_diff_value = True
                    if report_id == 0 and t_state[0] == [0] and if_have_diff_value:
                        report_id = 0
                    else:
                        if_find_not_fix_line = False
                        for this_line_id in range(report_id + 1, len(trans_lines)):
                            if this_line_id not in fixed_lines:
                                report_id = this_line_id
                                if_find_not_fix_line = True
                                break
                        if not if_find_not_fix_line:
                            report_id = -1
            elif isinstance(report_id, list):
                if_have_diff_value = False
                for item in diff_info:
                    if item[0] == 'diff_value':
                        if_have_diff_value = True
                new_report_id = []
                for this_id, this_report_id in enumerate(report_id):
                    if this_report_id in fixed_lines:
                        continue
                    else:
                        new_report_id.append(this_report_id)
                if new_report_id:
                    report_id = new_report_id[:]
                else:
                    if report_id == [0] and t_state[0] == [0] and if_have_diff_value:
                        report_id = [0]
                    else:
                        if_find_not_fix_line = False
                        for this_line_id in range(report_id[-1]+1, len(trans_lines)):
                            if this_line_id not in fixed_lines:
                                report_id = this_line_id
                                if_find_not_fix_line = True
                                break
                        if not if_find_not_fix_line:
                            report_id = -1
    return report_id


def run(path_to_map, path_to_stmtmap, path_to_code, path_to_DATABASE, path_to_fixcode, target_model_name, source_lang, target_lang, model_name, path_to_unmapped_stmt):
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
    path_path2anchors = {}
    for k, v in path2pair.items():
        for v_pair in v:
            v_source_path = v_pair.source_path
            v_target_paths = '####'.join(v_pair.target_paths)
            if f'{v_source_path}>>>>{v_target_paths}' not in path_path2anchors:
                path_path2anchors[f'{v_source_path}>>>>{v_target_paths}'] = v_pair.anchors
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
        unmapped_stmt_lines = open(f'{path_to_unmapped_stmt}/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt').readlines()
        unmapped_stmts = []
        for unmapped_stmt_line in unmapped_stmt_lines:
            if unmapped_stmt_line.strip():
                unmapped_stmts.append(int(unmapped_stmt_line.strip()))

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

        fixed_stmts = []
        for line_id in range(len(trans_lines)):
            if line_id in transline2stmt:
                this_line_stmts = transline2stmt[line_id]
                this_line_stmts_stmts = []
                for stmt_id in this_line_stmts:
                    if trans_stmt_list[stmt_id] != 'comment-0':
                        this_line_stmts_stmts.append(stmt_id)
                patch_count = trans_lines[line_id].count('// Patch')
                if patch_count >= len(this_line_stmts_stmts):
                    fixed_stmts.extend(this_line_stmts_stmts)

        fixed_lines = []
        for this_trans_stmt_id, this_trans_stmt_list_pos in zip([stmt_id for stmt_id in range(len(trans_stmt_list))], trans_stmt_list_pos):
            if this_trans_stmt_id in fixed_stmts:
                for pos in this_trans_stmt_list_pos:
                    if pos[0] not in fixed_lines:
                        fixed_lines.append(pos[0])

        source_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
        trans_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')
        report_id = compare_stepbystep_for_fix(source_traces, trans_traces, source_lang, target_lang, line_M, len(source_lines), len(trans_lines), source_lines, trans_lines, trans_line_def_variables, fixed_lines)

        if isinstance(report_id, list):
            report_id = list(set(report_id))
            report_id.sort()
        else:
            if report_id == -1:
                if unmapped_stmts:
                    unmapped_lines = []
                    for stmt_id, poss in enumerate(trans_stmt_list_pos):
                        if stmt_id and stmt_id in unmapped_stmts and poss[0][0] not in unmapped_lines:
                            if_rerepair = False
                            for pos in poss:
                                if '// Patch' in trans_lines[pos[0]]:
                                    if_rerepair = True
                            if not if_rerepair:
                                unmapped_lines.append(poss[0][0])
                    if unmapped_lines:
                        report_id = unmapped_lines[0]
                    else:
                        report_id = 0
                else:
                    report_id = 0

            if report_id == -1:
                report_id = 0

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
        if isinstance(report_id, list):
            FL_trans_line_ids = report_id[:]
        else:
            FL_trans_line_ids = [report_id]
        for_without_dec = []
        stmt_id = -1
        for stmt, tree in zip(trans_stmt_list[:-1], this_trans_trees[:-1]):
            stmt_id += 1
            if stmt.startswith('for_statement-0||||for-0||||(-0||||assignment_expression-0||||identifier-0||||=-0||||') and ' // Patch' not in trans_lines[this_trans_trees[stmt_id+1].line_id]:
                for_without_dec.append([stmt_id, tree.children[2].children[0].text, trans_stmt_list_pos[stmt_id][-1][0]+1])

        all_new_code_id = 0
        for this_trans_stmt_id, this_trans_stmt_list, this_trans_stmt_list_depth, this_this_trans_trees, this_trans_stmt_list_pos in zip(
                [stmt_id for stmt_id in range(len(trans_stmt_list))],
                trans_stmt_list, trans_stmt_list_depth, this_trans_trees, trans_stmt_list_pos):
            new_code_id = 0
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
                if this_trans_stmt_id == 0:
                    new_fix_code_list = []
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
                    sort_fix_codes_dict = {}
                    for fix_code_list_id, fix_code_list in enumerate(new_fix_code_list):
                        sort_fix_code_lists = []
                        sort_fix_codes = []
                        for fix_code_list_item in [fix_code_list]:
                            if fix_code_list_item not in sort_fix_codes:
                                sort_fix_codes.append(fix_code_list_item)
                                sort_fix_code_lists.append([1, 1, fix_code_list_item])
                        sort_fix_codes_dict[fix_code_list_id] = sort_fix_code_lists[:]
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
                        max_possible_choices = 10
                        time_limit = 1000000000
                        start_time = time.time()
                        possible_maps_list = match(FL_source_tree, [], source_lang, target_lang, maps, trans_path2tree, path_path2anchors)
                        if not possible_maps_list:
                            search, search_result = check_new_rule(f'{task1_name}-Synthesis', FL_source_stmt)
                            if search:
                                possible_maps_force_list = search_result
                            else:
                                possible_maps_force_list, _ = match_force(FL_source_tree, [],
                                                                                root_node2map,
                                                                                source_lang, target_lang,
                                                                                maps, source_path2tree, trans_path2tree, depth,
                                                                                max_depth,
                                                                                max_possible_choices, start_time, time_limit,
                                                                                False, path_path2anchors)
                                possible_maps_force_list = remove_parenthesis(possible_maps_force_list)
                                save_new_rule(f'{task1_name}-Synthesis', FL_source_stmt, possible_maps_force_list)
                            possible_maps_list.extend(possible_maps_force_list)
                        exis_possible_maps_list = []
                        for this_possible_maps in possible_maps_list:
                            this_exis_possible_maps = []
                            for this_possible_map_tree in this_possible_maps[0]:
                                this_exis_possible_maps.extend(this_possible_map_tree.getDFS(target_lang))
                            exis_possible_maps_list.append(this_exis_possible_maps)
                        possible_maps_realforce_list, _ = match_force_begin(FL_source_tree, [],
                                                                  root_node2map,
                                                                  source_lang, target_lang,
                                                                  maps, source_path2tree, trans_path2tree, depth,
                                                                  max_depth,
                                                                  max_possible_choices, start_time, time_limit,
                                                                  False, exis_possible_maps_list, path_path2anchors)
                        possible_maps_realforce_list = remove_parenthesis(possible_maps_realforce_list)
                        possible_maps_list.extend(possible_maps_realforce_list)
                        possible_maps_list = rephrase_maps(possible_maps_list, target_lang)

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

                        templates = []
                        if possible_maps_list:
                            for possible_maps in possible_maps_list[:10]:
                                template = []
                                source_number_lists = []
                                traverse_tree_number(FL_source_tree, source_number_lists)
                                for stmt_id, stmt in enumerate(possible_maps[0]):
                                    target_number_lists = []
                                    traverse_tree_number(stmt, target_number_lists)
                                    if_int_same = True
                                    if len(set(source_number_lists)) != len(set(target_number_lists)):
                                        if_int_same = False
                                    template_anchors = possible_maps[1][:]
                                    new_template_anchors = []
                                    for template_anchor in template_anchors:
                                        template_anchor_1 = template_anchor[0]
                                        template_anchor_2 = template_anchor[1]
                                        new_template_anchor_2 = [[this_template_anchor_2[0], 0] for this_template_anchor_2 in template_anchor_2 if this_template_anchor_2[1] == stmt_id]
                                        if new_template_anchor_2:
                                            new_template_anchors.append([template_anchor_1, new_template_anchor_2])
                                    template_anchors = new_template_anchors
                                    if this_this_trans_trees.type == 'for_statement' and stmt.type == 'for_statement' and ' in ' in FL_source_tree.text:
                                        template_anchors = [template_anchor for template_anchor in template_anchors if template_anchor[0] != [1]]
                                    this_template, var_dict, var_list, number_dict, string_dict, type_dict, pretoken = mytree2template(stmt, [], FL_source_tree, template_anchors, source_lang, target_lang, '', [], [], [], [], [], '', if_int_same, trans_use_variables)
                                    if len(var_dict) > 6 or len(number_dict) > 6 or len(string_dict) > 6:
                                        continue
                                    print('------------------------')
                                    print(stmt.text)
                                    print(this_template)
                                    this_template = change_format(this_template, stmt, indent, FL_source_depth-first_depth, FL_source_stmt, this_trans_stmt_list)
                                    if_multi_assign = False
                                    if stmt.type == 'declaration' and len(stmt.children) == 5 and stmt.children[2].type == ',' and this_template.count('=') == 2:
                                        new_template_anchors = []
                                        first_var = []
                                        FL_source_tree_copy = copy.deepcopy(FL_source_tree)
                                        for template_anchor in template_anchors:
                                            if template_anchor[1][0][0] in [[1, 0]]:
                                                first_var.append(FL_source_tree.getChild(template_anchor[0]).text)
                                        if first_var:
                                            if_assign = False
                                            for template_anchor in template_anchors:
                                                if is_prefix_sublist(template_anchor[1][0][0], [1]):
                                                    new_template_anchors.append(template_anchor)
                                                elif is_prefix_sublist(template_anchor[1][0][0], [3]):
                                                    new_template_anchors.append(template_anchor)
                                                    if FL_source_tree.getChild(template_anchor[0]).text in first_var:
                                                        FL_source_tree_child = FL_source_tree_copy.getChild(template_anchor[0])
                                                        FL_source_tree_child.text = 'tmp_1'
                                                        FL_source_tree_copy.changeChild(template_anchor[0], FL_source_tree_child)
                                                        if_assign = True
                                            new_this_template, var_dict, var_list, number_dict, string_dict, type_dict, pretoken = mytree2template(stmt, [], FL_source_tree_copy, new_template_anchors, source_lang, target_lang, '', [], [], [], [], [], '', if_int_same, trans_use_variables)

                                            if new_this_template.count(',') == 1:
                                                declarations = new_this_template.split(',')

                                                first_type = declarations[0].split(' ')[0].strip()
                                                first_var = ' '.join(declarations[0].split(' ')[1:]).split('=')[0].strip()
                                                first_val = ' '.join(declarations[0].split(' ')[1:]).split('=')[1].strip()
                                                second_var = declarations[1].split('=')[0].strip()
                                                second_val = declarations[1].split('=')[1].strip()
                                                if if_assign:
                                                    if_multi_assign = True
                                                    this_this_template = '{'+f'{first_type} tmp_1 = {first_var}; {first_var} = {first_val}, {second_var} = {second_val}'+'}'
                                                    if [[this_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]] not in templates:
                                                        templates.append([[this_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]])
                                            del FL_source_tree_copy
                                    elif stmt.type == 'declaration' and len(stmt.children) == 7 and stmt.children[2].type == ',' and stmt.children[4].type == ',' and this_template.count('=') == 3:
                                        new_template_anchors = []
                                        first_var = []
                                        second_var = []
                                        FL_source_tree_copy = copy.deepcopy(FL_source_tree)
                                        for template_anchor in template_anchors:
                                            if template_anchor[1][0][0] in [[1, 0]]:
                                                first_var.append(FL_source_tree.getChild(template_anchor[0]).text)
                                            if template_anchor[1][0][0] in [[3, 0]]:
                                                second_var.append(FL_source_tree.getChild(template_anchor[0]).text)
                                        if first_var and second_var:
                                            if_assign = False
                                            for template_anchor in template_anchors:
                                                if is_prefix_sublist(template_anchor[1][0][0], [1]):
                                                    new_template_anchors.append(template_anchor)
                                                elif is_prefix_sublist(template_anchor[1][0][0], [3]):
                                                    new_template_anchors.append(template_anchor)
                                                    if FL_source_tree.getChild(template_anchor[0]).text in first_var:
                                                        FL_source_tree_child = FL_source_tree_copy.getChild(template_anchor[0])
                                                        FL_source_tree_child.text = 'tmp_1'
                                                        FL_source_tree_copy.changeChild(template_anchor[0], FL_source_tree_child)
                                                        if_assign = True
                                                elif is_prefix_sublist(template_anchor[1][0][0], [5]):
                                                    new_template_anchors.append(template_anchor)
                                                    if FL_source_tree.getChild(template_anchor[0]).text in first_var:
                                                        FL_source_tree_child = FL_source_tree_copy.getChild(template_anchor[0])
                                                        FL_source_tree_child.text = 'tmp_1'
                                                        FL_source_tree_copy.changeChild(template_anchor[0], FL_source_tree_child)
                                                        if_assign = True
                                                    elif FL_source_tree.getChild(template_anchor[0]).text in second_var:
                                                        FL_source_tree_child = FL_source_tree_copy.getChild(template_anchor[0])
                                                        FL_source_tree_child.text = 'tmp_2'
                                                        FL_source_tree_copy.changeChild(template_anchor[0], FL_source_tree_child)
                                                        if_assign = True
                                            new_this_template, var_dict, var_list, number_dict, string_dict, type_dict, pretoken = mytree2template(stmt, [], FL_source_tree_copy, new_template_anchors, source_lang, target_lang, '', [], [], [], [], [], '', if_int_same, trans_use_variables)
                                            declarations = new_this_template.split(',')
                                            first_type = declarations[0].split(' ')[0].strip()
                                            first_var = ' '.join(declarations[0].split(' ')[1:]).split('=')[0].strip()
                                            first_val = ' '.join(declarations[0].split(' ')[1:]).split('=')[1].strip()
                                            second_var = declarations[1].split('=')[0].strip()
                                            second_val = declarations[1].split('=')[1].strip()
                                            third_var = declarations[2].split('=')[0].strip()
                                            third_val = declarations[2].split('=')[1].strip()
                                            if if_assign:
                                                if_multi_assign = True
                                                this_this_template = '{'+f'{first_type} tmp_1 = {first_var}, tmp_2 = {second_var}; {first_var} = {first_val}, {second_var} = {second_val}, {third_var} = {third_val}'+'}'
                                                if [[this_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]] not in templates:
                                                    templates.append([[this_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]])
                                            del FL_source_tree_copy
                                    if '<type_1> <type_2> ' in this_template:
                                        this_template = this_template.replace('<type_1> <type_2> ', '<type_1> ')
                                    if this_template.startswith('<type_1> ') and 'static_cast<<type_2>>' in this_template:
                                        this_template = this_template.replace('static_cast<<type_2>>', 'static_cast<<type_1>>')
                                    if '.end()' in this_template:
                                        another_this_template = change_format4end(this_template, var_list)
                                        templates.append([[another_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]])
                                    if "'" in this_template:
                                        another_this_template = this_template.replace("'", '"')
                                        templates.append([[another_this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same]])
                                    if 'if (if (' not in this_template and not if_multi_assign:
                                        template.append([this_template, var_dict, number_dict, string_dict, type_dict, stmt.type, if_int_same])
                                if template not in templates:
                                    templates.append(template)
                        templates_strs_set = []
                        templates_set = []
                        for template in templates:
                            template_str = ''
                            for stmt in template:
                                template_str += stmt[0]
                            if template_str not in templates_strs_set:
                                templates_strs_set.append(template_str)
                                templates_set.append(template)
                        templates = templates_set[:]
                        templates_woconst_strs_set = []
                        templates_woconst_set = []
                        for template in templates:
                            template_str = ''
                            for stmt in template:
                                template_str += stmt[0]
                            if template_str not in templates_woconst_strs_set and 'const ' not in template_str:
                                templates_woconst_strs_set.append(template_str)
                                templates_woconst_set.append(template)
                        if templates_woconst_set:
                            templates = templates_woconst_set[:]

                        filled_templates = []
                        if '_' in source_use_variables:
                            source_use_variables = [item for item in source_use_variables if item != '_']
                            source_use_variables.append('i_')
                        if '_' in use_variables:
                            use_variables = [item for item in use_variables if item != '_']
                            use_variables.append('i_')
                        if '_' in this_variables:
                            this_variables = [item for item in this_variables if item != '_']
                            this_variables.append('i_')
                        for template in templates:
                            this_filled_template = []
                            for stmt in template:
                                if 'tmp_1' in stmt[0]:
                                    this_variables.append('tmp_1')
                                if 'tmp_2' in stmt[0]:
                                    this_variables.append('tmp_2')
                                filled_template = fill_template(stmt[0], stmt[1], stmt[2], stmt[3], stmt[4], stmt[5], stmt[6], this_variables, use_consts, use_strings, use_types,
                                                                source_use_variables, trans_use_variables, source_use_consts, trans_use_consts, source_use_strings, trans_use_strings, source_lang)
                                this_filled_template.append(filled_template)
                            if this_filled_template != [[]]:
                                filled_templates.append(this_filled_template)

                        if FL_source_stmt.startswith('if_statement-0||||if-0||||'):
                            new_filled_templates = []
                            for filled_template in filled_templates:
                                if filled_template and filled_template[0]:
                                    this_filled_template = filled_template[0][0]
                                    if check_same(FL_source_tree.text, this_filled_template):
                                        new_filled_templates.append(filled_template[:])
                                        break
                            if new_filled_templates:
                                filled_templates = new_filled_templates[:]

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
                                    filled_template = fill_template(stmt[0], stmt[1], stmt[2], stmt[3], stmt[4], stmt[5], stmt[6],
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
                        for stmt_choices_id, stmt_choices in enumerate(fix_code_choices_list):
                            if fix_code_list == []:
                                for choice in stmt_choices:
                                    fix_code_list.append(choice)
                            else:
                                this_new_fix_code_list = []
                                for item in fix_code_list:
                                    for choice in stmt_choices:
                                        this_item = copy.deepcopy(item)
                                        if stmt_choices_id > 0 and fix_code_choices_list[stmt_choices_id-1] and (fix_code_choices_list[stmt_choices_id-1][0].startswith('for') or fix_code_choices_list[stmt_choices_id-1][0].startswith('while') or fix_code_choices_list[stmt_choices_id-1][0].startswith('if')):
                                            this_item += '{\n    ' + choice
                                        else:
                                            this_item += '\n' + choice
                                        this_new_fix_code_list.append(this_item)
                                fix_code_list = copy.deepcopy(this_new_fix_code_list)
                        fix_code_lists.append(fix_code_list)
                    sort_fix_codes_dict = {}
                    for fix_code_list_id, fix_code_list in enumerate(fix_code_lists):
                        sort_fix_code_lists = []
                        sort_fix_codes = []
                        for fix_code_list_item in fix_code_list:
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
                                this_fix_code_list = copy.deepcopy(fix_code_list_item)
                                if ' ' in this_fix_code_list:
                                    this_fix_code_list = fix_code_list_item.replace(' ', '')
                                BLEUscore = nltk.translate.bleu_score.sentence_bleu([trans_FL_code], this_fix_code_list, weights=(0.5, 0.5))
                                del trans_FL_code
                                del this_fix_code_list
                            else:
                                score = 0
                                score += fix_code_list_item.count('long long')
                                score += fix_code_list_item.count('mpz_class') * 2
                                score += fix_code_list_item.count('__int128') * 2
                                score += fix_code_list_item.count('{0}')
                                score += fix_code_list_item.count(', 0)')
                                score += fix_code_list_item.count('=')
                                score += fix_code_list_item.count('tmp_')
                                score += fix_code_list_item.count('\n') * 2
                                score -= fix_code_list_item.count('const') * 2
                                this_source_FL_codes = copy.deepcopy(source_FL_codes)
                                if ' ' in this_source_FL_codes:
                                    this_source_FL_codes = this_source_FL_codes.replace(' ', '')
                                this_fix_code_list = copy.deepcopy(fix_code_list_item)
                                if ' ' in this_fix_code_list:
                                    this_fix_code_list = fix_code_list_item.replace(' ', '')
                                BLEUscore = nltk.translate.bleu_score.sentence_bleu(this_source_FL_codes, this_fix_code_list, weights=(0.5, 0.5))
                                if BLEUscore > 0.6:
                                    score = 100
                                del this_source_FL_codes
                                del this_fix_code_list
                            if fix_code_list_item not in sort_fix_codes:
                                sort_fix_codes.append(fix_code_list_item)
                                sort_fix_code_lists.append([score, BLEUscore, fix_code_list_item])
                        sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[2])
                        sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[1], reverse=True)
                        sort_fix_code_lists = sorted(sort_fix_code_lists, key=lambda x: x[0], reverse=True)
                        sort_fix_codes_dict[fix_code_list_id] = sort_fix_code_lists[:]
                new_fix_code_set = set()
                new_fix_code_list = []
                pre_new_fix_code_list= [1]
                while len(pre_new_fix_code_list) != len(new_fix_code_list):
                    pre_new_fix_code_list = new_fix_code_list[:]
                    for this_k, this_v in sort_fix_codes_dict.items():
                        for this_this_v in this_v:
                            if this_this_v[2] not in new_fix_code_set:
                                new_fix_code_set.add(this_this_v[2])
                                new_fix_code_list.append(this_this_v[2])
                                break
                for fix_code_str in new_fix_code_list:
                    all_fix_code_str = copy.copy(fix_code_str)
                    for trans_line in trans_lines:
                        if '// Patch' in trans_line:
                            all_fix_code_str += trans_line
                    while '// Patch' in fix_code_str:
                        fix_code_str = fix_code_str.replace('// Patch', '')
                    while 'long long long long' in fix_code_str:
                        fix_code_str = fix_code_str.replace('long long long long', 'long long')
                    while 'mpz_class mpz_class' in fix_code_str:
                        fix_code_str = fix_code_str.replace('mpz_class mpz_class', 'mpz_class')
                    if new_code_id > 230:
                        break
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
                    if_if_have_bracket = False
                    if len(this_line2pos[-1]) == 1 and new_code_lines[this_line2pos[-1][0][0]][this_line2pos[-1][0][1]] == '}':
                        for this_this_line2pos in this_line2pos[:-1]:
                            for pos in reversed(this_this_line2pos):
                                if new_code_lines[pos[0]][pos[1]] == '{':
                                    if_if_have_bracket = True
                                new_code_lines[pos[0]] = new_code_lines[pos[0]][:pos[1]] + new_code_lines[pos[0]][pos[1]+1:]
                        replace_pos = this_line2pos[-2][0][:]
                    elif fix_code_str.startswith('if'):
                        for this_this_line2pos in this_line2pos[:1]:
                            for pos in reversed(this_this_line2pos):
                                if new_code_lines[pos[0]][pos[1]] == '{':
                                    if_if_have_bracket = True
                                new_code_lines[pos[0]] = new_code_lines[pos[0]][:pos[1]] + new_code_lines[pos[0]][pos[1]+1:]
                        replace_pos = this_line2pos[0][0][:]
                    else:
                        for this_this_line2pos in this_line2pos[:]:
                            for pos in reversed(this_this_line2pos):
                                if new_code_lines[pos[0]][pos[1]] == '{':
                                    if_if_have_bracket = True
                                new_code_lines[pos[0]] = new_code_lines[pos[0]][:pos[1]] + new_code_lines[pos[0]][pos[1]+1:]
                        replace_pos = this_line2pos[-1][0][:]
                    if fix_code_str.strip().startswith('for') and fix_code_str.count(';') == 2 and len(this_line2pos) >= 3:
                        new_code_lines[this_line2pos[0][0][0]] = new_code_lines[this_line2pos[0][0][0]][:this_line2pos[0][0][1]] + fix_code_str.split(';')[0].strip()+';' + ' ' + new_code_lines[this_line2pos[0][0][0]][this_line2pos[0][0][1]:]
                        new_code_lines[this_line2pos[1][0][0]] = new_code_lines[this_line2pos[1][0][0]][:this_line2pos[1][0][1]] + fix_code_str.split(';')[1].strip()+';' + ' ' + new_code_lines[this_line2pos[1][0][0]][this_line2pos[1][0][1]:]
                        if len(this_line2pos) == 3:
                            new_code_lines[this_line2pos[2][0][0]] = new_code_lines[this_line2pos[2][0][0]][:this_line2pos[2][0][1]] + fix_code_str.split(';')[2].strip() + ' ' + new_code_lines[this_line2pos[2][0][0]][this_line2pos[2][0][1]:]
                        else:
                            new_code_lines[this_line2pos[2][0][0]] = new_code_lines[this_line2pos[2][0][0]][:this_line2pos[2][0][1]] + fix_code_str.split(';')[2].strip() + ' {' + new_code_lines[this_line2pos[2][0][0]][this_line2pos[2][0][1]:]
                    elif fix_code_str.strip().startswith('for') and fix_code_str.count(';') == 3 and len(this_line2pos) >= 3:
                        new_code_lines[this_line2pos[0][0][0]] = new_code_lines[this_line2pos[0][0][0]][:this_line2pos[0][0][1]] + fix_code_str.split(';')[0].strip()+';' + ' ' + new_code_lines[this_line2pos[0][0][0]][this_line2pos[0][0][1]:]
                        new_code_lines[this_line2pos[1][0][0]] = new_code_lines[this_line2pos[1][0][0]][:this_line2pos[1][0][1]] + fix_code_str.split(';')[1].strip()+';' + ' ' + new_code_lines[this_line2pos[1][0][0]][this_line2pos[1][0][1]:]
                        new_code_lines[this_line2pos[2][0][0]] = new_code_lines[this_line2pos[2][0][0]][:this_line2pos[2][0][1]] + fix_code_str.split(';')[2].strip() + '; ' + new_code_lines[this_line2pos[2][0][0]][this_line2pos[2][0][1]:]
                    elif new_code_lines[replace_pos[0]][replace_pos[1]:].strip() != '' and not new_code_lines[replace_pos[0]][replace_pos[1]:].strip().startswith('\\'):
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                    else:
                        if fix_code_str.strip().endswith(';') or fix_code_str.strip().endswith('{'):
                            new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                        else:
                            if not if_if_have_bracket and fix_code_str.startswith('if'):
                                new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                            elif not if_if_have_bracket and 'tmp_' in fix_code_str:
                                new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' ' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                            else:
                                new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:replace_pos[1]] + fix_code_str + ' {' + new_code_lines[replace_pos[0]][replace_pos[1]:]
                    if new_code_lines[replace_pos[0]][-1] == '\n':
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]][:-1] + ' // Patch' + new_code_lines[replace_pos[0]][-1]
                    else:
                        new_code_lines[replace_pos[0]] = new_code_lines[replace_pos[0]] + ' // Patch'

                    if fix_code_str.strip().startswith('for') and fix_code_str.count(';') >= 2 and len(this_line2pos) >= 3:
                        for this_this_line2pos in this_line2pos[:2]:
                            if new_code_lines[this_this_line2pos[0][0]][-1] == '\n':
                                new_code_lines[this_this_line2pos[0][0]] = new_code_lines[this_this_line2pos[0][0]][:-1] + ' // Patch' + new_code_lines[this_this_line2pos[0][0]][-1]
                            else:
                                new_code_lines[this_this_line2pos[0][0]] = new_code_lines[this_this_line2pos[0][0]] + ' // Patch'
                    for new_code_line_id, new_code_line in enumerate(new_code_lines):
                        if '{\n    ' in new_code_line and '// Patch' in new_code_line:
                            new_code_lines[new_code_line_id] = new_code_lines[new_code_line_id].replace('{\n    ', '{ //Patch\n    ')
                    for item in for_without_dec:
                        this_next_line = new_code_lines[item[2]]
                        this_index = ''
                        for this_char in this_next_line:
                            if this_char == ' ':
                                this_index += ' '
                            else:
                                break
                        new_code_lines.insert(item[2], f'{this_index}{item[1]} --;\n')
                    if 'sort' in all_fix_code_str or '.size()' in all_fix_code_str or '.begin()' in all_fix_code_str or '.end()' in all_fix_code_str:
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
                                elif f'int {this_use_var} [ ]' in first_line:
                                    first_line = first_line.replace(f'int {this_use_var} []', f'vector<int> {this_use_var}')
                                elif f'int *{this_use_var}' in first_line:
                                    first_line = first_line.replace(f'int *{this_use_var}', f'vector<int> {this_use_var}')
                                elif f'int* {this_use_var}' in first_line:
                                    first_line = first_line.replace(f'int* {this_use_var}', f'vector<int> {this_use_var}')
                                elif f'int * {this_use_var}' in first_line:
                                    first_line = first_line.replace(f'int * {this_use_var}', f'vector<int> {this_use_var}')
                        new_code_lines[0] = first_line
                        f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                        print(''.join(new_code_lines), file=f_out)
                        f_out.close()
                        new_code_id += 1
                        all_new_code_id += 1
                    else:
                        if 'long long' in all_fix_code_str:
                            first_line = new_code_lines[0]
                            first_line_items = first_line.split('f_filled')
                            return_type = first_line_items[0].strip()
                            if return_type in ['int']:
                                new_new_code_lines = new_code_lines[:]
                                func_def_line = first_line_items[1]
                                func_def_line = func_def_line.replace("int", "long long")
                                new_new_code_lines[0] = f'long long f_filled{func_def_line}'
                                f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                                print(''.join(new_new_code_lines), file=f_out)
                                f_out.close()
                                new_code_id += 1
                                all_new_code_id += 1
                        elif 'mpz_class' in all_fix_code_str:
                            first_line = new_code_lines[0]
                            first_line_items = first_line.split('f_filled')
                            return_type = first_line_items[0].strip()
                            if return_type in ['int', 'long long']:
                                new_new_code_lines = new_code_lines[:]
                                new_new_code_lines[0] = f'mpz_class f_filled{first_line_items[1]}'
                                f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                                print(''.join(new_new_code_lines), file=f_out)
                                f_out.close()
                                new_code_id += 1
                                all_new_code_id += 1
                        elif '__int128' in all_fix_code_str:
                            first_line = new_code_lines[0]
                            first_line_items = first_line.split('f_filled')
                            return_type = first_line_items[0].strip()
                            if return_type in ['int', 'long long']:
                                new_new_code_lines = new_code_lines[:]
                                new_new_code_lines[0] = f'__int128 f_filled{first_line_items[1]}'
                                f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                                print(''.join(new_new_code_lines), file=f_out)
                                f_out.close()
                                new_code_id += 1
                                all_new_code_id += 1
                        f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                        print(''.join(new_code_lines), file=f_out)
                        f_out.close()
                        new_code_id += 1
                        all_new_code_id += 1
                new_code_lines = copy.deepcopy(trans_lines)
                for FL_trans_line_id in FL_trans_line_ids:
                    new_code_lines[FL_trans_line_id] = new_code_lines[FL_trans_line_id][:-1] + '// Patch\n'
                f_out = open(f'{save_fixcode_dir}/{ID}/{all_new_code_id}.{target_ext}', 'w')
                print(''.join(new_code_lines), file=f_out)
                f_out.close()
                new_code_id += 1
                all_new_code_id += 1
    return None, None, None, None


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
        "--target_model_name",
        default='TransCoder',
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
        "--path_to_map",
        default='RulER_map',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_stmtmap",
        default='RulER_stmtmap',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_code",
        default='/home/ubuntu/RulER/DATABASE/DATA/CODE',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_fixcode",
        default='Fix_Code',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_DATABASE",
        default='/home/ubuntu/RulER/DATABASE',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_unmapped_stmt",
        default='RulER_unmapped_stmt',
        type=str,
        required=True,
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
    path_to_unmapped_stmt = args.path_to_unmapped_stmt
    count_right, count_wrong, count_right_B, count_wrong_B = run(path_to_map, path_to_stmtmap, path_to_code, path_to_DATABASE, path_to_fixcode, target_model_name, source_lang, target_lang, model_name, path_to_unmapped_stmt)

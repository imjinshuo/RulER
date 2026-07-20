import os.path

from utils import *
import argparse


def run(path_to_map, path_to_unmapped_stmt, path_to_save_FL, path_to_label, path_to_code, target_model_name, source_lang, target_lang):
    generated_map = loadMap(f'{path_to_map}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')
    save_FL_dir = f'{path_to_save_FL}/{target_model_name}/{source_lang}-{target_lang}'
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

    code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}'
    transcode_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}'
    script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace'
    script_files = os.listdir(script_dir)

    IDs = [file.split('.')[0] for file in script_files]
    IDs.sort()
    sum = 0
    Correct_FL = 0
    Correct_FL_CODE = 0
    Correct_FL_LeetCode = 0
    Correct_FL_CTCI = 0
    Wrong_FL = 0
    Wrong_FL_CODE = 0
    Wrong_FL_LeetCode = 0
    Wrong_FL_CTCI = 0
    miss_FL = 0
    miss_FL_CODE = 0
    miss_FL_LeetCode = 0
    miss_FL_CTCI = 0
    all_FL_case_count = 0
    all_FL_case_count_CODE = 0
    all_FL_case_count_LeetCode = 0
    all_FL_case_count_CTCI = 0
    for ID in IDs:
        unmapped_stmts = []
        if os.path.exists(f'{path_to_unmapped_stmt}/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt'):
            unmapped_stmt_lines = open(f'{path_to_unmapped_stmt}/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt').readlines()
            for unmapped_stmt_line in unmapped_stmt_lines:
                if unmapped_stmt_line.strip():
                    unmapped_stmts.append(int(unmapped_stmt_line.strip()))

        all_FL_case_count += 1
        if ID.startswith('CTCI_'):
            all_FL_case_count_CTCI += 1
        elif ID.isdigit():
            all_FL_case_count_LeetCode += 1
        else:
            all_FL_case_count_CODE += 1
        sum += 1

        if ID not in generated_map:
            Wrong_FL += 1
            if ID.startswith('CTCI_'):
                Wrong_FL_CTCI += 1
            elif ID.isdigit():
                Wrong_FL_LeetCode += 1
            else:
                Wrong_FL_CODE += 1
            miss_FL += 1
            if ID.startswith('CTCI_'):
                miss_FL_CTCI += 1
            elif ID.isdigit():
                miss_FL_LeetCode += 1
            else:
                miss_FL_CODE += 1
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

        trans_predecessors, trans_successors, trans_stmt_use_consts, trans_stmt_def_variables, trans_stmt_use_variables, trans_line_def_variables = parse_vari_dep(
            trans_stmt_list, trans_lines, trans_stmt_list_pos, target_lang, this_trans_trees)

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

        source_traces = load_trace(
            f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
        trans_traces = load_trace(
            f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')
        report_id, _ = compare_stepbystep(source_traces, trans_traces, source_lang, target_lang, line_M, len(source_lines), len(trans_lines), source_lines, trans_lines, trans_line_def_variables, fixed_lines)

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

        f_fl = open(f'{save_FL_dir}/{ID}.txt', 'w')
        print(report_id, file=f_fl)
        f_fl.close()

        if report_id in ID2label[ID]:
            Correct_FL += 1
            if ID.startswith('CTCI_'):
                Correct_FL_CTCI += 1
            elif ID.isdigit():
                Correct_FL_LeetCode += 1
            else:
                Correct_FL_CODE += 1
        else:
            Wrong_FL += 1
            if ID.startswith('CTCI_'):
                Wrong_FL_CTCI += 1
            elif ID.isdigit():
                Wrong_FL_LeetCode += 1
            else:
                Wrong_FL_CODE += 1

    print(f'{target_model_name}-{source_lang}-{target_lang}')
    print('ALL: ', all_FL_case_count)
    print('Correct_FL: ', Correct_FL)
    print('S_FL', round(Correct_FL/(Correct_FL+Wrong_FL), 3))
    print('CODE-ALL: ', all_FL_case_count_CODE)
    print('CODE-Correct_FL: ', Correct_FL_CODE)
    print('CODE-S_FL', round(Correct_FL_CODE/(Correct_FL_CODE+Wrong_FL_CODE), 3))
    print('LEET-ALL: ', all_FL_case_count_LeetCode)
    print('LEET-Correct_FL: ', Correct_FL_LeetCode)
    print('LEET-S_FL', round(Correct_FL_LeetCode/(Correct_FL_LeetCode+Wrong_FL_LeetCode), 3))
    print('CTCI-ALL: ', all_FL_case_count_CTCI)
    print('CTCI-Correct_FL: ', Correct_FL_CTCI)
    print('CTCI-S_FL', round(Correct_FL_CTCI/(Correct_FL_CTCI+Wrong_FL_CTCI), 3))
    print('')
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
        "--path_to_map",
        default='RulER_map',
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
    parser.add_argument(
        "--path_to_save_FL",
        default='RulER_FL',
        type=str,
        required=True,
        help=""
    )
    parser.add_argument(
        "--path_to_label",
        default='/home/ubuntu/RulER/DATABASE/DATA/BUG',
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
    args = parser.parse_args()
    source_lang = args.source_lang
    target_lang = args.target_lang
    target_model_name = args.target_model_name
    path_to_map = args.path_to_map
    path_to_unmapped_stmt = args.path_to_unmapped_stmt
    path_to_save_FL = args.path_to_save_FL
    path_to_label = args.path_to_label
    path_to_code = args.path_to_code
    count_right, count_wrong, count_right_B, count_wrong_B = run(path_to_map, path_to_unmapped_stmt, path_to_save_FL, path_to_label, path_to_code, target_model_name, source_lang, target_lang)

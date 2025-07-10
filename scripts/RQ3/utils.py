import os
import json
import random
import shutil
import statistics
import string

from tree_sitter import Language, Parser, Node
import tree_sitter
import copy
from tqdm import tqdm, trange
import itertools
import pickle
import re
import time
import nltk
import Levenshtein

punc = string.punctuation


CPP_LANGUAGE = Language("build/cpp.so", "cpp")
Python_LANGUAGE = Language("build/python.so", "python")
Java_LANGUAGE = Language("build/java.so", "java")
CPP_parser = Parser()
CPP_parser.set_language(CPP_LANGUAGE)
Python_parser = Parser()
Python_parser.set_language(Python_LANGUAGE)
Java_parser = Parser()
Java_parser.set_language(Java_LANGUAGE)


python_block_name = ['block', 'elif_clause', 'else_clause', 'except_clause']
java_block_name = ['block', 'elif_clause', 'else_clause', 'catch_clause']
cpp_block_name = ['compound_statement', 'elif_clause', 'else_clause', 'catch_clause']


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


# def traverse_tree_unnamed_node(node, record):
#     for n in node.children:
#         if n.is_named is False:
#             record.extend(n.text)
#         traverse_tree_unnamed_node(n, record)


def mytree2text(mytree, code_str):
    if mytree.children == []:
        if code_str:
            code_str = code_str + ' ' + mytree.text
        else:
            code_str = code_str + mytree.text
    elif mytree.type.startswith('string'):
        for child_id, child in enumerate(mytree.children):
            if child_id == 0:
                code_str = code_str + ' ' + child.text
            else:
                code_str = code_str + child.text
    else:
        for child in mytree.children:
            if child.type not in ['block', 'compound_statement', 'else', 'else_clause']:
                code_str = mytree2text(child, code_str)
    return code_str


def check_punc(str1):
    if_punc = True
    for char in str1:
        if char not in punc:
            if_punc = False
    if str1 in ['=', '==']:
        if_punc = False
    return if_punc


def template_add_str(str1, str2, if_start=False, pretoken=''):
    if_punc = check_punc(str2)
    if_prepunc = check_punc(pretoken)
    if pretoken in [',', ';', '=', '==', 'if', 'for', 'while', 'try', 'catch', 'switch']:
        str1 += ' ' + str2
    elif if_punc == False and pretoken in ['>', ')', ']', '}']:
        str1 += ' ' + str2
    elif str1 == '' or if_start or if_punc or if_prepunc:
        str1 += str2
    else:
        str1 += ' ' + str2
    pretoken = str2
    return str1, pretoken


cpp_predefined_identifiers = ['greater', 'vector']
def node_type_transfer_for_template(mytree, lang, var_dict, number_dict, type_dict):
    node_types = node_type_transfer(lang, mytree.type, mytree.text, mytree.variable_names)
    this_type = node_types[0]
    if this_type in ['sized_type_specifier-0', 'primitive_type-0', 'primitive_type-1', 'primitive_type-2', 'primitive_type-3', 'primitive_type-4', 'primitive_type-6', 'primitive_type-7', 'integral_type-0', 'floating_point_type-0']:
        type_dict.append(mytree.text)
        this_type = '<type_' + str(len(type_dict)) + '>'
    elif this_type in ['identifier-0', 'type_identifier-0'] and mytree.text not in cpp_predefined_identifiers:
        # if mytree.text not in var_dict:
        #     var_dict.append(mytree.text)
        var_dict.append(mytree.text)
        # this_type = '<variable_' + str(var_dict.index(mytree.text) + 1) +'>'
        this_type = '<variable_' + str(len(var_dict)) +'>'
    elif this_type.startswith('number_literal'):
        # if mytree.text not in number_dict:
        #     number_dict.append(mytree.text)
        number_dict.append(mytree.text)
        # this_type = '<constant_' + str(number_dict.index(mytree.text) + 1) +'>'
        this_type = '<constant_' + str(len(number_dict)) +'>'
    else:
        this_type = mytree.text
    return this_type, var_dict, number_dict, type_dict


def mytree2template(mytree, lang, code_str, var_dict, number_dict, string_dict, type_dict, pretoken):
    if 'comment' in mytree.type:
        None
    elif mytree.children == []:
        node_type, var_dict, number_dict, type_dict = node_type_transfer_for_template(mytree, lang, var_dict, number_dict, type_dict)
        code_str, pretoken = template_add_str(code_str, node_type, pretoken=pretoken)
    elif mytree.type in ['string_literal', 'char_literal']:

        if mytree.children[1].text not in string_dict:
            string_dict.append(mytree.children[1].text)
        # string_dict.append(mytree.children[1].text)
        this_string_text = '<string_' + str(string_dict.index(mytree.children[1].text) + 1) +'>'
        # this_string_text = '<string_' + str(len(string_dict)) +'>'

        # node_type, var_dict, number_dict = node_type_transfer_for_template(mytree.children[0], lang, var_dict, number_dict)
        # code_str, pretoken = template_add_str(code_str, node_type, pretoken=pretoken)
        code_str, pretoken = template_add_str(code_str, this_string_text, pretoken=pretoken)
        # node_type, var_dict, number_dict = node_type_transfer_for_template(mytree.children[0], lang, var_dict, number_dict)
        # code_str, pretoken = template_add_str(code_str, node_type, pretoken=pretoken)
    else:
        for child in mytree.children:
            if child.type not in ['block', 'compound_statement', 'else', 'elif_clause', 'else_clause', 'catch_clause', 'except_clause']:
                code_str, var_dict, number_dict, string_dict, type_dict, pretoken = mytree2template(child, lang, code_str, var_dict, number_dict, string_dict, type_dict, pretoken)
    return code_str, var_dict, number_dict, string_dict, type_dict, pretoken


def mytree2code(mytree, lang, code_str, pretoken):
    if 'comment' in mytree.type:
        None
    elif mytree.children == []:
        code_str, pretoken = template_add_str(code_str, mytree.text, pretoken=pretoken)
    elif mytree.type in ['string_literal', 'char_literal', 'string']:
        code_str, pretoken = template_add_str(code_str, mytree.text, pretoken=pretoken)
    else:
        for child in mytree.children:
            if child.type not in ['block', 'compound_statement', 'else', 'elif_clause', 'else_clause', 'catch_clause', 'except_clause']:
                code_str, pretoken = mytree2code(child, lang, code_str, pretoken)
    return code_str, pretoken


import itertools
def all_sublists(lst):
    sublists = []
    for r in range(len(lst) + 1):
        sublists.extend(itertools.combinations(lst, r))
    return [list(sublist) for sublist in sublists]


def select_variables(variables, num):
    choices = []
    if len(variables) == num:
        choices = [item for item in map(list, itertools.permutations(variables))]
    elif len(variables) > num:
        var_lists = [item for item in map(list, itertools.combinations(variables, num))]
        choices = []
        for var_list in var_lists:
            choices.extend([item for item in map(list, itertools.permutations(var_list))])
    else:
        var_lists1 = [item for item in map(list, itertools.combinations(variables, len(variables)))]
        var_lists2 = [item for item in map(list, itertools.combinations(variables, num-len(variables)))]
        var_lists = []
        for var_list1 in var_lists1:
            for var_list2 in var_lists2:
                this_var_list = var_list1[:]
                this_var_list.extend(var_list2)
                if this_var_list not in var_lists:
                    var_lists.append(this_var_list)
        choices = []
        for var_list in var_lists:
            choices.extend([item for item in map(list, itertools.permutations(var_list))])
    return choices


def repalce_variables(stmt, choice):
    for var_id, var in enumerate(choice):
        stmt = stmt.replace(f'<variable_{var_id+1}>', var)
    return stmt


def repalce_numbers(stmt, choice):
    for var_id, var in enumerate(choice):
        stmt = stmt.replace(f'<constant_{var_id+1}>', var)
    return stmt


def repalce_strings(stmt, choice):
    for var_id, var in enumerate(choice):
        stmt = stmt.replace(f'<string_{var_id+1}>', var)
    return stmt


def repalce_types(stmt, choice):
    for var_id, var in enumerate(choice):
        stmt = stmt.replace(f'<type_{var_id+1}>', var)
    return stmt


# def fill_template(stmt, var_dict, number_dict, string_dict, use_consts, use_variables, use_strings):
#     var_choices = []
#     for _ in range(len(var_dict)):
#         if var_choices == []:
#             var_choices.extend([[item] for item in use_variables])
#         else:
#             new_var_choices = []
#             for var in var_choices:
#                 for new_var in use_variables:
#                     this_var = var[:]
#                     this_var.append(new_var)
#                     new_var_choices.append(this_var)
#             var_choices = new_var_choices[:]
#     number_choices = []
#     for _ in range(len(number_dict)):
#         if number_choices == []:
#             number_choices.extend([[item] for item in use_consts])
#         else:
#             new_number_choices = []
#             for number in number_choices:
#                 for new_number in use_consts:
#                     this_number = number[:]
#                     this_number.append(new_number)
#                     new_number_choices.append(this_number)
#             number_choices = new_number_choices[:]
#     string_choices = []
#     for _ in range(len(string_dict)):
#         if string_choices == []:
#             string_choices.extend([[item] for item in use_strings])
#         else:
#             new_string_choices = []
#             for string in string_choices:
#                 for new_string in use_strings:
#                     this_string = string[:]
#                     this_string.append(new_string)
#                     new_string_choices.append(this_string)
#             string_choices = new_string_choices[:]
#     stmts1 = []
#     if var_dict:
#         for choice in var_choices:
#             this_stmt = repalce_variables(stmt, choice)
#             stmts1.append(this_stmt)
#     else:
#         stmts1.append(stmt)
#     stmts2 = []
#     if number_dict:
#         for choice in number_choices:
#             for stmt in stmts1:
#                 this_stmt = repalce_numbers(stmt, choice)
#                 stmts2.append(this_stmt)
#     else:
#         stmts2.extend(stmts1)
#     stmts3 = []
#     if string_dict:
#         for choice in string_choices:
#             for stmt in stmts2:
#                 this_stmt = repalce_strings(stmt, choice)
#                 stmts3.append(this_stmt)
#     else:
#         stmts3.extend(stmts2)
#     return stmts3


def update_var(stmt, stmt_var, stmt_type, use_variables, use_consts, use_strings, use_types, source_lang):
    if stmt_type in ['declaration']:
        if '0' not in use_consts and 'int' in use_types:
            use_consts.append('0')
        if 'false' not in use_consts and 'bool' in use_types:
            use_consts.append('false')
        if '0.0' not in use_consts and 'double' in use_types:
            use_consts.append('0.0')
    if 'long long' not in use_types:
        use_types.append('long long')
    if '__int128' not in use_types and source_lang == 'Python':
        use_types.append('__int128')
    if 'static_cast' in stmt_var and 'static_cast' not in use_variables:
        use_variables.append('static_cast')
    return use_variables, use_consts, use_strings, use_types


def fill_template(stmt, var_dict, number_dict, string_dict, type_dict, stmt_type, ori_use_variables, ori_use_consts, ori_use_strings, ori_use_types,
                  source_use_variables, trans_use_variables, source_use_consts, trans_use_consts, source_use_strings, trans_use_strings, source_lang, average_len=1000000, source_FL_code=''):
    ori_use_types.extend(type_dict)
    ori_use_types = list(set(ori_use_types))
    same_variables = []
    if len(source_use_variables) == len(trans_use_variables):
        for var1, var2 in zip(source_use_variables, trans_use_variables):
            if var1 == var2:
                same_variables.append(var1)
            else:
                same_variables.append(None)
    same_consts = []
    if len(source_use_consts) == len(trans_use_consts):
        for var1, var2 in zip(source_use_consts, trans_use_consts):
            if var1 == var2:
                same_consts.append(var1)
            else:
                same_consts.append(None)

    use_variables, use_consts, use_strings, use_types = update_var(stmt, var_dict, stmt_type, ori_use_variables[:], ori_use_consts[:], ori_use_strings[:], ori_use_types[:], source_lang)
    # var_choices = select_variables(use_variables, len(var_dict))
    var_choices = []
    for _ in range(len(var_dict)):
        if var_choices == []:
            var_choices.extend([[item] for item in use_variables])
        else:
            new_var_choices = []
            for var in var_choices:
                for new_var in use_variables:
                    this_var = var[:]
                    this_var.append(new_var)
                    new_var_choices.append(this_var)
            var_choices = new_var_choices[:]
    if 'static_cast' in use_variables:
        var_choices = [var_choice for var_choice in var_choices if 'static_cast' in var_choice]
    const_choices = []
    for _ in range(len(number_dict)):
        if const_choices == []:
            const_choices.extend([[item] for item in use_consts])
        else:
            new_number_choices = []
            for number in const_choices:
                for new_number in use_consts:
                    this_number = number[:]
                    this_number.append(new_number)
                    new_number_choices.append(this_number)
            const_choices = new_number_choices[:]
    type_choices = []
    for _ in range(len(type_dict)):
        if type_choices == []:
            type_choices.extend([[item] for item in use_types])
        else:
            new_type_choices = []
            for type in type_choices:
                for new_type in use_types:
                    this_type = type[:]
                    this_type.append(new_type)
                    new_type_choices.append(this_type)
            type_choices = new_type_choices[:]
    new_type_choices = []
    if 'long long' in ori_use_types or '__int128' in ori_use_types:
        new_type_choices = type_choices[:]
    else:
        for type_choice in type_choices:
            if 'long long' in type_choice and '__int128' in type_choice:
                continue
            new_type_choices.append(type_choice)
    new_new_type_choices = []
    for type_choice in new_type_choices:
        if type_choice and 'long long' in type_choice and type_choice[0] != 'long long':
            continue
        if type_choice and '__int128' in type_choice and type_choice[0] != '__int128':
            continue
        new_new_type_choices.append(type_choice)

    type_choice = new_new_type_choices[:]

    new_var_choices = []
    if len(source_use_variables) == len(trans_use_variables) and same_variables != [None for _ in range(len(source_use_variables))]:
        for choice in var_choices:
            if_valid = True
            for item1, item2 in zip(same_variables, choice):
                if item1 != None and item1 != item2:
                    if_valid = False
                    break
            if if_valid:
                new_var_choices.append(choice)
    else:
        new_var_choices = var_choices[:]

    # new_const_choices = []
    # if len(source_use_consts) == len(trans_use_consts) and same_consts != [None for _ in range(len(source_use_consts))]:
    #     for choice in const_choices:
    #         if_valid = True
    #         for item1, item2 in zip(same_consts, choice):
    #             if item1 != None and item1 != item2:
    #                 if_valid = False
    #                 break
    #         if if_valid:
    #             new_const_choices.append(choice)
    # else:
    #     new_const_choices = const_choices[:]

    string_choices = select_variables(use_strings, len(string_dict))
    stmts1 = []
    if var_dict:
        for choice in new_var_choices:
            this_stmt = repalce_variables(stmt, choice)
            if_invalid = False
            for var in use_variables:
                if f'{var}<{var}' in this_stmt or f'{var}>{var}' in this_stmt or f'{var}<={var}' in this_stmt or f'{var}>={var}' in this_stmt:
                    if_invalid = True
            if not if_invalid:
                stmts1.append(this_stmt)
    else:
        stmts1.append(stmt)
    stmts2 = []
    if number_dict:
        for choice in const_choices:
            for stmt in stmts1:
                this_stmt = repalce_numbers(stmt, choice)
                # if this_stmt.endswith('= {1};') or this_stmt.endswith('={1};'):
                #     continue
                stmts2.append(this_stmt)
    else:
        stmts2.extend(stmts1)
    stmts3 = []
    if string_dict:
        for choice in string_choices:
            for stmt in stmts2:
                this_stmt = repalce_strings(stmt, choice)
                stmts3.append(this_stmt)
    else:
        stmts3.extend(stmts2)
    stmts4 = []
    if type_dict:
        for choice in type_choice:
            for stmt in stmts3:
                if 'false' in stmt and 'long long' in choice:
                    continue
                this_stmt = repalce_types(stmt, choice)
                stmts4.append(this_stmt)
    else:
        stmts4.extend(stmts3)
    if len(stmts4) > average_len:
        sim_choice_pairs = []
        for stmt in stmts4:
            score = 0
            score += stmt.count('long long')
            score += stmt.count('__int128') * 2
            score += stmt.count('{0}')
            score += stmt.count(', 0)')
            score += stmt.count('=')
            # same_nodes = [node for node in ori_nodes if node in choice_nodes]
            BLEUscore = nltk.translate.bleu_score.sentence_bleu([source_FL_code], stmt, weights=(0.5, 0.5))
            sim_choice_pairs.append([score, BLEUscore, stmt])
        # sim_choice_pairs.sort(reverse=True)
        sim_choice_pairs = sorted(sim_choice_pairs, key=lambda x: x[1], reverse=True)
        sim_choice_pairs = sorted(sim_choice_pairs, key=lambda x: x[0], reverse=True)
        stmts4 = [item[2] for item in sim_choice_pairs[:average_len]]
    return stmts4


def change_format(this_template, stmt, indent, FL_source_depth, FL_source_stmt, FL_trans_stmt):
    if FL_source_stmt.startswith('parenthesized_expression'):
        if FL_trans_stmt.startswith('if_statement'):
            if this_template.startswith('('):
                this_template = 'if ' + this_template
    this_template = indent * FL_source_depth + this_template
    # if stmt.type in ['if_statement', 'for_statement', 'while_statement']:
    #     this_template = this_template + ' {'
    return this_template


def preprocess_funclines(func_lines, lang):
    if lang == 'C++':
        func_name = ''
        trans_code_lines = []
        for line_id, line in enumerate(func_lines):
            if line:
                if not trans_code_lines:
                    this_line_items = line.strip().split('(')
                    func_name = this_line_items[0].strip().split(' ')[-1].strip()
                this_line = line.replace(func_name, 'f_filled')
                trans_code_lines.append(this_line)
        return trans_code_lines
    elif lang == 'Python':
        func_name = ''
        trans_code_lines = []
        for line_id, line in enumerate(func_lines):
            if line:
                if not trans_code_lines:
                    this_line_items = line.strip().split('(')
                    func_name = this_line_items[0].strip().split(' ')[-1].strip()
                this_line = line.replace(func_name, 'f_filled')
                trans_code_lines.append(this_line)
        return trans_code_lines
    elif lang == 'Java':
        func_name = ''
        trans_code_lines = []
        if 'class' in func_lines[0]:
            this_func_lines = func_lines[1:]
            index_len = 0
            for char in func_lines[1]:
                if char == ' ':
                    index_len += 1
                else:
                    break
            index_str = ''
            for i in range(index_len):
                index_str += ' '
        else:
            this_func_lines = func_lines[:]
            index_len = 0
            for char in func_lines[0]:
                if char == ' ':
                    index_len += 1
                else:
                    break
            index_str = ''
            for i in range(index_len):
                index_str += ' '
        for line_id, line in enumerate(this_func_lines):
            if line:
                if line.startswith(index_str):
                    line = line[len(index_str):]
                if not trans_code_lines:
                    this_line_items = line.strip().split('(')
                    func_name = this_line_items[0].strip().split(' ')[-1].strip()
                this_line = line.replace(func_name, 'f_filled')
                if not trans_code_lines:
                    if 'static' not in line:
                        if 'public' in line:
                            this_line = this_line.replace('public ', 'public static ')
                        else:
                            this_line = 'static ' + this_line
                trans_code_lines.append(this_line)
                if this_line.startswith('}'):
                    break
        if trans_code_lines[-1] in ['}\n', '}'] and trans_code_lines[-2] != '}\n':
            return trans_code_lines[:]
        if trans_code_lines[-1] in ['}\n', '}'] and trans_code_lines[-2] == '}\n':
            return trans_code_lines[:-1]
        elif '}\n' in trans_code_lines:
            return trans_code_lines[:trans_code_lines.index('}\n')+1]
        elif '}' in trans_code_lines:
            return trans_code_lines[:trans_code_lines.index('}')+1]
        else:
            return trans_code_lines


def traverse_tree_unnamed_node_with_path(node, path, unvisited_path, record):
    if node.is_named is False:
        record.append(node.type)
    for n_id, n in enumerate(node.children):
        this_path = path[:]
        this_path.append(n_id)
        if this_path == unvisited_path:
            continue
        if n.is_named is False:
            record.append(n.type)
        else:
            traverse_tree_unnamed_node_with_path(n, this_path, unvisited_path, record)


# def check_unnamed_nodes_for_single_diff(target_tree1, target_tree2, target_diff_child1, target_diff_child2, source_diff_child1, source_diff_child2):
#     target_tree1_unnamed_list = []
#     traverse_tree_unnamed_node(target_tree1, target_tree1_unnamed_list)
#     target_tree2_unnamed_list = []
#     traverse_tree_unnamed_node(target_tree2, target_tree2_unnamed_list)
#
#     target_tree_child1_unnamed_list = []
#     traverse_tree_unnamed_node(target_diff_child1, target_tree_child1_unnamed_list)
#     target_tree_child2_unnamed_list = []
#     traverse_tree_unnamed_node(target_diff_child2, target_tree_child2_unnamed_list)
#
#     source_tree_child1_unnamed_list = []
#     traverse_tree_unnamed_node(source_diff_child1, source_tree_child1_unnamed_list)
#     source_tree_child2_unnamed_list = []
#     traverse_tree_unnamed_node(source_diff_child2, source_tree_child2_unnamed_list)
#
#     source_tree_child1_unnamed_list.sort()
#     source_tree_child2_unnamed_list.sort()
#     target_tree_child1_unnamed_list.sort()
#     target_tree_child2_unnamed_list.sort()
#     if source_tree_child1_unnamed_list == source_tree_child2_unnamed_list:
#         if target_tree_child1_unnamed_list != target_tree_child2_unnamed_list:
#             return False
#     if target_tree_child1_unnamed_list == target_tree_child2_unnamed_list:
#         if source_tree_child1_unnamed_list != source_tree_child2_unnamed_list:
#             return False
#
#     delete_target_tree1_unnamed_list = copy.deepcopy(target_tree1_unnamed_list)
#     for item in target_tree_child1_unnamed_list:
#         if item in delete_target_tree1_unnamed_list:
#             delete_target_tree1_unnamed_list.remove(item)
#     delete_target_tree2_unnamed_list = copy.deepcopy(target_tree2_unnamed_list)
#     for item in target_tree_child2_unnamed_list:
#         if item in delete_target_tree2_unnamed_list:
#             delete_target_tree2_unnamed_list.remove(item)
#     if delete_target_tree1_unnamed_list == delete_target_tree2_unnamed_list:
#         return True
#     else:
#         return False


# def check_unnamed_nodes_for_multi_diff(target_tree1, target_tree2, source_tree1, source_tree2, target_diff_child1, target_diff_child2, source_diff_child1, source_diff_child2, source_diff1, trans_diff1):
#     target_unvisited_path = [diff[0] for diff in trans_diff1]
#     source_unvisited_path = [diff[0] for diff in source_diff1]
#
#     target_tree1_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(target_tree1, [], target_unvisited_path, target_tree1_unnamed_list)
#     target_tree2_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(target_tree2, [], target_unvisited_path, target_tree2_unnamed_list)
#
#     source_tree1_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(source_tree1, [], source_unvisited_path, source_tree1_unnamed_list)
#     source_tree2_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(source_tree2, [], source_unvisited_path, source_tree2_unnamed_list)
#
#     target_tree_child1_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(target_diff_child1, [], [], target_tree_child1_unnamed_list)
#     target_tree_child2_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(target_diff_child2, [], [], target_tree_child2_unnamed_list)
#
#     source_tree_child1_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(source_diff_child1, [], [], source_tree_child1_unnamed_list)
#     source_tree_child2_unnamed_list = []
#     traverse_tree_unnamed_node_with_path(source_diff_child2, [], [], source_tree_child2_unnamed_list)
#
#     target_tree1_unnamed_list.sort()
#     target_tree2_unnamed_list.sort()
#     source_tree1_unnamed_list.sort()
#     source_tree2_unnamed_list.sort()
#     source_tree_child1_unnamed_list.sort()
#     source_tree_child2_unnamed_list.sort()
#     target_tree_child1_unnamed_list.sort()
#     target_tree_child2_unnamed_list.sort()
#
#     if source_tree_child1_unnamed_list == source_tree_child2_unnamed_list:
#         if target_tree_child1_unnamed_list != target_tree_child2_unnamed_list:
#             return False
#     if target_tree_child1_unnamed_list == target_tree_child2_unnamed_list:
#         if source_tree_child1_unnamed_list != source_tree_child2_unnamed_list:
#             return False
#
#     return True


def check_unnamed_nodes_for_diff(target_tree1, target_tree2, source_tree1, source_tree2, target_diff_child1, target_diff_child2, source_diff_child1, source_diff_child2, source_diff1, trans_diff1):
    target_unvisited_path = [diff for diff in trans_diff1]
    source_unvisited_path = [diff for diff in source_diff1]

    target_tree1_unnamed_list = []
    traverse_tree_unnamed_node_with_path(target_tree1, [], target_unvisited_path, target_tree1_unnamed_list)
    target_tree2_unnamed_list = []
    traverse_tree_unnamed_node_with_path(target_tree2, [], target_unvisited_path, target_tree2_unnamed_list)

    source_tree1_unnamed_list = []
    traverse_tree_unnamed_node_with_path(source_tree1, [], source_unvisited_path, source_tree1_unnamed_list)
    source_tree2_unnamed_list = []
    traverse_tree_unnamed_node_with_path(source_tree2, [], source_unvisited_path, source_tree2_unnamed_list)

    target_tree_child1_unnamed_list = []
    traverse_tree_unnamed_node_with_path(target_diff_child1, [], [], target_tree_child1_unnamed_list)
    target_tree_child2_unnamed_list = []
    traverse_tree_unnamed_node_with_path(target_diff_child2, [], [], target_tree_child2_unnamed_list)

    source_tree_child1_unnamed_list = []
    traverse_tree_unnamed_node_with_path(source_diff_child1, [], [], source_tree_child1_unnamed_list)
    source_tree_child2_unnamed_list = []
    traverse_tree_unnamed_node_with_path(source_diff_child2, [], [], source_tree_child2_unnamed_list)

    target_tree1_unnamed_list.sort()
    target_tree2_unnamed_list.sort()
    source_tree1_unnamed_list.sort()
    source_tree2_unnamed_list.sort()
    source_tree_child1_unnamed_list.sort()
    source_tree_child2_unnamed_list.sort()
    target_tree_child1_unnamed_list.sort()
    target_tree_child2_unnamed_list.sort()

    if source_tree_child1_unnamed_list == source_tree_child2_unnamed_list:
        if target_tree_child1_unnamed_list != target_tree_child2_unnamed_list:
            return False
    if target_tree_child1_unnamed_list == target_tree_child2_unnamed_list:
        if source_tree_child1_unnamed_list != source_tree_child2_unnamed_list:
            return False

    source_tree1_unnamed_list_except_source_tree_child1_unnamed_list = source_tree1_unnamed_list[:]
    for item in source_tree_child1_unnamed_list:
        source_tree1_unnamed_list_except_source_tree_child1_unnamed_list.remove(item)

    source_tree2_unnamed_list_except_source_tree_child2_unnamed_list = source_tree2_unnamed_list[:]
    for item in source_tree_child2_unnamed_list:
        source_tree2_unnamed_list_except_source_tree_child2_unnamed_list.remove(item)

    target_tree1_unnamed_list_except_target_tree_child1_unnamed_list = target_tree1_unnamed_list[:]
    for item in target_tree_child1_unnamed_list:
        target_tree1_unnamed_list_except_target_tree_child1_unnamed_list.remove(item)

    target_tree2_unnamed_list_except_target_tree_child2_unnamed_list = target_tree2_unnamed_list[:]
    for item in target_tree_child2_unnamed_list:
        target_tree2_unnamed_list_except_target_tree_child2_unnamed_list.remove(item)

    source_tree1_unnamed_list_except_source_tree_child1_unnamed_list.sort()
    source_tree2_unnamed_list_except_source_tree_child2_unnamed_list.sort()
    target_tree1_unnamed_list_except_target_tree_child1_unnamed_list.sort()
    target_tree2_unnamed_list_except_target_tree_child2_unnamed_list.sort()

    if source_tree1_unnamed_list_except_source_tree_child1_unnamed_list != source_tree2_unnamed_list_except_source_tree_child2_unnamed_list:
        return False
    if target_tree1_unnamed_list_except_target_tree_child1_unnamed_list != target_tree2_unnamed_list_except_target_tree_child2_unnamed_list:
        return False

    return True


def load_trace(trace_file_path, code_lines, source_lang, target_lang, lang, ID):
    if not os.path.isfile(trace_file_path):
        return []
    f = open(trace_file_path)
    lines = f.readlines()
    f.close()
    steps = []
    step = []
    if lang in ['Java', 'C++'] and code_lines[1].strip() == '{':
        offset = -1
    else:
        offset = 0
    for line in lines:
        if line == '\n':
            line_id = int(step[0][len('Line: '):])
            if line_id == 0:
                step[0] = int(step[0][len('Line: '):])
            else:
                step[0] = int(step[0][len('Line: '):]) + offset
            steps.append(step)
            step = []
        else:
            step.append(line.strip())
    return steps


def replace_repeat(ori_val):
    val = copy.deepcopy(ori_val)
    for i in range(100):
        if '<repeats' not in val:
            break
        this_match = re.search(r'[ \[]([^ \[]+) <repeats (\d+) times>', val)
        this_match_str = this_match.group()[1:]
        repeat_item = this_match.group(1)
        repeat_time = int(this_match.group(2))
        pre_val = val[:val.index(this_match_str)]
        syb_val = val[val.index(this_match_str)+len(this_match_str):]
        repeat_str = repeat_item
        for _ in range(repeat_time-1):
            repeat_str = repeat_str + ', ' + repeat_item
        val = pre_val + repeat_str + syb_val
    return val


def replace_repeat_string(ori_val):
    val = copy.deepcopy(ori_val)
    this_match = re.search(r' <repeats (\d+) times>', val)
    this_match_str = this_match.group()
    repeat_item = val[:val.index(this_match_str)][1:-1]
    repeat_time = int(this_match.group(1))
    repeat_str = repeat_item
    for _ in range(repeat_time - 1):
        repeat_str = repeat_str + repeat_item
    val = "\'" + repeat_str + "\'"
    return val


def read_var_val(var_val_str_list):
    var_vals = {}
    for var_str in var_val_str_list:
        var_str_list = var_str.split(' = ')
        var = var_str_list[0].strip()
        val = ' = '.join(var_str_list[1:]).strip()
        var_vals[var] = val
    return var_vals


def calculate_closure(t2s):
    count = 0
    uncompare_t_ids = []
    while(True):
        count += 1
        new_t2s = copy.deepcopy(t2s)
        keys = [i for i in t2s.keys()]
        keys.sort()
        pre_key = -2
        for key in keys:
            if key == pre_key + 1:
                pre_map = t2s[pre_key]
                this_map = t2s[key]
                inter_map = [item for item in pre_map if item in this_map]
                if inter_map and pre_map != this_map:
                    uncompare_t_ids.append(key)
                    new_map = pre_map[:]
                    new_map.extend(this_map)
                    new_map = list(set(new_map))
                    new_map.sort()
                    new_t2s[key] = new_map[:]
                    new_t2s[pre_key] = new_map[:]
            pre_key = key
        diff_items = {k: new_t2s[k] for k in new_t2s if k in t2s and new_t2s[k] != t2s[k]}
        if len(diff_items) == 0:
            break
        else:
            t2s = copy.deepcopy(new_t2s)
    return t2s, uncompare_t_ids


def loadMap(path):
    files = os.listdir(path)
    map = {}
    for file in files:
        f = open(f'{path}/{file}')
        lines = f.readlines()
        f.close()
        ID = file.split('.')[0]
        map[ID] = []
        for line in lines:
            if line.strip():
                map[ID].append([line.strip().split(';')[0], line.strip().split(';')[1]])
    return map


def loadFL(path):
    files = os.listdir(path)
    map = {}
    for file in files:
        f = open(f'{path}/{file}')
        lines = f.readlines()
        f.close()
        ID = file.split('.')[0]
        map[ID] = []
        for line in lines:
            if line.strip():
                map[ID].append(int(line.strip()))
    return map


def check_else(s_stmt, t_stmt, pos1_set, pos2_set):
    if s_stmt.startswith('if_') and (s_stmt.endswith('else-0') or s_stmt.endswith('else_clause-0')) \
            and t_stmt.startswith('if_') and (t_stmt.endswith('else-0') or t_stmt.endswith('else_clause-0')) and len(pos1_set) > 1 and len(pos2_set) > 1:
        return True
    else:
        return False


def M2lines(M, source_stmt_list_pos, trans_stmt_list_pos, source_lines, trans_lines, source_stmt_list, trans_stmt_list, sourceline2stmt, transline2stmt):
    line_M = {}
    for s_id in range(len(source_lines)):
        for t_id in range(len(trans_lines)):
            line_M[f'{s_id}-{t_id}'] = False
    line_M[f'{0}-{0}'] = True
    for k, v in M.items():
        if v:
            id1 = int(k.split('-')[0])
            id2 = int(k.split('-')[1])
            pos1_set = []
            for item in source_stmt_list_pos[id1]:
                if source_lines[item[0]][item[1]] not in ['{', '}', ';'] and item[0] not in pos1_set:
                    pos1_set.append(item[0])
            pos2_set = []
            for item in trans_stmt_list_pos[id2]:
                if trans_lines[item[0]][item[1]] not in ['{', '}', ';'] and item[0] not in pos2_set:
                    pos2_set.append(item[0])

            s_stmt = source_stmt_list[id1]
            t_stmt = trans_stmt_list[id2]

            # if s_stmt.startswith('if_statement-0') and t_stmt.startswith('if_statement-0') and pos1_set and pos2_set \
            #         and source_lines[pos1_set[0]].strip().startswith('else if') and trans_lines[pos2_set[0]].strip().startswith('else if'):
            #     pos1_set = [pos1_set[0]]
            #     pos2_set = [pos2_set[0]]

            if (s_stmt.startswith('if_statement-0') or s_stmt.startswith('parenthesized_expression-0')) and (t_stmt.startswith('if_statement-0') or t_stmt.startswith('parenthesized_expression-0')) and len(pos1_set) != len(pos2_set):
                if_else1 = False
                if_else2 = False
                for pos1 in pos1_set:
                    if source_lines[pos1].strip().startswith('else if') or source_lines[pos1].strip().startswith('else') or source_lines[pos1].strip().startswith('elif'):
                        if_else1 = True
                for pos2 in pos2_set:
                    if trans_lines[pos2].strip().startswith('else if') or trans_lines[pos2].strip().startswith('else') or trans_lines[pos2].strip().startswith('elif'):
                        if_else1 = True
                if if_else1 or if_else1:
                    pos1_set = [pos1_set[0]]
                    pos2_set = [pos2_set[0]]

            if check_else(s_stmt, t_stmt, pos1_set, pos2_set):
                if_pos1_set = pos1_set[:-1]
                else_pos1_set = [pos1_set[-1]]
                if_pos2_set = pos2_set[:-1]
                else_pos2_set = [pos2_set[-1]]
                for pos1 in if_pos1_set:
                    for pos2 in if_pos2_set:
                        line_M[f'{pos1}-{pos2}'] = True
                for pos1 in else_pos1_set:
                    for pos2 in else_pos2_set:
                        line_M[f'{pos1}-{pos2}'] = True
            else:
                if len(pos1_set) == len(pos2_set):
                    for pos1, pos2 in zip(pos1_set, pos2_set):
                        line_M[f'{pos1}-{pos2}'] = True
                elif len(pos1_set) != 1 and len(pos2_set) == 1 and not if_continue(pos1_set):
                    line_M[f'{pos1_set[0]}-{pos2_set[0]}'] = True
                elif len(pos2_set) != 1 and len(pos1_set) == 1 and not if_continue(pos2_set):
                    line_M[f'{pos1_set[0]}-{pos2_set[0]}'] = True
                else:
                    for pos1 in pos1_set:
                        for pos2 in pos2_set:
                            line_M[f'{pos1}-{pos2}'] = True
    # closures = find_closure(line_M, source_lines, trans_lines)
    # for closure in closures:
    #     S = list(closure[0])
    #     F = list(closure[1])
    #     if len(S) == 1 or len(F) == 1:
    #         continue
    #     S.sort()
    #     F.sort()
    #     s_mapped_stmts = []
    #     for line_id in S:
    #         if line_id in sourceline2stmt:
    #             s_mapped_stmts.extend(sourceline2stmt[line_id])
    #     t_mapped_stmts = []
    #     for line_id in F:
    #         if line_id in transline2stmt:
    #             t_mapped_stmts.extend(transline2stmt[line_id])
    #     s_mapped_stmts = set(s_mapped_stmts)
    #     t_mapped_stmts = set(t_mapped_stmts)
    #     if len(S) == len(F) and len(s_mapped_stmts) == 1 and len(t_mapped_stmts) == 1:
    #         for s_idx, s_id in enumerate(S):
    #             for f_idx, f_id in enumerate(F):
    #                 if s_idx != f_idx:
    #                     line_M[f'{s_id}-{f_id}'] = False
    unmapped_s_elses = []
    for s_stmt_id, s_stmt in enumerate(source_stmt_list):
        if s_stmt.startswith('if_'):
            if_mapped = False
            for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
                if M[f'{s_stmt_id}-{t_stmt_id}']:
                    if_mapped = True
            if not if_mapped:
                pos_set = []
                for item in source_stmt_list_pos[s_stmt_id]:
                    if source_lines[item[0]].strip() not in ['{', '}'] and item[0] not in pos_set:
                        pos_set.append(item[0])
                s_stmt_tokens = s_stmt.split('||||')
                else_counts1 = s_stmt_tokens.count('else-0')
                else_counts2 = s_stmt_tokens.count('else_clause-0')
                else_counts = else_counts1 + else_counts2
                if len(pos_set) > else_counts:
                    for pos_id in pos_set[len(pos_set)-else_counts:]:
                        if pos_id not in unmapped_s_elses:
                            unmapped_s_elses.append(pos_id)
    unmapped_t_elses = []
    for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
        if t_stmt.startswith('if_'):
            if_mapped = False
            for s_stmt_id, s_stmt in enumerate(source_stmt_list):
                if M[f'{s_stmt_id}-{t_stmt_id}']:
                    if_mapped = True
            if not if_mapped:
                pos_set = []
                for item in trans_stmt_list_pos[t_stmt_id]:
                    if trans_lines[item[0]].strip() not in ['{', '}'] and item[0] not in pos_set:
                        pos_set.append(item[0])
                t_stmt_tokens = t_stmt.split('||||')
                else_counts1 = t_stmt_tokens.count('else-0')
                else_counts2 = t_stmt_tokens.count('else_clause-0')
                else_counts = else_counts1 + else_counts2
                if len(pos_set) > else_counts:
                    for pos_id in pos_set[len(pos_set)-else_counts:]:
                        if pos_id not in unmapped_t_elses:
                            unmapped_t_elses.append(pos_id)
    if unmapped_s_elses and unmapped_t_elses:
        for s_pos in unmapped_s_elses:
            for t_pos in unmapped_t_elses:
                if_valid = False
                pre_s_id = s_pos
                pre_t_id = t_pos
                for i in range(s_pos):
                    if source_lines[s_pos-1-i].strip() not in ['{', '}']:
                        pre_s_id = s_pos-1-i
                        break
                for i in range(t_pos):
                    if trans_lines[t_pos-1-i].strip() not in ['{', '}']:
                        pre_t_id = t_pos-1-i
                        break
                nex_s_id = s_pos
                nex_t_id = t_pos
                for i in range(len(source_lines)-1-s_pos):
                    if source_lines[s_pos+1+i].strip() not in ['{', '}']:
                        nex_s_id = s_pos+1+i
                        break
                for i in range(len(trans_lines)-1-t_pos):
                    if trans_lines[t_pos+1+i].strip() not in ['{', '}']:
                        nex_t_id = t_pos+1+i
                        break
                if f'{pre_s_id}-{pre_t_id}' in line_M and line_M[f'{pre_s_id}-{pre_t_id}']:
                    if_valid = True
                if f'{nex_s_id}-{nex_t_id}' in line_M and line_M[f'{nex_s_id}-{nex_t_id}']:
                    if_valid = True
                if if_valid:
                    line_M[f'{s_pos}-{t_pos}'] = True

    return line_M


def next_s_state(traces, state, line_M, len_t, source_lang, source_lines):
    new_state = [[], [], []]
    if state[0]:
        last_id = state[2][-1]
    else:
        last_id = -1
    if last_id >= len(traces) - 1:
        return new_state, False
    step_M = []
    if_first = True
    for step_id, step in enumerate(traces):
        if step_id <= last_id:
            continue
        if source_lines[step[0]].strip() == ';':
            continue
        this_step_M = [t_id for t_id in range(len_t) if line_M[f'{step[0]}-{t_id}']]
        var_vals = read_var_val(step[1:])
        if if_first:
            step_M = copy.deepcopy(this_step_M)
            new_state[0].append(step[0])
            new_state[1].append(var_vals)
            new_state[2].append(step_id)
            if_first = False
        else:
            if this_step_M == step_M:
                new_state[0].append(step[0])
                new_state[1].append(var_vals)
                new_state[2].append(step_id)
            else:
                break
    return new_state, True


def next_t_state(traces, state, line_M, len_s, target_lang, trans_lines):
    new_state = [[], [], []]
    if state[0]:
        last_id = state[2][-1]
    else:
        last_id = -1
    if last_id >= len(traces) - 1:
        return new_state, False
    step_M = []
    if_start = False
    for step_id, step in enumerate(traces):
        if step_id <= last_id:
            continue
        if trans_lines[step[0]].strip() == ';':
            continue
        this_step_M = [s_id for s_id in range(len_s) if line_M[f'{s_id}-{step[0]}']]
        var_vals = read_var_val(step[1:])
        if not if_start:
            step_M = copy.deepcopy(this_step_M)
            new_state[0].append(step[0])
            new_state[1].append(var_vals)
            new_state[2].append(step_id)
            if_start = True
        else:
            if this_step_M == step_M:
                new_state[0].append(step[0])
                new_state[1].append(var_vals)
                new_state[2].append(step_id)
            else:
                break
    return new_state, True

import ast
def compare_value(var, s_val, t_val, s_vals, t_vals, current_s_trace_id, current_t_trace_id):
    if s_val == t_val:
        return True
    else:
        this_s_vals = []
        this_t_vals = []
        if var in s_vals:
            for item in s_vals[var]:
                if item[0] <= current_s_trace_id[0]:
                    continue
                this_s_vals.append(item[1])
                break
        if var in t_vals:
            for item in t_vals[var]:
                if item[0] <= current_t_trace_id[0]:
                    continue
                this_t_vals.append(item[1])
                break
        if_same = False
        for item in this_s_vals:
            if item in this_t_vals:
                if_same = True
        if if_same:
            return True
        else:
            if s_val in ['{}', '[]'] and t_val in ['{}', '[]']:
                return True
            if s_val.startswith('{') and ': ' in s_val and t_val.startswith('[[') and ' = ' in t_val:
                this_t_val = copy.deepcopy(t_val)
                this_t_val = this_t_val.replace(', [', ', ')
                this_t_val = this_t_val.replace('] = ', ': ')
                this_t_val = this_t_val.replace(']', '}')
                this_t_val = this_t_val.replace('[', '{')
                this_t_val = this_t_val.replace('{{', '{')
                this_s_val = ast.literal_eval(s_val)
                this_t_val = ast.literal_eval(this_t_val)
                if this_s_val == this_t_val:
                    return True
            if s_val.startswith('[') and '[[' not in s_val and t_val.startswith('[[') and ' = ' in t_val:
                this_t_val = copy.deepcopy(t_val)
                this_t_val = this_t_val.replace(', [', ', ')
                this_t_val = this_t_val.replace('] = ', ': ')
                this_t_val = this_t_val.replace('[[', '{')
                this_t_val = this_t_val.replace(']', '}')
                this_s_val = copy.deepcopy(s_val)
                this_s_val = this_s_val.replace('[', '{')
                this_s_val = this_s_val.replace(']', '}')
                this_s_val = ast.literal_eval(this_s_val)
                this_t_val = ast.literal_eval(this_t_val)
                this_t_val = set([v for k, v in this_t_val.items()])
                if this_s_val == this_t_val:
                    return True
            return False


def compare_stepbystep(source_traces, trans_traces, source_lang, target_lang, line_M, len_s, len_t, source_lines, trans_lines, trans_line_def_variables):
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

    while if_step:
        s_state, s_suc = next_s_state(source_traces, s_state, line_M, len_t, source_lang, source_lines)
        t_state, t_suc = next_t_state(trans_traces, t_state, line_M, len_s, target_lang, trans_lines)
        if not s_suc or not t_suc:
            if_step = False
            diff_info.append(['diff_path'])
        else:
            s_expect_t = set()
            for t_stmt_id in range(len_t):
                if line_M[f'{s_state[0][-1]}-{t_stmt_id}']:
                    s_expect_t.add(t_stmt_id)
            if len(s_expect_t):
                if t_state[0][-1] not in s_expect_t:
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
                                s_val_int = int(s_val)
                                t_val_int = int(t_val)
                                if s_val_int + 1 == t_val_int:
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
                if len(pre_t_state[0]):
                    report_id = pre_t_state[0][-1]
                else:
                    report_id = 0
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
            if '// Patch ' in trans_lines[report_id] and report_id != 0:
                report_id = report_id + 1
    return report_id


def get_unmapped_lines(M, source_lines, trans_lines, source_stmt_list, trans_stmt_list, source_stmt_list_pos, trans_stmt_list_pos):
    unmapped_s_line_ids = []
    unmapped_t_line_ids = []
    for s_stmt_id, s_stmt in enumerate(source_stmt_list):
        if_mapped = False
        for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
            if M[f'{s_stmt_id}-{t_stmt_id}']:
                if_mapped = True
        if not if_mapped:
            pos_set = []
            for item in source_stmt_list_pos[s_stmt_id]:
                if source_lines[item[0]].strip() not in ['{', '}'] and item[0] not in pos_set:
                    pos_set.append(item[0])
            unmapped_s_line_ids.extend(pos_set)
    for t_stmt_id, t_stmt in enumerate(trans_stmt_list):
        if_mapped = False
        for s_stmt_id, s_stmt in enumerate(source_stmt_list):
            if M[f'{s_stmt_id}-{t_stmt_id}']:
                if_mapped = True
        if not if_mapped:
            pos_set = []
            for item in trans_stmt_list_pos[t_stmt_id]:
                if trans_lines[item[0]].strip() not in ['{', '}'] and item[0] not in pos_set:
                    pos_set.append(item[0])
            unmapped_t_line_ids.extend(pos_set)
    return unmapped_s_line_ids, unmapped_t_line_ids


def validate_expr_operator(source_path1, target_path1, this_new_map):
    for opr in ['==', '!', '>', '<', '=', '!=', '|', '&', '||', '&&', '/', '//', '*', '+', '-', '%']:
        s_count1 = source_path1.count(f'{opr}-0')
        t_count1 = target_path1.count(f'{opr}-0')
        s_count2 = this_new_map[0].count(f'{opr}-0')
        t_count2 = this_new_map[1][0].count(f'{opr}-0')
        if s_count1 == t_count1 and s_count2 != t_count2:
            return False
    for opr in ['!']:
        s_count1 = source_path1.count(f'{opr}')
        t_count1 = target_path1.count(f'{opr}')
        s_count2 = this_new_map[0].count(f'{opr}')
        t_count2 = this_new_map[1][0].count(f'{opr}')
        if s_count1 == t_count1 and s_count2 != t_count2:
            return False
    return True


def validate_buildmap(source_path1, target_path1, map, source_lang, target_lang, invalid_expr_maps):
    if '\n-0' in map[0] or '\n-0' in map[1][0]:
        return False
    if map in invalid_expr_maps:
        return False
    if map[0] == 'identifier-0' and map[1][0] != 'identifier-0':
        return False
    if map[1][0] == 'identifier-0' and map[0] != 'identifier-0':
        return False
    if source_lang == 'Python' and target_lang == 'C++':
        if map[0].startswith('if_'):
            if map[0].count('==') != map[1][0].count('=='):
                return False
            if map[0].count('>=') != map[1][0].count('>='):
                return False
            if map[0].count('<=') != map[1][0].count('<='):
                return False
            if map[0].count('>') != map[1][0].count('>'):
                return False
            if map[0].count('<') != map[1][0].count('<'):
                return False
            if map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('for_'):
            if '==' in map[0] and map[0].count('==') != map[1][0].count('=='):
                return False
            if '>=' in map[0] and map[0].count('>=') != map[1][0].count('>='):
                return False
            if '<=' in map[0] and map[0].count('<=') != map[1][0].count('<='):
                return False
            if '>' in map[0] and map[0].count('>') != map[1][0].count('>'):
                return False
            if '<' in map[0] and map[0].count('<') != map[1][0].count('<'):
                return False
            if '!=' in map[0] and map[0].count('!=') != map[1][0].count('!='):
                return False
        if (map[0].startswith('binary_operator') or map[0].startswith('parenthesized_expression-0')) and (map[1][0].startswith('binary_expression') or map[1][0].startswith('parenthesized_expression-0')):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
            if map[0].count('/') != map[1][0].count('/'):
                return False
            if map[0].count('%') != map[1][0].count('%'):
                return False
        if map[0].startswith('binary_operator') and map[1][0].startswith('binary_expression'):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
        if map[0] == '/-0' and map[1][0] != '/-0':
            return False
        if map[0] == '+-0' and map[1][0] != '+-0':
            return False
        if map[0] == '--0' and map[1][0] != '--0':
            return False
        if map[0] == '*-0' and map[1][0] != '*-0':
            return False
        if map[0] == '%-0' and map[1][0] != '%-0':
            return False
        if map[1][0] == '/-0' and map[0] != '/-0':
            return False
        if map[1][0] == '+-0' and map[0] != '+-0':
            return False
        if map[1][0] == '--0' and map[0] != '--0':
            return False
        if map[1][0] == '*-0' and map[0] != '*-0':
            return False
        if map[1][0] == '%-0' and map[0] != '%-0':
            return False
        if map[0].startswith('parenthesized_expression-0||||') and not map[1][0].startswith('parenthesized_expression-0||||'):
            return False
        if map[1][0].startswith('parenthesized_expression-0||||') and not map[0].startswith('parenthesized_expression-0||||'):
            return False
        if map[0] == 'subscript-0||||identifier-0||||[-0||||identifier-0||||]-0' and map[1][0] != 'subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0':
            return False
        if map[0] != 'subscript-0||||identifier-0||||[-0||||identifier-0||||]-0' and map[1][0] == 'subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0':
            return False

    if source_lang == 'C++' and target_lang == 'Python':
        if map[0].startswith('if_'):
            if map[0].count('==') != map[1][0].count('=='):
                return False
            if map[0].count('>=') != map[1][0].count('>='):
                return False
            if map[0].count('<=') != map[1][0].count('<='):
                return False
            if map[0].count('>') != map[1][0].count('>'):
                return False
            if map[0].count('<') != map[1][0].count('<'):
                return False
            if map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('for_'):
            if '==' in map[0] and map[0].count('==') != map[1][0].count('=='):
                return False
            if '>=' in map[0] and map[0].count('>=') != map[1][0].count('>='):
                return False
            if '<=' in map[0] and map[0].count('<=') != map[1][0].count('<='):
                return False
            if '>' in map[0] and map[0].count('>') != map[1][0].count('>'):
                return False
            if '<' in map[0] and map[0].count('<') != map[1][0].count('<'):
                return False
            if '!=' in map[0] and map[0].count('!=') != map[1][0].count('!='):
                return False
        if (map[0].startswith('binary_expression') or map[0].startswith('parenthesized_expression-0')) and (map[1][0].startswith('binary_operator') or map[1][0].startswith('parenthesized_expression-0')):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
            if map[0].count('/') != map[1][0].count('/'):
                return False
            if map[0].count('%') != map[1][0].count('%'):
                return False
        if map[0].startswith('binary_expression') and map[1][0].startswith('binary_operator'):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
        if map[0] == '/-0' and map[1][0] != '/-0':
            return False
        if map[0] == '+-0' and map[1][0] != '+-0':
            return False
        if map[0] == '--0' and map[1][0] != '--0':
            return False
        if map[0] == '*-0' and map[1][0] != '*-0':
            return False
        if map[0] == '%-0' and map[1][0] != '%-0':
            return False
        if map[1][0] == '/-0' and map[0] != '/-0':
            return False
        if map[1][0] == '+-0' and map[0] != '+-0':
            return False
        if map[1][0] == '--0' and map[0] != '--0':
            return False
        if map[1][0] == '*-0' and map[0] != '*-0':
            return False
        if map[1][0] == '%-0' and map[0] != '%-0':
            return False
        if map[0].startswith('parenthesized_expression-0||||') and not map[1][0].startswith('parenthesized_expression-0||||'):
            return False
        if map[1][0].startswith('parenthesized_expression-0||||') and not map[0].startswith('parenthesized_expression-0||||'):
            return False
        if map[0] == 'subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0' and map[1][0] != 'subscript-0||||identifier-0||||[-0||||identifier-0||||]-0':
            return False
        if map[0] != 'subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0' and map[1][0] == 'subscript-0||||identifier-0||||[-0||||identifier-0||||]-0':
            return False
    if source_lang == 'Java' and target_lang == 'C++':
        if map[0].startswith('if_'):
            if map[0].count('==') != map[1][0].count('=='):
                return False
            if map[0].count('>=') != map[1][0].count('>='):
                return False
            if map[0].count('<=') != map[1][0].count('<='):
                return False
            if map[0].count('>') != map[1][0].count('>'):
                return False
            if map[0].count('<') != map[1][0].count('<'):
                return False
            if map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('for_'):
            if '==' in map[0] and map[0].count('==') != map[1][0].count('=='):
                return False
            if '>=' in map[0] and map[0].count('>=') != map[1][0].count('>='):
                return False
            if '<=' in map[0] and map[0].count('<=') != map[1][0].count('<='):
                return False
            if '>' in map[0] and map[0].count('>') != map[1][0].count('>'):
                return False
            if '<' in map[0] and map[0].count('<') != map[1][0].count('<'):
                return False
            if '!=' in map[0] and map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('modifiers-0||||') and map[1][0].startswith('sized_type_specifier-0||||'):
            return False
        if '(-0||||integral_type-0||||int-0||||)-0' in map[0] and '(-0||||type_descriptor-0||||primitive_type-0||||)-0' in map[1][0]:
            if map[0].endswith('||||)-0||||;-0') and not map[1][0].endswith('||||)-0||||;-0'):
                return False
            if map[1][0].endswith('||||)-0||||;-0') and not map[0].endswith('||||)-0||||;-0'):
                return False
        if (map[0].startswith('binary_expression') or map[0].startswith('parenthesized_expression-0')) and (map[1][0].startswith('binary_expression')  or map[1][0].startswith('parenthesized_expression-0')):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
            if map[0].count('/') != map[1][0].count('/'):
                return False
            if map[0].count('%') != map[1][0].count('%'):
                return False
        if map[0] == '/-0' and map[1][0] != '/-0':
            return False
        if map[0] == '+-0' and map[1][0] != '+-0':
            return False
        if map[0] == '--0' and map[1][0] != '--0':
            return False
        if map[0] == '*-0' and map[1][0] != '*-0':
            return False
        if map[0] == '%-0' and map[1][0] != '%-0':
            return False
        if map[1][0] == '/-0' and map[0] != '/-0':
            return False
        if map[1][0] == '+-0' and map[0] != '+-0':
            return False
        if map[1][0] == '--0' and map[0] != '--0':
            return False
        if map[1][0] == '*-0' and map[0] != '*-0':
            return False
        if map[1][0] == '%-0' and map[0] != '%-0':
            return False

    if source_lang == 'C++' and target_lang == 'Java':
        if map[0].startswith('if_'):
            if map[0].count('==') != map[1][0].count('=='):
                return False
            if map[0].count('>=') != map[1][0].count('>='):
                return False
            if map[0].count('<=') != map[1][0].count('<='):
                return False
            if map[0].count('>') != map[1][0].count('>'):
                return False
            if map[0].count('<') != map[1][0].count('<'):
                return False
            if map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('for_'):
            if '==' in map[0] and map[0].count('==') != map[1][0].count('=='):
                return False
            if '>=' in map[0] and map[0].count('>=') != map[1][0].count('>='):
                return False
            if '<=' in map[0] and map[0].count('<=') != map[1][0].count('<='):
                return False
            if '>' in map[0] and map[0].count('>') != map[1][0].count('>'):
                return False
            if '<' in map[0] and map[0].count('<') != map[1][0].count('<'):
                return False
            if '!=' in map[0] and map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('sized_type_specifier-0||||') and map[1][0].startswith('modifiers-0||||'):
            return False
        if '(-0||||type_descriptor-0||||primitive_type-0||||)-0' in map[0] and '(-0||||integral_type-0||||int-0||||)-0' in map[1][0]:
            if map[0].endswith('||||)-0||||;-0') and not map[1][0].endswith('||||)-0||||;-0'):
                return False
            if map[1][0].endswith('||||)-0||||;-0') and not map[0].endswith('||||)-0||||;-0'):
                return False
        if (map[0].startswith('binary_expression') or map[0].startswith('parenthesized_expression-0')) and (map[1][0].startswith('binary_expression')  or map[1][0].startswith('parenthesized_expression-0')):
            if map[0].count('+') != map[1][0].count('+'):
                return False
            if map[0].count('-') != map[1][0].count('-'):
                return False
            if map[0].count('*') != map[1][0].count('*'):
                return False
            if map[0].count('/') != map[1][0].count('/'):
                return False
            if map[0].count('%') != map[1][0].count('%'):
                return False
        if map[0] == '/-0' and map[1][0] != '/-0':
            return False
        if map[0] == '+-0' and map[1][0] != '+-0':
            return False
        if map[0] == '--0' and map[1][0] != '--0':
            return False
        if map[0] == '*-0' and map[1][0] != '*-0':
            return False
        if map[0] == '%-0' and map[1][0] != '%-0':
            return False
        if map[1][0] == '/-0' and map[0] != '/-0':
            return False
        if map[1][0] == '+-0' and map[0] != '+-0':
            return False
        if map[1][0] == '--0' and map[0] != '--0':
            return False
        if map[1][0] == '*-0' and map[0] != '*-0':
            return False
        if map[1][0] == '%-0' and map[0] != '%-0':
            return False
    ori_pct = len(path2nodes(map[0]))/len(path2nodes(source_path1))
    new_pct = len(path2nodes(map[1][0]))/len(path2nodes(target_path1))
    # if source_path1 == 'expression_statement-0||||method_invocation-0||||identifier-0||||.-0||||identifier-52||||argument_list-0||||(-0||||array_access-0||||identifier-0||||[-0||||identifier-0||||]-0||||,-0||||array_access-0||||identifier-0||||[-0||||identifier-0||||]-0||||)-0||||;-0':
    #     if target_path1 == 'expression_statement-0||||assignment_expression-0||||subscript_expression-0||||identifier-0||||[-0||||subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0||||]-0||||=-0||||subscript_expression-0||||identifier-0||||[-0||||identifier-0||||]-0||||;-0':
    #         print('')
    diff = abs(ori_pct-new_pct)
    if diff > 1/3:
        return False
    return True


def check_error_path(path):
    if 'ERROR' in path:
        return False
    if path.startswith('if_') and 'expression_statement' in path:
        return False
    if path.startswith('if_') and path.count('if_') > 1:
        return False
    return True


def check_ERROR_map(map):
    if not check_error_path(map[0]):
        return False
    for path in map[1]:
        if not check_error_path(path):
            return False
    return True


def get_anchors(source_path2pair, source_path1, target_path1_list):
    if source_path1 in source_path2pair:
        pairs = source_path2pair[source_path1]
        for pair in pairs:
            if pair.target_paths == target_path1_list:
                return pair.anchors
    return []


def validate_anchor(tree1, tree2, path1, path2, exist_anchors):
    tree_text1 = mytree2text(tree1, '')
    tree_text2 = mytree2text(tree2, '')
    if tree1.children == [] and tree2.children == []:
        if tree_text1 == tree_text2:
            return True
        else:
            return False
    else:
        if_already_anchor = False
        if tree1.children == []:
            for anchor in exist_anchors:
                if anchor[0] == path1:
                    if_already_anchor = True
        if tree2.children == []:
            for anchor in exist_anchors:
                for t_anchor in anchor[1]:
                    if t_anchor[0] == path2:
                        if_already_anchor = True
        if if_already_anchor:
            return False
        if tree1.children == []:
            tree1_token = tree_text1
            tree2_tokens = tree_text2.split()
            if tree1_token in tree2_tokens:
                return True
        if tree2.children == []:
            tree2_token = tree_text2
            tree1_tokens = tree_text1.split()
            if tree2_token in tree1_tokens:
                return True
        BLEUscore = nltk.translate.bleu_score.sentence_bleu([tree_text1.split()], tree_text2.split(), weights=(0.5, 0.5))
        if BLEUscore > 0.6:
            return True
        else:
            return False


def validate_map(map, source_lang, target_lang, invalid_stmt_maps):
    if 'comment' in map[0] and 'comment' not in ''.join(map[1]):
        return False
    if 'comment' not in map[0] and 'comment' in ''.join(map[1]):
        return False
    if '\n-0' in map[0] or '\n-0' in map[1][0]:
        return False
    if map in invalid_stmt_maps:
        return False
    if map[0].startswith('comparison_operator') and ''.join(map[1]).startswith('if_statement'):
        return False
    if map[0].startswith('if_statement') and ''.join(map[1]).startswith('comparison_operator'):
        return False
    if map[0].startswith('parenthesized_expression') and ''.join(map[1]).startswith('if_statement'):
        return False
    if map[0].startswith('if_statement') and ''.join(map[1]).startswith('parenthesized_expression'):
        return False
    if (source_lang == 'Python' and target_lang == 'C++') or (source_lang == 'C++' and target_lang == 'Python'):
        if map[0].startswith('if_'):
            if map[0].count('==') != map[1][0].count('=='):
                return False
            if map[0].count('>=') != map[1][0].count('>='):
                return False
            if map[0].count('<=') != map[1][0].count('<='):
                return False
            if map[0].count('>') != map[1][0].count('>'):
                return False
            if map[0].count('<') != map[1][0].count('<'):
                return False
            if map[0].count('!=') != map[1][0].count('!='):
                return False
        if map[0].startswith('for_'):
            if '==' in map[0] and map[0].count('==') != map[1][0].count('=='):
                return False
            if '>=' in map[0] and map[0].count('>=') != map[1][0].count('>='):
                return False
            if '<=' in map[0] and map[0].count('<=') != map[1][0].count('<='):
                return False
            if '>' in map[0] and map[0].count('>') != map[1][0].count('>'):
                return False
            if '<' in map[0] and map[0].count('<') != map[1][0].count('<'):
                return False
            if '!=' in map[0] and map[0].count('!=') != map[1][0].count('!='):
                return False

        if map[0].startswith('line_comment-0') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('line_comment-0') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('line_comment-0') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('comment-0') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('comment-0') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('comment-0') and map[0].startswith('expression_statement-0||||'):
            return False

        if map[0].startswith('return_statement-0||||') and not map[1][0].startswith('return_statement-0||||'):
            return False
        if map[1][0].startswith('return_statement-0||||') and not map[0].startswith('return_statement-0||||'):
            return False
        if map[0].startswith('for_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('for_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('for_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('if_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('if_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('if_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('while_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('while_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('while_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False
        if 'expression_statement-0||||;-0' in map[1][0]:
            # print('')
            return False

    elif (source_lang == 'Java' and target_lang == 'C++') or (source_lang == 'C++' and target_lang == 'Java'):
        if map[0].startswith('line_comment-0') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('line_comment-0') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('line_comment-0') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('line_comment-0') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('comment-0') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('comment-0') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('comment-0') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('comment-0') and map[0].startswith('expression_statement-0||||'):
            return False

        if map[0].startswith('try_with_resources_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('try_with_resources_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('try_statement-0||||') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('try_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False

        if map[0].startswith('try_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('try_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('try_with_resources_statement-0||||') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('try_with_resources_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False

        if map[0].startswith('if_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('if_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('if_statement-0||||') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('if_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('for_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('for_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('for_statement-0||||') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('for_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False
        if map[0].startswith('while_statement-0||||') and map[1][0].startswith('declaration-0||||'):
            return False
        if map[0].startswith('while_statement-0||||') and map[1][0].startswith('expression_statement-0||||'):
            return False
        if map[1][0].startswith('while_statement-0||||') and map[0].startswith('declaration-0||||'):
            return False
        if map[1][0].startswith('while_statement-0||||') and map[0].startswith('expression_statement-0||||'):
            return False

        if map[0].startswith('local_variable_declaration-0||||type_identifier-213||||variable_declarator-0||||'):  # java "Scanner"
            return False
        if map[0].startswith('return_statement-0||||') and not map[1][0].startswith('return_statement-0||||'):
            return False
        if map[1][0].startswith('return_statement-0||||') and not map[0].startswith('return_statement-0||||'):
            return False
    return True


def validate_path(path1, path2, lang):
    if lang == 'Java':
        if path1 == path2:
            return False
        if path1.count('assignment_expression-0') > 1 or path2.count('assignment_expression-0') > 1:
            return False
        tree1_nodes = path2nodes(path1)
        tree2_nodes = path2nodes(path2)
        if tree1_nodes[0] != tree2_nodes[0]:
            return False
        if tree1_nodes[0] == 'expression_statement-0' and tree2_nodes[0] == 'expression_statement-0' and tree1_nodes[1] != tree2_nodes[1]:
            return False
    elif lang == 'Python':
        if path1 == path2:
            return False
        if path1.count('assignment_expression-0') > 1 or path2.count('assignment_expression-0') > 1:
            return False
        tree1_nodes = path2nodes(path1)
        tree2_nodes = path2nodes(path2)
        if tree1_nodes[0] != tree2_nodes[0]:
            return False
        if tree1_nodes[0] == 'expression_statement-0' and tree2_nodes[0] == 'expression_statement-0' and tree1_nodes[1] != tree2_nodes[1]:
            return False
    elif lang == 'C++':
        if path1 == path2:
            return False
        if path1.count('assignment_expression-0') > 1 or path2.count('assignment_expression-0') > 1:
            return False
        if path1.count('<<-0') > 1 or path2.count('<<-0') > 1:
            if path1.count('<<-0') != path2.count('<<-0'):
                return False
        tree1_nodes = path2nodes(path1)
        tree2_nodes = path2nodes(path2)
        if tree1_nodes[0] != tree2_nodes[0]:
            return False
        if tree1_nodes[0] == 'expression_statement-0' and tree2_nodes[0] == 'expression_statement-0' and tree1_nodes[1] != tree2_nodes[1]:
            return False
    return True


def read_code(file_path, lang):
    f = open(file_path)
    lines = f.readlines()
    filter_lines = []
    if lang == 'Java':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if line.strip().endswith(';') and line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line.replace(';', ') ;')
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            filter_lines.append(this_line)
    elif lang == 'Python':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line + ' )'
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            if line.strip().startswith('if (') and line.strip().endswith(') :'):
                this_line = this_line.replace('if (', 'if')
                this_line = this_line.replace(') :', ':')
            if line.strip().startswith('while (') and line.strip().endswith(') :'):
                this_line = this_line.replace('while (', 'while')
                this_line = this_line.replace(') :', ':')
            filter_lines.append(this_line)
    elif lang == 'C++':
        for line in lines:
            this_line = copy.deepcopy(line)
            if line.strip().startswith('return int ('):
                this_line = this_line.replace('return int (', 'return ( int ) (')
            if 'std :: ' in line:
                this_line = this_line.replace('std :: ', '')
            if line.strip().endswith(';') and line.count('return ( int ) ') == 1 and line.count('return ( int ) (') == 0:
                this_line = this_line.replace('return ( int ) ', 'return ( int ) ( ')
                this_line = this_line.replace(';', ') ;')
            if '= int ( ' in line:
                this_line = this_line.replace('= int ( ', '= ( int ) ( ')
            if line.strip().startswith('while ( ( ') and line.strip().endswith(' ) ) {') and line.count('(') == 2:
                this_line = this_line.replace('while ( ( ', 'while ( ')
                this_line = this_line.replace(' ) ) {', ' ) {')
            if line.strip().startswith('if ( ( ') and line.strip().endswith(' ) ) {') and line.count('(') == 2:
                this_line = this_line.replace('if ( ( ', 'if ( ')
                this_line = this_line.replace(' ) ) {', ' ) {')
            filter_lines.append(this_line)
    wholecode = ''.join(lines)
    f.close()
    return wholecode, filter_lines


def diff_contain(diff1, diff2):
    if len(diff1) != (len(diff2) + 1):
        return []
    else:
        more_diff1 = []
        for this_diff1 in diff1:
            if this_diff1 not in diff2:
                more_diff1.append(this_diff1)
        if len(more_diff1) == 1:
            return more_diff1
        else:
            return []


def integrate_match_id(match_ids_lists):
    ids = []
    for match_id_list in match_ids_lists:
        if match_id_list and [len(match_id_list), match_id_list] not in ids:
            ids.append([len(match_id_list), match_id_list])
    ids.sort(reverse=False)
    if ids:
        return ids[0][1]
    else:
        return []


def integrate_diff_id(match_diff_list):
    max_len = 0
    for diff_id_list in match_diff_list:
        if diff_id_list and diff_id_list[0] > max_len:
            max_len = diff_id_list[0]
    ids = []
    for diff_id_list in match_diff_list:
        if diff_id_list and diff_id_list[0] == max_len:
            ids.extend(diff_id_list[1])
    ids.sort()
    if ids:
        return ids[0]
    else:
        return -1


def match(ori_tree, ori_walk_path, source_lang, target_lang, maps, trans_path2tree):
    ori_subtree = ori_tree.getChild(ori_walk_path)
    ori_subtree_path = '||||'.join(ori_subtree.getDFS(source_lang))
    # print(f"{color.BOLD}{depth}{color.END}")
    if ori_subtree_path in maps:
        possible_subtrees = []
        for this_target_tree_paths in maps[ori_subtree_path]:
            # if len(this_target_tree_paths) == 1:
            this_target_trees = [trans_path2tree[this_target_tree_path] for this_target_tree_path in this_target_tree_paths if this_target_tree_path in trans_path2tree]
            if_contained = False
            for this_possible_subtrees in possible_subtrees:
                if len(this_possible_subtrees) == len(this_target_trees):
                    if_diff = False
                    for this_possible_subtree, this_target_tree in zip(this_possible_subtrees, this_target_trees):
                        this_diff = compare_MyTree(this_target_tree, this_possible_subtree, target_lang)
                        if this_diff:
                            if_diff = True
                    if not if_diff:
                        if_contained = True
            if not if_contained:
                possible_subtrees.append(this_target_trees)
        return possible_subtrees
    else:
        return []


def get_set(lists_of_choices, source_lang):
    text2choices = {}
    for list_id, list_of_choices in enumerate(lists_of_choices):
        text = '####'.join(['||||'.join(item.getDFS(source_lang)) for item in list_of_choices])
        if text not in text2choices:
            text2choices[text] = list_of_choices
    return_choices = []
    for k, v in text2choices.items():
        return_choices.append(v)
    return return_choices


def match_force_begin(ori_tree, ori_walk_path, root_node2map, source_lang, target_lang, maps, source_path2tree, trans_path2tree, depth, max_depth, max_possible_choices, start_time, time_limit, if_search):
    print(ori_walk_path)
    this_time = time.time()
    if this_time - start_time > time_limit:
        print('Time out...')
        return [], if_search
    ori_subtree = ori_tree.getChild(ori_walk_path)
    ori_subtree_path = '||||'.join(ori_subtree.getDFS(source_lang))
    ori_subtree_children = ori_subtree.children
    ori_subtree_type = node_type_transfer(source_lang, ori_subtree.type, ori_subtree.text, ori_subtree.variable_names)
    # print(f"{color.BOLD}{depth}{color.END}")
    if depth >= max_depth:
        return [], if_search
    if ori_subtree_type[0] in root_node2map:
        possible_subtrees = []
        map_choices = root_node2map[ori_subtree_type[0]]
        map_choices_counts = []
        for choice_id, map_choice in enumerate(map_choices):
            if ori_subtree_path == map_choice.source_path:
                continue
            ori_nodes = ori_subtree_path.split('||||')
            choice_nodes = map_choice.source_path.split('||||')
            # same_nodes = [node for node in ori_nodes if node in choice_nodes]
            BLEUscore = nltk.translate.bleu_score.sentence_bleu([ori_nodes], choice_nodes, weights=(0.5, 0.5))
            map_choices_counts.append([BLEUscore, choice_id])
        map_choices_counts.sort(reverse=True)
        fail_source_paths = []
        succ_infos = {}
        for map_choice_id, map_choice_count in enumerate(map_choices_counts):
            # if map_choice_id == 1 and depth == 0:
            #     print('')
            map_choice = map_choices[map_choice_count[1]]
            this_time = time.time()
            if this_time - start_time > time_limit:
                print('Time out...')
                break
            # if map_choice.source_tree.text == 'int m = S / 60;':
            #     print('')
            # print(map_choice_id)
            # if map_choice.source_path.startswith('call-0||||'):
            #     print('')
            # if map_choice.source_path.startswith('call-0||||attribute-0||||'):
            #     print('')
            # if map_choice_id in [61, 63, 73, 84]:
            #     print('')
            map_choice_source_anchors = [anchor[0] for anchor in map_choice.anchors]
            map_choice_target_anchors = [anchor[1] for anchor in map_choice.anchors]
            choice_tree_children = map_choice.source_tree.children
            if len(ori_subtree_children) != len(choice_tree_children):
                continue

            diff_paths = compare_MyTree(ori_subtree, map_choice.source_tree, source_lang)
            if not diff_paths:
                continue
                # raise Exception('I do not think this exception can be triggered...')

            if_valid = True
            exact_matched_uncompared_idxs = []
            loose_matched_uncompared_idxs = []
            for this_diff_path in diff_paths:
                this_diff_path_ids = this_diff_path[0]
                if_exact_match = False
                if_loose_match = False
                for uncompared_idx, uncompared_ids in enumerate(map_choice_source_anchors):
                    if len(this_diff_path_ids) < len(uncompared_ids):
                        continue
                    if len(this_diff_path_ids) == len(uncompared_ids):
                        if this_diff_path_ids == uncompared_ids:
                            if_exact_match = True
                            exact_matched_uncompared_idxs.append(uncompared_idx)
                    elif len(this_diff_path_ids) > len(uncompared_ids):
                        if this_diff_path_ids[:len(uncompared_ids)] == uncompared_ids:
                            if_loose_match = True
                            loose_matched_uncompared_idxs.append(uncompared_idx)
                if not if_exact_match and not if_loose_match:
                    if_valid = False
            filter_matched_uncompared_idxs = []
            matched_uncompared_idxs = []
            matched_uncompared_idxs.extend(exact_matched_uncompared_idxs)
            matched_uncompared_idxs.extend(loose_matched_uncompared_idxs)
            same_source_anchor_paths = []
            for matched_uncompared_idx1 in matched_uncompared_idxs:
                matched_uncompared_idx1_anchor = map_choice_source_anchors[matched_uncompared_idx1]
                if_redundancy = False
                for matched_uncompared_idx2 in matched_uncompared_idxs:
                    if matched_uncompared_idx1 == matched_uncompared_idx2:
                        continue
                    matched_uncompared_idx2_anchor = map_choice_source_anchors[matched_uncompared_idx2]
                    if matched_uncompared_idx1_anchor == matched_uncompared_idx2_anchor:
                        if matched_uncompared_idx1_anchor not in same_source_anchor_paths:
                            same_source_anchor_paths.append(matched_uncompared_idx1_anchor)
                        else:
                            if_redundancy = True
                    elif len(matched_uncompared_idx1_anchor) > len(matched_uncompared_idx2_anchor) and matched_uncompared_idx1_anchor[:len(matched_uncompared_idx2_anchor)] == matched_uncompared_idx2_anchor:
                        if_redundancy = True
                if not if_redundancy:
                    filter_matched_uncompared_idxs.append(matched_uncompared_idx1)

            if_contain_fail_source_path = False
            for matched_uncompared_idx in filter_matched_uncompared_idxs:
                uncompared_ids = map_choice_source_anchors[matched_uncompared_idx][0]
                if uncompared_ids in fail_source_paths:
                    if_contain_fail_source_path = True
            if if_valid and not if_contain_fail_source_path:
                filter_matched_uncompared_idxs = list(set(filter_matched_uncompared_idxs))
                this_possible_subtrees_list = []
                base_trans_trees = copy.deepcopy(map_choice.trans_trees)
                this_possible_subtrees_list.append(base_trans_trees)
                for matched_uncompared_idx in filter_matched_uncompared_idxs:
                    uncompared_ids = map_choice_source_anchors[matched_uncompared_idx]
                    uncompared_target_anchors = map_choice_target_anchors[matched_uncompared_idx]
                    for uncompared_target_anchor in uncompared_target_anchors:
                        uncompared_target_ids = uncompared_target_anchor[0]
                        uncompared_target_stmt_ids = uncompared_target_anchor[1]
                        this_ori_walk_path = ori_walk_path[:]
                        this_ori_walk_path.extend(uncompared_ids)
                        this_ori_walk_path_str = '-'.join([str(this_this_ori_walk_path) for this_this_ori_walk_path in this_ori_walk_path])
                        if this_ori_walk_path_str in succ_infos:
                            return_subtrees = succ_infos[this_ori_walk_path_str]
                        else:
                            return_subtrees, if_search = match_force(ori_tree, this_ori_walk_path, root_node2map,
                                                                     source_lang, target_lang, maps, source_path2tree,
                                                                     trans_path2tree, depth + 1, max_depth,
                                                                     max_possible_choices, start_time, time_limit,
                                                                     if_search)
                            succ_infos['-'.join([str(this_this_ori_walk_path) for this_this_ori_walk_path in this_ori_walk_path])] = return_subtrees
                        if not return_subtrees:
                            fail_source_paths.append(uncompared_ids)
                        # if not return_subtrees:
                        #     return_subtrees = [[MyTree('NO_RESTRICTION', [], True, 'NO_RESTRICTION', -1, [])]]
                        this_time = time.time()
                        if this_time - start_time > time_limit:
                            # return_subtrees = return_subtrees[:1]
                            print('Time out...')
                            return [], if_search
                        this_this_possible_subtrees_list = []
                        for return_subtree in return_subtrees:
                            if len(return_subtree) != 1:
                                continue
                            for this_possible_subtrees in this_possible_subtrees_list:
                                try:
                                    this_this_pre_trans_trees = copy.deepcopy(this_possible_subtrees)
                                    this_this_pre_trans_trees[uncompared_target_stmt_ids].changeChild(uncompared_target_ids, return_subtree[0])
                                    this_this_possible_subtrees_list.append(this_this_pre_trans_trees)
                                except:
                                    continue
                                # this_time = time.time()
                                # if this_time - start_time > time_limit:
                                #     print('Time out...')
                                #     break
                        this_possible_subtrees_list = this_this_possible_subtrees_list[:]
                        # this_possible_subtrees = copy.deepcopy(this_this_possible_subtrees[:MAX_TREES])
                        # print(len(this_possible_subtrees_list))
                        if len(this_possible_subtrees_list) > max_possible_choices:
                            random.shuffle(this_possible_subtrees_list)
                            this_possible_subtrees_list = this_possible_subtrees_list[:max_possible_choices]
                for item1 in this_possible_subtrees_list:
                    # if 'expression_statement-0||||assignment_expression-0||||identifier-0||||=-0||||binary_expression-0||||identifier-0||||/-0||||number_literal-0||||;-0' == '||||'.join(item1[0].getDFS(target_lang)):
                    #     print('')
                    possible_subtrees.append(item1)
            if possible_subtrees:
                continue
                # break
            else:
                if_search = False
        possible_subtrees = get_set(possible_subtrees, source_lang)
        return possible_subtrees, if_search
    elif ori_subtree_path in maps:
        if_search = True
        possible_subtrees = []
        for this_target_tree_paths in maps[ori_subtree_path]:
            # if len(this_target_tree_paths) == 1:
            this_target_trees = [trans_path2tree[this_target_tree_path] for this_target_tree_path in
                                 this_target_tree_paths if this_target_tree_path in trans_path2tree]
            if_contained = False
            for this_possible_subtrees in possible_subtrees:
                if len(this_possible_subtrees) == len(this_target_trees):
                    if_diff = False
                    for this_possible_subtree, this_target_tree in zip(this_possible_subtrees, this_target_trees):
                        this_diff = compare_MyTree(this_target_tree, this_possible_subtree, target_lang)
                        if this_diff:
                            if_diff = True
                    if not if_diff:
                        if_contained = True
            if not if_contained:
                possible_subtrees.append(this_target_trees)
        possible_subtrees = get_set(possible_subtrees, source_lang)
        return possible_subtrees, if_search
    else:
        return [], if_search


def match_force(ori_tree, ori_walk_path, root_node2map, source_lang, target_lang, maps, source_path2tree, trans_path2tree, depth, max_depth, max_possible_choices, start_time, time_limit, if_search):
    print(ori_walk_path)
    this_time = time.time()
    if this_time - start_time > time_limit:
        print('Time out...')
        return [], if_search
    ori_subtree = ori_tree.getChild(ori_walk_path)
    ori_subtree_path = '||||'.join(ori_subtree.getDFS(source_lang))
    ori_subtree_children = ori_subtree.children
    ori_subtree_type = node_type_transfer(source_lang, ori_subtree.type, ori_subtree.text, ori_subtree.variable_names)
    # print(f"{color.BOLD}{depth}{color.END}")
    if depth >= max_depth:
        return [], if_search
    if ori_subtree_path in maps:
        if_search = True
        possible_subtrees = []
        for this_target_tree_paths in maps[ori_subtree_path]:
            # if len(this_target_tree_paths) == 1:
            this_target_trees = [trans_path2tree[this_target_tree_path] for this_target_tree_path in
                                 this_target_tree_paths if this_target_tree_path in trans_path2tree]
            if_contained = False
            for this_possible_subtrees in possible_subtrees:
                if len(this_possible_subtrees) == len(this_target_trees):
                    if_diff = False
                    for this_possible_subtree, this_target_tree in zip(this_possible_subtrees, this_target_trees):
                        this_diff = compare_MyTree(this_target_tree, this_possible_subtree, target_lang)
                        if this_diff:
                            if_diff = True
                    if not if_diff:
                        if_contained = True
            if not if_contained:
                possible_subtrees.append(this_target_trees)
        possible_subtrees = get_set(possible_subtrees, source_lang)
        return possible_subtrees, if_search
    elif ori_subtree_type[0] in root_node2map:
        possible_subtrees = []
        map_choices = root_node2map[ori_subtree_type[0]]
        map_choices_counts = []
        for choice_id, map_choice in enumerate(map_choices):
            if ori_subtree_path == map_choice.source_path:
                continue
            ori_nodes = ori_subtree_path.split('||||')
            choice_nodes = map_choice.source_path.split('||||')
            # same_nodes = [node for node in ori_nodes if node in choice_nodes]
            BLEUscore = nltk.translate.bleu_score.sentence_bleu([ori_nodes], choice_nodes, weights=(0.5, 0.5))
            map_choices_counts.append([BLEUscore, choice_id])
        map_choices_counts.sort(reverse=True)
        fail_source_paths = []
        succ_infos = {}
        for map_choice_id, map_choice_count in enumerate(map_choices_counts):
            map_choice = map_choices[map_choice_count[1]]
            this_time = time.time()
            if this_time - start_time > time_limit:
                print('Time out...')
                break
            # if map_choice.source_tree.text == 'int m = S / 60;':
            #     print('')
            # print(map_choice_id)
            # if map_choice.source_path.startswith('call-0||||'):
            #     print('')
            # if map_choice.source_path.startswith('call-0||||attribute-0||||'):
            #     print('')
            # if map_choice_id in [61, 63, 73, 84]:
            #     print('')
            map_choice_source_anchors = [anchor[0] for anchor in map_choice.anchors]
            map_choice_target_anchors = [anchor[1] for anchor in map_choice.anchors]
            choice_tree_children = map_choice.source_tree.children
            if len(ori_subtree_children) != len(choice_tree_children):
                continue

            diff_paths = compare_MyTree(ori_subtree, map_choice.source_tree, source_lang)
            if not diff_paths:
                raise Exception('I do not think this exception can be triggered...')

            if_valid = True
            exact_matched_uncompared_idxs = []
            loose_matched_uncompared_idxs = []
            for this_diff_path in diff_paths:
                this_diff_path_ids = this_diff_path[0]
                if_exact_match = False
                if_loose_match = False
                for uncompared_idx, uncompared_ids in enumerate(map_choice_source_anchors):
                    if len(this_diff_path_ids) < len(uncompared_ids):
                        continue
                    if len(this_diff_path_ids) == len(uncompared_ids):
                        if this_diff_path_ids == uncompared_ids:
                            if_exact_match = True
                            exact_matched_uncompared_idxs.append(uncompared_idx)
                    elif len(this_diff_path_ids) > len(uncompared_ids):
                        if this_diff_path_ids[:len(uncompared_ids)] == uncompared_ids:
                            if_loose_match = True
                            loose_matched_uncompared_idxs.append(uncompared_idx)
                if not if_exact_match and not if_loose_match:
                    if_valid = False
            filter_matched_uncompared_idxs = []
            matched_uncompared_idxs = []
            matched_uncompared_idxs.extend(exact_matched_uncompared_idxs)
            matched_uncompared_idxs.extend(loose_matched_uncompared_idxs)
            same_source_anchor_paths = []
            for matched_uncompared_idx1 in matched_uncompared_idxs:
                matched_uncompared_idx1_anchor = map_choice_source_anchors[matched_uncompared_idx1]
                if_redundancy = False
                for matched_uncompared_idx2 in matched_uncompared_idxs:
                    if matched_uncompared_idx1 == matched_uncompared_idx2:
                        continue
                    matched_uncompared_idx2_anchor = map_choice_source_anchors[matched_uncompared_idx2]
                    if matched_uncompared_idx1_anchor == matched_uncompared_idx2_anchor:
                        if matched_uncompared_idx1_anchor not in same_source_anchor_paths:
                            same_source_anchor_paths.append(matched_uncompared_idx1_anchor)
                        else:
                            if_redundancy = True
                    elif len(matched_uncompared_idx1_anchor) > len(
                            matched_uncompared_idx2_anchor) and matched_uncompared_idx1_anchor[
                                                                :len(matched_uncompared_idx2_anchor)] == matched_uncompared_idx2_anchor:
                        if_redundancy = True
                if not if_redundancy:
                    filter_matched_uncompared_idxs.append(matched_uncompared_idx1)

            if_contain_fail_source_path = False
            for matched_uncompared_idx in filter_matched_uncompared_idxs:
                uncompared_ids = map_choice_source_anchors[matched_uncompared_idx][0]
                if uncompared_ids in fail_source_paths:
                    if_contain_fail_source_path = True
            if if_valid and not if_contain_fail_source_path:
                filter_matched_uncompared_idxs = list(set(filter_matched_uncompared_idxs))
                this_possible_subtrees_list = []
                base_trans_trees = copy.deepcopy(map_choice.trans_trees)
                this_possible_subtrees_list.append(base_trans_trees)
                for matched_uncompared_idx in filter_matched_uncompared_idxs:
                    uncompared_ids = map_choice_source_anchors[matched_uncompared_idx]
                    uncompared_target_anchors = map_choice_target_anchors[matched_uncompared_idx]
                    for uncompared_target_anchor in uncompared_target_anchors:
                        uncompared_target_ids = uncompared_target_anchor[0]
                        uncompared_target_stmt_ids = uncompared_target_anchor[1]
                        this_ori_walk_path = ori_walk_path[:]
                        this_ori_walk_path.extend(uncompared_ids)
                        this_ori_walk_path_str = '-'.join(
                            [str(this_this_ori_walk_path) for this_this_ori_walk_path in this_ori_walk_path])
                        if this_ori_walk_path_str in succ_infos:
                            return_subtrees = succ_infos[this_ori_walk_path_str]
                        else:
                            return_subtrees, if_search = match_force(ori_tree, this_ori_walk_path, root_node2map,
                                                                     source_lang, target_lang, maps, source_path2tree,
                                                                     trans_path2tree, depth + 1, max_depth,
                                                                     max_possible_choices, start_time, time_limit,
                                                                     if_search)
                            succ_infos['-'.join([str(this_this_ori_walk_path) for this_this_ori_walk_path in
                                                 this_ori_walk_path])] = return_subtrees
                        if not return_subtrees:
                            fail_source_paths.append(uncompared_ids)
                        # if not return_subtrees:
                        #     return_subtrees = [[MyTree('NO_RESTRICTION', [], True, 'NO_RESTRICTION', -1, [])]]
                        this_time = time.time()
                        if this_time - start_time > time_limit:
                            # return_subtrees = return_subtrees[:1]
                            print('Time out...')
                            return [], if_search
                        this_this_possible_subtrees_list = []
                        for return_subtree in return_subtrees:
                            if len(return_subtree) != 1:
                                continue
                            for this_possible_subtrees in this_possible_subtrees_list:
                                try:
                                    this_this_pre_trans_trees = copy.deepcopy(this_possible_subtrees)
                                    this_this_pre_trans_trees[uncompared_target_stmt_ids].changeChild(
                                        uncompared_target_ids, return_subtree[0])
                                    this_this_possible_subtrees_list.append(this_this_pre_trans_trees)
                                except:
                                    continue
                                # this_time = time.time()
                                # if this_time - start_time > time_limit:
                                #     print('Time out...')
                                #     break
                        this_possible_subtrees_list = this_this_possible_subtrees_list[:]
                        # this_possible_subtrees = copy.deepcopy(this_this_possible_subtrees[:MAX_TREES])
                        # print(len(this_possible_subtrees_list))
                        if len(this_possible_subtrees_list) > max_possible_choices:
                            random.shuffle(this_possible_subtrees_list)
                            this_possible_subtrees_list = this_possible_subtrees_list[:max_possible_choices]
                for item1 in this_possible_subtrees_list:
                    possible_subtrees.append(item1)
            if possible_subtrees:
                continue
                # break
            else:
                if_search = False
        possible_subtrees = get_set(possible_subtrees, source_lang)
        return possible_subtrees, if_search
    else:
        return [], if_search


class MyMap(object):
    def __init__(self, source_lang, trans_lang, source_path, target_paths, source_tree, trans_trees, anchors):
        self.source_lang = source_lang
        self.trans_lang = trans_lang
        self.source_path = source_path
        self.target_paths = target_paths
        self.source_tree = source_tree
        self.trans_trees = trans_trees
        self.anchors = anchors

    def addAnchor(self, new_anchor, if_force=False):
        if_conflict = self.check_anchor_conflict(new_anchor)
        if if_force:
            if_conflict = False
        if_add = False
        if not if_conflict:
            for anchor_id, anchor in enumerate(self.anchors):
                if new_anchor[0] == anchor[0]:
                    self.anchors[anchor_id][1].append([new_anchor[1], new_anchor[2]])
                    if_add = True
            if not if_add:
                self.anchors.append([new_anchor[0], [[new_anchor[1], new_anchor[2]]]])
                if_add = True
        return if_add

    def check_anchor_conflict(self, new_anchor):
        for anchor in self.anchors:
            if new_anchor[0] == anchor[0]:
                for t_anchor in anchor[1]:
                    if t_anchor[1] == new_anchor[2]:
                        if t_anchor[0] == new_anchor[1]:
                            return True
                        elif len(t_anchor[0]) > len(new_anchor[1]) and t_anchor[0][:len(new_anchor[1])] == new_anchor[1]:
                            return True
                        elif len(t_anchor[0]) < len(new_anchor[1]) and t_anchor[0] == new_anchor[1][:len(t_anchor[0])]:
                            return True
            elif len(anchor[0]) > len(new_anchor[0]) and anchor[0][:len(new_anchor[0])] == new_anchor[0]:
                for t_anchor in anchor[1]:
                    if t_anchor[1] == new_anchor[2]:
                        if t_anchor[0] == new_anchor[1]:
                            continue
                        elif len(t_anchor[0]) > len(new_anchor[1]) and t_anchor[0][:len(new_anchor[1])] == new_anchor[1]:
                            continue
                        elif len(t_anchor[0]) < len(new_anchor[1]) and t_anchor[0] == new_anchor[1][:len(t_anchor[0])]:
                            return True
                        else:
                            return True
            elif len(anchor[0]) < len(new_anchor[0]) and anchor[0] == new_anchor[0][:len(anchor[0])]:
                for t_anchor in anchor[1]:
                    if t_anchor[1] == new_anchor[2]:
                        if t_anchor[0] == new_anchor[1]:
                            continue
                        elif len(t_anchor[0]) > len(new_anchor[1]) and t_anchor[0][:len(new_anchor[1])] == new_anchor[1]:
                            return True
                        elif len(t_anchor[0]) < len(new_anchor[1]) and t_anchor[0] == new_anchor[1][:len(t_anchor[0])]:
                            continue
                        else:
                            return True
            else:
                for t_anchor in anchor[1]:
                    if t_anchor[1] == new_anchor[2]:
                        if t_anchor[0] == new_anchor[1]:
                            return True
                        elif len(t_anchor[0]) > len(new_anchor[1]) and t_anchor[0][:len(new_anchor[1])] == new_anchor[1]:
                            return True
                        elif len(t_anchor[0]) < len(new_anchor[1]) and t_anchor[0] == new_anchor[1][:len(t_anchor[0])]:
                            return True
                        else:
                            continue
        return False


class MyTree(object):
    def __init__(self, type, children, is_named, text, line_id, variable_names):
        self.type = type
        self.children = children
        self.is_named = is_named
        self.text = text
        self.line_id = line_id
        self.variable_names = variable_names

    def addChild(self, child):
        self.children.append(child)

    def getChild(self, path):
        this_tree = MyTree(self.type, copy.deepcopy(self.children), self.is_named, self.text, self.line_id, self.variable_names)
        for path_id in path:
            this_tree = this_tree.children[path_id]
        return this_tree

    def getDFS(self, lang):
        nodes = []
        node_types = node_type_transfer(lang, self.type, self.text, self.variable_names)
        nodes.extend(node_types)
        for child in self.children:
            this_nodes = child.getDFS(lang)
            nodes.extend(this_nodes)
        return nodes

    def copy(self, newtree):
        self.type = newtree.type
        self.children = newtree.children
        self.is_named = newtree.is_named
        self.text = newtree.text
        self.line_id = newtree.line_id

    def changeChild(self, path, new_child):
        if len(path) == 1:
            self.children[path[0]].copy(new_child)
        elif len(path) == 2:
            self.children[path[0]].children[path[1]].copy(new_child)
        elif len(path) == 3:
            self.children[path[0]].children[path[1]].children[path[2]].copy(new_child)
        elif len(path) == 4:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].copy(new_child)
        elif len(path) == 5:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].copy(new_child)
        elif len(path) == 6:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].children[path[5]].copy(new_child)
        elif len(path) == 7:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].children[path[5]].children[path[6]].copy(new_child)
        elif len(path) == 8:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].children[path[5]].children[path[6]].children[path[7]].copy(new_child)
        elif len(path) == 9:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].children[path[5]].children[path[6]].children[path[7]].children[path[8]].copy(new_child)
        elif len(path) == 10:
            self.children[path[0]].children[path[1]].children[path[2]].children[path[3]].children[path[4]].children[path[5]].children[path[6]].children[path[7]].children[path[8]].children[path[9]].copy(new_child)
        else:
            raise Exception('Unsupported Depth')


def diff_MyTree(tree1, tree2, lang, path=None, brother=0, pre_node=None):
    if path is None:  # 需要该以下，在要求是identifier-0
        path = []
    if tree1.type == 'NO_RESTRICTION' or tree2.type == 'NO_RESTRICTION':
        None
    elif node_type_transfer(lang, tree1.type, tree1.text, tree1.variable_names) != node_type_transfer(lang, tree2.type, tree2.text, tree2.variable_names):
        if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
            yield [path, '=']
        elif brother:
            yield [path, 'diff_type']
        # elif tree1.type == 'parenthesized_expression' or tree2.type == 'parenthesized_expression':
        #     yield [path, 'parenthesized_expression']
        else:
            yield [path, 'diff_type']
    elif len(tree1.children) != len(tree2.children):
        if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
            yield [path, '=']
        elif brother:
            yield [path, 'diff_children']
        # elif tree1.type == 'parenthesized_expression' or tree2.type == 'parenthesized_expression':
        #     yield [path, 'parenthesized_expression']
        else:
            yield [path, 'diff_children']
    # elif tree1.type == 'parenthesized_expression' and tree2.type == 'parenthesized_expression':
    #     print('')
    else:
        brother = brother + len(tree1.children) - 1
        pre_node = None
        for child_id in range(len(tree1.children)):
            this_path = copy.deepcopy(path)
            this_path.append(child_id)
            if tree1.children[child_id].type == 'NO_RESTRICTION' or tree2.children[child_id].type == 'NO_RESTRICTION':
                None
            elif node_type_transfer(lang, tree1.children[child_id].type, tree1.children[child_id].text, tree1.children[child_id].variable_names) != node_type_transfer(lang, tree2.children[child_id].type, tree2.children[child_id].text, tree2.children[child_id].variable_names):
                # if tree1.type == 'parenthesized_expression' and tree2.type == 'parenthesized_expression':
                #     yield [path, 'parenthesized_expression']
                if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
                    yield [this_path, '=']
                elif brother:
                    yield [this_path, 'diff_type']
                else:
                    yield [this_path, 'diff_type']
            elif len(tree1.children[child_id].children) != len(tree2.children[child_id].children):
                # if tree1.type == 'parenthesized_expression' and tree2.type == 'parenthesized_expression':
                #     yield [path, 'parenthesized_expression']
                if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
                    yield [this_path, '=']
                elif brother:
                    yield [this_path, 'diff_children']
                else:
                    yield [this_path, 'diff_children']
            else:
                for diff_path in diff_MyTree(tree1.children[child_id], tree2.children[child_id], lang, path=this_path, brother=brother, pre_node=pre_node):
                    yield diff_path
            pre_node = tree1.children[child_id].type


def compare_MyTree(tree1, tree2, lang):
    diff_paths = []
    for diff_path in diff_MyTree(tree1, tree2, lang, brother=0, pre_node=None):
        if diff_path:
            diff_paths.append(diff_path)
    # if diff_paths and diff_paths[0][0] == []:
    #     print('')
    return diff_paths


def compare_node_type(target_list, type_list):
    if len(target_list) != len(type_list):
        return False
    if_match = True
    for target, type in zip(target_list, type_list):
        if target.endswith('-0'):
            target_list = target.split('-')
            target_name = '-'.join(target_list[:-1])
            type_list = type.split('-')
            type_name = '-'.join(type_list[:-1])
            if target_name != type_name and target_name != 'identifier':
                if_match = False
        else:
            if target != type:
                if_match = False
    return if_match


def diff_MyTree_loose(tree1, tree2, lang, path=None, brother=0, pre_node=None):
    if path is None:  # 需要该以下，在要求是identifier-0
        path = []
    if tree1.type == 'NO_RESTRICTION' or tree2.type == 'NO_RESTRICTION':
        None
    elif not compare_node_type(node_type_transfer(lang, tree1.type, tree1.text, tree1.variable_names), node_type_transfer(lang, tree2.type, tree2.text, tree2.variable_names)):
        if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
            yield [path, '=']
        elif brother:
            yield [path, 'diff_type']
        else:
            yield [path, 'backbone']
    elif len(tree1.children) != len(tree2.children):
        if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
            yield [path, '=']
        elif brother:
            yield [path, 'diff_children']
        else:
            yield [path, 'backbone']
    else:
        brother = brother + len(tree1.children) - 1
        pre_node = None
        for child_id in range(len(tree1.children)):
            this_path = copy.deepcopy(path)
            this_path.append(child_id)
            if tree1.children[child_id].type == 'NO_RESTRICTION' or tree2.children[child_id].type == 'NO_RESTRICTION':
                None
            elif not compare_node_type(node_type_transfer(lang, tree1.children[child_id].type, tree1.children[child_id].text, tree1.children[child_id].variable_names), node_type_transfer(lang, tree2.children[child_id].type, tree2.children[child_id].text, tree2.children[child_id].variable_names)):
                if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
                    yield [this_path, '=']
                elif brother:
                    yield [this_path, 'diff_type']
                else:
                    yield [this_path, 'backbone']
            elif len(tree1.children[child_id].children) != len(tree2.children[child_id].children):
                if pre_node in ['=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|=']:
                    yield [this_path, '=']
                elif brother:
                    yield [this_path, 'diff_children']
                else:
                    yield [this_path, 'backbone']
            else:
                for diff_path in diff_MyTree_loose(tree1.children[child_id], tree2.children[child_id], lang, path=this_path, brother=brother, pre_node=pre_node):
                    yield diff_path
            pre_node = tree1.children[child_id].type


def compare_MyTree_loose(tree1, tree2, lang):
    diff_paths = []
    for diff_path in diff_MyTree_loose(tree1, tree2, lang, brother=0, pre_node=None):
        if diff_path:
            diff_paths.append(diff_path)
    return diff_paths


def path2nodes(path):
    if '||||' in path:
        return path.split('||||')
    else:
        return [path]


def traverse_tree2subtrees(node, path, records):
    for n_id, n in enumerate(node.children):
        this_path = copy.deepcopy(path)
        this_path.append(n_id)
        this_subtree = copy.deepcopy(n)
        records.append([this_path, this_subtree])
        traverse_tree2subtrees(n, this_path, records)


def traverse_tree2MyTree(node, root_node, lang, variable_names, if_exclude_block=False, if_exclude_last_child=False):
    if if_exclude_last_child:
        for n_id, n in enumerate(node.children):
            if n_id != len(node.children)-1:
                this_node = MyTree(n.type, [], n.is_named, n.text.decode("utf-8"), n.start_point[0], variable_names)
                root_node.addChild(this_node)
                traverse_tree2MyTree(n, this_node, lang, variable_names, if_exclude_block=False)
            else:
                if lang == 'Python':
                    this_node = MyTree('block', [], True, '', n.start_point[0], variable_names)
                    root_node.addChild(this_node)
                elif lang == 'Java':
                    this_node = MyTree('block', [], True, '', n.start_point[0], variable_names)
                    root_node.addChild(this_node)
                elif lang == 'C++':
                    this_node = MyTree('compound_statement', [], True, '', n.start_point[0], variable_names)
                    root_node.addChild(this_node)
    elif if_exclude_block:
        pre_n_type = ''
        for n_id, n in enumerate(node.children):
            this_node = MyTree(n.type, [], n.is_named, n.text.decode("utf-8"), n.start_point[0], variable_names)
            if pre_n_type == 'else':
                pre_n_type = n.type
                continue
            root_node.addChild(this_node)
            if not (lang == 'Python' and n.type in python_block_name) and not (lang == 'Java' and n.type in java_block_name) and not ( lang == 'C++' and n.type in cpp_block_name):
                traverse_tree2MyTree(n, this_node, lang, variable_names, if_exclude_block=False)
            pre_n_type = n.type
    else:
        for n_id, n in enumerate(node.children):
            this_node = MyTree(n.type, [], n.is_named, n.text.decode("utf-8"), n.start_point[0], variable_names)
            root_node.addChild(this_node)
            traverse_tree2MyTree(n, this_node, lang, variable_names, if_exclude_block=False)


def tree2MyTree(treesitter_tree, lang, variable_names, if_exclude_block=False, if_exclude_last_child=False):
    if type(treesitter_tree) == Node:
        mytree = MyTree(treesitter_tree.type, [], treesitter_tree.is_named, treesitter_tree.text.decode("utf-8"), treesitter_tree.start_point[0], variable_names)
        traverse_tree2MyTree(treesitter_tree, mytree, lang, variable_names, if_exclude_block=if_exclude_block, if_exclude_last_child=if_exclude_last_child)
        return mytree
    else:
        mytree = MyTree(treesitter_tree.root_node.type, [], treesitter_tree.root_node.is_named, treesitter_tree.root_node.text.decode("utf-8"), treesitter_tree.root_node.start_point[0], variable_names)
        traverse_tree2MyTree(treesitter_tree.root_node, mytree, lang, variable_names, if_exclude_block=if_exclude_block, if_exclude_last_child=if_exclude_last_child)
        return mytree


def tree2MyTree_if_else(treesitter_tree, lang, variable_names, if_exclude_block=False, if_exclude_last_child=False):
    mytree = MyTree(treesitter_tree.type, [], treesitter_tree.is_named, treesitter_tree.text.decode("utf-8"), treesitter_tree.start_point[0], variable_names)
    traverse_tree2MyTree_if_else(treesitter_tree, mytree, lang, variable_names, if_exclude_block=if_exclude_block, if_exclude_last_child=if_exclude_last_child)
    return mytree


def traverse_tree2MyTree_if_else(node, root_node, lang, variable_names, if_exclude_block=False, if_exclude_last_child=False):
    for n_id, n in enumerate(node.children[:4]):
        if n_id in [0, 1]:
            this_node = MyTree(n.type, [], n.is_named, n.text.decode("utf-8"), n.start_point[0], variable_names)
            root_node.addChild(this_node)
            traverse_tree2MyTree(n, this_node, lang, variable_names, if_exclude_block=False)
        elif n_id in [2]:
            if lang == 'Java':
                this_node = MyTree('block', [], True, '', n.start_point[0], variable_names)
                root_node.addChild(this_node)
            elif lang == 'C++':
                this_node = MyTree('compound_statement', [], True, '', n.start_point[0], variable_names)
                root_node.addChild(this_node)
        elif n_id in [3]:
            this_node = MyTree('else', [], False, '', n.start_point[0], variable_names)
            root_node.addChild(this_node)


def load_map(file_path):
    maps = {}
    f_map = open(file_path)
    map_lines = f_map.readlines()
    f_map.close()
    count_1to1 = 0
    count_1ton = 0
    for map_line in map_lines:
        if not map_line.strip():
            continue
        info = map_line.strip().split('\t')
        source_path = info[0]
        mapped_paths = info[1]
        if '####' in mapped_paths:
            mapped_paths = mapped_paths.split('####')
            count_1to1 += 1
        else:
            mapped_paths = [mapped_paths]
            count_1ton += 1
        if source_path not in maps:
            maps[source_path] = [mapped_paths]
        else:
            maps[source_path].append(mapped_paths)
    return maps


def load_map_for_locate(file_path):
    maps = {}
    f_map = open(file_path)
    map_lines = f_map.readlines()
    f_map.close()
    for map_line in map_lines:
        if not map_line.strip():
            continue
        info = map_line.strip().split('\t')
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
    # for k, v in maps.items():
    #     if len(v) != 1 and len(v) != 2:
    #         print('')
    # print('')
    maps['identifier-0'] = [['identifier-0']]
    return maps


def traverse_tree_ERROR(node, record):
    for n_id, n in enumerate(node.children):
        if n.type == 'ERROR':
            record.append(n.type)
        traverse_tree_ERROR(n, record)


def validate_tree(tree):
    contained_error = []
    traverse_tree_ERROR(tree, contained_error)
    if contained_error:
        return False
    else:
        return True


def load_maps2trees(task_name):
    tree_dir = f'{task_name}/maps2tree'
    f_map_info = open(f'{tree_dir}/info.txt', 'r')
    lines = f_map_info.readlines()
    maps2trees = {}
    for id, line in enumerate(lines):
        this_map = line.strip()
        with open(f'{tree_dir}/{id}.pkl', 'rb') as f:
            this_trees = pickle.load(f)
            maps2trees[this_map] = this_trees
    return maps2trees


def save_maps2trees(task_name, map, trees):
    tree_dir = f'{task_name}/maps2tree'
    if not os.path.exists(tree_dir):
        os.makedirs(tree_dir, exist_ok=True)
    info_path = f'{tree_dir}/info.txt'
    f_map_info = open(info_path, 'a')
    print(map, file=f_map_info)
    f_map_info.close()
    exis_files = os.listdir(tree_dir)
    id = len(exis_files) - 1
    outp = open(f'{tree_dir}/{id}.pkl', 'wb')
    pickle.dump(trees, outp, pickle.HIGHEST_PROTOCOL)
    outp.close()


def update_maps2trees(task_name, maps2trees):
    tree_dir = f'{task_name}/maps2tree'
    os.makedirs(tree_dir, exist_ok=True)
    exist_files = os.listdir(tree_dir)
    for exist_file in exist_files:
        if os.path.isdir(f'{tree_dir}/{exist_file}'):
            shutil.rmtree(f'{tree_dir}/{exist_file}')
        else:
            os.remove(f'{tree_dir}/{exist_file}')
    f_map_info = open(f'{tree_dir}/info.txt', 'w')
    id = 0
    for map, trees in maps2trees.items():
        print(map, file=f_map_info)
        outp = open(f'{tree_dir}/{id}.pkl', 'wb')
        pickle.dump(trees, outp, pickle.HIGHEST_PROTOCOL)
        outp.close()
        id += 1
    f_map_info.close()


def check_new_rule(task_name, path):
    tree_dir = f'{task_name}'
    if os.path.exists(tree_dir):
        f_map_info = open(f'{tree_dir}/info.txt', 'r')
        lines = f_map_info.readlines()
        for id, line in enumerate(lines):
            if path == line.strip():
                with open(f'{tree_dir}/{id}.pkl', 'rb') as f:
                    this_trees = pickle.load(f)
                    return True, this_trees
    return False, []


def save_new_rule(task_name, ori_path, target_trees):
    tree_dir = f'{task_name}'
    os.makedirs(tree_dir, exist_ok=True)
    if os.path.exists(f'{tree_dir}/info.txt'):
        f_map_info = open(f'{tree_dir}/info.txt', 'r')
        lines = [line for line in f_map_info.readlines() if line.strip()]
        f_map_info.close()
    else:
        lines = []

    id = len(lines)
    outp = open(f'{tree_dir}/{id}.pkl', 'wb')
    pickle.dump(target_trees, outp, pickle.HIGHEST_PROTOCOL)
    outp.close()

    f_map_info = open(f'{tree_dir}/info.txt', 'a')
    print(ori_path, file=f_map_info)
    f_map_info.close()



def load_path2pair(task_name, source_lang, target_lang, loop_time):
    tree_dir = f'{task_name}/{source_lang}-{target_lang}-path2pair-{loop_time}'
    if os.path.isdir(tree_dir):
        f_map_info = open(f'{tree_dir}/info.txt', 'r')
        lines = f_map_info.readlines()
        root_node2map = {}
        for id, line in enumerate(lines):
            this_path = line.strip()
            f = open(f'{tree_dir}/{id}.pkl', 'rb')
            this_map = pickle.load(f)
            f.close()
            if this_path not in root_node2map:
                root_node2map[this_path] = [this_map]
            else:
                root_node2map[this_path].append(this_map)
        return root_node2map
    return {}


def save_path2pair(task_name, path2tree, source_lang, target_lang, loop_time):
    tree_dir = f'{task_name}/{source_lang}-{target_lang}-path2pair-{loop_time}'
    os.makedirs(tree_dir, exist_ok=True)
    exist_files = os.listdir(tree_dir)
    for exist_file in exist_files:
        if os.path.isdir(f'{tree_dir}/{exist_file}'):
            shutil.rmtree(f'{tree_dir}/{exist_file}')
        else:
            os.remove(f'{tree_dir}/{exist_file}')
    f_map_info = open(f'{tree_dir}/info.txt', 'w')
    id = 0
    for k, val in path2tree.items():
        for v in val:
            print(k, file=f_map_info)
            outp = open(f'{tree_dir}/{id}.pkl', 'wb')
            pickle.dump(v, outp, pickle.HIGHEST_PROTOCOL)
            outp.close()
            id += 1
    f_map_info.close()


def init_count(nonleaf_nodes, leaf_nodes, mul_leaf_nodes):
    nonleaf_counts = {}
    for k, v in nonleaf_nodes.items():
        nonleaf_counts[k] = [0 for _ in range(v)]
    leaf_counts = {}
    for k, v in leaf_nodes.items():
        leaf_counts[k] = [0 for _ in range(v)]
    mul_leaf_counts = {}
    for k, v in mul_leaf_nodes.items():
        mul_leaf_counts[k] = [0 for _ in range(v)]
    return nonleaf_counts, leaf_counts, mul_leaf_counts


def read_node_file(lang):
    if lang == 'C++':
        f_in = open('node/cpp-node-types.json', 'r')
        nodes = json.load(f_in)
        mul_leaf_nodes = {'comment':2, 'primitive_type':8, 'number_literal':11, 'escape_sequence':15, 'string_content':26, 'preproc_directive':4, 'identifier':546, 'type_identifier': 17, 'field_identifier':546}
        nonleaf_nodes = {}
        leaf_nodes = {}
        for node in nodes:
            if node['type'] in mul_leaf_nodes:
                continue
            elif ('fields' in node.keys() and node['fields'] != {}) or ('children' in node.keys() and node['children'] != {}):
                nonleaf_nodes[node['type']] = 1
            else:
                if node['type'][0] == '_':
                    continue
                leaf_nodes[node['type']] = 1
        # nonleafnodes_dict = {}
        # for k, v in nonleaf_nodes.items():
        #     for id in range(v):
        #         nonleafnodes_dict[f'{k}-{id}'] = []
        return nonleaf_nodes
    elif lang == 'Python':
        f_in = open('node/python-node-types.json', 'r')
        nodes = json.load(f_in)
        mul_leaf_nodes = {'float':4, 'integer':3, 'escape_sequence':10, 'string_start':3, 'identifier':73}
        nonleaf_nodes = {}
        leaf_nodes = {}
        operator_nodes = []
        for node in nodes:
            if node['type'] in mul_leaf_nodes:
                continue
            elif ('fields' in node.keys() and node['fields'] != {}) or ('children' in node.keys() and node['children'] != {}):
                nonleaf_nodes[node['type']] = 1
            else:
                if node['type'][0] == '_':
                    continue
                leaf_nodes[node['type']] = 1
            if node['type'] in ['binary_operator', 'boolean_operator']:
                operator_nodes.extend([this_type['type'] for this_type in node['fields']['operator']['types']])
        # nonleafnodes_dict = {}
        # for k, v in nonleaf_nodes.items():
        #     for id in range(v):
        #         nonleafnodes_dict[f'{k}-{id}'] = []
        return nonleaf_nodes, operator_nodes
    elif lang == 'Java':
        f_in = open('node/java-node-types.json', 'r')
        nodes = json.load(f_in)
        mul_leaf_nodes = {'string_fragment': 15, 'decimal_integer_literal': 2, 'decimal_floating_point_literal': 4, 'escape_sequence': 9, 'identifier': 108, 'type_identifier':80}
        nonleaf_nodes = {}
        leaf_nodes = {}
        operator_nodes = []
        for node in nodes:
            if node['type'] in mul_leaf_nodes:
                continue
            elif ('fields' in node.keys() and node['fields'] != {}) or ('children' in node.keys() and node['children'] != {}):
                nonleaf_nodes[node['type']] = 1
            else:
                if node['type'][0] == '_':
                    continue
                leaf_nodes[node['type']] = 1
            if node['type'] == 'binary_expression':
                operator_nodes.extend([this_type['type'] for this_type in node['fields']['operator']['types']])
        # nonleafnodes_dict = {}
        # for k, v in nonleaf_nodes.items():
        #     for id in range(v):
        #         nonleafnodes_dict[f'{k}-{id}'] = []
        return nonleaf_nodes, operator_nodes
    else:
        raise Exception("Unsupported Language!")


def check_node_exist(lang, node_type, node_str, variable_names):
    if lang == 'C++':
        if node_type == 'comment':
            contained_Ft, length = C_comment(node_str)
            return contained_Ft
        if node_type == 'primitive_type':
            contained_Ft, length = C_primitive_type(node_str)
            return contained_Ft
        if node_type == 'number_literal':
            contained_Ft, length = C_number_literal(node_str)
            return contained_Ft
        if node_type == 'escape_sequence':
            contained_Ft, length = C_escape_sequence(node_str)
            return contained_Ft
        if node_type == 'string_content':
            contained_Ft, length = C_string_content(node_str)
            return contained_Ft
        if node_type == 'preproc_directive':
            contained_Ft, length = C_preproc_directive(node_str)
            return contained_Ft
        if node_type == 'identifier':
            if node_str in variable_names:
                return [0]
            contained_Ft, length = Cpp_identifier(node_str)
            return contained_Ft
        if node_type == 'type_identifier':
            contained_Ft, length = Cpp_type_identifier(node_str)
            return contained_Ft
        if node_type == 'field_identifier':
            contained_Ft, length = Cpp_field_identifier(node_str)
            return contained_Ft
        return [0]
    elif lang == 'Python':
        if node_type == 'float':
            contained_Ft, length = Python_float(node_str)
            return contained_Ft
        if node_type == 'integer':
            contained_Ft, length = Python_integer(node_str)
            return contained_Ft
        if node_type == 'escape_sequence':
            contained_Ft, length = Python_escape_sequence(node_str)
            return contained_Ft
        if node_type == 'string_start':
            contained_Ft, length = Python_string_start(node_str)
            return contained_Ft
        if node_type == 'identifier':
            if node_str in variable_names:
                return [0]
            contained_Ft, length = Python_identifier(node_str)
            return contained_Ft
        return [0]
    elif lang == 'Java':
        if node_type == 'string_fragment':
            contained_Ft, length = Java_string_fragment(node_str)
            return contained_Ft
        if node_type == 'decimal_integer_literal':
            contained_Ft, length = Java_decimal_integer_literal(node_str)
            return contained_Ft
        if node_type == 'decimal_floating_point_literal':
            contained_Ft, length = Java_decimal_floating_point_literal(node_str)
            return contained_Ft
        if node_type == 'escape_sequence':
            contained_Ft, length = Java_escape_sequence(node_str)
            return contained_Ft
        if node_type == 'identifier':
            if node_str in variable_names:
                return [0]
            contained_Ft, length = Java_identifier(node_str)
            return contained_Ft
        if node_type == 'type_identifier':
            contained_Ft, length = Java_type_identifier(node_str)
            return contained_Ft
        return [0]


def Java_string_fragment(node_str):
    contained_Ft = []
    templates = ['%a', '%b', '%c', '%d', '%e', '%f', '%g', '%h', '%n', '%o', '%s', '%t', '%x', '%.']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id+1)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 15


def Java_decimal_integer_literal(node_str):
    contained_Ft = []
    if node_str[-1] == 'l' or node_str[-1] == 'L':
        contained_Ft.append(1)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 2


def Java_decimal_floating_point_literal(node_str):
    contained_Ft = []
    if node_str[-1] == 'f' or node_str[-1] == 'F':
        contained_Ft.append(1)
    if node_str[-1] == 'd' or node_str[-1] == 'D':
        contained_Ft.append(2)
    if '.' in node_str:
        contained_Ft.append(3)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 4


def Java_escape_sequence(node_str):
    contained_Ft = []
    templates = ['\\t', '\\b', "\\'", '\\f', '\\"', '\\n', '\\r', '\\:', '\\\\']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id)
    return contained_Ft, 9


def Java_identifier(node_str):
    contained_Ft = []
    templates = ['onClose', 'parallelPrefix', 'element', 'TITLECASE_LETTER', 'doubleStream', 'reduce', 'setDSTSavings',
                 'getDisplayCountry', 'floorMod', 'emptyLongSpliterator', 'MARCH', 'after', 'OptionalLong',
                 'setTimeOfDay', 'getRawOffset', 'concat', 'ArrayDeque', 'inheritedChannel', 'isNull', 'longStream',
                 'PRIVATE_USE', 'Characteristics', 'reset', 'getISO3Language', 'getName', 'Vector', 'nextFloat',
                 'MILLISECOND', 'stop', 'getVariant', 'cos', 'clearExtensions', 'CONTROL', 'toCharArray',
                 'getAnnotatedSuperclass', 'hasNext', 'getLast', 'checkedSortedMap', 'nanoTime', 'SuppressWarnings',
                 'flip', 'unmodifiableSortedMap', 'setFirstDayOfWeek', 'getActions', 'get', 'setContextClassLoader',
                 'PropertyResourceBundle', 'FIELD_COUNT', 'isDigit', 'wrap', 'exec', 'nextUp', 'redirectInput',
                 'TreeMap', 'loadClass', 'rotate', 'descendingIterator', 'currentClassLoader', 'isTitleCase',
                 'notifyAll', 'clearAssertionStatus', 'subSet', 'comparing', 'FORMAT', 'halt',
                 'newPermissionCollection', 'isJavaLetter', 'SortedSet', 'map', 'Collectors', 'PRIVATE_USE_EXTENSION',
                 'FINAL_QUOTE_PUNCTUATION', 'getInstance', 'AssertionError', 'thenComparingLong',
                 'DIRECTIONALITY_SEGMENT_SEPARATOR', 'limit', 'NoSuchElementException', 'synchronizedCollection',
                 'synchronizedSortedSet', 'checkTopLevelWindow', 'Builder', 'FEBRUARY', 'Boolean',
                 'getAvailableCurrencies', 'TTL_NO_EXPIRATION_CONTROL', 'setSigners', 'finalize', 'Decoder',
                 'navigableKeySet', 'ClassValue', 'delimiter', 'divideUnsigned', 'getMax', 'noneOf', 'checkAccess',
                 'chars', 'IllegalStateException', 'getFormats', 'computeFields', 'emptySpliterator', 'ENGLISH',
                 'comparingDouble', 'Spliterators', 'WeakHashMap', 'useRadix', 'traceInstructions', 'isParallel',
                 'IdentityHashMap', 'toLowerCase', 'END_PUNCTUATION', 'ordinal', 'setScript', 'deleteObserver',
                 'NEGATIVE_INFINITY', 'needsReload', 'Runtime', 'mapToDouble', 'BaseStream', 'checkMemberAccess',
                 'DIRECTIONALITY_OTHER_NEUTRALS', 'isWeekDateSupported', 'schedule', 'isLeapYear',
                 'IllegalThreadStateException', 'destroyForcibly', 'getSeconds', 'radix', 'getAllStackTraces', 'add',
                 'parallelStream', 'getWeeksInWeekYear', 'findLibrary', 'CharSequence', 'definePackage', 'Deque',
                 'Stack', 'unmodifiableNavigableSet', 'containsAll', 'DIRECTIONALITY_NONSPACING_MARK', 'subSequence',
                 'LINE_SEPARATOR', 'MIN_PRIORITY', 'isBmpCodePoint', 'getDeclaredConstructor', 'start', 'isNaN',
                 'equalsIgnoreCase', 'ResourceBundle.Control', 'getMaxPriority', 'isHighSurrogate', 'TreeSet',
                 'isValidCodePoint', 'toZoneId', 'getHours', 'forLanguageTag', 'floatValue', 'lower', 'CHINA',
                 'AbstractIntSpliterator', 'InheritableThreadLocal', 'filter', 'indexOf', 'valueOf', 'toRadians',
                 'Iterator', 'listIterator', 'reversed', 'checkMulticast', 'getTypeName', 'LinkageError',
                 'POSITIVE_INFINITY', 'getTimeZone', 'copy', 'countStackFrames', 'E', 'Dictionary', 'setName',
                 'checkedSortedSet', 'random', 'tailSet', 'getFirst', 'AbstractDoubleSpliterator', 'type',
                 'FormatFlagsConversionMismatchException', 'identityHashCode', 'lineSeparator', 'getWeight', 'rint',
                 'file', 'SecurityManager', 'fill', 'AbstractQueue', 'getActualMinimum', 'ceilingEntry',
                 'ExceptionInInitializerError', 'parse', 'in', 'classLoaderDepth', 'getGreatestMinimum', 'isDaemon',
                 'getDisplayScript', 'getAverage', 'getDisplayNames', 'setDefaultAssertionStatus', 'getDisplayName',
                 'averagingLong', 'NORM_PRIORITY', 'emptyIterator', 'scheduledExecutionTime', 'node', 'notify',
                 'OfPrimitive', 'DISTINCT', 'getImplementationVendor', 'IllegalFormatWidthException', 'format',
                 'checkAccept', 'WEEK_OF_MONTH', 'hasPrevious', 'parseUnsignedLong', 'negateExact', 'compileClasses',
                 'newInstance', 'summarizingDouble', 'substring', 'interrupt', 'checkAwtEventQueueAccess',
                 'StringJoiner', 'internalGet', 'NoSuchMethodException', 'first', 'NullPointerException',
                 'handleKeySet', 'isIdeographic', 'numberOfTrailingZeros', 'Hashtable', 'trimToSize', 'average', 'ERA',
                 'InvalidPropertiesFormatException', 'getFields', 'descendingMap', 'NavigableSet', 'findFirst', 'boxed',
                 'StringIndexOutOfBoundsException', 'runFinalization', 'emptyNavigableSet', 'ITALY', 'sinh',
                 'getProperty', 'codePoints', 'getLanguage', 'UPPERCASE', 'MissingFormatArgumentException',
                 'getExtensionKeys', 'GregorianCalendar', 'setEmptyValue', 'DIRECTIONALITY_WHITESPACE',
                 'getSpecificationTitle', 'getSpecificationVersion', 'iterate', 'OTHER_NUMBER', 'isLetterOrDigit',
                 'locale', 'split', 'ORDERED', 'cancel', 'put', 'getValue', 'setOut', 'setEndRule', 'toLanguageTag',
                 'InputMismatchException', 'TimerTask', 'PRC', 'getNumericValue', 'enable', 'containsKey', 'lowerKey',
                 'asLongStream', 'singletonList', 'enumerate', 'isInterrupted', 'useDelimiter',
                 'getAvailableCalendarTypes', 'StringBuffer', 'deepHashCode', 'AUGUST', 'getContextClassLoader',
                 'copySign', 'DIRECTIONALITY_ARABIC_NUMBER', 'MIN_WEIGHT', 'complementOf', 'isTimeSet',
                 'toLocaleString', 'toDegrees', 'availableProcessors', 'comparingInt', 'EnumMap', 'String', 'Locale',
                 'inCheck', 'UnknownFormatFlagsException', 'Cloneable', 'anyMatch', 'mapEquivalents', 'getClasses',
                 'peek', 'StringBuilder', 'rangeClosed', 'MIN_EXPONENT', 'setStackTrace', 'removeElement',
                 'getSecurityManager', 'flatMapToDouble', 'enumeration', 'capacity', 'getAsDouble', 'Exception',
                 'forEach', 'toArray', 'hasNextBigDecimal', 'Calendar', 'hasMoreTokens', 'getSystemClassLoader', 'from',
                 'logicalAnd', 'intern', 'higherKey', 'CloneNotSupportedException', 'addElement', 'pollFirstEntry',
                 'trim', 'addExact', 'maxMemory', 'getWeekYear', 'previousIndex', 'checkPermission',
                 'hasCharacteristics', 'flush', 'setMonth', 'compileClass', 'setLenient', 'Set',
                 'getUncaughtExceptionHandler', 'appendCodePoint', 'hasExtensions', 'copyOfRange', 'SUBSIZED',
                 'logicalOr', 'remove', 'complete', 'list', 'AutoCloseable', 'getMinimum', 'getNumericCode',
                 'countObservers', 'floor', 'keySet', 'formatTo', 'ints', 'InstantiationError', 'join',
                 'ClassNotFoundException', 'DIRECTIONALITY_PARAGRAPH_SEPARATOR', 'ZONE_OFFSET', 'getListener',
                 'elementAt', 'exit', 'incrementExact', 'storeToXML', 'EMPTY_LIST', 'hasNextShort', 'length', 'Subset',
                 'binarySearch', 'Category', 'setStartYear', 'SECOND', 'computeIfAbsent', 'builder', 'parallelSetAll',
                 'EventObject', 'ClassCastException', 'getDeclaredConstructors', 'asLifoQueue', 'isISOControl',
                 'getSource', 'setChanged', 'MAX_VALUE', 'BC', 'YEAR', 'Encoder', 'nextBytes', 'getYear', 'supplier',
                 'ListIterator', 'previousSetBit', 'TUESDAY', 'getSuperclass', 'removeLast', 'SIZED', 'getState',
                 'unmodifiableMap', 'MAX_HIGH_SURROGATE', 'frequency', 'getOrDefault', 'hypot', 'setCharAt',
                 'StackOverflowError', 'countTokens', 'getMethod', 'getConstructor', 'UPPERCASE_LETTER', 'averagingInt',
                 'RuntimePermission', 'Collections', 'retainAll', 'checkRead', 'getUnicodeLocaleAttributes', 'Arrays',
                 'isUnicodeIdentifierStart', 'skip', 'environment', 'redirectErrorStream', 'UUID', 'MIN_SURROGATE',
                 'IllegalFormatFlagsException', 'nameUUIDFromBytes', 'getEnclosingClass', 'spliteratorUnknownSize',
                 'INHERIT', 'combine', 'System', 'contentEquals', 'pollLast', 'regionMatches', 'getDeclaredMethod',
                 'tailMap', 'offsetByCodePoints', 'getEncoder', 'setLocale', 'mapToLong', 'setDate', 'freeMemory',
                 'getDSTSavings', 'setWeekDate', 'read', 'copyValueOf', 'OCTOBER', 'isMemberClass', 'values', 'getSum',
                 'Math', 'Formatter', 'inDaylightTime', 'pollFirst', 'DIRECTIONALITY_RIGHT_TO_LEFT_ARABIC', 'PIPE',
                 'setLanguageTag', 'lowSurrogate', 'swap', 'ceil', 'addUnicodeLocaleAttribute', 'log1p', 'MONTH',
                 'command', 'characteristics', 'HashSet', 'getLong', 'ALL_STYLES', 'rehash',
                 'NegativeArraySizeException', 'useDaylightTime', 'NON_SPACING_MARK', 'getDeclaredMethods', 'elements',
                 'search', 'setElementAt', 'IntSummaryStatistics', 'Double', 'getAsLong', 'spliterator', 'decode',
                 'currentThread', 'scheduleAtFixedRate', 'getAvailableIDs', 'StringTokenizer', 'multiplyExact',
                 'equals', 'setValue', 'getResourceAsStream', 'LinkedHashMap',
                 'DIRECTIONALITY_EUROPEAN_NUMBER_TERMINATOR', 'summarizingLong', 'codePointBefore', 'SHORT_FORMAT',
                 'SURROGATE', 'setMinimalDaysInFirstWeek', 'setStartRule', 'SUNDAY', 'checkPackageDefinition',
                 'getISOLanguages', 'Runnable', 'intBitsToFloat', 'reducing', 'CANADA', 'orElse', 'mapToInt', 'time',
                 'getUnicodeLocaleKeys', 'getContents', 'EMPTY_SET', 'stripExtensions', 'exitValue', 'isWhitespace',
                 'xor', 'subtractExact', 'setMinutes', 'save', 'TypeNotPresentException', 'HOUR_OF_DAY', 'getPriority',
                 'THURSDAY', 'getFirstDayOfWeek', 'contains', 'getDeclaredClasses',
                 'DIRECTIONALITY_POP_DIRECTIONAL_FORMAT', 'lastEntry', 'classDepth', 'GERMAN', 'remainderUnsigned',
                 'counting', 'checkLink', 'elementCount', 'isJavaLetterOrDigit', 'reverse', 'DIRECTIONALITY_UNDEFINED',
                 'cbrt', 'filterTags', 'Float', 'getDisplayLanguage', 'toUnsignedLong',
                 'IllegalFormatCodePointException', 'withoutPadding', 'List', 'DIRECTIONALITY_LEFT_TO_RIGHT_EMBEDDING',
                 'getInCheck', 'copyInto', 'Scanner', 'getISO3Country', 'OfLong', 'setInstant', 'to', 'and',
                 'ThreadLocal', 'cardinality', 'Collector', 'getMinutes', 'getOffset', 'toMap', 'DASH_PUNCTUATION',
                 'getActualMaximum', 'intValue', 'compareTo', 'DuplicateFormatFlagsException', 'IDENTITY_FINISH',
                 'getErrorStream', 'synchronizedMap', 'addLast', 'Comparable', 'observesDaylightTime', 'andNot',
                 'STANDARD_TIME', 'printStackTrace', 'getLeastMaximum', 'range', 'rotateRight', 'HashMap', 'build',
                 'RandomAccess', 'UNASSIGNED', 'Enum', 'UnsupportedOperationException', 'JANUARY',
                 'groupingByConcurrent', 'getAnnotatedInterfaces', 'nextBigDecimal', 'computeValue', 'mapping',
                 'DIRECTIONALITY_EUROPEAN_NUMBER_SEPARATOR', 'unmodifiableNavigableMap', 'setTime', 'DAY_OF_WEEK',
                 'IllegalFormatException', 'getDeclaredFields', 'BootstrapMethodError', 'setMaxPriority',
                 'PARAGRAPH_SEPARATOR', 'getLocale', 'keys', 'ArrayIndexOutOfBoundsException', 'forEachOrdered',
                 'forDigit', 'round', 'IllegalArgumentException', 'gc', 'flatMap', 'unordered', 'compute',
                 'isSpaceChar', 'hasMoreElements', 'LinkedList', 'resume', 'addFirst', 'SafeVarargs', 'console',
                 'isAnnotationPresent', 'IntStream', 'deleteCharAt', 'FRENCH', 'getNoFallbackControl',
                 'isJavaIdentifierStart', 'deepToString', 'MATH_SYMBOL', 'findWithinHorizon', 'descendingKeySet',
                 'getInputStream', 'getMimeDecoder', 'Deprecated', 'setUncaughtExceptionHandler', 'replaceAll', 'BYTES',
                 'setGregorianChange', 'EMPTY_MAP', 'DIRECTIONALITY_LEFT_TO_RIGHT_OVERRIDE', 'InternalError',
                 'bitCount', 'isSynthetic', 'previous', 'byteValue', 'hasNextFloat', 'before',
                 'isUnicodeIdentifierPart', 'AM', 'activeGroupCount', 'DATE', 'MIN_LOW_SURROGATE', 'ProcessBuilder',
                 'suspend', 'allowThreadSuspension', 'summingInt', 'isInstance', 'parseLong', 'Package', 'toLongArray',
                 'SIZE', 'runFinalizersOnExit', 'withInitial', 'getCandidateLocales', 'waitFor',
                 'isIdentifierIgnorable', 'loadFromXML', 'getLocalizedOutputStream', 'getResources', 'log10',
                 'getTimeToLive', 'NoSuchFieldError', 'checkPrintJobAccess', 'Spliterator', 'Queue', 'atan', 'pop',
                 'setPriority', 'AbstractMethodError', 'offer', 'isDefined', 'emptyListIterator', 'VirtualMachineError',
                 'UNORDERED', 'toUnsignedInt', 'MAX_RADIX', 'defaults', 'LONG_FORMAT', 'clockSequence', 'emptyList',
                 'MIN_CODE_POINT', 'NARROW_FORMAT', 'getUnicodeLocaleType', 'inheritIO', 'shuffle', 'ofNullable',
                 'LONG_STANDALONE', 'encodeToString', 'MissingResourceException', 'getSimpleName', 'scalb',
                 'findInLine', 'LinkedHashSet', 'MODIFIER_SYMBOL', 'compare', 'getChars', 'ALTERNATE', 'flatMapToLong',
                 'requireNonNull', 'MissingFormatWidthException', 'Void', 'SORTED', 'AbstractSequentialList',
                 'naturalOrder', 'Pair', 'ClassLoader', 'distinct', 'StreamSupport', 'IllformedLocaleException',
                 'checkSystemClipboardAccess', 'removeFirstOccurrence', 'ensureCapacity',
                 'IncompatibleClassChangeError', 'setTimeZone', 'DAY_OF_WEEK_IN_MONTH', 'nextClearBit',
                 'EventListenerProxy', 'isEnum', 'emptyNavigableMap', 'BigDecimalLayoutForm', 'deleteObservers',
                 'toCollection', 'getMinimalDaysInFirstWeek', 'finisher', 'doubles', 'Properties', 'initCause',
                 'DIRECTIONALITY_RIGHT_TO_LEFT_OVERRIDE', 'lowestOneBit', 'areFieldsSet', 'clear', 'FORMAT_CLASS',
                 'nextBigInteger', 'OTHER_SYMBOL', 'descendingSet', 'CHINESE', 'clone', 'ServiceLoader',
                 'comparingByValue', 'toList', 'getLocalizedMessage', 'unmodifiableSortedSet', 'toString',
                 'toHexString', 'exp', 'hash', 'minBy', 'isFinite', 'getField', 'checkedSet', 'currentLoadedClass',
                 'WEDNESDAY', 'emptySortedMap', 'accept', 'poll', 'ListResourceBundle', 'IEEEremainder', 'allOf',
                 'setSecurityManager', 'notifyObservers', 'out', 'WALL_TIME', 'getAnnotations', 'EnumSet', 'removeIf',
                 'AbstractCollection', 'Error', 'InstantiationException', 'SHORT_STANDALONE', 'checkConnect', 'JULY',
                 'nextBoolean', 'copyOf', 'SEPTEMBER', 'variant', 'nonNull', 'orElseThrow', 'getModifiers',
                 'randomUUID', 'checkedQueue', 'dumpStack', 'set', 'setLanguage', 'setTimeInMillis',
                 'checkPackageAccess', 'interrupted', 'setWeekDefinition', 'destroy', 'getTimezoneOffset', 'TimeZone',
                 'toChars', 'checkedMap', 'MAX_PRIORITY', 'match', 'getBaseBundleName', 'min',
                 'removeUnicodeLocaleAttribute', 'getSystemResources', 'checkExit', 'getEnclosingConstructor',
                 'removeShutdownHook', 'defineClass', 'getResource', 'totalMemory', 'loadLibrary', 'setAll',
                 'EventListener', 'SimpleImmutableEntry', 'toCodePoint', 'IllegalAccessError', 'highestOneBit',
                 'LOWERCASE_LETTER', 'checkSetFactory', 'DIRECTIONALITY_RIGHT_TO_LEFT', 'ROOT', 'getGregorianChange',
                 'parent', 'getLineNumber', 'matches', 'Observable', 'floatToRawIntBits', 'ThreadGroup', 'JAPANESE',
                 'currentTimeMillis', 'getMaximum', 'singletonMap', 'getExtension', 'CURRENCY_SYMBOL',
                 'getProtectionDomain', 'State', 'noneMatch', 'getEnclosingMethod', 'OTHER_PUNCTUATION',
                 'clearProperty', 'averagingDouble', 'checkedNavigableSet', 'nullsLast', 'START_PUNCTUATION',
                 'decrementExact', 'IllegalAccessException', 'getDeclaringClass', 'synchronizedNavigableSet',
                 'parseInt', 'Map', 'getDay', 'setSize', 'getCount', 'UNICODE_LOCALE_EXTENSION', 'getUrlDecoder',
                 'emptyEnumeration', 'FALSE', 'getFallbackLocale', 'getObject', 'longValue', 'RuntimeException',
                 'setVariant', 'nextLine', 'isLocalClass', 'checkedCollection', 'Process', 'merge', 'nextElement',
                 'compareToIgnoreCase', 'getExponent', 'collectingAndThen', 'synchronizedList', 'getGenericSuperclass',
                 'isPrimitive', 'LanguageRange', 'getMostSignificantBits', 'count', 'isLowSurrogate',
                 'ServiceConfigurationError', 'getStackTrace', 'hasSameRules', 'timestamp', 'nextIndex',
                 'LongSummaryStatistics', 'nextDouble', 'hashCode', 'getAnnotationsByType', 'CONNECTOR_PUNCTUATION',
                 'flatMapToInt', 'nextGaussian', 'store', 'insert', 'newBundle', 'checkDelete', 'FRIDAY', 'SATURDAY',
                 'isSupplementaryCodePoint', 'setSeconds', 'getKey', 'MODIFIER_LETTER', 'forEachRemaining', 'setLength',
                 'tanh', 'offerFirst', 'UnsatisfiedLinkError', 'asDoubleStream', 'hasNextBigInteger', 'checkWrite',
                 'getPackages', 'inClass', 'summaryStatistics', 'forName', 'parallel', 'getDirectionality',
                 'synchronizedSortedMap', 'codePointCount', 'IllegalFormatConversionException', 'allMatch', 'charValue',
                 'partitioningBy', 'implies', 'MIN_HIGH_SURROGATE', 'getTime', 'deepEquals', 'numberOfLeadingZeros',
                 'intersects', 'useLocale', 'FORMAT_PROPERTIES', 'disjoint', 'isLenient', 'previousClearBit',
                 'codePointAt', 'DIRECTIONALITY_RIGHT_TO_LEFT_EMBEDDING', 'setRawOffset', 'isAssignableFrom',
                 'SplittableRandom', 'CASE_INSENSITIVE_ORDER', 'isJavaIdentifierPart', 'InterruptedException', 'sorted',
                 'IMMUTABLE', 'NoClassDefFoundError', 'Comparator', 'parseUnsignedInt', 'getAnnotation',
                 'TRADITIONAL_CHINESE', 'getMethodName', 'toUpperCase', 'traceMethodCalls', 'LONG',
                 'UnknownFormatConversionException', 'getBundle', 'Number', 'clearChanged', 'abs', 'floorEntry', 'TRUE',
                 'hasChanged', 'hasNextInt', 'elementData', 'removeFirst', 'DAY_OF_YEAR', 'OutOfMemoryError', 'Thread',
                 'mapToObj', 'toResourceName', 'summingDouble', 'PI', 'pow', 'getImplementationVersion', 'FRANCE',
                 'arraycopy', 'getThreadGroup', 'roll', 'charCount', 'OptionalDouble', 'ceiling',
                 'DIRECTIONALITY_BOUNDARY_NEUTRAL', 'sum', 'setParent', 'Object', 'DIRECTIONALITY_LEFT_TO_RIGHT',
                 'toConcurrentMap', 'OptionalInt', 'acos', 'headMap', 'getMessage', 'getId', 'getFileName', 'cast',
                 'getParent', 'setExtension', 'longBitsToDouble', 'iterator', 'setCalendarType',
                 'MIN_SUPPLEMENTARY_CODE_POINT', 'FormattableFlags', 'Redirect', 'OTHER_LETTER', 'estimateSize',
                 'LongStream', 'PrimitiveIterator', 'NONNULL', 'sqrt', 'comparator', 'getUrlEncoder', 'getType', 'AD',
                 'getBytes', 'findAny', 'isPresent', 'nextShort', 'NARROW_STANDALONE', 'ITALIAN', 'indexOfSubList',
                 'toUnsignedString', 'setProperties', 'getID', 'groupingBy', 'asSubclass', 'mapLibraryName', 'Stream',
                 'atan2', 'activeCount', 'findResource', 'comparingLong', 'getDefault', 'getClassLoadingLock',
                 'toBundleName', 'UncaughtExceptionHandler', 'hasNextLine', 'getCountry', 'UnicodeScript',
                 'stringPropertyNames', 'getLocalizedInputStream', 'singleton', 'MAX_WEIGHT', 'emptyIntSpliterator',
                 'getInterfaces', 'isAnonymousClass', 'cosh', 'parseByte', 'isNativeMethod', 'setProperty',
                 'UnsupportedClassVersionError', 'OfInt', 'getClassContext', 'Throwable', 'comparingByKey', 'peekLast',
                 'err', 'addSuppressed', 'containsValue', 'directory', 'IllegalMonitorStateException',
                 'insertElementAt', 'DECEMBER', 'AbstractSpliterator', 'JUNE', 'checkSecurityAccess', 'getISOCountries',
                 'parseFloat', 'getSuppressed', 'getenv', 'isMirrored', 'FORMAT_DEFAULT', 'getSecurityContext',
                 'isSurrogatePair', 'sin', 'hasNextByte', 'MAX_EXPONENT', 'handleGetObject', 'Objects', 'MIN_RADIX',
                 'VerifyError', 'loadInstalled', 'doubleValue', 'PriorityQueue', 'asList',
                 'setDefaultUncaughtExceptionHandler', 'booleanValue', 'FilteringMode', 'peekFirst', 'getScript',
                 'Date', 'firstKey', 'load', 'next', 'signum', 'thenComparing', 'parseShort', 'empty',
                 'synchronizedSet', 'computeTime', 'replace', 'isInfinite', 'append', 'SPACE_SEPARATOR',
                 'ENCLOSING_MARK', 'checkListen', 'sleep', 'size', 'getSpecificationVendor', 'ThreadDeath', 'Class',
                 'checkExec', 'startsWith', 'lastIndexOfSubList', 'Short', 'isLetter', 'ArrayList', 'UnknownError',
                 'unmodifiableCollection', 'Base64', 'EmptyStackException', 'maxBy', 'lastIndexOf', 'accumulator',
                 'reverseBytes', 'doubleToLongBits', 'BitSet', 'run', 'getDefaultFractionDigits',
                 'FormatterClosedException', 'digit', 'CONCURRENT', 'isUpperCase', 'push', 'compareUnsigned',
                 'firstEntry', 'log', 'FunctionalInterface', 'logicalXor', 'getControl', 'appendTo', 'NavigableMap',
                 'uncaughtException', 'replaceFirst', 'getSymbol', 'UTC', 'delete', 'nextSetBit', 'toGenericString',
                 'getRange', 'getComparator', 'newSetFromMap', 'SortedMap', 'LETTER_NUMBER', 'getImplementationTitle',
                 'hasNextDouble', 'Compiler', 'getCanonicalName', 'nextByte', 'toByteArray', 'getCause', 'HOUR',
                 'toGMTString', 'stream', 'getDefaultUncaughtExceptionHandler', 'DECIMAL_DIGIT_NUMBER', 'SHORT',
                 'parseBoolean', 'floorKey', 'SimpleTimeZone', 'propertyNames', 'holdsLock', 'getDecoder',
                 'hasNextLong', 'isAlphabetic', 'NoSuchFieldException', 'addAll', 'setDefault', 'ifPresent',
                 'getStringArray', 'wait', 'getDeclaredAnnotationsByType', 'ArrayStoreException', 'isSet',
                 'getConstructors', 'tan', 'version', 'TooManyListenersException', 'unmodifiableSet', 'setSeed',
                 'UnicodeBlock', 'registerAsParallelCapable', 'getDeclaredAnnotations', 'tryAdvance', 'findResources',
                 'NumberFormatException', 'generate', 'setYear', 'US', 'isArray', 'clearCache', 'of', 'UTC_TIME',
                 'resolveClass', 'floorDiv', 'Entry', 'isLowerCase', 'inClassLoader', 'getClass', 'purge', 'Byte',
                 'Iterable', 'getString', 'floatToIntBits', 'LEFT_JUSTIFY', 'thenComparingDouble', 'KOREA',
                 'removeElementAt', 'getComponentType', 'AbstractMap', 'MAX_LOW_SURROGATE', 'getEnumConstants',
                 'nextDown', 'getSystemResource', 'setHours', 'charAt', 'getBoolean', 'last', 'emptyDoubleSpliterator',
                 'emptySet', 'isAnnotation', 'getLeastSignificantBits', 'synchronizedNavigableMap', 'removeAll',
                 'rotateLeft', 'entrySet', 'JAPAN', 'findSystemClass', 'higher', 'lowerEntry',
                 'ConcurrentModificationException', 'Enumeration', 'putAll', 'getMethods', 'disable', 'isEmpty', 'MAY',
                 'initialValue', 'isSealed', 'setPackageAssertionStatus', 'MAX_CODE_POINT', 'desiredAssertionStatus',
                 'lastKey', 'StrictMath', 'checkPropertiesAccess', 'setDaemon', 'DoubleSummaryStatistics',
                 'ArithmeticException', 'summarizingInt', 'expm1', 'removeEldestEntry', 'GERMANY', 'findClass',
                 'OfDouble', 'AM_PM', 'getAvailableLocales', 'COMBINING_SPACING_MARK', 'getClassLoader', 'UK',
                 'IllegalFormatPrecisionException', 'TTL_DONT_CACHE', 'isDestroyed', 'computeIfPresent',
                 'hasNextBoolean', 'toSet', 'MINUTE', 'getMimeEncoder', 'setClassAssertionStatus',
                 'removeLastOccurrence', 'firstElement', 'getDeclaredField', 'getKeys', 'MIN_VALUE', 'Appendable',
                 'offerLast', 'DIRECTIONALITY_EUROPEAN_NUMBER', 'getTimeInMillis', 'getMonth', 'checkedNavigableMap',
                 'getDeclaredAnnotation', 'Timer', 'getGenericInterfaces', 'longs', 'MONDAY', 'addObserver', 'NOVEMBER',
                 'ClassCircularityError', 'EnumConstantNotPresentException', 'getSystemResourceAsStream', 'toIntExact',
                 'AbstractList', 'nextLong', 'PM', 'joining', 'APRIL', 'getCurrencyCode', 'isSurrogate', 'Long', 'or',
                 'getSigners', 'getProperties', 'update', 'unmodifiableList', 'fillInStackTrace', 'toBinaryString',
                 'Observer', 'CANADA_FRENCH', 'source', 'getDisplayVariant', 'Optional', 'headSet', 'putIfAbsent',
                 'summingLong', 'getMin', 'lastElement', 'SimpleEntry', 'AbstractLongSpliterator',
                 'checkPropertyAccess', 'yield', 'setRegion', 'nextToken', 'emptySortedSet', 'emptyMap',
                 'IndexOutOfBoundsException', 'DAY_OF_MONTH', 'checkedList', 'setErr', 'setFields', 'addShutdownHook',
                 'isInterface', 'intStream', 'reload', 'close', 'AbstractSet', 'Formattable', 'checkCreateClassLoader',
                 'getRuntime', 'ulp', 'lookup', 'Readable', 'StackTraceElement', 'getClassName', 'sort',
                 'redirectOutput', 'trySplit', 'ReflectiveOperationException', 'MAX_SURROGATE', 'getDate', 'MIN_NORMAL',
                 'reverseOrder', 'Integer', 'DST_OFFSET', 'capacityIncrement', 'getInteger', 'max', 'isSpace',
                 'INITIAL_QUOTE_PUNCTUATION', 'ceilingKey', 'getPackage', 'ClassFormatError', 'ResourceBundle',
                 'orElseGet', 'subMap', 'removeRange', 'thenComparingInt', 'isCompatibleWith', 'NoSuchMethodError',
                 'setID', 'combiner', 'removeAllElements', 'getTypeParameters', 'UNDECIMBER', 'parseDouble',
                 'getExactSizeIfKnown', 'KOREAN', 'sequential', 'modCount', 'toTitleCase', 'name', 'isAlive',
                 'doubleToRawLongBits', 'TYPE', 'nextInt', 'toZonedDateTime', 'SIMPLIFIED_CHINESE', 'ioException',
                 'Override', 'collect', 'DoubleStream', 'fromString', 'redirectError', 'nullsFirst', 'setIn', 'nCopies',
                 'parallelSort', 'getCalendarType', 'higherEntry', 'Random', 'subList', 'PropertyPermission', 'asin',
                 'nextAfter', 'WEEK_OF_YEAR', 'findLoadedClass', 'fields', 'shortValue',
                 'DIRECTIONALITY_COMMON_NUMBER_SEPARATOR', 'getOutputStream', 'pollLastEntry', 'toOctalString',
                 'parentOf', 'highSurrogate', 'toInstant', 'Collection', 'Character', 'lookupTag',
                 'setUnicodeLocaleKeyword', 'SecurityException', 'Currency', 'endsWith']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 1427


def Java_type_identifier(node_str):
    contained_Ft = []
    templates = ['StrictMath', 'HashMap', 'IllegalFormatWidthException', 'InputMismatchException',
                 'FormatterClosedException', 'StringBuilder', 'AbstractSequentialList', 'Throwable', 'Formatter',
                 'Error', 'BootstrapMethodError', 'IncompatibleClassChangeError', 'NoSuchFieldError',
                 'AbstractIntSpliterator', 'Double', 'UUID', 'InterruptedException', 'TreeSet', 'IntSummaryStatistics',
                 'Timer', 'ClassCastException', 'LongStream', 'Void', 'Exception', 'NegativeArraySizeException',
                 'FormatFlagsConversionMismatchException', 'Thread', 'Decoder', 'GregorianCalendar', 'LinkedHashMap',
                 'IllegalFormatCodePointException', 'System', 'Set', 'MissingFormatArgumentException',
                 'IndexOutOfBoundsException', 'Iterator', 'SortedMap', 'Spliterators', 'StringJoiner', 'Boolean',
                 'Builder', 'AbstractMap', 'Base64', 'NoClassDefFoundError', 'IllegalStateException',
                 'ServiceConfigurationError', 'Object', 'TimerTask', 'AssertionError', 'DuplicateFormatFlagsException',
                 'Locale', 'Optional', 'Number', 'SortedSet', 'LongSummaryStatistics', 'Queue', 'Observer',
                 'ClassFormatError', 'Long', 'ExceptionInInitializerError', 'IllegalFormatConversionException',
                 'SuppressWarnings', 'Encoder', 'OfInt', 'UnicodeScript', 'ClassValue', 'NavigableMap',
                 'PrimitiveIterator', 'OfDouble', 'SimpleEntry', 'Float', 'SecurityManager', 'OutOfMemoryError',
                 'Observable', 'Hashtable', 'Collections', 'EmptyStackException', 'IdentityHashMap',
                 'IllegalFormatFlagsException', 'ArithmeticException', 'ClassNotFoundException', 'Dictionary',
                 'NoSuchMethodException', 'UnsatisfiedLinkError', 'Cloneable', 'UncaughtExceptionHandler', 'Pair',
                 'AbstractMethodError', 'EventListenerProxy', 'ServiceLoader', 'TypeNotPresentException',
                 'ListResourceBundle', 'Category', 'InstantiationError', 'MissingResourceException', 'Iterable',
                 'UnsupportedOperationException', 'IllformedLocaleException', 'IllegalFormatException',
                 'InstantiationException', 'Deque', 'Spliterator', 'LinkedList', 'Redirect', 'Override',
                 'StreamSupport', 'EnumMap', 'OptionalInt', 'Byte', 'InheritableThreadLocal',
                 'IllegalFormatPrecisionException', 'IllegalAccessException', 'EventListener', 'StringTokenizer',
                 'NoSuchElementException', 'Comparable', 'FormattableFlags', 'VerifyError',
                 'AbstractLongSpliterator', 'Formattable', 'Integer', 'Calendar', 'StringIndexOutOfBoundsException',
                 'LinkageError', 'StringBuffer', 'Currency', 'EventObject', 'StackOverflowError', 'Vector', 'Character',
                 'IllegalThreadStateException', 'UnknownFormatFlagsException', 'ClassCircularityError',
                 'VirtualMachineError', 'ReflectiveOperationException', 'IllegalArgumentException', 'RuntimePermission',
                 'ArrayList', 'ThreadLocal', 'Stream', 'SecurityException', 'WeakHashMap', 'Random',
                 'ResourceBundle', 'Collection', 'DoubleStream', 'ProcessBuilder', 'CloneNotSupportedException',
                 'NoSuchMethodError', 'ThreadDeath', 'Objects', 'AutoCloseable', 'LinkedHashSet', 'IntStream',
                 'AbstractSpliterator', 'RandomAccess', 'DoubleSummaryStatistics', 'PropertyPermission',
                 'PropertyResourceBundle', 'BitSet', 'OptionalLong', 'PriorityQueue', 'Stack', 'OfPrimitive',
                 'Characteristics', 'TimeZone', 'ThreadGroup', 'FunctionalInterface', 'RuntimeException', 'SafeVarargs',
                 'OptionalDouble', 'UnknownError', 'ClassLoader', 'HashSet', 'Process', 'StackTraceElement',
                 'SimpleTimeZone', 'NumberFormatException', 'Comparator', 'AbstractSet', 'BigDecimalLayoutForm',
                 'Collectors', 'Short', 'ArrayDeque', 'Entry', 'ListIterator', 'CharSequence', 'Subset', 'Properties',
                 'UnicodeBlock', 'Map', 'ResourceBundle.Control', 'NullPointerException',
                 'UnsupportedClassVersionError', 'AbstractDoubleSpliterator', 'Deprecated', 'Collector',
                 'InvalidPropertiesFormatException', 'FilteringMode', 'MissingFormatWidthException', 'Runnable',
                 'Enumeration', 'SimpleImmutableEntry', 'AbstractCollection', 'Runtime',
                 'UnknownFormatConversionException', 'ConcurrentModificationException', 'Enum',
                 'State', 'TooManyListenersException', 'List', 'IllegalAccessError', 'Scanner', 'Appendable',
                 'AbstractList', 'IllegalMonitorStateException', 'Math', 'ArrayStoreException', 'NoSuchFieldException',
                 'ArrayIndexOutOfBoundsException', 'Package', 'InternalError', 'SplittableRandom', 'Readable',
                 'AbstractQueue', 'EnumSet', 'Class', 'Date', 'String', 'TreeMap', 'Arrays', 'Compiler', 'OfLong',
                 'NavigableSet', 'EnumConstantNotPresentException', 'BaseStream', 'LanguageRange']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 238


def C_comment(node_str):
    contained_Ft = []
    if '//' in node_str:
        contained_Ft.append(0)
    if '/*' in node_str and '*/' in node_str:
        contained_Ft.append(1)
    return contained_Ft, 2


# def C_primitive_type(node_str):
#     contained_Ft = []
#     templates = ['int', 'char', 'float', 'double', 'bool', 'void', 'size_t', 'ssize_t', 'uint32_t']
#     if node_str in templates:
#         contained_Ft.append(templates.index(node_str)+1)
#     else:
#         contained_Ft.append(0)
#     return contained_Ft, 10

def C_primitive_type(node_str):
    contained_Ft = []
    templates = ['int', 'char', 'float', 'double', 'bool', 'void', 'size_t', 'ssize_t']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str))
    else:
        contained_Ft.append(0)
    return contained_Ft, 8

def C_number_literal(node_str):
    contained_Ft = []
    if node_str[:2] in ['0x', '0X']:
        contained_Ft.append(1)
    if node_str[:2] in ['0b', '0B']:
        contained_Ft.append(2)
    if node_str[:2] not in ['0x', '0X', '0b', '0B'] and node_str[0] == '0' and node_str != '0':
        contained_Ft.append(3)
    if node_str[:2] not in ['0x', '0X'] and ('e' in node_str or 'E' in node_str):
        contained_Ft.append(4)
    if node_str[-1] == 'f':
        contained_Ft.append(5)
    if 'U' in node_str or 'u' in node_str:
        contained_Ft.append(6)
    if ('L' in node_str or 'l' in node_str) and not ('LL' in node_str or 'll' in node_str):
        contained_Ft.append(7)
    if ('LL' in node_str or 'll' in node_str) and not ('L' in node_str or 'l' in node_str):
        contained_Ft.append(8)
    if node_str[0] == '-':
        contained_Ft.append(9)
    if '.' in node_str:
        contained_Ft.append(10)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 11


def C_escape_sequence(node_str):
    contained_Ft = []
    templates = ['\\a', '\\b', '\\f', '\\n', '\\r', '\\t', '\\v', "\\'", '\\"', '\\?', '\\e', '\\s', '\\d', '\\\\', '\\x']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id)
    return contained_Ft, 15


def C_string_content(node_str):
    contained_Ft = []
    templates = ['%c', '%d', '%e', '%E', '%f', '%g', '%G', '%i', '%ld', '%li', '%lf', '%Lf', '%lu', '%lli', '%lld', '%llu', '%o', '%p', '%s', '%u', '%x', '%X', '%n', '%%', '%.']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id+1)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 26


def C_preproc_directive(node_str):
    contained_Ft = []
    templates = ['#line', '#progma', '#undef', '#error']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id)
    return contained_Ft, 4


def C_identifier(node_str):  # https://www.ibm.com/docs/en/i/7.3?topic=extensions-standard-c-library-functions-table-by-name
    contained_Ft = []
    templates = ['y1', 'wcsrtombs', 'fabs', 'gmtime', 'rand', 'yn', 'div', 'erfc', 'rand_r', 'strlen', 'wctrans',
                 'assert', 'malloc', 'putc', 'strncmp', 'fileno', 'getenv', 'strtod128', 'ldexp', 'iswalpha',
                 'fgetpos', 'localtime64_r', 'mbrlen', 'iswpunct', 'fgetwc', 'exit', 'sprintf', 'nextafterl',
                 'quantized64', 'ungetwc', 'floor', 'ldiv', 'toupper', 'hypot', 'wcscoll', 'wcstol', 'strncpy',
                 'gamma', 'va_copy', 'wcschr', 'wcstod', 'localtime', 'strcat', 'strerror', 'sin', 'strfmon',
                 'log10', 'isalpha', 'ceil', 'strftime', 'ftell', 'time64', 'wcstof', 'fwscanf', 'islower',
                 'difftime64', 'vwscanf', 'mktime64', 'wcsrchr', 'log', 'towupper', 'vprintf', 'clearerr', 'strtok',
                 'swprintf', 'wmemset', 'wcsncpy', 'realloc', 'iswalnum', 'fdopen', 'fprintf', 'strcoll', 'tan',
                 'mbstowcs', 'fread', 'iswctype', 'strtod64', 'vsnprintf', 'wcstok', 'wctob', 'strtof', 'memchr',
                 'snprintf', 'exp', 'wcsncat', 'quantexpd128', 'memcpy', 'fwide', 'modf', 'strtok_r', 'vswprintf',
                 'localtime_r', 'wcsstr', 'strchr', 'j1', 'iswxdigit', 'strtold', 'vsprintf', 'wmemchr', 'wmemcmp',
                 'strspn', 'cos', 'wcstombs', 'wctomb', 'gmtime64', 'mbsinit', 'setjmp', 'fgetc', 'wcstoul', 'vscanf',
                 'iswlower', 'system', 'vswscanf', 'quantized32', 'gmtime_r', 'vfprintf', 'strtol', 'time', 'fmod',
                 'isgraph', 'rename', 'wcswidth', 'getwc', 'pow', 'atoi', 'quantexpd32', 'catopen', 'iswblank',
                 'iswspace', 'isdigit', 'samequantumd32', 'wcscmp', 'memcmp', 'raise', 'ctime_r', 'ungetc',
                 'wcsftime', 'wcstold', 'vfwprintf', 'isalnum', 'atan2', 'vwprintf', 'perror', 'putenv', 'atof',
                 'labs', 'wscanf', 'tolower', 'abort', 'strxfrm', 'catclose', 'regerror', 'strcspn', 'cosh',
                 'nexttowardl', 'gmtime64_r', 'wmemcpy', 'fscanf', 'j0', 'regcomp', 'mbtowc', 'fgetws',
                 'samequantumd128', 'vsscanf', 'wcslocaleconv', 'sqrt', 'asctime', 'nl_langinfo', 'quantexpd64',
                 'setbuf', 'sscanf', 'wcsncmp', 'wcsxfrm', 'wmemmove', 'asin', 'wprintf', 'va_start', 'wcscpy',
                 'atexit', 'isupper', 'tmpfile', 'wcscspn', 'btowc', 'tmpnam', 'mktime', 'strncasecmp', 'towctrans',
                 'clock', 'fputwc', 'rewind', 'mblen', 'strtod32', 'iswdigit', 'ferror', 'atan', 'printf', 'strstr',
                 'wcstod128', 'localtime64', 'fsetpos', 'ctime64_r', 'puts', 'qsort', 'setvbuf', 'va_end', 'iswcntrl',
                 'wcspbrk', 'jn', 'free', 'signal', 'wcstod64', 'fseek', 'ctime64', 'nextafter', 'fputws', 'isspace',
                 'frexp', 'freopen', 'acos', 'towlower', 'y0', 'memset', 'strptime', 'regfree', 'fclose', 'isxdigit',
                 'fwprintf', 'memmove', 'putwchar', 'toascii', 'quantized128', 'strrchr', 'va_arg', 'ispunct', 'wcscat',
                 'fputc', 'strcpy', 'isascii', 'feof', 'abs', 'wcsptime', 'wcsspn', 'asctime_r', 'bsearch', 'wcrtomb',
                 'strpbrk', 'fgets', 'iswgraph', 'mbsrtowc', 'wcslen', 'putchar', 'strcmp', 'wcstod32', 'gets', 'srand',
                 'iswprint', 'atol', 'erf', 'mbrtowc', 'setlocale', 'scanf', 'iswupper', 'fopen', 'strtod', 'difftime',
                 'longjmp', 'sinh', 'calloc', 'fputs', 'tanh', 'wctype', 'remove', 'getwchar', 'catgets', 'fflush',
                 'isblank', 'isprint', 'nexttoward', 'srtcasecmp', 'vfscanf', 'swscanf', 'samequantumd64', 'iscntrl',
                 'fwrite', 'getc', 'ctime', 'strncat', 'localeconv', 'strtoul', 'getchar', 'vfwscanf']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 292


def Cpp_identifier(node_str):
    contained_Ft = []
    templates = ['asctime_r', 'for_each', 'fabs', 'CHAR_BIT', 'hash_function', 'putenv', 'INT_MIN', 'wmemcpy',
                 'fgetpos', 'cos', 'UCHAR_MAX', 'signbit', 'forward', 'fesetround', 'strtok', 'wctomb', 'time64',
                 'erase', 'flip', 'catclose', 'isascii', 'strtod32', 'fopen', 'rewind', 'llrint', 'abs', 'isnan',
                 'lower_bound', 'fill_n', 'towctrans', 'is_permutation', 'end', 'data', 'quick_exit', 'to_wstring',
                 'cbrt', 'wctype', 'isalpha', 'endl', 'ilogb', 'fsetpos', 'bucket_count', 'merge', 'ispunct', 'sqrt',
                 'isxdigit', 'NULL', 'va_arg', 'frexp', 'memcpy', 'tie', 'INT_MAX', 'clog', 'regfree', 'freopen',
                 'wcsrchr', 'prev_permutation', 'key_eq', 'longjmp', 'unique', 'vfprintf', 'strtold', 'conj',
                 'push_back', 'fwscanf', 'gmtime64', 'top', 'lrint', 'mktime', 'cin', 'swscanf', 'wcslocaleconv',
                 'strptime', 'feholdexcept', 'mktime64', 'iswcntrl', 'random_shuffle', 'setvbuf', 'M_E', 'getc',
                 'emplace', 'mbrtowc', 'wprintf', 'iswctype', 'iswblank', 'stold', 'towlower', 'wmemcmp', 'nexttowardl',
                 'isgraph', 'to_string', 'to_ullong', 'ULLONG_MAX', 'fputwc', 'clear', 'replace_copy', 'strcspn',
                 'localtime_r', 'load_factor', 'yn', 'resize', 'get', 'cbefore_begin', 'round', 'equal_range',
                 'realloc', 'strncmp', 'wcslen', 'wcsftime', 'sprintf', 'wcin', 'localtime64', 'cbegin', 'strcpy',
                 'wcsrtombs', 'gmtime_r', 'mbtowc', 'rint', 'fetestexcept', 'reverse', 'samequantumd64', 'wcscat',
                 'reserve', 'samequantumd128', 'perror', 'abort', 'va_end', 'swap', 'none', 'memcmp', 'iter_swap',
                 'acosh', 'size', 'localeconv', 'fegetexceptflag', 'tmpfile', 'wcstok', 'MB_LEN_MAX', 'labs', 'find_if',
                 'scanf', 'assert', 'putc', 'difftime', 'wcstod128', 'clearerr', 'move', 'find', 'imag', 'set',
                 'copy_backward', 'wcstol', 'gamma', 'wcout', 'strfmon', 'towupper', 'floor', 'crend', 'stable_sort',
                 'bucket_size', 'printf', 'erf', 'set_union', 'atan', 'feclearexcept', 'calloc', 'CLOCKS_PER_SEC', 'jn',
                 'strcmp', 'is_heap_until', 'remove_copy_if', 'hypot', 'polar', 'inplace_merge', 'vwprintf', 'getchar',
                 'WCHAR_MAX', 'stoull', 'ldiv', 'insert_after', 'EXIT_SUCCESS', 'CHAR_MIN', 'all_of', 'wmemmove',
                 'make_pair', 'btowc', 'is_partitioned', 'push', 'fread', 'is_sorted', 'partial_sort', 'exit', 'fscanf',
                 'remainder', 'nth_element', 'generate', 'c32rtomb', 'wcstoll', 'gets', 'isalnum', 'wcsncat',
                 'fwprintf', 'getline', 'catopen', 'partial_sort_copy', 'nan', 'getenv', 'wcschr', 'ungetc', 'stoi',
                 'isgreater', 'stoul', 'scalbn', 'tgamma', 'MB_CUR_MAX', 'fgetwc', 'strncasecmp', 'pop_front',
                 'ungetwc', 'fgetc', 'fegetround', 'isinf', 'crbegin', 'erase_after', 'islower', 'vswscanf',
                 'shrink_to_fit', 'clock', 'qsort', 'llabs', 'atof', 'fesetenv', 'tuple_cat', 'strxfrm',
                 'at_quick_exit', 'search_n', 'iswprint', 'max_element', 'log10', 'j1', 'wcstoull', 'sort_heap',
                 'wcrtomb', 'SHRT_MAX', 'fgets', 'fmin', 'min_element', 'find_first_of', 'vsscanf', 'quantexpd128',
                 'back', 'nexttoward', 'wcscoll', 'partition_point', 'front', 'setlocale', 'islessgreater',
                 'next_permutation', 'emplace_hint', 'islessequal', 'vscanf', 'includes', 'fgetws', 'atexit', 'puts',
                 'lround', 'lldiv', 'wcscspn', 'quantexpd64', 'wcstombs', 'fma', 'sin', 'adjacent_find', 'generate_n',
                 'mismatch', 'iswlower', 'nextafter', 'mbsinit', 'nextafterl', 'lexicographical_compare', 'mbrlen',
                 'at', 'getwc', 'fmod', 'isprint', 'rotate_copy', 'va_start', 'strpbrk', 'search', 'replace_if',
                 'partition', 'emplace_front', 'strtoull', 'SHRT_MIN', 'assign', 'gmtime64_r', 'arg', 'wcstod',
                 'vfscanf', 'declval', 'stof', 'wctrans', 'malloc', 'logb', 'strrchr', 'cout', 'wcsspn', 'bucket',
                 'USHRT_MAX', 'begin', 'none_of', 'wcscmp', 'strtoul', 'atoll', 'wmemset', 'LONG_MIN', 'fclose',
                 'vfwscanf', 'strtok_r', 'M_PI', 'strncpy', 'raise', 'iswpunct', 'vsnprintf', 'isupper',
                 'binary_search', 'scalbln', 'mbsrtowcs', 'mblen', 'feof', 'vwscanf', 'cosh', 'wcstod32', 'atanh',
                 'copy_n', 'rbegin', 'fwide', 'find_if_not', 'strcat', 'feraiseexcept', 'strtod', 'difftime64',
                 'fwrite', 'log2', 'push_front', 'strftime', 'sscanf', 'tolower', 'sinh', 'expm1', 'va_copy', 'ctime',
                 'log1p', 'pop', 'cerr', 'EXIT_FAILURE', 'quantized64', 'llround', 'set_difference', 'rand_r', 'isless',
                 'reverse_copy', 'mbstowcs', 'shuffle', 'vsprintf', 'CHAR_MAX', 'to_ulong', 'fputs', 'wcsxfrm',
                 'mbsrtowc', 'ctime_r', 'y0', 'isnormal', 'iswupper', 'unique_copy', 'fpclassify', 'isblank',
                 'localtime', 'rehash', 'ctime64_r', 'tanh', 'test', 'isunordered', 'memmove', 'fdopen', 'upper_bound',
                 'vswprintf', 'wcstod64', 'INFINITY', 'wcstof', 'any_of', 'y1', 'free', 'wcsptime', 'wctob', 'min',
                 'system', 'div', 'find_end', 'setjmp', 'remove', 'asin', 'mbrtoc32', 'modf', 'copy_if', 'log',
                 'wcsncmp', 'wcstold', 'fill', 'vfwprintf', 'signal', 'atol', 'erfc', 'j0', 'remove_if', 'strlen',
                 'fputws', 'swprintf', 'pow', 'acos', 'minmax', 'key_comp', 'iswgraph', 'reset', 'toupper', 'rand',
                 'HUGE_VALF', 'stod', 'isgreaterequal', 'sort', 'samequantumd32', 'fflush', 'emplace_after', 'max',
                 'stoll', 'max_size', 'LLONG_MIN', 'isdigit', 'proj', 'copysign', 'errno', 'mbrtoc16',
                 'max_load_factor', 'HUGE_VAL', 'nl_langinfo', 'isspace', 'strchr', 'get_allocator', 'push_heap',
                 'time', 'any', 'lgamma', 'ceil', 'asctime', 'insert', 'quantized32', 'iswxdigit', '_Exit', 'trunc',
                 'replace', 'fileno', 'putwc', 'splice_after', 'strtol', 'offsetof', 'vprintf', 'remove_copy',
                 'move_backward', 'HUGE_VALL', 'wcscpy', 'count', 'strcoll', 'fmax', 'LLONG_MAX', 'iswalnum',
                 'WCHAR_MIN', 'strerror', 'gmtime', 'asinh', 'emplace_back', 'setbuf', 'real', 'pop_heap', 'SCHAR_MIN',
                 'fseek', 'copy', 'strtof', 'empty', 'iswalpha', 'regcomp', 'is_sorted_until', 'ferror', 'wcswidth',
                 'ftell', 'replace_copy_if', 'ldexp', 'exp2', 'strtod128', 'transform', 'strspn', 'ULONG_MAX',
                 'c16rtomb', 'getwchar', 'max_bucket_count', 'quantexpd32', 'partition_copy', 'bsearch', 'all',
                 'wcspbrk', 'nearbyint', 'atoi', 'value_comp', 'move_if_noexcept', 'swap_ranges', 'wscanf', 'strstr',
                 'wcstoul', 'tmpnam', 'feupdateenv', 'isfinite', 'memchr', 'rend', 'equal', 'exp', 'srtcasecmp', 'NAN',
                 'rename', 'rotate', 'ctime64', 'stol', 'tan', 'atan2', 'before_begin', 'wcsstr', 'set_intersection',
                 'pop_back', 'count_if', 'WEOF', 'memset', 'fdim', 'SCHAR_MAX', 'splice', 'make_heap', 'minmax_element',
                 'regerror', 'set_symmetric_difference', 'catgets', 'is_heap', 'cend', 'fprintf', 'localtime64_r',
                 'fesetexceptflag', 'strncat', 'toascii', 'LONG_MAX', 'RAND_MAX', 'putchar', 'make_tuple', 'wmemchr',
                 'strtoll', 'fegetenv', 'snprintf', 'iscntrl', 'srand', 'UINT_MAX', 'remquo', 'norm', 'putwchar',
                 'fputc', 'iswdigit', 'quantized128', 'wcsncpy', 'strtod64', 'forward_as_tuple', 'stable_partition',
                 'iswspace']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 577


def Cpp_type_identifier(node_str):
    contained_Ft = []
    templates = ['array', 'deque', 'forward_list', 'list', 'map', 'multimap', 'queue', 'priority_queue', 'set',
                 'multiset', 'stack', 'unordered_map', 'unordered_multimap', 'unordered_set', 'unordered_multiset',
                 'vector', 'wchar_t', 'string']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 19


def Cpp_field_identifier(node_str):
    contained_Ft = []  # '    int prevDiff = INT_MAX ;'
    templates = ['isdigit', 'sprintf', 'partial_sort_copy', 'nth_element', 'to_string', 'fputwc', 'erase_after',
                 'acosh', 'max', 'modf', 'fegetenv', 'mktime', 'snprintf', 'INT_MAX', 'asctime', 'difftime64',
                 'erf', 'strtod32', 'wmemset', 'regerror', 'swprintf', 'nexttoward', 'stable_sort', 'signbit',
                 'begin', 'llround', 'inplace_merge', 'push_heap', 'localtime64', 'lround', 'fegetround',
                 'hash_function', 'log1p', 'fill_n', 'fgetws', 'fesetenv', 'putwchar', 'unique_copy', 'wscanf',
                 'ctime64', 'strtod128', 'cbrt', 'labs', 'wcstold', 'va_copy', 'iswspace', 'c32rtomb', 'M_PI',
                 'feholdexcept', 'is_permutation', 'endl', 'binary_search', 'polar', 'at_quick_exit', 'M_E',
                 'realloc', 'forward', 'iswlower', 'clear', 'btowc', 'fetestexcept', 'wcstof', 'reset',
                 'pop_back', 'mblen', 'calloc', 'includes', 'assign', 'ldexp', 'cosh', 'fgets', 'isspace',
                 'isalnum', 'abort', 'localtime64_r', 'getc', 'prev_permutation', 'rand_r', 'mbstowcs',
                 'log10', 'memcmp', 'setlocale', 'make_pair', 'wcin', 'generate', 'raise', 'regcomp', 'strncmp',
                 'mbsrtowcs', 'resize', 'towctrans', 'strcoll', 'putenv', 'strtol', 'getchar', 'to_ulong',
                 'tanh', 'memset', 'lgamma', 'atan', 'strtoll', 'atoi', 'rename', 'ferror', 'wmemchr', 'remove',
                 'remainder', 'sinh', 'sin', 'wcsftime', 'fseek', 'get_allocator', 'time64', 'samequantumd128',
                 'wcsncpy', 'size', 'set_union', 'regfree', 'fopen', 'max_size', 'asin', 'emplace', 'move',
                 'all_of', 'all', 'wcstod', 'wcstok', 'localtime', 'lrint', 'transform', 'vwscanf', 'strtod64',
                 'fdim', 'strtof', 'partition_copy', 'to_ullong', 'rbegin', 'copy_backward', 'real', 'vscanf',
                 'wcstod32', 'isnan', 'bsearch', 'fileno', 'strspn', 'top', 'wmemmove', 'va_end', 'copysign',
                 'generate_n', 'INT_MIN', 'search_n', 'strchr', 'vwprintf', 'atol', 'push_back', 'tmpnam',
                 'towupper', 'qsort', 'atoll', 'count', 'free', 'emplace_after', 'atan2', 'copy', 'puts',
                 'stold', 'catclose', 'memcpy', 'is_sorted_until', 'offsetof', 'mbsinit', 'strxfrm', 'rfind',
                 'value_comp', 'rotate_copy', 'mbsrtowc', 'make_tuple', 'y0', 'quantexpd64', 'ftell',
                 'mbrtowc', 'wcstoull', 'fmin', 'strtok_r', 'gmtime', 'fputws', 'fesetround', 'scalbn',
                 'quick_exit', 'cin', 'div', 'fwprintf', 'find', 'reverse', 'pop', 'next_permutation',
                 'setjmp', 'ispunct', 'isblank', 'ctime64_r', 'getwchar', 'strcat', 'random_shuffle',
                 'log2', 'wcsspn', 'pow', 'clog', 'move_backward', 'printf', 'fmax', 'assert', 'iswalpha',
                 'equal', 'is_sorted', 'wcstombs', 'wcslen', 'emplace_front', 'wcstol', 'hypot', 'bucket',
                 'iswgraph', 'is_heap', 'find_if_not', 'fabs', 'find_end', 'arg', 'rehash', 'cout', 'cbegin',
                 'wcscoll', 'fwrite', 'key_eq', 'quantexpd32', 'min', 'fegetexceptflag', 'replace', 'isnormal',
                 'cend', 'erase', 'wcstod64', 'nextafterl', 'iswcntrl', 'strrchr', 'move_if_noexcept', 'getenv',
                 'sort_heap', 'difftime', 'strstr', 'longjmp', 'iswctype', 'strcspn', 'splice', 'trunc',
                 'iter_swap', 'stoull', 'acos', 'ungetc', 'isgreaterequal', 'search', 'wcschr', 'pop_front',
                 'wctomb', 'front', 'fill', 'max_load_factor', 'clock', 'is_partitioned', 'crend',
                 'remove_copy_if', 'mbrtoc32', 'va_start', 'islower', 'strtod', 'isunordered', 'vprintf',
                 'fpclassify', 'shrink_to_fit', 'fdopen', 'declval', 'strncpy', 'make_heap', 'fclose',
                 'mismatch', 'strcpy', 'memchr', 'swscanf', 'catgets', 'remove_if', 'fputc', 'iswdigit',
                 'partition', 'wcscpy', 'wprintf', 'iscntrl', 'srand', 'emplace_back', 'replace_copy_if',
                 'va_arg', 'before_begin', 'tmpfile', 'wctrans', 'towlower', 'iswalnum', 'data', 'stof',
                 'ctime', 'putwc', 'insert', 'quantized128', 'malloc', 'imag', 'fesetexceptflag', 'empty',
                 'wcswidth', 'for_each', 'rand', 'test', 'fmod', 'min_element', 'feclearexcept', 'islessgreater',
                 'perror', 'freopen', 'adjacent_find', 'proj', 'strtoul', 'fread', 'iswupper', 'find_if',
                 'vfwscanf', 'isfinite', 'mbtowc', 'exp2', 'rotate', 'push', 'expm1', 'fputs', 'samequantumd32',
                 'partial_sort', 'lexicographical_compare', 'atexit', 'iswblank', 'exit', 'llrint', 'wmemcpy',
                 'to_wstring', 'quantized64', 'isgreater', 'tolower', 'set_symmetric_difference', 'nexttowardl',
                 'frexp', 'push_front', 'reserve', 'flip', 'ldiv', 'strlen', 'wcscmp', 'unique',
                 'set_intersection', 'crbegin', 'stol', 'tuple_cat', 'signal', 'stoll', 'wcsptime',
                 'errno', 'toascii', 'minmax_element', 'fgetpos', 'key_comp', 'isprint', 'wcslocaleconv',
                 'nan', 'y1', 'strtold', 'time', 'set_difference', 'setbuf', 'llabs', 'isascii',
                 'abs', 'wctype', 'gmtime64_r', 'jn', 'clearerr', 'mbrlen', 'asinh', 'upper_bound',
                 'tie', 'vsnprintf', 'localtime_r', 'bucket_size', 'ceil', 'strcmp', 'wcstod128',
                 'vswprintf', 'wmemcmp', 'partition_point', 'tan', 'tgamma', 'max_bucket_count',
                 'remove_copy', 'cerr', 'set', 'isalpha', 'fwscanf', 'logb', 'setvbuf', 'strptime',
                 'isgraph', 'fgetwc', 'gmtime64', 'fgetc', 'wcsrtombs', 'wcout', 'sqrt', 'exp', 'ctime_r',
                 'emplace_hint', 'isinf', 'stoul', 'mbrtoc16', 'system', 'sscanf', 'catopen', 'getline',
                 'putc', 'mktime64', 'wcstoll', 'insert_after', 'wcsrchr', 'vfprintf', 'replace_copy',
                 'toupper', 'forward_as_tuple', 'feraiseexcept', 'asctime_r', 'lldiv', 'remquo', 'vfwprintf',
                 'islessequal', 'wcrtomb', 'at', 'shuffle', 'gamma', 'vsprintf', 'sort', 'wcsxfrm', 'any_of',
                 'strtok', 'find_first_of', 'fflush', 'wcspbrk', 'copy_if', 'feof', 'isless', 'fprintf',
                 'is_heap_until', 'atof', 'minmax', 'log', 'vfscanf', 'swap', 'replace_if', 'rewind', '_Exit',
                 'pop_heap', 'stod', 'nl_langinfo', 'feupdateenv', 'none_of', 'strtoull', 'j1', 'localeconv',
                 'load_factor', 'strpbrk', 'atanh', 'ilogb', 'lower_bound', 'strncat', 'rend', 'conj',
                 'strerror', 'c16rtomb', 'yn', 'vsscanf', 'get', 'rint', 'max_element', 'gmtime_r',
                 'srtcasecmp', 'none', 'any', 'isxdigit', 'reverse_copy', 'j0', 'wcscspn', 'erfc',
                 'quantized32', 'swap_ranges', 'wcsncmp', 'wctob', 'scanf', 'strftime', 'fsetpos', 'isupper',
                 'fma', 'quantexpd128', 'norm', 'wcstoul', 'stoi', 'cbefore_begin', 'fwide', 'wcsstr',
                 'nearbyint', 'iswxdigit', 'gets', 'strncasecmp', 'count_if', 'wcsncat', 'floor', 'end',
                 'merge', 'iswpunct', 'back', 'stable_partition', 'ungetwc', 'strfmon', 'cos', 'nextafter',
                 'getwc', 'round', 'putchar', 'iswprint', 'splice_after', 'vswscanf', 'memmove', 'equal_range',
                 'wcscat', 'bucket_count', 'scalbln', 'samequantumd64', 'fscanf', 'copy_n']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str) + 1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 547


def Python_float(node_str):
    contained_Ft = []
    if node_str[0] == '-':
        contained_Ft.append(1)
    if 'E' in node_str or 'e' in node_str:
        contained_Ft.append(2)
    if node_str[-1] == 'j':
        contained_Ft.append(3)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 4


def Python_integer(node_str):
    contained_Ft = []
    if node_str[:2] in ['0x', '0X']:
        contained_Ft.append(1)
    if node_str[0] == '-':
        contained_Ft.append(3)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 3


def Python_escape_sequence(node_str):
    contained_Ft = []
    templates = ["\\'", '\\"', '\\\\', '\\n', '\\r', '\\t', '\\b', '\\f', '\\v', '\\a']
    for id, template in enumerate(templates):
        if template in node_str:
            contained_Ft.append(id)
    return contained_Ft, 10


def Python_string_start(node_str):
    contained_Ft = []
    if node_str[0] == 'f':
        contained_Ft.append(1)
    if node_str[0] == 'r':
        contained_Ft.append(2)
    if not contained_Ft:
        contained_Ft.append(0)
    return contained_Ft, 3


def Python_identifier(node_str):  # https://docs.python.org/3/library/functions.html
    contained_Ft = []
    templates = ['setattr', 'count', 'bin', 'complex', 'delattr', 'oct', 'isdisjoint', 'tell', 'set', 'callable',
                 'vars', 'rindex', 'round', 'pop', 'add', 'slice', 'choice', 'classmethod', 'put', 'format', 'any',
                 'list', 'max', 'betavariate', 'tan', 'isfinite', 'ceil', 'popitem', 'isupper', 'insert', 'partition',
                 'fromkeys', 'triangular', 'isqrt', 'degrees', 'startswith', 'len', 'fmod', 'copysign', 'isclose',
                 'rjust', 'type', 'delete', 'strip', 'nan', 'paretovariate', 'expandtabs', 'maketrans', 'exec', 'atan',
                 'isinstance', 'frozenset', '__import__', 'write', 'float', 'issubclass', 'dict', 'gauss', 'lgamma',
                 'log', 'isprintable', 'normalvariate', 'weibullvariate', 'asinh', 'trunc', 'input', 'bytes', 'sin',
                 'intersection', 'isnumeric', 'repr', 'split', 'rstrip', 'acos', 'append', 'print', 'prod', 'casefold',
                 'splitlines', 'iter', 'locals', 'expovariate', 'lstrip', 'gammavariate', 'seek', 'getstate',
                 'lognormvariate', 'factorial', 'breakpoint', 'isidentifier', 'erf', 'dist', 'randint', 'exp', 'frexp',
                 'gcd', 'hasattr', 'log10', 'translate', 'items', 'randrange', 'atanh', 'uniform', 'ascii', 'tuple',
                 'eval', 'globals', 'rfind', 'format_map', 'rpartition', 'ldexp', 'shuffle', 'staticmethod', 'islower',
                 'int', 'read', 'anext', 'sort', 'seekable', 'floor', 'range', 'get', 'isspace', 'sample', 'cosh',
                 'rsplit', 'copy', 'isascii', 'flush', 'open', 'cos', 'dir', 'log2', 'enumerate', 'title', 'sum',
                 'bool', 'keys', 'values', 'difference', 'union', 'tau', 'seed', 'endswith', 'isdigit', 'lower',
                 'upper', 'setdefault', 'readline', 'choices', 'pi', 'math', 'acosh', 'detach', 'random', 'gamma',
                 'inf', 'sinh', 'difference_update', 'sqrt', 'asin', 'aiter', 'head', 'reversed', 'isinf', 'writelines',
                 'expm1', 'encode', 'clear', 'symmetric_difference', 'fileno', 'sorted', 'chr', 'readable', 'center',
                 'erfc', 'pow', 'capitalize', 'writable', 'replace', 'isalpha', 'issuperset', 'property', 'swapcase',
                 'isatty', 'comb', 'index', 'vonmisesvariate', 'extend', 'zip', 'help', 'fsum', 'object', 'bytearray',
                 'setstate', 'tanh', 'super', 'discard', 'update', 'readlines', 'getattr', 'ord', 'isdecimal',
                 'reverse', 'remove', 'join', 'issubset', 'divmod', 'min', 'compile', 'map',
                 'symmetric_difference_update', 'abs', 'truncate', 'e', 'find', 'atan2', 'patch', 'request',
                 'getrandbits', 'log1p', 'radians', 'next', 'remainder', 'isalnum', 'zfill', 'id',
                 'intersection_update', 'str', 'filter', 'hex', 'perm', 'istitle', 'close', 'hash', 'fabs',
                 'memoryview', 'hypot', 'ljust', 'isnan', 'post', 'all']
    if node_str in templates:
        contained_Ft.append(templates.index(node_str)+1)
    else:
        contained_Ft.append(0)
    return contained_Ft, 243


def node_type_transfer(lang, node_type, node_str, variable_names):
    node_str = str(node_str)
    if node_type == 'NO_RESTRICTION':
        return ['NO_RESTRICTION-0']
    ftr_list = check_node_exist(lang, node_type, node_str, variable_names)
    node_type_list = []
    if ftr_list:
        for ftr in ftr_list:
            node_type_list.append(f'{node_type}-{ftr}')
    else:
        node_type_list.append(f'{node_type}-0')
    return node_type_list


def traverse_tree_type(node: Node, lang, record, variable_names):
    for n in node.children:
        # if (lang == 'Python' and n.type not in python_block_name) or (lang == 'Java' and n.type not in java_block_name) or (lang == 'C++' and n.type not in cpp_block_name):
        node_types = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
        record.extend(node_types)
        traverse_tree_type(n, lang, record, variable_names)


def traverse_tree_type_if_else(node: Node, lang, record, depth, variable_names):
    if depth:
        for n_id, n in enumerate(node.children):
            node_types = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
            record.extend(node_types)
            traverse_tree_type_if_else(n, lang, record, depth + 1, variable_names)
    else:
        for n_id, n in enumerate(node.children):
            if n_id in [0, 1]:
                node_types = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                record.extend(node_types)
                traverse_tree_type_if_else(n, lang, record, depth + 1, variable_names)


def traverse_tree_type_exclude_block(node: Node, lang, record, variable_names):
    pre_node_type = ''
    for n in node.children:
        if pre_node_type == 'else':
            pre_node_type = n.type
            continue
        elif (lang == 'Python' and n.type in python_block_name) or (lang == 'Java' and n.type in java_block_name) or ( lang == 'C++' and n.type in cpp_block_name):
            record.append(n.type+'-0')
            pre_node_type = n.type
            continue
        node_types = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
        record.extend(node_types)
        traverse_tree_type(n, lang, record, variable_names)
        pre_node_type = n.type


def traverse_tree_type_exclude_last_child(node: Node, lang, record, variable_names):
    for n in node.children[:-1]:
        node_types = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
        record.extend(node_types)
        traverse_tree_type(n, lang, record, variable_names)


def delete_code(code_lines, map):
    this_code_lines = []
    for line_id in range(len(code_lines)):
        this_line = ''
        for chr_id in range(len(code_lines[line_id])):
            if [line_id, chr_id] in map:
                this_line += ' '
            else:
                this_line += code_lines[line_id][chr_id]
        this_code_lines.append(this_line)
    return this_code_lines


def calculate_map(star_pos, end_pos, code_lines):
    map = []
    if star_pos[0] == end_pos[0]:
        for line_id in range(len(code_lines)):
            for chr_id in range(len(code_lines[line_id])):
                if line_id == star_pos[0] and chr_id >= star_pos[1] and chr_id < end_pos[1]:
                    map.append([line_id, chr_id])
                elif line_id == star_pos[0] and chr_id == end_pos[1] and code_lines[line_id][chr_id] == ' ':
                    map.append([line_id, chr_id])
    else:
        for line_id in range(len(code_lines)):
            for chr_id in range(len(code_lines[line_id])):
                if line_id == star_pos[0]:
                    if chr_id >= star_pos[1]:
                        map.append([line_id, chr_id])
                elif line_id > star_pos[0] and line_id < end_pos[0]:
                    map.append([line_id, chr_id])
                elif line_id == end_pos[0]:
                    if chr_id < end_pos[1]:
                        map.append([line_id, chr_id])
                    elif chr_id == end_pos[1] and code_lines[line_id][chr_id] == ' ':
                        map.append([line_id, chr_id])
    return map


def reduce_pos_of_java_tree(stmts):
    new_stmts = []
    for stmt in stmts:
        this_stmt = stmt[:]
        for pos_id, pos in enumerate(this_stmt[2]):
            this_stmt[2][pos_id][0] = this_stmt[2][pos_id][0] - 1
        new_stmts.append(this_stmt)
    return new_stmts


def traverse_tree(node: Node, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, only_path=False, fun_block=0, mine=True, target_stmt_id=[]):
    start_idx = 0
    if (lang == 'Python' and node.type == 'function_definition') or (lang == 'Java' and node.type == 'program') or (lang == 'C++' and node.type == 'function_definition'):
        start_idx = -1
    if only_block:
        if only_path:
            stmts = []
            for n in node.children[start_idx:]:
                if n.is_named:
                    if (lang == 'Python' and n.type in ['block']) or (lang == 'Java' and n.type in ['block']) or (lang == 'C++' and n.type in ['compound_statement']):
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, only_path=only_path, fun_block=fun_block+1, mine=mine)
                        stmts.extend(sub_stmt_list)
                    elif (lang == 'Python' and n.type in python_block_name) or (lang == 'Java' and n.type in java_block_name) or (lang == 'C++' and n.type in cpp_block_name):
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type_exclude_block(n, lang, record, variable_names)
                        this_root_my_tree = tree2MyTree(n, lang, variable_names, if_exclude_block=True)
                        this_path = '||||'.join(record)
                        this_map = []
                        for this_n in n.children:
                            if (lang == 'Python' and this_n.type not in python_block_name) or (lang == 'Java' and this_n.type not in java_block_name) or (lang == 'C++' and this_n.type not in cpp_block_name):
                                this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))
                            else:
                                for block_child in this_n.children:
                                    if mine and not block_child.is_named:
                                        this_map.extend(calculate_map(block_child.start_point, block_child.end_point, code_lines))
                        stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=True, exclude_last_child=False, only_path=only_path, fun_block=fun_block + 1, mine=mine)
                        stmts.extend(sub_stmt_list)
        else:
            stmts = []
            for n in node.children[start_idx:]:
                if n.is_named:
                    if (lang == 'Python' and n.type in ['block']) or (lang == 'Java' and n.type in ['block']) or (lang == 'C++' and n.type in ['compound_statement']):
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, fun_block=fun_block + 1, mine=mine)
                        stmts.append(sub_stmt_list)
                    elif (lang == 'Python' and n.type in python_block_name) or lang == 'Java' and n.type in java_block_name or (lang == 'C++' and n.type in cpp_block_name):
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type_exclude_block(n, lang, record, variable_names)
                        this_root_my_tree = tree2MyTree(n, lang, variable_names, if_exclude_block=True)
                        this_path = '||||'.join(record)
                        this_map = []
                        for this_n in n.children:
                            if (lang == 'Python' and this_n.type not in python_block_name) or (
                                    lang == 'Java' and this_n.type not in java_block_name) or (
                                    lang == 'C++' and this_n.type not in cpp_block_name):
                                this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))
                            else:
                                for block_child in this_n.children:
                                    if not block_child.is_named:
                                        this_map.extend(
                                            calculate_map(block_child.start_point, block_child.end_point, code_lines))
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=True, exclude_last_child=False, fun_block=fun_block + 1, mine=mine)
                        this_all_len = [len(item) for item in sub_stmt_list]
                        this_root_path = copy.deepcopy(sub_stmt_list[this_all_len.index(max(this_all_len))])
                        this_root_path.append([this_path, this_root_my_tree, this_map, fun_block])
                        this_none_blank_sub_stmt_list = [item for item in sub_stmt_list if
                                                         len(item) < max(this_all_len)]
                        this_none_blank_sub_stmt_list.append(this_root_path)
                        stmts.append(this_none_blank_sub_stmt_list)
    elif exclude_last_child:
        stmts = []
        record = node_type_transfer(lang, node.type, node.text.decode("utf-8"), variable_names)
        traverse_tree_type_exclude_last_child(node, lang, record, variable_names)
        if lang == 'Java':
            record.append('block-0')
        elif lang == 'Python':
            record.append('block-0')
        elif lang == 'C++':
            record.append('compound_statement-0')
        this_root_my_tree = tree2MyTree(node, lang, variable_names, if_exclude_last_child=True)
        this_path = '||||'.join(record)
        this_map = []
        for this_n in node.children[:-1]:
            this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))

        if node.children[-1].type.startswith('for_') or node.children[-1].type.startswith('if_') or node.children[-1].type.startswith('elif_') or node.children[-1].type.startswith('else_') or node.children[-1].type.startswith('while_') or node.children[-1].type.startswith('try_') or node.children[-1].type.startswith('catch_'):
            if only_path:
                stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                sub_stmt_list = traverse_tree(node.children[-1], lang, code_lines, variable_names, only_block=False, exclude_last_child=True, only_path=only_path, fun_block=fun_block + 1, mine=mine)
                stmts.extend(sub_stmt_list)
            else:
                sub_stmt_list = traverse_tree(node.children[-1], lang, code_lines, variable_names, only_block=False, exclude_last_child=True, fun_block=fun_block + 1, mine=mine)
                this_all_len = [len(item) for item in sub_stmt_list]
                this_root_path = copy.deepcopy(sub_stmt_list[this_all_len.index(max(this_all_len))])
                this_root_path.append([this_path, this_root_my_tree, this_map, fun_block])
                sub_stmt_list.append(this_root_path)
                stmts.append(sub_stmt_list)
        else:
            if only_path:
                stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                last_record = node_type_transfer(lang, node.children[-1].type, node.children[-1].text.decode("utf-8"), variable_names)
                traverse_tree_type(node.children[-1], lang, last_record, variable_names)
                this_my_tree = tree2MyTree(node.children[-1], lang, variable_names)
                last_this_path = '||||'.join(last_record)
                stmts.append([last_this_path, this_my_tree, calculate_map(node.children[-1].start_point, node.children[-1].end_point, code_lines), fun_block+1])
            else:
                this_root_path0 = []
                this_root_path1 = []
                this_root_path1.append([this_path, this_root_my_tree, this_map, fun_block])
                last_record = node_type_transfer(lang, node.children[-1].type, node.children[-1].text.decode("utf-8"), variable_names)
                traverse_tree_type(node.children[-1], lang, last_record, variable_names)
                this_my_tree = tree2MyTree(node.children[-1], lang, variable_names)
                last_this_path = '||||'.join(last_record)
                this_root_path1.append([last_this_path, this_my_tree, calculate_map(node.children[-1].start_point, node.children[-1].end_point, code_lines), fun_block+1])
                stmts.append([this_root_path0, this_root_path1])
    else:
        stmts = []
        for node_child_n_id, n in enumerate(node.children[start_idx:]):
            if target_stmt_id:
                if node_child_n_id not in target_stmt_id:
                    continue
            if n.is_named:
                if_contain_block = False
                for next_n in n.children:
                    if next_n.is_named:
                        if (lang == 'Python' and next_n.type in python_block_name) or (lang == 'Java' and next_n.type in java_block_name) or (lang == 'C++' and next_n.type in cpp_block_name):
                            if_contain_block = True
                if (lang == 'Python' and n.type in python_block_name) or (lang == 'Java' and n.type in java_block_name) or (lang == 'C++' and n.type in cpp_block_name):
                    if only_path:
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, only_path=only_path, fun_block=fun_block+1, mine=mine)
                        stmts.extend(sub_stmt_list)
                    else:
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, fun_block=fun_block + 1, mine=mine)
                        stmts.append(sub_stmt_list)
                elif n.type.startswith('if_') and lang in ['Java', 'C++'] and len(n.children) == 5 and n.children[3].type == 'else' and ((lang == 'Java' and n.children[2].type != 'block') or (lang == 'C++' and n.children[2].type != 'compound_statement')) and ((lang == 'Java' and n.children[4].type != 'block') or (lang == 'C++' and n.children[4].type != 'compound_statement')):
                    record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                    traverse_tree_type_if_else(n, lang, record, 0, variable_names)
                    if lang == 'Java':
                        record.extend(['block-0', 'else-0'])
                    elif lang == 'C++':
                        record.extend(['compound_statement-0', 'else-0'])
                    this_root_my_tree = tree2MyTree_if_else(n, lang, variable_names)
                    this_path = '||||'.join(record)
                    this_map = []
                    this_map.extend(calculate_map(n.children[0].start_point, n.children[0].end_point, code_lines))
                    this_map.extend(calculate_map(n.children[1].start_point, n.children[1].end_point, code_lines))
                    this_map.extend(calculate_map(n.children[3].start_point, n.children[3].end_point, code_lines))
                    item1 = [this_path, this_root_my_tree, this_map, fun_block]

                    record2 = node_type_transfer(lang, n.children[2].type, n.children[2].text.decode("utf-8"), variable_names)
                    traverse_tree_type(n.children[2], lang, record2, variable_names)
                    this_root_my_tree2 = tree2MyTree(n.children[2], lang, variable_names)
                    this_path2 = '||||'.join(record2)
                    this_map2 = []
                    this_map2.extend(calculate_map(n.children[2].start_point, n.children[2].end_point, code_lines))
                    item2 = [this_path2, this_root_my_tree2, this_map2, fun_block+2]

                    record3 = node_type_transfer(lang, n.children[3].type, n.children[3].text.decode("utf-8"), variable_names)
                    traverse_tree_type(n.children[3], lang, record3, variable_names)
                    this_root_my_tree3 = tree2MyTree(n.children[3], lang, variable_names)
                    this_path3 = '||||'.join(record3)
                    this_map3 = []
                    this_map3.extend(calculate_map(n.children[3].start_point, n.children[3].end_point, code_lines))
                    item3 = [this_path3, this_root_my_tree3, this_map3, fun_block+1]

                    record4 = node_type_transfer(lang, n.children[4].type, n.children[4].text.decode("utf-8"), variable_names)
                    traverse_tree_type(n.children[4], lang, record4, variable_names)
                    this_root_my_tree4 = tree2MyTree(n.children[4], lang, variable_names)
                    this_path4 = '||||'.join(record4)
                    this_map4 = []
                    this_map4.extend(calculate_map(n.children[4].start_point, n.children[4].end_point, code_lines))
                    item4 = [this_path4, this_root_my_tree4, this_map4, fun_block+3]
                    if only_path:
                        stmts.append(item1)
                        stmts.append(item2)
                        stmts.append(item3)
                        stmts.append(item4)
                    else:
                        stmts.append([[], [item1, item2, item3, item4]])
                elif if_contain_block:
                    # if lang == 'C++' and '{' not in n.text.decode("utf-8"):
                    #     print('')
                    if only_path:
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type_exclude_block(n, lang, record, variable_names)
                        this_root_my_tree = tree2MyTree(n, lang, variable_names, if_exclude_block=True)
                        this_path = '||||'.join(record)
                        this_map = []
                        pre_this_n = ''
                        blocks = []
                        for this_n_id, this_n in enumerate(n.children):
                            if (lang == 'Python' and this_n.type in python_block_name) or (lang == 'Java' and this_n.type in java_block_name) or (lang == 'C++' and this_n.type in cpp_block_name):
                                blocks.append([this_n, True, this_n_id])
                                for block_child in this_n.children:
                                    if mine and not block_child.is_named:
                                        this_map.extend(calculate_map(block_child.start_point, block_child.end_point, code_lines))
                            elif pre_this_n == 'else':
                                blocks.append([this_n, False, this_n_id])
                            elif (lang == 'Python' and this_n.type not in python_block_name) or (lang == 'Java' and this_n.type not in java_block_name) or (lang == 'C++' and this_n.type not in cpp_block_name):
                                this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))
                            else:
                                for block_child in this_n.children:
                                    if mine and not block_child.is_named:
                                        this_map.extend(calculate_map(block_child.start_point, block_child.end_point, code_lines))
                            pre_this_n = this_n.type
                        stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                        for block in blocks:
                            if block[1]:
                                for block_child_id, block_child in enumerate(block[0].children):
                                    if block_child.is_named:
                                        sub_stmt_list = traverse_tree(block[0], lang, code_lines, variable_names, only_block=False, exclude_last_child=False, only_path=only_path, fun_block=fun_block+1, mine=mine, target_stmt_id=[block_child_id])
                                        stmts.extend(sub_stmt_list)
                            else:
                                sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, only_path=only_path, fun_block=fun_block, mine=mine, target_stmt_id=[block[2]])
                                stmts.extend(sub_stmt_list)
                    else:
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type_exclude_block(n, lang, record, variable_names)
                        this_root_my_tree = tree2MyTree(n, lang, variable_names, if_exclude_block=True)
                        this_path = '||||'.join(record)
                        this_map = []
                        pre_this_n = ''
                        blocks = []
                        for this_n in n.children:
                            if (lang == 'Python' and this_n.type in python_block_name) or (lang == 'Java' and this_n.type in java_block_name) or (lang == 'C++' and this_n.type in cpp_block_name):
                                blocks.append([this_n, True])
                                for block_child in this_n.children:
                                    if not block_child.is_named:
                                        this_map.extend(calculate_map(block_child.start_point, block_child.end_point, code_lines))
                            elif pre_this_n == 'else':
                                blocks.append([this_n, False])
                            elif (lang == 'Python' and this_n.type not in python_block_name) or (lang == 'Java' and this_n.type not in java_block_name) or (lang == 'C++' and this_n.type not in cpp_block_name):
                                this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))
                            else:
                                for block_child in this_n.children:
                                    if not block_child.is_named:
                                        this_map.extend(calculate_map(block_child.start_point, block_child.end_point, code_lines))
                        sub_stmt_list = traverse_tree(n, lang, code_lines, variable_names, only_block=True, exclude_last_child=False, fun_block=fun_block + 1, mine=mine)
                        this_all_len = [len(item) for item in sub_stmt_list]
                        this_root_path = copy.deepcopy(sub_stmt_list[this_all_len.index(max(this_all_len))])
                        this_root_path.append([this_path, this_root_my_tree, this_map, fun_block])
                        this_none_blank_sub_stmt_list = [item for item in sub_stmt_list if len(item) < max(this_all_len)]
                        this_none_blank_sub_stmt_list.append(this_root_path)
                        stmts.append(this_none_blank_sub_stmt_list)
                elif (n.type.startswith('for_') or n.type.startswith('if_') or n.type.startswith('elif_') or n.type.startswith('else_') or n.type.startswith('while_')) and if_contain_block == False:
                    record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                    traverse_tree_type_exclude_last_child(n, lang, record, variable_names)
                    this_root_my_tree = tree2MyTree(n, lang, variable_names, if_exclude_last_child=True)
                    this_path = '||||'.join(record)
                    this_map = []
                    for this_n in n.children[:-1]:
                        this_map.extend(calculate_map(this_n.start_point, this_n.end_point, code_lines))
                    if only_path:
                        if n.children[-1].type.startswith('for_') or n.children[-1].type.startswith('if_') or n.children[-1].type.startswith('elif_') or n.children[-1].type.startswith('else_') or n.children[-1].type.startswith('while_'):
                            if lang == 'Java':
                                stmts.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'Python':
                                stmts.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'C++':
                                stmts.append([this_path + '||||compound_statement-0', this_root_my_tree, this_map, fun_block])
                            sub_stmt_list = traverse_tree(n.children[-1], lang, code_lines, variable_names, only_block=False, exclude_last_child=True, only_path=only_path, fun_block=fun_block+1, mine=mine)
                            stmts.extend(sub_stmt_list)
                        elif n.children[-1].start_point == n.children[-1].end_point or len(n.children[-1].text.decode("utf-8")) == 1:
                            this_map.extend(calculate_map(n.children[-1].start_point, n.children[-1].end_point, code_lines))
                            stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                        else:
                            if lang == 'Java':
                                stmts.append([this_path+'||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'Python':
                                stmts.append([this_path+'||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'C++':
                                stmts.append([this_path + '||||compound_statement-0', this_root_my_tree, this_map, fun_block])
                            last_record = node_type_transfer(lang, n.children[-1].type, n.children[-1].text.decode("utf-8"), variable_names)
                            traverse_tree_type(n.children[-1], lang, last_record, variable_names)
                            this_my_tree = tree2MyTree(n.children[-1], lang, variable_names)
                            last_this_path = '||||'.join(last_record)
                            stmts.append([last_this_path, this_my_tree, calculate_map(n.children[-1].start_point, n.children[-1].end_point, code_lines), fun_block+1])
                    else:
                        if n.children[-1].type.startswith('for_') or n.children[-1].type.startswith('if_') or n.children[-1].type.startswith('elif_') or n.children[-1].type.startswith('else_') or n.children[-1].type.startswith('while_'):
                            sub_stmt_list = traverse_tree(n.children[-1], lang, code_lines, variable_names, only_block=False, exclude_last_child=True, fun_block=fun_block + 1, mine=mine)
                            this_all_len = [len(item) for item in sub_stmt_list]
                            this_root_path = copy.deepcopy(sub_stmt_list[this_all_len.index(max(this_all_len))])
                            if lang == 'Java':
                                this_root_path.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'Python':
                                this_root_path.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'C++':
                                this_root_path.append([this_path + '||||compound_statement-0', this_root_my_tree, this_map, fun_block])
                            sub_stmt_list.append(this_root_path)
                            stmts.append(sub_stmt_list)
                        elif n.children[-1].start_point == n.children[-1].end_point or len(n.children[-1].text.decode("utf-8")) == 1:
                            this_map.extend(calculate_map(n.children[-1].start_point, n.children[-1].end_point, code_lines))
                            stmts.append([this_path, this_root_my_tree, this_map, fun_block])
                        else:
                            this_root_path0 = []
                            this_root_path1 = []
                            if lang == 'Java':
                                this_root_path1.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'Python':
                                this_root_path1.append([this_path + '||||block-0', this_root_my_tree, this_map, fun_block])
                            elif lang == 'C++':
                                this_root_path1.append([this_path + '||||compound_statement-0', this_root_my_tree, this_map, fun_block])
                            last_record = node_type_transfer(lang, n.children[-1].type, n.children[-1].text.decode("utf-8"), variable_names)
                            traverse_tree_type(n.children[-1], lang, last_record, variable_names)
                            this_my_tree = tree2MyTree(n.children[-1], lang, variable_names)
                            last_this_path = '||||'.join(last_record)
                            this_root_path1.append([last_this_path, this_my_tree, calculate_map(n.children[-1].start_point, n.children[-1].end_point, code_lines), fun_block+1])
                            stmts.append([this_root_path0, this_root_path1])
                else:
                    if only_path:
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type(n, lang, record, variable_names)
                        this_path = '||||'.join(record)
                        this_my_tree = tree2MyTree(n, lang, variable_names)
                        stmts.append([this_path, this_my_tree, calculate_map(n.start_point, n.end_point, code_lines), fun_block])
                    else:
                        record = node_type_transfer(lang, n.type, n.text.decode("utf-8"), variable_names)
                        traverse_tree_type(n, lang, record, variable_names)
                        this_path = '||||'.join(record)
                        this_my_tree = tree2MyTree(n, lang, variable_names)
                        stmts.append([this_path, this_my_tree, calculate_map(n.start_point, n.end_point, code_lines), fun_block])
    if only_path:
        return stmts
    else:
        item_idx = []
        list_idx = []
        # 区分是否为block
        for id in range(len(stmts)):
            if len(stmts[id]) == 4 and type(stmts[id][1]) == MyTree:
                item_idx.append(id)
            else:
                list_idx.append(id)
        # 获取删除组合
        max_ID_list = []
        if len(stmts) > 1 and len(stmts[-1]) == 4 and type(stmts[-1][1]) == MyTree and (stmts[-1][0].startswith('return') or stmts[-1][0].startswith('expression_statement-0||||call-0||||identifier-53||||') or stmts[-1][0].startswith('expression_statement-0||||method_invocation-0||||field_access-0||||identifier-436||||.-0||||identifier-769||||.-0||||identifier-0||||argument_list-0||||(-0||||')):
            ID_list = [[]]
            for id in range(len(stmts)):
                if id in list_idx:
                    if only_block and len(stmts[id]) == 2:
                        continue
                    this_list = []
                    this_list.append(id)
                    if this_list not in ID_list:
                        ID_list.append(this_list)
            this_list = []
            for id in range(len(stmts)-1):
                this_list.append(len(stmts)-2-id)
                this_list_addlistid = copy.deepcopy(this_list)
                for list_id in list_idx:
                    if list_id in this_list_addlistid:
                        this_list_addlistid.remove(list_id)
                if this_list_addlistid not in ID_list:
                    ID_list.append(copy.deepcopy(this_list_addlistid))
            max_ID_list = [len(stmts)-1-id for id in range(len(stmts))]
        elif item_idx == [] and list_idx != []:
            ID_list = [[]]
            for id in range(len(stmts)):
                if only_block and (len(stmts[id]) == 2 or stmts[id] == [[]]):  # 这个block只有一个stmt
                    continue
                this_list = []
                this_list.append(id)
                if this_list not in ID_list:
                    ID_list.append(this_list)
            max_ID_list = [len(stmts) - 1 - id for id in range(len(stmts))]
        else:
            ID_list = [[]]
            for id in range(len(stmts)):
                if id in list_idx:
                    if only_block and len(stmts[id]) == 2:
                        continue
                    this_list = []
                    this_list.append(id)
                    if this_list not in ID_list:
                        ID_list.append(this_list)
            this_list = []
            for id in range(len(stmts)):
                this_list.append(len(stmts) - 1 - id)
                this_list_addlistid = copy.deepcopy(this_list)
                for list_id in list_idx:
                    if list_id in this_list_addlistid:
                        this_list_addlistid.remove(list_id)
                if this_list_addlistid not in ID_list:
                    ID_list.append(copy.deepcopy(this_list_addlistid))
            # if list_idx == []:
            this_list = [len(stmts) - 1 - id for id in range(len(stmts))]
            if this_list in ID_list:
                ID_list.remove(this_list)
            max_ID_list = [len(stmts) - 1 - id for id in range(len(stmts))]
        # 将block（每个有多种选项）进行填充
        # print('')
        list_of_ID_list = fill_stmt(ID_list, stmts, list_idx, only_block)
        fill_max_ID_list = fill_stmt_for_max(max_ID_list, stmts, list_idx)
        list_of_ID_list.append(fill_max_ID_list)
        return_stmt_list = []
        return_stmt_list_record = []
        # 将非block进行填充
        for this_list in list_of_ID_list:
            return_stmts = []
            return_stmts_record = []
            for id in this_list:
                if type(id) == int:
                    if id in list_idx:
                        raise Exception("I do not think this exception can be triggered!")
                    else:
                        return_stmts.append(stmts[id])
                        return_stmts_record.append([stmts[id][0], stmts[id][2]])
                else:
                    return_stmts.append(id)
                    return_stmts_record.append([id[0], id[2]])
            if return_stmts_record not in return_stmt_list_record:
                return_stmt_list.append(copy.deepcopy(return_stmts))
                return_stmt_list_record.append(copy.deepcopy(return_stmts_record))
        return return_stmt_list


def fill_stmt_for_max(max_ID_list, stmts, list_idx):
    list_of_ID_list = copy.deepcopy(max_ID_list)
    for id, stmt_id in enumerate(list_of_ID_list):
        if stmt_id in list_idx:
            this_stmt_choices = stmts[stmt_id]
            this_stmt_len_choices = [[len(choice), choice_id] for choice_id, choice in enumerate(this_stmt_choices)]
            this_stmt_len_choices.sort()
            max_stmt_len_choice = this_stmt_choices[this_stmt_len_choices[-1][1]]
            list_of_ID_list[id] = max_stmt_len_choice
            # list_of_ID_list.pop(id)
            # for choice_item_id, choice_item in enumerate(max_stmt_len_choice):
            #     list_of_ID_list.insert(id + choice_item_id, choice_item)
    return_list_of_ID_list =[]
    for item in list_of_ID_list:
        if type(item) == int:
            return_list_of_ID_list.append(item)
        else:
            return_list_of_ID_list.extend(item)
    return return_list_of_ID_list


def fill_stmt(ID_list, stmts, list_idx, only_block):
    list_of_ID_lists = copy.deepcopy(ID_list)
    list_of_ID_lists_record = []
    for item in list_of_ID_lists:
        this_list_of_ID_lists_record = []
        for item_id in item:
            if type(item_id) == int:
                this_list_of_ID_lists_record.append(item_id)
            else:
                this_list_of_ID_lists_record.append([item_id[0], item_id[2]])
        list_of_ID_lists_record.append(this_list_of_ID_lists_record)
    while(True):
        new_list_of_ID_lists = []
        new_list_of_ID_lists_record = []
        for list_of_ID_list in list_of_ID_lists:
            if_contain_list = False
            for stmt_id in list_of_ID_list:
                if stmt_id in list_idx:
                    if_contain_list = True
            if if_contain_list:
                for id, stmt_id in enumerate(list_of_ID_list):
                    if stmt_id in list_idx:
                        this_stmt_choices = stmts[stmt_id]
                        this_stmt_len_choices = [[len(choice), choice_id] for choice_id, choice in enumerate(this_stmt_choices)]
                        if only_block:
                            this_stmt_len_choices.sort()
                            if this_stmt_len_choices:
                                this_stmt_len_choices.pop(-1)
                        this_stmt_len_choices = [this_stmt_choices[item[1]] for item in this_stmt_len_choices]
                        for this_stmt_choice in this_stmt_len_choices:
                            new_list_of_ID_list = copy.deepcopy(list_of_ID_list)
                            new_list_of_ID_list.pop(id)
                            for choice_item_id, choice_item in enumerate(this_stmt_choice):
                                new_list_of_ID_list.insert(id+choice_item_id, choice_item)
                            new_list_of_ID_list_record = []
                            for new_list_item in new_list_of_ID_list:
                                if type(new_list_item) == int:
                                    new_list_of_ID_list_record.append(new_list_item)
                                else:
                                    new_list_of_ID_list_record.append([new_list_item[0], new_list_item[2]])
                            if new_list_of_ID_list_record not in new_list_of_ID_lists_record:
                                new_list_of_ID_lists.append(new_list_of_ID_list)
                                new_list_of_ID_lists_record.append(new_list_of_ID_list_record)
            else:
                new_list_of_ID_list = copy.deepcopy(list_of_ID_list)
                new_list_of_ID_list_record = []
                for new_list_item in new_list_of_ID_list:
                    if type(new_list_item) == int:
                        new_list_of_ID_list_record.append(new_list_item)
                    else:
                        new_list_of_ID_list_record.append([new_list_item[0], new_list_item[2]])
                if new_list_of_ID_list_record not in new_list_of_ID_lists_record:
                    new_list_of_ID_lists.append(new_list_of_ID_list)
                    new_list_of_ID_lists_record.append(new_list_of_ID_list_record)
        if new_list_of_ID_lists_record != list_of_ID_lists_record:
            list_of_ID_lists = copy.deepcopy(new_list_of_ID_lists)
            list_of_ID_lists_record = copy.deepcopy(new_list_of_ID_lists_record)
        else:
            break
    return list_of_ID_lists


def filter_traverse_tree_paths(list_stmts):
    new_list_of_stmts = []
    new_list_of_positions = []
    new_list_of_stmts_positions = []
    new_list_of_depth = []
    trees = []
    path2tree = {}
    for stmt in list_stmts:
        if stmt[0] in ['else-0']:
            continue
        if stmt[0] not in path2tree:
            path2tree[stmt[0]] = stmt[1]
        if [stmt[0], stmt[2]] not in new_list_of_stmts_positions:
            new_list_of_stmts_positions.append([stmt[0], stmt[2]])
            new_list_of_stmts.append(stmt[0])
            new_list_of_positions.append(stmt[2])
            new_list_of_depth.append(stmt[3])
            trees.append(stmt[1])
    return new_list_of_stmts, new_list_of_depth, trees, path2tree, new_list_of_positions, new_list_of_stmts_positions


# def max_traverse_tree_paths(list_of_list_stmts, position=False):
#     max_stmt_list = []
#     for stmt_list in list_of_list_stmts:
#         if len(stmt_list) > len(max_stmt_list):
#             max_stmt_list = stmt_list[:]
#     if position:
#         return_max_stmt_list = [item[1] for item in max_stmt_list]
#     else:
#         return_max_stmt_list = [item[0] for item in max_stmt_list]
#     return return_max_stmt_list


def find_variable_for_def(tree, variables, lang, start=True):
    for child in tree.children:
        if child.type in ['[', '++', '--', '('] or '=' in child.type:
            start = False
        node_types = node_type_transfer(lang, child.type, child.text, [])
        this_type = node_types[0]
        if start and (this_type == 'identifier-0' or child.text in ['sum', 'count']):
            if type(child) == tree_sitter.Node:
                if tree.text.decode() not in ['print', 'main']:
                    variables.append(child.text.decode())
            else:
                if tree.text not in ['print', 'main']:
                    variables.append(child.text)
        find_variable_for_def(child, variables, lang, start=start)


def find_variable_for_def_in_for(tree, variables, lang, start=True):
    for child in tree.children:
        if child.type in ['in']:
            start = False
        node_types = node_type_transfer(lang, child.type, child.text, [])
        this_type = node_types[0]
        if start and (this_type == 'identifier-0' or child.text in ['sum', 'count']):
            if type(child) == tree_sitter.Node:
                variables.append(child.text.decode())
            else:
                variables.append(child.text)
        find_variable_for_def_in_for(child, variables, lang, start=start)


def find_variable_for_func(tree, variables, lang, start=False):
    if tree.type in ['block', 'compound_statement']:
        start = False
    if tree.type in ['parameters', 'formal_parameters', 'parameter_list']:
        start = True
    for child in tree.children:
        if child.type in ['block', 'compound_statement']:
            start = False
            break
        if child.type in ['type']:
            continue
        node_types = node_type_transfer(lang, child.type, child.text, [])
        this_type = node_types[0]
        if start and this_type == 'identifier-0':
            if type(child) == tree_sitter.Node:
                variables.append(child.text.decode())
            else:
                variables.append(child.text)
        find_variable_for_func(child, variables, lang, start=start)


def find_def_variable(tree, variables, lang):
    if tree.type in ['function_definition', 'method_declaration']:
        find_variable_for_func(tree, variables, lang)
    if tree.type in ['declaration', 'local_variable_declaration',
                      'assignment_expression', 'variable_declarator', 'update_expression',
                      'assignment', 'augmented_assignment', 'pattern_list']:
        find_variable_for_def(tree, variables, lang)
    elif lang == 'Python' and tree.type in ['for_statement']:
        find_variable_for_def_in_for(tree, variables, lang)
    else:
        for child in tree.children:
            find_def_variable(child, variables, lang)


def if_find_variable_for_def(tree, if_def, start=True):
    for child in tree.children:
        if '=' in child.type:
            if_def.append(1)
        if_find_variable_for_def(child, if_def, start=start)


def if_find_variable_for_def_in_for(tree, if_def, start=True):
    for child in tree.children:
        if child.type in ['in']:
            if_def.append(1)
        if_find_variable_for_def_in_for(child, if_def, start=start)


def if_find_def_variable(tree, if_def, lang):
    if tree.type in ['function_definition', 'method_declaration']:
        if_def.append(1)
    if tree.type in ['declaration', 'local_variable_declaration',
                      'assignment_expression', 'variable_declarator', 'update_expression',
                      'assignment', 'augmented_assignment', 'pattern_list']:
        if_find_variable_for_def(tree, if_def)
    elif lang == 'Python' and tree.type in ['for_statement']:
        if_find_variable_for_def_in_for(tree, if_def)
    else:
        for child in tree.children:
            if_find_def_variable(child, if_def, lang)


# def verify_extended_mapping(tree1, tree2, def_vars1, def_vars2, source_lang, target_lang):
#     this_def_variables1 = []
#     find_def_variable(tree1, this_def_variables1, source_lang)
#     this_usesd_variables2 = []
#     find_use_variable(tree1, this_usesd_variables2, source_lang)
#     this_usesd_variables_filt1 = []
#     for var in this_usesd_variables2:
#         if var in def_vars1:
#             this_usesd_variables_filt1.append(var)
#     this_def_variables2 = []
#     find_def_variable(tree2, this_def_variables2, target_lang)
#     this_usesd_variables2 = []
#     find_use_variable(tree2, this_usesd_variables2, target_lang)
#     this_usesd_variables_filt2 = []
#     for var in this_usesd_variables2:
#         if var in def_vars2:
#             this_usesd_variables_filt2.append(var)
#     # if set(this_def_variables1) == set(this_def_variables2) and set(this_usesd_variables_filt1) == set(this_usesd_variables_filt2):
#         # return True
#     if set(this_usesd_variables_filt1) == set(this_usesd_variables_filt2):
#         return True
#     else:
#         return False


def verify_build_mapping(tree1, trees2, def_vars1, def_vars2, source_lang, target_lang):
    this_def_variables1 = []
    find_def_variable(tree1, this_def_variables1, source_lang)
    this_usesd_variables2 = []
    find_use_variable(tree1, this_usesd_variables2, source_lang)
    this_usesd_variables_filt1 = []
    for var in this_usesd_variables2:
        if var in def_vars1 and var not in this_def_variables1 and var not in this_usesd_variables_filt1:
            this_usesd_variables_filt1.append(var)
    this_def_variables2 = []
    for tree2 in trees2:
        find_def_variable(tree2, this_def_variables2, target_lang)
    this_usesd_variables2 = []
    for tree2 in trees2:
        find_use_variable(tree2, this_usesd_variables2, target_lang)
    this_usesd_variables_filt2 = []
    for var in this_usesd_variables2:
        if var in def_vars2 and var not in this_def_variables2 and var not in this_usesd_variables_filt2:
            this_usesd_variables_filt2.append(var)

    # if len(trees2) == 1:
    #     if set(this_def_variables1) == set(this_def_variables2) and set(this_usesd_variables_filt1) == set(this_usesd_variables_filt2):
    #         return True
    #     else:
    #         return False
    # else:
    #     if set(this_def_variables1).issubset(this_def_variables2) and set(this_usesd_variables_filt1) == set(this_usesd_variables_filt2):
    #         return True
    #     else:
    #         return False

    if set(this_usesd_variables_filt1) == set(this_usesd_variables_filt2):
        return True
    else:
        return False


def parse_vari_dep(stmt_list, lines, stmt_list_pos, lang, this_trees):
    def_use_deps = []
    var_info = {}
    use_consts = []
    def_variables = {}
    line_def_variables = {}
    use_variables = {}
    for stmt_id, source_stmt in enumerate(stmt_list):
        this_use_consts = []
        find_use_consts(this_trees[stmt_id], this_use_consts)
        use_consts.append(this_use_consts)
        # print(lines[stmt_list_pos[stmt_id][0][0]])

        this_def_variables = []
        find_def_variable(this_trees[stmt_id], this_def_variables, lang)
        if stmt_id in def_variables:
            for var in this_def_variables:
                if var not in def_variables[stmt_id]:
                    def_variables[stmt_id].append(var)
        else:
            def_variables[stmt_id] = list(set(this_def_variables[:]))

        for this_pos in stmt_list_pos[stmt_id]:
            if this_pos[0] in line_def_variables:
                for var in this_def_variables:
                    if var not in line_def_variables[this_pos[0]]:
                        line_def_variables[this_pos[0]].append(var)
            else:
                line_def_variables[this_pos[0]] = this_def_variables[:]

        for this_var in set(this_def_variables):
            if this_var not in var_info:
                var_info[this_var] = [stmt_id]
            else:
                var_info[this_var].append(stmt_id)
        if stmt_id == 0:  # ignore function line
            continue
        this_usesd_variables = []
        find_use_variable(this_trees[stmt_id], this_usesd_variables, lang)
        for this_var in set(this_usesd_variables):
            if this_var in var_info:
                if stmt_id in use_variables:
                    if this_var not in use_variables[stmt_id]:
                        use_variables[stmt_id].append(this_var)
                else:
                    use_variables[stmt_id] = [this_var]
                for var_info_item in var_info[this_var]:
                    def_use_deps.append([stmt_id, var_info_item])
    predecessors = {stmt_id: [] for stmt_id in range(len(stmt_list))}
    successors = {stmt_id: [] for stmt_id in range(len(stmt_list))}
    for dep in def_use_deps:
        if dep[0] not in successors[dep[1]]:
            successors[dep[1]].append(dep[0])
        if dep[1] not in predecessors[dep[0]]:
            predecessors[dep[0]].append(dep[1])
    return predecessors, successors, use_consts, def_variables, use_variables, line_def_variables


# def parse_vari_dep(stmt_list, lines, stmt_list_pos, lang, this_trees):
#     def_use_deps = []
#     var_info = {}
#     use_consts = []
#     for stmt_id, source_stmt in enumerate(stmt_list):
#         this_use_consts = []
#         find_use_consts(this_trees[stmt_id], this_use_consts)
#         use_consts.append(this_use_consts)
#         # print(lines[stmt_list_pos[stmt_id][0][0]])
#         this_def_variables = []
#         find_def_variable(this_trees[stmt_id], this_def_variables, lang)
#         if_def = []
#         if_find_def_variable(this_trees[stmt_id], if_def, lang)
#         for this_var in set(this_def_variables):
#             if this_var not in var_info:
#                 var_info[this_var] = [stmt_id]
#             else:
#                 var_info[this_var].append(stmt_id)
#         if stmt_id == 0:  # ignore function line
#             continue
#         this_usesd_variables = []
#         find_use_variable(this_trees[stmt_id], this_usesd_variables, lang)
#         this_usesd_variables_filt = copy.deepcopy(this_usesd_variables)
#         stmt_text = mytree2text(this_trees[stmt_id], '')
#         if if_def:
#             for item in this_def_variables:
#                 if item in this_usesd_variables_filt:
#                     if lang == 'Python':
#                         if stmt_text.startswith('for') and item == stmt_text[len('for '):stmt_text.index(' in ')]:
#                             continue
#                         else:
#                             this_usesd_variables_filt.remove(item)
#                     else:
#                         this_usesd_variables_filt.remove(item)
#         # print(f'def: {this_def_variables}')
#         # print(f'use: {this_usesd_variables}')
#         # print(f'def: {this_def_variables_filt}')
#         # print(f'use: {this_usesd_variables_filt}')
#         for this_var in set(this_usesd_variables_filt):
#             if this_var in var_info:
#                 if this_var in this_def_variables:
#                     if len(var_info[this_var]) > 1:
#                         def_use_deps.append([stmt_id, var_info[this_var][-2]])
#                     else:
#                         continue
#                 else:
#                     for var_info_item in var_info[this_var]:
#                         def_use_deps.append([stmt_id, var_info_item])
#     predecessors = {stmt_id: [] for stmt_id in range(len(stmt_list))}
#     successors = {stmt_id: [] for stmt_id in range(len(stmt_list))}
#     for dep in def_use_deps:
#         if dep[0] not in successors[dep[1]]:
#             successors[dep[1]].append(dep[0])
#         if dep[1] not in predecessors[dep[0]]:
#             predecessors[dep[0]].append(dep[1])
#     return predecessors, successors, use_consts


def find_use_variable(tree, variables, lang):
    node_types = node_type_transfer(lang, tree.type, tree.text, [])
    if node_types:
        this_type = node_types[0]
        if this_type == 'identifier-0' or tree.text in ['sum', 'count']:
            if type(tree) == tree_sitter.Node:
                if tree.text.decode() not in ['print', 'main', 'System', 'out', 'println', 'cout', 'endl']:
                    variables.append(tree.text.decode())
            else:
                if tree.text not in ['print', 'main', 'System', 'out', 'println', 'cout', 'endl']:
                    variables.append(tree.text)
        for child in tree.children:
            find_use_variable(child, variables, lang)
    else:
        this_type = tree.type
        if this_type == 'identifier':
            if type(tree) == tree_sitter.Node:
                if tree.text.decode() not in ['print', 'main', 'System', 'out', 'println', 'cout', 'endl']:
                    variables.append(tree.text.decode())
            else:
                if tree.text not in ['print', 'main', 'System', 'out', 'println', 'cout', 'endl']:
                    variables.append(tree.text)
        for child in tree.children:
            find_use_variable(child, variables, lang)


def find_use_consts(tree, consts):
    if tree.type in ['integer', 'true', 'false', 'number_literal', 'decimal_integer_literal']:
        if type(tree) == tree_sitter.Node:
            if tree.text.decode() not in consts:
                consts.append(tree.text.decode().lower())
        else:
            if tree.text not in consts:
                consts.append(tree.text.lower())
    for child in tree.children:
        find_use_consts(child, consts)


def find_use_strings(tree, consts):
    if tree.type in ['string_literal', 'char_literal', 'character_literal', 'string']:
        if type(tree) == tree_sitter.Node:
            if tree.text.decode() not in consts:
                consts.append(tree.text.decode().lower())
        else:
            if tree.text not in consts:
                consts.append(tree.text.lower())
    else:
        for child in tree.children:
            find_use_strings(child, consts)


def find_use_types(tree, types):
    if tree.type in ['sized_type_specifier', 'primitive_type']:
        if type(tree) == tree_sitter.Node:
            if tree.text.decode() not in types:
                types.append(tree.text.decode().lower())
        else:
            if tree.text not in types:
                types.append(tree.text.lower())
    else:
        for child in tree.children:
            find_use_types(child, types)


def code_parse(lang, code):
    assert lang in ['C++', 'Python', 'Java']
    if lang == 'C++':
        tree = CPP_parser.parse(bytes(code, "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree, variable_names
    if lang == 'Python':
        tree = Python_parser.parse(bytes(code, "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree, variable_names
    if lang == 'Java':
        tree = Java_parser.parse(bytes(code, "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree, variable_names


def rephrase(code_lines):
    # print('')
    new_code_lines = []
    for line in code_lines:
        if ' [ ] [ ] = new ' in line:
            type_var = [item for item in line.split(' [ ] [ ] = new ')[0].split(' ') if item]
            val = line.split(' [ ] [ ] = new ')[1]
            type = type_var[0]
            var = type_var[1]
            new_line = f'{type} [ ] [ ] {var} = new {val}'
            new_code_lines.append(new_line)
        elif ' [ ] = new ' in line:
            type_var = [item for item in line.split(' [ ] = new ')[0].split(' ') if item]
            val = line.split(' [ ] = new ')[1]
            type = type_var[0]
            var = type_var[1]
            new_line = f'{type} [ ] {var} = new {val}'
            new_code_lines.append(new_line)
        else:
            new_code_lines.append(line)
    return new_code_lines


def code_parse_for_map(lang, code):
    assert lang in ['C++', 'Python', 'Java']
    if lang == 'C++':
        tree = CPP_parser.parse(bytes(''.join(code), "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree, variable_names
    if lang == 'Python':
        tree = Python_parser.parse(bytes(''.join(code), "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree, variable_names
    if lang == 'Java':
        pre_code_lines = copy.deepcopy(code)
        pre_code_lines = rephrase(pre_code_lines)
        pre_code = ''.join(pre_code_lines)
        pre_code = 'public class ClassName{\n' + pre_code + '}\n'
        tree = Java_parser.parse(bytes(pre_code, "utf8"))
        variable_names = []
        find_def_variable(tree.root_node, variable_names, lang)
        variable_names = list(set(variable_names))
        return tree.root_node.children[0].children[3], variable_names


def check_continuous(diff_line_ids):
    if not diff_line_ids:
        return False
    else:
        if_continuous = True
        pre_id = diff_line_ids[0]
        for id in diff_line_ids[1:]:
            if id == pre_id + 1:
                pre_id = id
            else:
                if_continuous = False
                break
        return if_continuous


def delete(lang, code_lines):
    tree, variable_names = code_parse(lang, ''.join(code_lines))
    stmt_lists = []
    if lang == 'Java':
        stmt_lists = traverse_tree(tree.root_node, lang, code_lines, variable_names, only_block=False, exclude_last_child=False, fun_block=0)
    elif lang == 'Python':
        stmt_lists = traverse_tree(tree.root_node.children[0], lang, code_lines, variable_names, only_block=False, exclude_last_child=False, fun_block=0)
    elif lang == 'C++':
        stmt_lists = traverse_tree(tree.root_node.children[0], lang, code_lines, variable_names, only_block=False, exclude_last_child=False, fun_block=0)
    delete_code_dict = {}
    delete_code_list = []
    path2tree = {}
    for stmt_list in stmt_lists:
        this_deleted_code_lines = copy.deepcopy(code_lines)
        for item in stmt_list:
            this_deleted_code_lines = delete_code(this_deleted_code_lines, item[2])
            if item[0] not in path2tree:
                path2tree[item[0]] = [item[1]]
        delete_code_list.append([this_deleted_code_lines, [[this_stmt[0], this_stmt[2], this_stmt[3]] for this_stmt in stmt_list]])
    for i in delete_code_list:
        for j in delete_code_list:
            if i == j:
                continue
            code1 = i[0]
            code2 = j[0]
            stmt1 = i[1]
            stmt2 = j[1]
            assert len(code1) == len(code2)

            more_delete_stmts = [item for item in stmt1 if item not in stmt2]
            less_delete_stmts = [item for item in stmt2 if item not in stmt1]
            if less_delete_stmts or not more_delete_stmts:
                continue
            diff_line_ids = []
            line_id = -1
            for line1, line2 in zip(code1, code2):
                line_id += 1
                if line1 != line2:
                    diff_line_ids.append(line_id)
            if not diff_line_ids:
                continue
            if_continuous = check_continuous(diff_line_ids)
            if not if_continuous:
                continue
            if len(more_delete_stmts) == 1:
                if more_delete_stmts[0][0] not in delete_code_dict:
                    delete_code_dict[more_delete_stmts[0][0]] = [[j[0], i[0], path2tree[more_delete_stmts[0][0]]]]
                else:
                    delete_code_dict[more_delete_stmts[0][0]].append([j[0], i[0], path2tree[more_delete_stmts[0][0]]])
            else:
                first_diff_id = diff_line_ids[0]
                more_delete_stmts_depths = [item[2] for item in more_delete_stmts]
                min_more_delete_stmts_depth = min(more_delete_stmts_depths)
                count_of_min_depth = [item[2] for item in more_delete_stmts if item[2] == min_more_delete_stmts_depth]
                if len(count_of_min_depth) != 1:
                    continue
                min_depth_more_delete_stmt = [item[0] for item in more_delete_stmts if item[2] == min_more_delete_stmts_depth]
                min_depth_more_delete_stmt_pos = [item[1] for item in more_delete_stmts if item[2] == min_more_delete_stmts_depth]
                if min_depth_more_delete_stmt_pos[0][0][0] != first_diff_id:
                    raise Exception('they should be the same!')
                if min_depth_more_delete_stmt[0] not in delete_code_dict:
                    delete_code_dict[min_depth_more_delete_stmt[0]] = [[j[0], i[0], path2tree[min_depth_more_delete_stmt[0]]]]
                else:
                    delete_code_dict[min_depth_more_delete_stmt[0]].append([j[0], i[0], path2tree[min_depth_more_delete_stmt[0]]])
    return delete_code_dict


def if_continue(ids):
    if len(ids) > 1:
        if_cont = True
        pre_id = ids[0]
        for id in ids[1:]:
            if id == pre_id + 1:
                pre_id = id
            else:
                if_cont = False
        return if_cont
    else:
        return True


# def traverse_maps(match_ids):
#     mappings = []
#     for key, val in match_ids.items():
#         if not val:
#             continue
#         if mappings:
#             new_mappings = []
#             for this_v in val:
#                 for mapping in mappings:
#                     this_mapping = copy.deepcopy(mapping)
#                     this_mapping.append([key, this_v])
#                     new_mappings.append(this_mapping)
#             mappings = copy.deepcopy(new_mappings)
#         else:
#             for this_v in val:
#                 mappings.append([[key, this_v]])
#     return mappings


def findsubsets(s, n):
    return list(itertools.combinations(s, n))


def get_sublists(lst):
    subsets = []
    for n in range(0, len(lst)):
        subsets.extend(findsubsets(set(lst), n))
    sublists = []
    for subset in subsets:
        sublist = list(subset)
        sublist.sort()
        if sublist not in sublists:
            sublists.append(sublist)
    sublists = sorted(sublists, key=len, reverse=True)
    return sublists


def verify_maps_step(M, s_ids, mapped_trans_stmts, source_predecessors, source_successors, trans_predecessors, trans_successors, source_use_consts, trans_use_consts, if_reverse=True):
    source_use_consts_set = set()
    for s_id in s_ids:
        for item in source_use_consts[s_id]:
            if item not in source_use_consts_set:
                source_use_consts_set.add(item)
    trans_use_consts_set = set()
    for t_id in mapped_trans_stmts:
        for item in trans_use_consts[t_id]:
            if item not in trans_use_consts_set:
                trans_use_consts_set.add(item)

    s_predecessors = []
    for s_stmt in s_ids:
        for item in source_predecessors[s_stmt]:
            if item not in s_ids:
                s_predecessors.append(item)
    t_predecessors = []
    for t_stmt in mapped_trans_stmts:
        for item in trans_predecessors[t_stmt]:
            if item not in mapped_trans_stmts:
                t_predecessors.append(item)

    s_successors = []
    for s_stmt in s_ids:
        for item in source_successors[s_stmt]:
            if item not in s_ids:
                s_successors.append(item)
    t_successors = []
    for t_stmt in mapped_trans_stmts:
        for item in trans_successors[t_stmt]:
            if item not in mapped_trans_stmts:
                t_successors.append(item)

    if_valid = True

    if not (source_use_consts_set.issubset(trans_use_consts_set) or trans_use_consts_set.issubset(source_use_consts_set)):
        if_valid = False

    for t_pre_id in t_predecessors:
        if not if_reverse:
            t_pre_id_mapped_s_ids = [this_s_id for this_s_id in range(len(source_predecessors)) if M[f'{this_s_id}-{t_pre_id}'] and this_s_id not in s_ids]
        else:
            t_pre_id_mapped_s_ids = [this_s_id for this_s_id in range(len(source_predecessors)) if M[f'{t_pre_id}-{this_s_id}'] and this_s_id not in s_ids]
        if t_pre_id_mapped_s_ids == []:
            continue
        if_mapped = False
        for s_pre_id in s_predecessors:
            if not if_reverse:
                if M[f'{s_pre_id}-{t_pre_id}']:
                    if_mapped = True
            else:
                if M[f'{t_pre_id}-{s_pre_id}']:
                    if_mapped = True
        if not if_mapped:
            if_valid = False
    for t_pre_id in t_successors:
        if not if_reverse:
            t_pre_id_mapped_s_ids = [this_s_id for this_s_id in range(len(source_predecessors)) if M[f'{this_s_id}-{t_pre_id}'] and this_s_id not in s_ids]
        else:
            t_pre_id_mapped_s_ids = [this_s_id for this_s_id in range(len(source_predecessors)) if M[f'{t_pre_id}-{this_s_id}'] and this_s_id not in s_ids]
        if t_pre_id_mapped_s_ids == []:
            continue
        if_mapped = False
        for s_pre_id in s_successors:
            if not if_reverse:
                if M[f'{s_pre_id}-{t_pre_id}']:
                    if_mapped = True
            else:
                if M[f'{t_pre_id}-{s_pre_id}']:
                    if_mapped = True
        if not if_mapped:
            if_valid = False
    return if_valid, t_predecessors, t_successors


def find_closure(M, source_stmts, trans_stmts):
    closures = []
    for s in range(len(source_stmts)):
        S = [s]
        F = []
        while(True):
            ori_S = copy.deepcopy(S)
            ori_F = copy.deepcopy(F)
            for this_s in S:
                for this_f in range(len(trans_stmts)):
                    if M[f'{this_s}-{this_f}'] and this_f not in F:
                        F.append(this_f)
            for this_f in F:
                for this_s in range(len(source_stmts)):
                    if M[f'{this_s}-{this_f}'] and this_s not in S:
                        S.append(this_s)
            if set(S) == set(ori_S) and set(F) == set(ori_F):
                break
        if S and F and [set(S), set(F)] not in closures:
            closures.append([set(S), set(F)])
    return closures


def verify_maps(M, source_stmt_list, trans_stmt_list, source_predecessors, source_successors, trans_predecessors, trans_successors, source_use_consts, trans_use_consts):
    for s_id, s_stmt in enumerate(source_stmt_list):
        mapped_trans_stmts = []
        for t_id in range(len(trans_stmt_list)):
            if M[f'{s_id}-{t_id}']:
                mapped_trans_stmts.append(t_id)
        if len(mapped_trans_stmts) > 1:
            if_valid, _, _ = verify_maps_step(M, [s_id], mapped_trans_stmts, source_predecessors, source_successors, trans_predecessors, trans_successors, source_use_consts, trans_use_consts, if_reverse=False)
            if not if_valid:
                sublists = get_sublists(mapped_trans_stmts)
                pass_subs = []
                for sublist in sublists:
                    this_if_valid, t_predecessors, t_successors = verify_maps_step(M, [s_id], sublist, source_predecessors, source_successors, trans_predecessors, trans_successors, source_use_consts, trans_use_consts, if_reverse=False)
                    if this_if_valid:
                        pass_subs.append([len(t_predecessors)+len(t_successors), sublist])
                max_len = max([pass_sub[0] for pass_sub in pass_subs])
                max_len_subs = [[len(pass_sub[1]), pass_sub[1]] for pass_sub in pass_subs if pass_sub[0] == max_len]
                max_len_subs.sort()
                for pass_sub in max_len_subs:
                    sublist = pass_sub[1]
                    for t_id in mapped_trans_stmts:
                        if t_id not in sublist:
                            M[f'{s_id}-{t_id}'] = False
                    break
            elif not if_continue(mapped_trans_stmts):
                delta_ids = [[abs(item-s_id), item] for item in mapped_trans_stmts]
                delta_ids.sort()
                for t_delta_id in delta_ids[1:]:
                    M[f'{s_id}-{t_delta_id[1]}'] = False
                break
    for t_id, t_stmt in enumerate(trans_stmt_list):
        mapped_source_stmts = []
        for s_id in range(len(source_stmt_list)):
            if M[f'{s_id}-{t_id}']:
                mapped_source_stmts.append(s_id)
        if len(mapped_source_stmts) > 1:
            if_valid, _, _ = verify_maps_step(M, [t_id], mapped_source_stmts, trans_predecessors, trans_successors, source_predecessors, source_successors, trans_use_consts, source_use_consts, if_reverse=True)
            if not if_valid:
                sublists = get_sublists(mapped_source_stmts)
                pass_subs = []
                for sublist in sublists:
                    this_if_valid, s_predecessors, s_successors = verify_maps_step(M, [t_id], sublist, trans_predecessors, trans_successors, source_predecessors, source_successors, trans_use_consts, source_use_consts, if_reverse=True)
                    if this_if_valid:
                        pass_subs.append([len(s_predecessors)+len(s_successors), sublist])
                max_len = max([pass_sub[0] for pass_sub in pass_subs])
                max_len_subs = [[len(pass_sub[1]), pass_sub[1]] for pass_sub in pass_subs if pass_sub[0] == max_len]
                max_len_subs.sort()
                for pass_sub in max_len_subs:
                    sublist = pass_sub[1]
                    for s_id in mapped_source_stmts:
                        if s_id not in sublist:
                            M[f'{s_id}-{t_id}'] = False
                    break
            elif not if_continue(mapped_source_stmts):
                for s_id in mapped_source_stmts[1:]:
                    M[f'{s_id}-{t_id}'] = False
                break
    closures = find_closure(M, source_stmt_list, trans_stmt_list)
    for closure in closures:
        S = list(closure[0])
        F = list(closure[1])
        S.sort()
        F.sort()
        if len(S) <= 1 or len(F) <= 1:
            continue
        if len(S) != len(F):
            min_len = min(len(S), len(F))
            if min_len == len(S):
                subsets = findsubsets(set(F), min_len)
                maps = []
                for subset in subsets:
                    this_map = []
                    this_subset = list(subset)
                    this_subset.sort()
                    for s_id, f_id in zip(S, this_subset):
                        this_map.append([s_id, f_id])
                    this_score = 0
                    for pair in this_map:
                        this_score += abs(pair[0]-pair[1])
                    maps.append([this_score, this_map])
                maps.sort()
                select_map = maps[0]
                for s_idx, s_id in enumerate(S):
                    for f_idx, f_id in enumerate(F):
                        if [s_id, f_id] not in select_map:
                            M[f'{s_id}-{f_id}'] = False
        if len(S) == len(F):
            if_S_same_AST = True
            for s_id1 in S:
                for s_id2 in S:
                    if source_stmt_list[s_id1] != source_stmt_list[s_id2]:
                        if_S_same_AST = False
            if_F_same_AST = True
            for s_id1 in S:
                for s_id2 in S:
                    if source_stmt_list[s_id1] != source_stmt_list[s_id2]:
                        if_F_same_AST = False
            if if_S_same_AST and if_F_same_AST:
                for s_idx, s_id in enumerate(S):
                    for f_idx, f_id in enumerate(F):
                        if s_idx != f_idx:
                            M[f'{s_id}-{f_id}'] = False
    return M


def find_seq(unmapped_s_ids):
    unmapped_s_id_seqs = []
    seq = []
    for id, this_id in enumerate(unmapped_s_ids):
        if not seq:
            seq.append(this_id)
        else:
            if (seq[-1] + 1) == this_id:
                seq.append(this_id)
            else:
                unmapped_s_id_seqs.append(seq)
                seq = [this_id]
    if seq:
        unmapped_s_id_seqs.append(seq)
    return unmapped_s_id_seqs


def extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees):
    for k, v in extend_new_updated_M.items():
        if v:
            ids = k.split('-')
            s_id = int(ids[0])
            t_id = int(ids[1])
            if s_id in unmapped_s_id_seq:
                unmapped_s_id_seq.remove(s_id)
            if t_id in unmapped_t_id_seq:
                unmapped_t_id_seq.remove(t_id)
    sim_scores = []
    pass_s_ids = []
    pass_t_ids = []
    for s_id in unmapped_s_id_seq:
        for t_id in unmapped_t_id_seq:
            s_def_varis = source_stmt_def_variables[s_id] if s_id in source_stmt_def_variables else []
            s_use_varis = source_stmt_use_variables[s_id]if s_id in source_stmt_use_variables else []
            t_def_varis = trans_stmt_def_variables[t_id] if t_id in trans_stmt_def_variables else []
            t_use_varis = trans_stmt_use_variables[t_id] if t_id in trans_stmt_use_variables else []
            # this_score = 0
            # same_use_varis = [var for var in s_use_varis if var in t_use_varis]
            # diff_use_varis1 = [var for var in s_use_varis if var not in t_use_varis]
            # diff_use_varis2 = [var for var in t_use_varis if var not in s_use_varis]
            # this_score = len(same_use_varis) - len(diff_use_varis1) - len(diff_use_varis2)
            if (s_def_varis == t_def_varis or s_use_varis == t_use_varis) and s_id not in pass_s_ids and t_id not in pass_t_ids:
                extend_new_updated_M[f'{s_id}-{t_id}'] = True
                pass_s_ids.append(s_id)
                pass_t_ids.append(t_id)
            # sim_scores.append([this_score, [s_id, t_id]])
    # sim_scores.sort(reverse=True)
    # for score_pair in sim_scores:
    #     score = score_pair[0]
    #     pair = score_pair[1]
    #     if score and extend_new_updated_M[f'{pair[0]}-{pair[1]}'] == False and pair[0] not in pass_s_ids and pair[1] not in pass_t_ids:
    #         text_s = this_source_trees[pair[0]].text
    #         text_t = this_trans_trees[pair[1]].text
    #         distance = Levenshtein.distance(text_s, text_t) / max(len(text_s), len(text_t))
    #         if not distance < 0.9:
    #             continue
    #         extend_new_updated_M[f'{pair[0]}-{pair[1]}'] = True
    #         pass_s_ids.append(pair[0])
    #         pass_t_ids.append(pair[1])
    return extend_new_updated_M


def extend_by_sim(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, this_source_trees, this_trans_trees, source_stmt_list, trans_stmt_list):

    for k, v in extend_new_updated_M.items():
        if v:
            ids = k.split('-')
            s_id = int(ids[0])
            t_id = int(ids[1])
            if s_id in unmapped_s_id_seq:
                unmapped_s_id_seq.remove(s_id)
            if t_id in unmapped_t_id_seq:
                unmapped_t_id_seq.remove(t_id)
    pass_s_ids = []
    pass_t_ids = []
    s_if_stmts = []
    for id in unmapped_s_id_seq:
        if source_stmt_list[id].startswith('if_'):
            s_if_stmts.append(id)
    t_if_stmts = []
    for id in unmapped_t_id_seq:
        if trans_stmt_list[id].startswith('if_'):
            t_if_stmts.append(id)
    if len(s_if_stmts) == len(t_if_stmts):
        for s_id, t_id in zip(s_if_stmts, t_if_stmts):
            extend_new_updated_M[f'{s_id}-{t_id}'] = True
            pass_s_ids.append(s_id)
            pass_t_ids.append(t_id)
    s_for_stmts = []
    for id in unmapped_s_id_seq:
        if source_stmt_list[id].startswith('for_'):
            s_for_stmts.append(id)
    t_for_stmts = []
    for id in unmapped_t_id_seq:
        if trans_stmt_list[id].startswith('for_'):
            t_for_stmts.append(id)
    if len(s_for_stmts) == len(t_for_stmts):
        for s_id, t_id in zip(s_for_stmts, t_for_stmts):
            extend_new_updated_M[f'{s_id}-{t_id}'] = True
            pass_s_ids.append(s_id)
            pass_t_ids.append(t_id)

    sim_scores = []
    for s_id in unmapped_s_id_seq:
        for t_id in unmapped_t_id_seq:
            text_s = this_source_trees[s_id].text
            text_t = this_trans_trees[t_id].text
            distance = Levenshtein.distance(text_s, text_t)/max(len(text_s), len(text_t))
            sim_scores.append([distance, abs(s_id-t_id), [s_id, t_id]])
    sim_scores.sort()
    threshold = 0.9
    if len(unmapped_s_id_seq) != len(unmapped_t_id_seq) and (len(unmapped_s_id_seq) == 1 or len(unmapped_t_id_seq) == 1):
        threshold = 0.6
    for score_pair in sim_scores:
        score = score_pair[0]
        pair = score_pair[2]
        if score < threshold and extend_new_updated_M[f'{pair[0]}-{pair[1]}'] == False and pair[0] not in pass_s_ids and pair[1] not in pass_t_ids:
            extend_new_updated_M[f'{pair[0]}-{pair[1]}'] = True
            pass_s_ids.append(pair[0])
            pass_t_ids.append(pair[1])
    return extend_new_updated_M


# def extend_maps(new_updated_M, this_source_trees, this_trans_trees, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables):
#     extend_new_updated_M = copy.deepcopy(new_updated_M)
#     unmapped_s_ids = []
#     for s_stmt_id, s_stmt in enumerate(this_source_trees):
#         mapped_stmts = []
#         for t_stmt_id, t_stmt in enumerate(this_trans_trees):
#             if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
#                 mapped_stmts.append(t_stmt_id)
#         if not mapped_stmts:
#             unmapped_s_ids.append(s_stmt_id)
#     unmapped_t_ids = []
#     for t_stmt_id, t_stmt in enumerate(this_trans_trees):
#         mapped_stmts = []
#         for s_stmt_id, s_stmt in enumerate(this_source_trees):
#             if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
#                 mapped_stmts.append(s_stmt_id)
#         if not mapped_stmts:
#             unmapped_t_ids.append(t_stmt_id)
#
#     unmapped_s_id_seqs = find_seq(unmapped_s_ids)
#     unmapped_t_id_seqs = find_seq(unmapped_t_ids)
#
#     passed_s_seq_ids = []
#     passed_t_seq_ids = []
#
#     for s_seq_id, unmapped_s_id_seq in enumerate(unmapped_s_id_seqs):
#         for t_seq_id, unmapped_t_id_seq in enumerate(unmapped_t_id_seqs):
#             if s_seq_id not in passed_s_seq_ids and t_seq_id not in passed_t_seq_ids:
#                 s_pre = unmapped_s_id_seq[0]-1
#                 s_fol = unmapped_s_id_seq[-1]+1
#                 t_pre = unmapped_t_id_seq[0]-1
#                 t_fol = unmapped_t_id_seq[-1]+1
#                 if new_updated_M[f'{s_pre}-{t_pre}'] and s_fol >= len(this_source_trees) and t_fol >= len(this_trans_trees):
#                     extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
#                 elif s_fol < len(this_source_trees) and t_fol < len(this_trans_trees) and new_updated_M[f'{s_pre}-{t_pre}'] and new_updated_M[f'{s_fol}-{t_fol}']:
#                     extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
#
#     for s_seq_id, unmapped_s_id_seq in enumerate(unmapped_s_id_seqs):
#         for t_seq_id, unmapped_t_id_seq in enumerate(unmapped_t_id_seqs):
#             if s_seq_id not in passed_s_seq_ids and t_seq_id not in passed_t_seq_ids:
#                 s_pre = unmapped_s_id_seq[0]-1
#                 s_fol = unmapped_s_id_seq[-1]+1
#                 t_pre = unmapped_t_id_seq[0]-1
#                 t_fol = unmapped_t_id_seq[-1]+1
#                 if new_updated_M[f'{s_pre}-{t_pre}'] and s_fol >= len(this_source_trees) and t_fol >= len(this_trans_trees):
#                     extend_new_updated_M = extend_by_sim(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, this_source_trees, this_trans_trees)
#                     passed_s_seq_ids.append(s_seq_id)
#                     passed_t_seq_ids.append(t_seq_id)
#                 elif s_fol < len(this_source_trees) and t_fol < len(this_trans_trees) and new_updated_M[f'{s_pre}-{t_pre}'] and new_updated_M[f'{s_fol}-{t_fol}']:
#                     extend_new_updated_M = extend_by_sim(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, this_source_trees, this_trans_trees)
#                     passed_s_seq_ids.append(s_seq_id)
#                     passed_t_seq_ids.append(t_seq_id)
#     return extend_new_updated_M


# def extend_maps(new_updated_M, this_source_trees, this_trans_trees, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables):
#     extend_new_updated_M = copy.deepcopy(new_updated_M)
#     unmapped_s_ids = []
#     for s_stmt_id, s_stmt in enumerate(this_source_trees):
#         mapped_stmts = []
#         for t_stmt_id, t_stmt in enumerate(this_trans_trees):
#             if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
#                 mapped_stmts.append(t_stmt_id)
#         if not mapped_stmts:
#             unmapped_s_ids.append(s_stmt_id)
#     unmapped_t_ids = []
#     for t_stmt_id, t_stmt in enumerate(this_trans_trees):
#         mapped_stmts = []
#         for s_stmt_id, s_stmt in enumerate(this_source_trees):
#             if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
#                 mapped_stmts.append(s_stmt_id)
#         if not mapped_stmts:
#             unmapped_t_ids.append(t_stmt_id)
#
#     unmapped_s_id_seqs = find_seq(unmapped_s_ids)
#     unmapped_t_id_seqs = find_seq(unmapped_t_ids)
#
#     passed_s_seq_ids = []
#     passed_t_seq_ids = []
#
#     for s_seq_id, unmapped_s_id_seq in enumerate(unmapped_s_id_seqs):
#         for t_seq_id, unmapped_t_id_seq in enumerate(unmapped_t_id_seqs):
#             if s_seq_id not in passed_s_seq_ids and t_seq_id not in passed_t_seq_ids:
#                 s_pre = unmapped_s_id_seq[0]-1
#                 s_fol = unmapped_s_id_seq[-1]+1
#                 t_pre = unmapped_t_id_seq[0]-1
#                 t_fol = unmapped_t_id_seq[-1]+1
#                 if new_updated_M[f'{s_pre}-{t_pre}'] and s_fol >= len(this_source_trees) and t_fol >= len(this_trans_trees):
#                     extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
#                 elif s_fol < len(this_source_trees) and t_fol < len(this_trans_trees) and new_updated_M[f'{s_pre}-{t_pre}'] and new_updated_M[f'{s_fol}-{t_fol}']:
#                     extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
#     return extend_new_updated_M


def extend_maps(new_updated_M, this_source_trees, this_trans_trees, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, source_stmt_list, trans_stmt_list):
    extend_new_updated_M = copy.deepcopy(new_updated_M)
    unmapped_s_ids = []
    for s_stmt_id, s_stmt in enumerate(this_source_trees):
        mapped_stmts = []
        for t_stmt_id, t_stmt in enumerate(this_trans_trees):
            if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
                mapped_stmts.append(t_stmt_id)
        if not mapped_stmts:
            unmapped_s_ids.append(s_stmt_id)
    unmapped_t_ids = []
    for t_stmt_id, t_stmt in enumerate(this_trans_trees):
        mapped_stmts = []
        for s_stmt_id, s_stmt in enumerate(this_source_trees):
            if new_updated_M[f'{s_stmt_id}-{t_stmt_id}']:
                mapped_stmts.append(s_stmt_id)
        if not mapped_stmts:
            unmapped_t_ids.append(t_stmt_id)

    unmapped_s_id_seqs = find_seq(unmapped_s_ids)
    unmapped_t_id_seqs = find_seq(unmapped_t_ids)

    passed_s_seq_ids = []
    passed_t_seq_ids = []
    for s_seq_id, unmapped_s_id_seq in enumerate(unmapped_s_id_seqs):
        for t_seq_id, unmapped_t_id_seq in enumerate(unmapped_t_id_seqs):
            if s_seq_id not in passed_s_seq_ids and t_seq_id not in passed_t_seq_ids:
                s_pre = unmapped_s_id_seq[0]-1
                s_fol = unmapped_s_id_seq[-1]+1
                t_pre = unmapped_t_id_seq[0]-1
                t_fol = unmapped_t_id_seq[-1]+1
                if new_updated_M[f'{s_pre}-{t_pre}'] and s_fol >= len(this_source_trees) and t_fol >= len(this_trans_trees):
                    extend_new_updated_M = extend_by_sim(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, this_source_trees, this_trans_trees, source_stmt_list, trans_stmt_list)
                    passed_s_seq_ids.append(s_seq_id)
                    passed_t_seq_ids.append(t_seq_id)
                elif s_fol < len(this_source_trees) and t_fol < len(this_trans_trees) and new_updated_M[f'{s_pre}-{t_pre}'] and new_updated_M[f'{s_fol}-{t_fol}']:
                    extend_new_updated_M = extend_by_sim(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, this_source_trees, this_trans_trees, source_stmt_list, trans_stmt_list)
                    passed_s_seq_ids.append(s_seq_id)
                    passed_t_seq_ids.append(t_seq_id)

    passed_s_seq_ids = []
    passed_t_seq_ids = []

    for s_seq_id, unmapped_s_id_seq in enumerate(unmapped_s_id_seqs):
        for t_seq_id, unmapped_t_id_seq in enumerate(unmapped_t_id_seqs):
            if s_seq_id not in passed_s_seq_ids and t_seq_id not in passed_t_seq_ids:
                s_pre = unmapped_s_id_seq[0]-1
                s_fol = unmapped_s_id_seq[-1]+1
                t_pre = unmapped_t_id_seq[0]-1
                t_fol = unmapped_t_id_seq[-1]+1
                if new_updated_M[f'{s_pre}-{t_pre}'] and s_fol >= len(this_source_trees) and t_fol >= len(this_trans_trees):
                    extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
                    passed_s_seq_ids.append(s_seq_id)
                    passed_t_seq_ids.append(t_seq_id)
                elif s_fol < len(this_source_trees) and t_fol < len(this_trans_trees) and new_updated_M[f'{s_pre}-{t_pre}'] and new_updated_M[f'{s_fol}-{t_fol}']:
                    extend_new_updated_M = extend_by_variable(extend_new_updated_M, unmapped_s_id_seq, unmapped_t_id_seq, source_stmt_def_variables, source_stmt_use_variables, trans_stmt_def_variables, trans_stmt_use_variables, this_source_trees, this_trans_trees)
                    passed_s_seq_ids.append(s_seq_id)
                    passed_t_seq_ids.append(t_seq_id)
    return extend_new_updated_M


def check_overflow(var_val1_val2, pass_vars):
    if var_val1_val2[1] not in pass_vars:
        return False
    if var_val1_val2[2].count('-') != var_val1_val2[3].count('-'):
        return True
    else:
        return False

def check_float(var_val1_val2, pass_vars):
    if var_val1_val2[1] not in pass_vars:
        return False
    if var_val1_val2[2].count('.') != var_val1_val2[3].count('.'):
        return True
    else:
        return False


def line2stmt(stmt_list_pos):
    line2stmt = {}
    for stmt_id, stmt_pos in enumerate(stmt_list_pos):
        for pos in stmt_pos:
            if pos[0] not in line2stmt:
                line2stmt[pos[0]] = [stmt_id]
            elif stmt_id not in line2stmt[pos[0]]:
                line2stmt[pos[0]].append(stmt_id)
    return line2stmt
'if_statement-0||||if-0||||comparison_operator-0||||identifier-0||||<-0||||integer-0||||:-0||||block-0'
'boolean_operator-0||||comparison_operator-0||||identifier-0||||>=-0||||integer-0||||and-0||||comparison_operator-0||||identifier-0||||<-0||||integer-0'
def rephrase_stmt_trees(lang, source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos, code_lines):
    if lang == 'Python':
        id = -1
        for source_stmt, source_stmt_depth, source_tree, source_stmt_pos in zip(source_stmt_list, source_stmt_list_depth, this_source_trees, source_stmt_list_pos):
            id += 1
            if source_stmt.startswith('if_statement-0') and (source_stmt.endswith('||||elif_clause-0') or source_stmt.endswith('||||else_clause-0')):
                if source_stmt.endswith('||||elif_clause-0'):
                    source_stmt = source_stmt[:-len('||||elif_clause-0')]
                elif source_stmt.endswith('||||else_clause-0'):
                    source_stmt = source_stmt[:-len('||||else_clause-0')]
                source_tree.children = source_tree.children[:-1]
                pos_line_ids = []
                for item in source_stmt_pos:
                    if item[0] not in pos_line_ids:
                        pos_line_ids.append(item[0])
                new_source_stmt_pos = []
                if len(pos_line_ids) > 1:
                    max_line_id = max(pos_line_ids)
                    new_source_stmt_pos = [item for item in source_stmt_pos if item[0] != max_line_id]
                else:
                    new_source_stmt_pos = source_stmt_pos[:]
                source_stmt_list[id] = source_stmt
                this_source_trees[id] = source_tree
                source_stmt_list_pos[id] = new_source_stmt_pos[:]
                if source_stmt not in this_source_path2tree:
                    this_source_path2tree[source_stmt] = source_tree
            elif (source_stmt.startswith('boolean_operator-0') or source_stmt.startswith('comparison_operator-0')) and code_lines[source_stmt_pos[0][0]].strip().startswith('elif'):
                new_stmt_tree =MyTree('if_statement', [MyTree('if', [], False, 'if', source_tree.line_id, source_tree.variable_names),
                                                       copy.deepcopy(source_tree),
                                                       MyTree(':', [], False, ':', source_tree.line_id, source_tree.variable_names),
                                                       MyTree('block', [], True, '', source_tree.line_id+1, source_tree.variable_names)],
                                      True, 'if '+source_tree.text+' :\n', source_tree.line_id, source_tree.variable_names)
                source_stmt = f'if_statement-0||||if-0||||{source_stmt}||||:-0||||block-0'
                line_id = source_stmt_pos[0][0]
                idx = code_lines[line_id].index('elif')
                for this_id, ch in enumerate(code_lines[line_id][idx+2:]):
                    if ch == '\n':
                        break
                    if [line_id, idx+2+this_id] not in source_stmt_pos:
                        source_stmt_pos.append([line_id, idx+2+this_id])
                source_stmt_pos.sort()
                source_stmt_list[id] = source_stmt
                this_source_trees[id] = new_stmt_tree
                source_stmt_list_pos[id] = source_stmt_pos[:]
                if source_stmt not in this_source_path2tree:
                    this_source_path2tree[source_stmt] = new_stmt_tree
    if lang == 'C++':
        id = -1
        for source_stmt, source_stmt_depth, source_tree, source_stmt_pos in zip(source_stmt_list, source_stmt_list_depth, this_source_trees, source_stmt_list_pos):
            id += 1
            if source_stmt.startswith('if_statement-0') and source_stmt.endswith('||||else-0'):
                source_stmt = source_stmt[:-len('||||else-0')]
                source_tree.children = source_tree.children[:-1]
                pos_line_ids = []
                for item in source_stmt_pos:
                    if item[0] not in pos_line_ids:
                        pos_line_ids.append(item[0])
                new_source_stmt_pos = []
                if len(pos_line_ids) > 1:
                    max_line_id = max(pos_line_ids)
                    new_source_stmt_pos = [item for item in source_stmt_pos if item[0] != max_line_id]
                else:
                    new_source_stmt_pos = source_stmt_pos[:]
                source_stmt_list[id] = source_stmt
                this_source_trees[id] = source_tree
                source_stmt_list_pos[id] = new_source_stmt_pos[:]
                if source_stmt not in this_source_path2tree:
                    this_source_path2tree[source_stmt] = source_tree
    if lang == 'Java':
        id = -1
        for source_stmt, source_stmt_depth, source_tree, source_stmt_pos in zip(source_stmt_list, source_stmt_list_depth, this_source_trees, source_stmt_list_pos):
            id += 1
            if source_stmt.startswith('if_statement-0') and source_stmt.endswith('||||else-0'):
                source_stmt = source_stmt[:-len('||||else-0')]
                source_tree.children = source_tree.children[:-1]
                pos_line_ids = []
                for item in source_stmt_pos:
                    if item[0] not in pos_line_ids:
                        pos_line_ids.append(item[0])
                new_source_stmt_pos = []
                if len(pos_line_ids) > 1:
                    max_line_id = max(pos_line_ids)
                    new_source_stmt_pos = [item for item in source_stmt_pos if item[0] != max_line_id]
                else:
                    new_source_stmt_pos = source_stmt_pos[:]
                source_stmt_list[id] = source_stmt
                this_source_trees[id] = source_tree
                source_stmt_list_pos[id] = new_source_stmt_pos[:]
                if source_stmt not in this_source_path2tree:
                    this_source_path2tree[source_stmt] = source_tree
    return source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos

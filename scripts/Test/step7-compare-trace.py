from utils import *
import argparse
import ast
import copy
import argparse
import os
import pexpect
import re
import shutil
import time
from subprocess import Popen, PIPE
from tqdm import tqdm
import string

numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

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


def rewrite_script(source_script_for_trace_file, same_ids, lang):
    test_lines = open(source_script_for_trace_file).readlines()
    first_diff = -1
    for i in range(10):
        if i not in same_ids:
            first_diff = i
            break
    if first_diff != -1:
        same_ids = [i for i in range(10) if i != first_diff]
    if lang == 'C++':
        if same_ids:
            if_condition = f'i == {same_ids[0]}'
            for i in same_ids[1:]:
                if_condition = if_condition + f' || i == {i}'
        else:
            if_condition = ''

        new_target_code = []
        if_in_main = False
        for test_line in test_lines:
            if 'OUTPUT-OF-' in test_line or 'Pass_test_id-' in test_line:
                continue
            if 'main(' in test_line:
                if_in_main = True
            if test_line == '    {\n' and if_in_main:
                new_target_code.append(test_line)
                if same_ids:
                    new_target_code.append('        if(' + if_condition + ') continue;\n')
            else:
                new_target_code.append(test_line)
        return new_target_code
    elif lang == 'Java':
        if same_ids:
            if_condition = f'i == {same_ids[0]}'
            for i in same_ids[1:]:
                if_condition = if_condition + f' || i == {i}'
        else:
            if_condition = ''

        new_source_code = []
        if_in_main = False
        for test_line in test_lines:
            if 'OUTPUT-OF-' in test_line or 'Pass_test_id-' in test_line:
                continue
            if 'main(' in test_line:
                if_in_main = True
            if test_line == '    {\n' and if_in_main:
                new_source_code.append(test_line)
                if same_ids:
                    new_source_code.append('        if(' + if_condition + ') continue;\n')
            else:
                new_source_code.append(test_line)
        return new_source_code
    elif lang == 'Python':
        if same_ids:
            if_condition = f'i == {same_ids[0]}'
            for i in same_ids[1:]:
                if_condition = if_condition + f' or i == {i}'
        else:
            if_condition = ''

        new_source_code = []
        if_in_main = False
        for test_line in test_lines:
            if 'OUTPUT-OF-' in test_line or 'Pass_test_id-' in test_line:
                continue
            if "if __name__ == '__main__':" in test_line:
                if_in_main = True
            if test_line.startswith('    for i, ') and if_in_main:
                new_source_code.append(test_line)
                if same_ids:
                    new_source_code.append('        if ' + if_condition + ': continue\n')
            else:
                new_source_code.append(test_line)
        return new_source_code


def compare_value_for_fix(s_val, t_val):
    if s_val == t_val:
        return True
    else:
        if s_val in ['False'] and t_val in ['false']:
            return True
        if s_val in ['[]', '""', "''", '{}'] and t_val in ['[]', '""', "''", '{}']:
                return True
        if s_val.startswith("['") and s_val.endswith("']") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace("', '", '')
            s_val_str = s_val_str.replace("['", '')
            s_val_str = s_val_str.replace("']", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("{'") and s_val.endswith("'}") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace("', '", '')
            s_val_str = s_val_str.replace("{'", '')
            s_val_str = s_val_str.replace("'}", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("[") and s_val.endswith("]") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace(", ", '')
            s_val_str = s_val_str.replace("[", '')
            s_val_str = s_val_str.replace("]", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if s_val.startswith("{") and s_val.endswith("}") and t_val.startswith('"') and t_val.endswith('"'):
            s_val_str = s_val.replace(", ", '')
            s_val_str = s_val_str.replace("{", '')
            s_val_str = s_val_str.replace("}", '')
            t_val_str = t_val.replace('"', '')
            if s_val_str == t_val_str:
                return True
        if '(int *)' in s_val or '(int *)' in t_val:
            return True
        if '(int &)' in s_val or '(int &)' in t_val:
            return True
        if s_val in ['False'] and t_val in ['false']:
            return True
        if s_val in ['True'] and t_val in ['true']:
            return True
        if s_val in ['False'] and t_val in ['0']:
            return True
        if s_val in ['True'] and t_val in ['1']:
            return True
        if s_val in ['false'] and t_val in ['0']:
            return True
        if s_val in ['true'] and t_val in ['1']:
            return True
        if s_val in ['{}', '[]'] and t_val in ['{}', '[]']:
            return True
        if s_val in ['None', '-1'] and t_val in ['None', '-1']:
            return True
        if '\'' in s_val:
            s_val = s_val.replace('\'', '')
        if '"' in s_val:
            s_val = s_val.replace('"', '')
        if '\'' in t_val:
            t_val = t_val.replace('\'', '')
        if '"' in t_val:
            t_val = t_val.replace('"', '')
        if s_val == t_val:
            return True
        if '.0' in s_val and '.0' not in t_val:
            this_s_val = copy.deepcopy(s_val)
            this_s_val = this_s_val.replace('.0', '')
            if this_s_val == t_val:
                return True
        if '.0' in t_val and '.0' not in s_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace('.0', '')
            if this_t_val == s_val:
                return True
        if '.' in s_val and 'e' in s_val and '.' in t_val and 'e' in t_val:
            if s_val[0] == t_val[0]:
                return True
        if '.' in s_val and '.' in t_val:
            this_s_val = ast.literal_eval(s_val)
            this_t_val = ast.literal_eval(t_val)
            if isinstance(this_s_val, float) and isinstance(this_t_val, float) and round(this_s_val, 2) == round(this_t_val, 2):
                return True
        if s_val in ['{}', '[]'] and t_val in ['{}', '[]']:
            return True
        if '[' in s_val and '{' in t_val:
            this_t_val = t_val.replace('{', '[')
            this_t_val = this_t_val.replace('}', ']')
            if s_val == this_t_val:
                return True
        if '{' in s_val and '[' in t_val:
            this_s_val = s_val.replace('{', '[')
            this_s_val = this_s_val.replace('}', ']')
            if t_val == this_s_val:
                return True
        if s_val.startswith('{') and ': ' in s_val and t_val.startswith('[[') and ' = ' in t_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace(', [', ', ')
            this_t_val = this_t_val.replace('] = ', ': ')
            this_t_val = this_t_val.replace(']', '}')
            this_t_val = this_t_val.replace('[', '{')
            this_t_val = this_t_val.replace('{{', '{')
            try:
                this_s_val = ast.literal_eval(s_val)
                this_t_val = ast.literal_eval(this_t_val)
                if this_s_val == this_t_val:
                    return True
            except:
                return False
        if s_val.startswith('[') and '[[' not in s_val and t_val.startswith('[[') and ' = ' in t_val:
            this_t_val = copy.deepcopy(t_val)
            this_t_val = this_t_val.replace(', [', ', ')
            this_t_val = this_t_val.replace('] = ', ': ')
            this_t_val = this_t_val.replace('[[', '{')
            this_t_val = this_t_val.replace(']', '}')
            this_s_val = copy.deepcopy(s_val)
            this_s_val = this_s_val.replace('[', '{')
            this_s_val = this_s_val.replace(']', '}')
            try:
                this_s_val = ast.literal_eval(this_s_val)
                this_t_val = ast.literal_eval(this_t_val)
                this_t_val = set([v for k, v in this_t_val.items()])
                if this_s_val == this_t_val:
                    return True
            except:
                return False
        return False


def check_item_len(val, lang):
    if lang == 'C++':
        items = val[1:-1].split(', ')
        if_1 = True
        new_val = '"'
        for item in items:
            this_items = item.split(' ')
            if len(this_items) == 2 and this_items[0].isdigit() and len(this_items[1]) == 3 and this_items[1][0] == "'" and this_items[1][-1] == "'":
                new_val += this_items[1][1]
                continue
            else:
                if_1 = False
        new_val += '"'
        return if_1, new_val
    if lang == 'Java':
        items = val[1:-1].split(', ')
        if_1 = True
        new_val = '"'
        for item in items:
            if len(item) == 1 and item not in numbers:
                new_val += item
                continue
            else:
                if_1 = False
        new_val += '"'
        return if_1, new_val
    if lang == 'Python':
        items = val[1:-1].split(', ')
        if_1 = True
        new_val = '"'
        for item in items:
            if len(item) == 3 and item[0] in ["'", '"'] and item[2] in ["'", '"']:
                new_val += item[1]
                continue
            else:
                if_1 = False
        new_val += '"'
        return if_1, new_val


def change(info, lang):
    items = info.split('=')
    var = items[0].strip()
    val = '='.join(items[1:]).strip()
    new_val = ''
    if len(items) == 2:
        if val.endswith('.0') and '[' not in val and ']' not in val and '{' not in val and '}' not in val and ',' not in val:
            new_val = val[:-2]
        elif '.' in val and val.count('.') == 1 and '[' not in val and ']' not in val and '{' not in val and '}' not in val and ',' not in val and '\\' not in val:
            new_val = str(round(float(val), 3))
        elif val == 'True':
            new_val = 'true'
        elif val == 'False':
            new_val = 'false'
        elif 'std::set with 0 elements' in val:
            new_val = val.replace('std::set with 0 elements', 'set()')
        elif 'std::priority_queue wrapping: [' in val:
            new_val = val[len('std::priority_queue wrapping: '):]
        elif 'std::' in items[1]:
            if 'std::map' in items[1] or '_map ' in items[1]:
                new_val = '{}'
            else:
                new_val = '[]'
        elif val.count('[') == 1 and val.count(']') == 1 and val[0] == '[' and val[-1] == ']' and check_item_len(val, lang)[0]:
            _, new_val = check_item_len(val, lang)
        else:
            new_val = val
        if lang == 'C++':
            if ', <incomplete' in new_val:
                new_val = new_val[:new_val.index(', <incomplete')]
            if ' = <incomplete sequence ' in new_val and new_val[-1] == '>':
                new_val = new_val.replace(' = <incomplete sequence ', ' = \'')
                new_val = new_val[:-1] + '\''
            if new_val.startswith('<error') or new_val.startswith('<incomplete') or new_val.startswith(
                    'std::map'):
                new_val = ''
            else:
                if new_val.startswith('[') and '<repeats' in new_val:
                    new_val = replace_repeat(new_val)
                elif new_val.startswith('\'') and new_val.endswith('times>'):
                    new_val = replace_repeat_string(new_val)
                this_match = re.search(r"\d+ ('\d+')", new_val)
                if this_match and this_match.group() == new_val:
                    this_match_str = this_match.group(1)
                    new_val = this_match_str
                    new_val = new_val.replace("'", '"')
                this_match = re.findall(r"\d+ '\S+'", new_val)
                if this_match:
                    for this_this_match in this_match:
                        new_val = new_val.replace(this_this_match, this_this_match.split(' ')[1])
            if '[ ' in new_val:
                new_val = new_val.replace('[ ', '[')
            if 'set()' in new_val:
                new_val = new_val.replace('set()', '[]')
        elif lang == 'Java':
            this_match = re.search(r'\[[{, ]+\]', val)
            if this_match and this_match.group() == val:
                new_val = ''
            elif '空值' in new_val:
                new_val = new_val.replace('空值', '\"\"')
        elif lang == 'Python':
            if 'False' in new_val:
                new_val = new_val.replace('False', 'false')
            if 'True' in new_val:
                new_val = new_val.replace('True', 'true')
            if 'set()' in new_val:
                new_val = new_val.replace('set()', '[]')
            if new_val.startswith('{') and new_val.endswith('}') and ':' not in new_val:
                new_val = new_val.replace('{', '[')
                new_val = new_val.replace('}', ']')
            if new_val.startswith('{') and new_val.endswith('}') and ':' in new_val:
                this_val_str_list = new_val[1:-1].split(', ')
                this_val_str_list.sort()
                new_val = '{' + ', '.join(this_val_str_list) + '}'
    elif len(items) > 2:
        if lang == 'C++':
            new_val = '='.join(items[1:])
            this_match = re.findall(r"std::[^\[\]\{\}]+ = ", new_val)
            if this_match:
                for this_this_match in this_match:
                    if this_this_match in new_val:
                        new_val = new_val.replace(this_this_match, '')
            new_val = new_val.strip()
            if '[ [' in new_val:
                new_val = new_val.replace('[ [', '[[')
            if new_val.endswith(']]') and not new_val.startswith('[['):
                new_val = '[' + new_val
            if '[ ' in new_val:
                new_val = new_val.replace('[ ', '[')
            if 'std::map' in '='.join(items[1:]):
                new_val = new_val.replace('] = ', ': ')
                new_val = new_val.replace('[', '')
                new_val = new_val.replace(']', '')
                new_val = '{' + new_val.strip() + '}'
    if new_val:
        new_val = var + ' = ' + new_val.strip()
        return new_val.strip()
    else:
        return ''


def raise_exception_cpp(info, file_name):
    if not info.endswith('(gdb) ') and not info.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
        raise Exception(f'Not ends with (gdb) !---> {file_name}')


def raise_exception_java(info, file_name):
    if not info.endswith('main[1] '):
        raise Exception(f'Not ends with main[1] !---> {file_name}')


def raise_exception_python(info, file_name):
    if not info.endswith('(Pdb) '):
        raise Exception(f'Not ends with (Pdb) !---> {file_name}')


def find_line_id_cpp(txt):
    x = re.search('\r\n(\d+)\t', txt)
    if x:
        return int(x.group(1))
    else:
        raise Exception('no line id')


def find_line_id_java(txt):
    x = re.search('行=(\d+)', txt)
    if x:
        return x.group(1)
    else:
        raise Exception('no line id')


def find_line_id_python(txt):
    x = re.search('.py\((\d+)\)', txt)
    if x:
        return x.group(1)
    else:
        raise Exception('no line id')


def find_values_cpp_singlevari(txt):
    txt = txt.replace('\r\n', '')
    txt = txt.replace(',   ', ', ')
    if not ('*' in txt and '@' in txt and txt.strip().endswith('(gdb)')):
        return []
    txt = txt[:-len('(gdb)')-1]
    vari = txt.split('*')[1].split('@')[0].strip()
    val = '='.join(txt.split('=')[1:]).strip()
    values_lists = [f'{vari} = {val}']
    pocess_values_lists = []
    for values_list in values_lists:
        vari = values_list.split(' = ')[0]
        if 'std::vector of length' in values_list:
            if values_list.count(' = ') == 1:
                this_values_list = f'{vari} = []'
                pocess_values_lists.append(this_values_list)
            else:
                this_values_list = copy.deepcopy(values_list)
                while 'std::vector of length' in this_values_list:
                    x = re.search('std::vector of length [-\d]*, capacity [-\d]* = ', this_values_list)
                    if x:
                        research_st = x.group()
                        this_values_list = this_values_list.replace(research_st, '')
                    else:
                        break
                while 'std::vector<bool> of length' in this_values_list:
                    x = re.search('std::vector<bool> of length [-\d]*, capacity [-\d]* = ', this_values_list)
                    if x:
                        research_st = x.group()
                        this_values_list = this_values_list.replace(research_st, '')
                    else:
                        break
                if '{' in this_values_list:
                    this_values_list = this_values_list.replace('{', '[')
                if '}' in this_values_list:
                    this_values_list = this_values_list.replace('}', ']')
                if '[ [' in this_values_list:
                    this_values_list = this_values_list.replace('[ [', '[[')
                if '] ]' in this_values_list:
                    this_values_list = this_values_list.replace('] ]', ']]')
                if this_values_list.endswith('[\r') or '<error reading' in this_values_list:
                    continue
                else:
                    pocess_values_lists.append(this_values_list)
        else:
            this_values_list = copy.deepcopy(values_list)
            if '{' in this_values_list:
                this_values_list = this_values_list.replace('{', '[')
            if '}' in this_values_list:
                this_values_list = this_values_list.replace('}', ']')
            if '[ [' in this_values_list:
                this_values_list = this_values_list.replace('[ [', '[[')
            if '] ]' in this_values_list:
                this_values_list = this_values_list.replace('] ]', ']]')
            pocess_values_lists.append(this_values_list)
    return pocess_values_lists


def find_values_cpp(txt, listarg2len, token):
    lines = txt.split('\n')
    available_lines = lines[1:]
    values_lists = []
    this_value_list = []
    for item_id, item in enumerate(available_lines):
        if item.endswith(', \r') or item.endswith(', {\r') or item.endswith('= {\r'):
            this_value_list.append(item)
        else:
            if this_value_list:
                this_value_list.append(item)
                combined_str = ''
                for v in this_value_list:
                    if combined_str:
                        combined_str = combined_str + ' ' + v.strip()
                    else:
                        combined_str = v.strip()
                values_lists.append(combined_str)
                this_value_list = []
            else:
                if ' = ' in item:
                    values_lists.append(item)

    pocess_values_lists = []
    for values_list in values_lists:
        vari = values_list.split(' = ')[0]
        if vari in listarg2len:
            continue
        if 'std::unordered_map' in values_list:
            if 'std::unordered_map with 0 elements' in values_list:
                pocess_values_lists.append(token+' = {}')
            else:
                this_values_list = values_list.strip().split('=')
                new_values_list = this_values_list[2:]
                this_new_value = '='.join(new_values_list).strip()
                this_new_value = this_new_value.replace('[', '')
                this_new_value = this_new_value.replace(']', '')
                this_new_value = this_new_value.replace(' = ', ': ')
                pocess_values_lists.append(f'{token} = {this_new_value}')
        if 'std::unordered_set' in values_list:
            if 'std::unordered_set with 0 elements' in values_list:
                pocess_values_lists.append(token+' = {}')
            else:
                this_values_list = values_list.strip().split('=')
                new_values_list = this_values_list[2:]
                this_new_value = '='.join(new_values_list).strip()
                this_new_value = this_new_value.replace(' = ', ': ')
                for this_id in range(300):
                    if f'[{this_id}]: ' in this_new_value:
                        this_new_value = this_new_value.replace(f'[{this_id}]: ', '')
                pocess_values_lists.append(f'{token} = {this_new_value}')
        if 'std::vector of length' in values_list:
            if values_list.count(' = ') == 1:
                this_values_list = f'{vari} = []'
                pocess_values_lists.append(this_values_list)
            else:
                this_values_list = copy.deepcopy(values_list)
                while 'std::vector of length' in this_values_list:
                    x = re.search('std::vector of length [-\d]*, capacity [-\d]* = ', this_values_list)
                    if x:
                        research_st = x.group()
                        this_values_list = this_values_list.replace(research_st, '')
                    else:
                        break
                while 'std::vector<bool> of length' in this_values_list:
                    x = re.search('std::vector<bool> of length [-\d]*, capacity [-\d]* = ', this_values_list)
                    if x:
                        research_st = x.group()
                        this_values_list = this_values_list.replace(research_st, '')
                    else:
                        break
                if '{' in this_values_list:
                    this_values_list = this_values_list.replace('{', '[')
                if '}' in this_values_list:
                    this_values_list = this_values_list.replace('}', ']')
                if '[ [' in this_values_list:
                    this_values_list = this_values_list.replace('[ [', '[[')
                if '] ]' in this_values_list:
                    this_values_list = this_values_list.replace('] ]', ']]')
                if this_values_list.endswith('[\r') or '<error reading' in this_values_list:
                    continue
                else:
                    pocess_values_lists.append(this_values_list)
        else:
            this_values_list = copy.deepcopy(values_list)
            if '{' in this_values_list:
                this_values_list = this_values_list.replace('{', '[')
            if '}' in this_values_list:
                this_values_list = this_values_list.replace('}', ']')
            if '[ [' in this_values_list:
                this_values_list = this_values_list.replace('[ [', '[[')
            if '] ]' in this_values_list:
                this_values_list = this_values_list.replace('] ]', ']]')
            pocess_values_lists.append(this_values_list)
    return pocess_values_lists


punctuation = string.punctuation
def extract_cpp_code_line(line, ID):
    if ID in line:
        code = line.split(ID)[1].split('\r\n')[1].split('\t')[1]
        for punc in punctuation:
            if punc != '_' and punc in code:
                code = code.replace(punc, ' ')
        return code.split(' ')
    elif line.startswith('next'):
        code = line.split('\r\n')[-2].split('\t')[1]
        for punc in punctuation:
            if punc != '_' and punc in code:
                code = code.replace(punc, ' ')
        return code.split(' ')
    else:
        assert False


def extract_trace_cpp_diff_value(file_name, tmp_dir, listarg2len, f_trace_file, max_steps, lang, break_line_id, limit):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.cpp'
    f_code = open(file_path)
    code_lines = f_code.readlines()
    f_code.close()
    func_line_id = -1
    for line_id, code_line in enumerate(code_lines):
        if 'f_filled' in code_line and 'f_gold' not in code_line:
            func_line_id = line_id+1
            break
    if func_line_id == -1:
        raise Exception('Not found func line_id!')
    try:
        p = Popen(['g++', '-g', file_path, '-o', f'{tmp_dir}/output'], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
        stdout, stderr_data = p.communicate(timeout=4)
        p.kill()
    except:
        p.kill()
        return []

    compile_cmd = f"gdb {tmp_dir}/output"
    cmd = pexpect.spawn(compile_cmd)
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    a = re.sub(r'\x1b\[[0-9;]*m', '', a)
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"break {break_line_id}")
    time.sleep(1)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    a = re.sub(r'\x1b\[[0-9;]*m', '', a)
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"run")
    time.sleep(1)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
    print(current_line_info)
    raise_exception_cpp(current_line_info, file_name)
    cmd.sendline(f"next")
    time.sleep(0.2)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
    print(current_line_info)
    pre_line_info = copy.deepcopy(current_line_info)
    traces_list = []
    traces = []
    for i in range(max_steps):

        if 'The program is not being run.' in current_line_info:
            traces_list.append(traces)
            traces = []
            break

        this_trace = []
        line_id = find_line_id_cpp(pre_line_info)
        print(f"{color.BOLD}{color.YELLOW}{line_id}{color.END}")
        this_trace.append(pre_line_info)
        this_trace.append(int(line_id)-func_line_id)

        if len(traces) == limit:
            pre_line_info = copy.deepcopy(current_line_info)
            cmd.sendline(f"next")
            time.sleep(0.2)
            cmd.expect('.+')
            current_line_info = cmd.match.string.decode()
            current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
            print(current_line_info)

            cmd.sendline(f"info args")
            time.sleep(0.2)
            cmd.expect('.+')
            args_values_infos = ''
            args_values_info = cmd.match.string.decode()
            args_values_info = re.sub(r'\x1b\[[0-9;]*m', '', args_values_info)
            print(args_values_info)
            raise_exception_cpp(args_values_info, file_name)
            args_values_infos += args_values_info
            while args_values_info.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
                args_values_infos = args_values_infos.replace('--Type <RET> for more, q to quit, c to continue without paging--', '')
                cmd.sendline(f"<RET>")
                time.sleep(0.2)
                cmd.expect('.+')
                args_values_info = cmd.match.string.decode()
                args_values_info = re.sub(r'\x1b\[[0-9;]*m', '', args_values_info)
                print(args_values_info)
                raise_exception_cpp(args_values_info, file_name)
                args_values_info = args_values_info.replace('<RET>\r\n', '')
                args_values_infos += args_values_info

            args_values = find_values_cpp(args_values_infos, listarg2len, '')
            for args_value in args_values:
                print(f"{color.BOLD}{color.BLUE}{args_value}{color.END}")

            this_trace.append(args_values)

            cmd.sendline(f"info locals")
            time.sleep(0.2)
            cmd.expect('.+')
            locals_values_infos = ''
            locals_values_info = cmd.match.string.decode()
            locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
            print(locals_values_info)
            raise_exception_cpp(locals_values_info, file_name)
            locals_values_infos += locals_values_info
            while locals_values_infos.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
                locals_values_infos = locals_values_infos.replace('--Type <RET> for more, q to quit, c to continue without paging--', '')
                cmd.sendline(f"<RET>")
                time.sleep(0.2)
                cmd.expect('.+')
                locals_values_info = cmd.match.string.decode()
                locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                print(locals_values_info)
                raise_exception_cpp(locals_values_info, file_name)
                locals_values_info = locals_values_info.replace('<RET>\r\n', '')
                locals_values_infos += locals_values_info

            locals_values = find_values_cpp(locals_values_infos, listarg2len, '')
            this_trace[-1].extend([locals_value.strip() for locals_value in locals_values])

            listargs_values = []
            for arg, arg_len in listarg2len.items():


                cmd.sendline(f"p *{arg}@{arg_len}")
                time.sleep(0.2)
                cmd.expect('.+')
                locals_values_infos = ''
                locals_values_info = cmd.match.string.decode()
                locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                print(locals_values_info)
                raise_exception_cpp(locals_values_info, file_name)
                locals_values_infos += locals_values_info
                while locals_values_infos.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
                    locals_values_infos = locals_values_infos.replace(
                        '--Type <RET> for more, q to quit, c to continue without paging--', '')
                    cmd.sendline(f"<RET>")
                    time.sleep(0.2)
                    cmd.expect('.+')
                    locals_values_info = cmd.match.string.decode()
                    locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                    print(locals_values_info)
                    raise_exception_cpp(locals_values_info, file_name)
                    locals_values_info = locals_values_info.replace('<RET>\r\n', '')
                    locals_values_infos += locals_values_info

                locals_values = find_values_cpp_singlevari(locals_values_infos)
                listargs_values.extend(locals_values)
            this_trace[-1].extend([listargs_value.strip() for listargs_value in listargs_values])
        else:
            this_trace.append([])

        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace, lang)
        f_trace.close()

        if len(traces) > limit:
            traces_list.append(traces)
            traces = []
            break

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"continue")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
        print(current_line_info)
        raise_exception_cpp(current_line_info, file_name)

        if 'exited normally' in current_line_info:
            traces_list.append(traces)
            traces = []
            break

    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def extract_trace_cpp_diff_path(file_name, tmp_dir, listarg2len, f_trace_file, max_steps, lang, break_line_id, limit):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.cpp'
    f_code = open(file_path)
    code_lines = f_code.readlines()
    f_code.close()
    func_line_id = -1
    for line_id, code_line in enumerate(code_lines):
        if 'f_filled' in code_line and 'f_gold' not in code_line:
            func_line_id = line_id+1
            break
    if func_line_id == -1:
        raise Exception('Not found func line_id!')
    try:
        p = Popen(['g++', '-g', file_path, '-o', f'{tmp_dir}/output'], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
        stdout, stderr_data = p.communicate(timeout=4)
        p.kill()
    except:
        p.kill()
        return []

    compile_cmd = f"gdb {tmp_dir}/output"
    cmd = pexpect.spawn(compile_cmd)
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    a = re.sub(r'\x1b\[[0-9;]*m', '', a)
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"break {break_line_id}")
    time.sleep(1)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    a = re.sub(r'\x1b\[[0-9;]*m', '', a)
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"run")
    time.sleep(1)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
    print(current_line_info)
    raise_exception_cpp(current_line_info, file_name)
    cmd.sendline(f"next")
    time.sleep(0.2)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
    print(current_line_info)
    pre_line_info = copy.deepcopy(current_line_info)
    traces_list = []
    traces = []
    for i in range(max_steps):

        if 'The program is not being run.' in current_line_info:
            traces_list.append(traces)
            traces = []
            break

        this_trace = []
        line_id = find_line_id_cpp(current_line_info)
        print(f"{color.BOLD}{color.YELLOW}{line_id}{color.END}")
        this_trace.append(current_line_info)
        this_trace.append(int(line_id)-func_line_id)

        if len(traces) > limit:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        this_trace.append([])

        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace, lang)
        f_trace.close()

        cmd.sendline(f"continue")
        time.sleep(0.2)
        cmd.expect('.+')
        a = cmd.match.string.decode()
        a = re.sub(r'\x1b\[[0-9;]*m', '', a)
        print(a)
        raise_exception_cpp(a, file_name)

        if 'exited normally' in a:
            traces_list.append(traces)
            traces = []
            break

        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
        print(current_line_info)

        if 'exited normally' in current_line_info:
            break

    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def print_step_info(f_trace, step, lang):
    print(f'Line: {step[1]}', file=f_trace)
    if lang == 'Python':
        for vari, val in step[2][0].items():
            if type(val) == str:
                print(f'{vari} = \"{val}\"', file=f_trace)
            else:
                print(f'{vari} = {val}', file=f_trace)
        print('', file=f_trace)
    else:
        for var in step[2]:
            print(f'{var.strip()}', file=f_trace)
        print('', file=f_trace)


def compare_stepbystep_for_fix(source_traces, trans_traces, source_lang, target_lang, line_M, len_s, len_t, source_lines, trans_lines):
    report_id = 0
    diff_info = []
    same_info = []
    pre_s_state = [[], [], []]
    pre_t_state = [[], [], []]
    expect_t_state = []
    wrong_t_state = []
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
                        if source_lang == 'Java' and len(t_state[0]) == 1 and trans_lines[t_state[0][0]].strip().startswith('for') and len(s_expect_t) == 1 and source_lines[s_expect_t[0]-2].strip().startswith('for'):
                            None
                        else:
                            if_step = False
                            diff_info.append(['diff_path'])
                            expect_t_state = s_expect_t[:]
                            wrong_t_state = t_state[0][:]
                    except:
                        if_step = False
                        diff_info.append(['diff_path'])
                        expect_t_state = s_expect_t[:]
                        wrong_t_state = t_state[0][:]
            last_s_var_vals = s_state[1][-1]
            last_t_var_vals = t_state[1][-1]
            same_info = []
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
                                next_val = [val_str for val_str in trans_traces[t_state[2][-1]+1][1:] if f'{s_var} = ' in val_str]
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
                        same_info.append(['same-value', s_var, s_val, t_val])
            if if_step:
                pass_t_ids.extend(t_state[0])
        if if_step:
            pre_s_state = copy.deepcopy(s_state)
            pre_t_state = copy.deepcopy(t_state)
        else:
            if diff_info[0][0] == 'diff_value':
                report_id = t_state[0][-1]
            else:
                if if_target_non:
                    s_expect_t = set()
                    for t_stmt_id in range(len_t):
                        if s_state[0] and line_M[f'{s_state[0][-1]}-{t_stmt_id}']:
                            s_expect_t.add(t_stmt_id)
                    s_expect_t = list(s_expect_t)
                    wrong_t_state = pre_t_state[0][:]
                    if pre_t_state[2] and pre_t_state[2][0]-1 >= 0:
                        report_id = trans_traces[pre_t_state[2][0]-1][0]
                        pass_t_ids = pass_t_ids[:-1]
                        expect_t_state = s_expect_t[:]
                        wrong_t_state = pre_t_state[0][:]
                    elif len(pre_t_state[0]):
                        report_id = pre_t_state[0][-1]
                    else:
                        report_id = 0
                else:
                    if if_source_non:
                        wrong_t_state = t_state[0][:]
                    if len(pre_t_state[0]):
                        report_id = pre_t_state[0][-1]
                    else:
                        report_id = 0
    return diff_info, report_id, pass_t_ids, expect_t_state, wrong_t_state, if_source_non, if_target_non, same_info


def run_script(file_path, lang, tmp_dir):
    if lang == "Python":
        try:
            p = Popen(['python3', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stdout.decode().strip().count('OUTPUT-OF') == 0 and stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            output = stdout.decode().strip()
            if 'False' in output:
                output = output.replace('False', 'false')
            if 'True' in output:
                output = output.replace('True', 'true')
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', output
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "Java":
        try:
            p = Popen(['java', '--module-path', '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
                       '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE,
                      stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''

    elif lang == "C++":
        try:
            p = Popen(['g++', '-o', f'{tmp_dir}/output', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if not os.path.isfile(f'{tmp_dir}/output'):
                return 'compile_failed', ''
        except:
            p.kill()
            return 'compile_failed', ''
        try:
            p = Popen([f'{tmp_dir}/output'], cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr_data = p.communicate(timeout=5)
            p.kill()
            if stderr_data.decode() != '':
                return 'runtime_failed', str(stderr_data.decode()).strip()
            if stdout.decode().strip().count('OUTPUT-OF') == 0:
                return 'runtime_failed', str(stderr_data.decode()).strip()
            return 'success', stdout.decode().strip()
        except:
            p.kill()
            return 'infinite_loop', ''


def compare_uncompare(output):
    output_strip = output.strip()
    if '#Results:' not in output_strip:
        return []
    ori_output2_strip_list = [int(item.strip()) for item in output_strip.split('#Results:')[0].split('Pass_test_id-') if item != '']
    return ori_output2_strip_list


def compare(output1, output2):
    output1_strip = output1.strip()
    output2_strip = output2.strip()
    ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
    ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
    if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
        ori_output1_strip_list = ori_output1_strip_list[1:]
    if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
        ori_output2_strip_list = ori_output2_strip_list[1:]
    output1_strip_list = []
    output1_strip_dict = {}
    for i in range(10):
        for item in ori_output1_strip_list:
            if item.startswith(f'{i}:\n'):
                if item.endswith('.0\n'):
                    output1_strip_list.append(item[len(f'{i}:\n'):-len('.0\n')]+'\n')
                    output1_strip_dict[i] = item[len(f'{i}:\n'):-len('.0\n')]+'\n'
                elif item.endswith('.0'):
                    output1_strip_list.append(item[len(f'{i}:\n'):-len('.0')])
                    output1_strip_dict[i] = item[len(f'{i}:\n'):-len('.0')]
                else:
                    output1_strip_list.append(item[len(f'{i}:\n'):])
                    output1_strip_dict[i] = item[len(f'{i}:\n'):]
    output2_strip_list = []
    output2_strip_dict = {}
    for i in range(10):
        for item in ori_output2_strip_list:
            if item.startswith(f'{i}:\n'):
                if item.endswith('.0\n'):
                    output2_strip_list.append(item[len(f'{i}:\n'):-len('.0\n')]+'\n')
                    output2_strip_dict[i] = item[len(f'{i}:\n'):-len('.0\n')]+'\n'
                elif item.endswith('.0'):
                    output2_strip_list.append(item[len(f'{i}:\n'):-len('.0')])
                    output2_strip_dict[i] = item[len(f'{i}:\n'):-len('.0')]
                else:
                    output2_strip_list.append(item[len(f'{i}:\n'):])
                    output2_strip_dict[i] = item[len(f'{i}:\n'):]
    if output1_strip_list == output2_strip_list:
        return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    else:
        if ('true' in output1 or 'false' in output1) and ('1' in output2 or '0' in output2):
            output1_strip = output1_strip.replace('true', '1')
            output1_strip = output1_strip.replace('false', '0')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif ('True' in output1 or 'False' in output1) and ('1' in output2 or '0' in output2):
            output1_strip = output1_strip.replace('True', '1')
            output1_strip = output1_strip.replace('False', '0')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif ('True' in output1 or 'False' in output1) and ('true' in output2 or 'false' in output2):
            output1_strip = output1_strip.replace('True', 'true')
            output1_strip = output1_strip.replace('False', 'false')
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output1_strip_list.append(item[len(f'{i}:\n'):])
                        output1_strip_dict[i] = item[len(f'{i}:\n'):]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        output2_strip_list.append(item[len(f'{i}:\n'):])
                        output2_strip_dict[i] = item[len(f'{i}:\n'):]
        elif '.' in output1 and 'e' in output1 and '.' in output2 and 'e' in output2:
            ori_output1_strip_list = output1_strip.split('OUTPUT-OF-')
            ori_output2_strip_list = output2_strip.split('OUTPUT-OF-')
            if len(ori_output1_strip_list) and ori_output1_strip_list[0] == '':
                ori_output1_strip_list = ori_output1_strip_list[1:]
            if len(ori_output2_strip_list) and ori_output2_strip_list[0] == '':
                ori_output2_strip_list = ori_output2_strip_list[1:]
            output1_strip_list = []
            output1_strip_dict = {}
            for i in range(10):
                for item in ori_output1_strip_list:
                    if item.startswith(f'{i}:\n'):
                        if '.' in item and 'e' in item:
                            output1_strip_list.append(item[len(f'{i}:\n'):].split('e')[0][0])
                            output1_strip_dict[i] = item[len(f'{i}:\n'):].split('e')[0][0]
                        else:
                            output1_strip_list.append(item[len(f'{i}:\n'):][0])
                            output1_strip_dict[i] = item[len(f'{i}:\n'):][0]
            output2_strip_list = []
            output2_strip_dict = {}
            for i in range(10):
                for item in ori_output2_strip_list:
                    if item.startswith(f'{i}:\n'):
                        if '.' in item and 'e' in item:
                            output2_strip_list.append(item[len(f'{i}:\n'):].split('e')[0][0])
                            output2_strip_dict[i] = item[len(f'{i}:\n'):].split('e')[0][0]
                        else:
                            output2_strip_list.append(item[len(f'{i}:\n'):][0])
                            output2_strip_dict[i] = item[len(f'{i}:\n'):][0]
        if output1_strip_list == output2_strip_list:
            return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        same = []
        for id in range(10):
            if id in output1_strip_dict and id in output2_strip_dict:
                if output1_strip_dict[id] == output2_strip_dict[id]:
                    same.append(id)
        return same


def run(path_to_map, path_to_code, path_to_DATABASE, target_model_name, source_lang, target_lang, model_name, tmp_dir):
    os.makedirs(tmp_dir, exist_ok=True)
    generated_map = loadMap(f'{path_to_map}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    passinfo_lines = open(f'ori_passinfo/{target_model_name}-{source_lang}-{target_lang}-passInfo.txt').readlines()
    passinfo_ID2info = {}
    for line in passinfo_lines:
        ID, this_info = line.strip().split('####')
        this_info_list = this_info.split('\t')
        if this_info_list != ['']:
            passinfo_ID2info[ID] = [int(item) for item in this_info_list[:]]
        else:
            passinfo_ID2info[ID] = []

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
    args_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace'
    source_script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script'
    trans_script_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script'
    source_traces_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces'
    trans_traces_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces'
    source_script_for_trace_dir = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{source_lang}-script-for-trace'
    trans_script_for_trace_dir = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace'

    info_files = os.listdir(f'info/{target_model_name}-{source_lang}-{target_lang}')
    uncompared = []
    f_uncompared = open(f'{target_model_name}-{source_lang}-{target_lang}-uncompared.txt')
    uncompared_lines = f_uncompared.readlines()
    for line in uncompared_lines:
        if line.strip():
            uncompared.append(line.strip())
    f_uncompared.close()
    os.makedirs(f'FAIL', exist_ok=True)
    os.makedirs(f'new_passinfo', exist_ok=True)
    os.makedirs(f't_passinfo/{target_model_name}-{source_lang}-{target_lang}', exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}', exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}', exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace',
                exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script',
                exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script',
                exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces', exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces', exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace',
                exist_ok=True)
    os.makedirs(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace',
                exist_ok=True)

    log_file = f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}.txt'
    trace_dir = f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces-after-fix'
    os.makedirs(trace_dir, exist_ok=True)
    f_log_file = open(log_file, 'w')
    f_log_file.close()
    info_files.sort()
    for info_file in info_files:
        ID = info_file.split('.')[0]
        info_lines = open(f'info/{target_model_name}-{source_lang}-{target_lang}/{info_file}').readlines()
        info_lines = [line.strip() for line in info_lines if line.strip()]
        info = []
        for info_line in info_lines:
            val = int(info_line.split('\t')[0])
            if '|' in info_line:
                ids = info_line.split('\t')[1].split('|')
            else:
                ids = [info_line.split('\t')[1]]
            ids = [int(item) for item in ids]
            ids.sort()
            info.append([val, ids])
        info.sort(reverse=True)
        if info and info[0][0] == 10:
            continue
        elif info:
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

            source_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
            trans_traces = load_trace(f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')
            diff_info, report_id, pass_t_ids, expect_t_state, wrong_t_state, if_source_non, if_target_non, same_info = compare_stepbystep_for_fix(source_traces, trans_traces, source_lang, target_lang, line_M, len(source_lines), len(trans_lines), source_lines, trans_lines)

            ID_pass_info = passinfo_ID2info[ID]
            first_diff_id = -1
            for pass_id in range(10):
                if pass_id not in ID_pass_info:
                    first_diff_id = pass_id
                    break

            assert first_diff_id != -1

            new_pass_info = []

            if_fix_ids = []
            if_not_wrong_ids = []
            time_limit = 1800
            start_time = time.time()
            for info_item in info:
                this_time = time.time()
                if this_time - start_time > time_limit:
                    print('Time out...')
                    break

                filter_info_item = []
                for this_info_id, info_id in enumerate(info_item[1][:]):
                    target_script = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{info_id}.cpp'
                    target_script_lines_str = ''.join(open(target_script).readlines())
                    if 'mpz_class' in target_script_lines_str or '#include <gmpxx.h>' in target_script_lines_str:
                        continue
                    filter_info_item.append(info_id)
                this_new_pass_info = []
                for this_info_id, info_id in enumerate(filter_info_item[:30]):
                    this_time = time.time()
                    if this_time - start_time > time_limit:
                        print('Time out...')
                        break

                    source_script = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}'
                    exist_files = os.listdir(f'{tmp_dir}/')
                    for exist_file in exist_files:
                        if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                            shutil.rmtree(f'{tmp_dir}/{exist_file}')
                        else:
                            os.remove(f'{tmp_dir}/{exist_file}')
                    time.sleep(0.3)
                    shutil.copyfile(source_script, f'{tmp_dir}/{ID}.{source_ext}')
                    source_info, source_output = run_script(f'{tmp_dir}/{ID}.{source_ext}', source_lang, tmp_dir)

                    target_script = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{info_id}.cpp'
                    exist_files = os.listdir(f'{tmp_dir}/')

                    target_script_lines_str = ''.join(open(target_script).readlines())

                    if 'mpz_class' in target_script_lines_str or '#include <gmpxx.h>' in target_script_lines_str:
                        continue

                    shutil.copyfile(target_script, f'{tmp_dir}/{ID}.{target_ext}')
                    target_info, target_output = run_script(f'{tmp_dir}/{ID}.{target_ext}', target_lang, tmp_dir)

                    if target_info != 'success':
                        continue

                    if ID in uncompared:
                        this_source_same_ids = compare_uncompare(target_output)
                    else:
                        this_source_same_ids = compare(source_output, target_output)

                    this_new_pass_info.append(this_source_same_ids)

                    if len(passinfo_ID2info[ID]) > len(this_source_same_ids):
                        continue

                    if_have_passed = False
                    if first_diff_id in this_source_same_ids:
                        if_have_passed = True
                        for pass_id in range(10):
                            if pass_id not in this_source_same_ids:
                                first_diff_id = pass_id
                                break

                    if not if_have_passed:

                        exist_files = os.listdir(f'{tmp_dir}/')
                        for exist_file in exist_files:
                            if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                                shutil.rmtree(f'{tmp_dir}/{exist_file}')
                            else:
                                os.remove(f'{tmp_dir}/{exist_file}')

                        fix_script_lines = rewrite_script(f'{trans_script_for_trace_dir}/{ID}/{info_id}.{target_ext}', passinfo_ID2info[ID], target_lang)

                        f_fix_scirpt = open(f'{tmp_dir}/{ID}.{target_ext}', 'w')
                        print(''.join(fix_script_lines), file=f_fix_scirpt)
                        f_fix_scirpt.close()

                        script_lines = open(f'{tmp_dir}/{ID}.{target_ext}').readlines()
                        func_line_id = 0
                        for line_id, line in enumerate(script_lines):
                            if 'f_filled' in line:
                                func_line_id = line_id
                                break

                        script_path = f'{tmp_dir}/{ID}.{target_ext}'
                        arg_path = f'{args_dir}/{ID}.args'
                        f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace'
                        listarg2len = {}
                        if target_lang == 'C++':
                            test_f = open(script_path)
                            test_lines = test_f.readlines()
                            test_f.close()
                            args = []
                            for test_line in test_lines:
                                if 'f_filled' in test_line and 'f_gold' not in test_line and 'if(' not in test_line:
                                    match = re.search(r'f_filled\s*\((.+)\)\s*', test_line)
                                    if not match:
                                        raise Exception('Not Match!')
                                    args_string = match.group(1)
                                    args_list = [item.strip() for item in args_string.strip().split(',')]
                                    for arg in args_list:
                                        if ' ' not in arg:
                                            args.append([arg.strip(), False])
                                        else:
                                            if '*' in arg:
                                                args.append([arg.strip().split(' ')[-1], True])
                                            elif '[' in arg:
                                                match2 = re.search(r'\S+\s(.+)\[', arg)
                                                if not match2:
                                                    raise Exception('Not Match Args!')
                                                args.append([match2.group(1), True])
                                            else:
                                                args.append([arg.strip().split(' ')[-1], False])
                                    break

                            f_args = open(arg_path)
                            args_lines = f_args.readlines()
                            f_args.close()
                            args_info = []
                            for args_line in args_lines:
                                if args_line == '0\n':
                                    args_info.append([])
                                else:
                                    args_info.append(args_line.strip().split('\t'))
                            if len(args) == len(args_info):
                                for arg, arg_info in zip(args, args_info):
                                    if arg[1]:
                                        listarg2len[arg[0].strip()] = int(arg_info[0])

                        traces_list = []
                        if_fixed = False
                        if_not_wrong = False
                        if diff_info and diff_info[0][0] == 'diff_value':
                            for i in range(1):
                                f_log = open(log_file, 'a')
                                print(f'{ID}-{i}', file=f_log)
                                f_log.close()
                                try:
                                    f_trace = open(f'{trace_dir}/{ID}.txt', 'w')
                                    f_trace.close()
                                    traces_list = extract_trace_cpp_diff_value(ID, tmp_dir, listarg2len, f'{trace_dir}/{ID}.txt', 10000, target_lang, func_line_id+report_id+1, pass_t_ids.count(report_id))
                                    if not traces_list:
                                        raise Exception('No trace!')
                                    break
                                except:
                                    continue
                            if traces_list:
                                for this_trace_list in traces_list[0]:
                                    this_change_this_trace_list = [change(item, target_lang) for item in this_trace_list[2]]
                                    var_vals = read_var_val(this_change_this_trace_list)
                                    for k, v in var_vals.items():
                                        if k == diff_info[0][1]:
                                            if compare_value_for_fix(diff_info[0][2], v):
                                                if_fixed = True
                                    for k, v in var_vals.items():
                                        if same_info and k == same_info[0][1]:
                                            if not compare_value_for_fix(same_info[0][2], v):
                                                if_fixed = False
                        elif diff_info and diff_info[0][0] == 'diff_path':
                            if len(pass_t_ids) != 9999:
                                for i in range(1):
                                    f_log = open(log_file, 'a')
                                    print(f'{ID}-{i}', file=f_log)
                                    f_log.close()
                                    try:
                                        f_trace = open(f'{trace_dir}/{ID}.txt', 'w')
                                        f_trace.close()
                                        traces_list = extract_trace_cpp_diff_path(ID, tmp_dir, listarg2len, f'{trace_dir}/{ID}.txt', 10000, target_lang, func_line_id+report_id+1, pass_t_ids.count(report_id))
                                        if not traces_list:
                                            raise Exception('No trace!')
                                        break
                                    except:
                                        continue
                            if expect_t_state and traces_list:
                                ori_pass_count = pass_t_ids.count(report_id)
                                if len(traces_list[0]) >= ori_pass_count and traces_list[0][ori_pass_count-1][1] in expect_t_state:
                                    if_fixed = True
                            if wrong_t_state and traces_list:
                                ori_pass_count = pass_t_ids.count(report_id)
                                if len(traces_list[0]) >= ori_pass_count and traces_list[0][ori_pass_count-1][1] not in wrong_t_state:
                                    if_not_wrong = True
                        if if_not_wrong:
                            if_not_wrong_ids.append([info_id, if_have_passed, this_source_same_ids, first_diff_id])
                        if if_fixed:
                            if_fix_ids.append([info_id, if_have_passed, this_source_same_ids, first_diff_id])
                            break
                    else:
                        if_fix_ids.append([info_id, if_have_passed, this_source_same_ids, first_diff_id])
                new_pass_info.append(this_new_pass_info)
            if if_fix_ids == [] and if_not_wrong_ids != []:
                if_fix_ids = if_not_wrong_ids[:]
            if_fix_ids.sort()
            if if_fix_ids:
                fix_id = if_fix_ids[0]
                if not fix_id[1]:
                    shutil.copy(f'{source_traces_dir}/{ID}.txt', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
                    f_t_passinfo = open(f't_passinfo/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt', 'w')
                    print(len(pass_t_ids), file=f_t_passinfo)
                    f_t_passinfo.close()

                    if len(pass_t_ids) > 9000:
                        shutil.copy(f'{trans_traces_dir}/{ID}.txt', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')

                    shutil.copy(f'{target_model_name}-data/{source_lang}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}/{ID}.{source_ext}')
                    shutil.copy(f'Fix_Code/{target_model_name}-{source_lang}-{target_lang}/{ID}/{fix_id[0]}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}/{ID}.{target_ext}')
                    shutil.copy(f'{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                    shutil.copy(f'{source_script_dir}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script/{ID}.{source_ext}')
                    shutil.copy(f'{trans_script_dir}/{ID}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script/{ID}.{target_ext}')

                    new_source_script_lines = rewrite_script(f'{source_script_for_trace_dir}/{ID}.{source_ext}', passinfo_ID2info[ID], source_lang)
                    new_trans_script_lines = rewrite_script(f'{trans_script_for_trace_dir}/{ID}/{fix_id[0]}.{target_ext}', passinfo_ID2info[ID], target_lang)
                    f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}', 'w')
                    print(''.join(new_source_script_lines), file=f_o)
                    f_o.close()
                    f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}', 'w')
                    print(''.join(new_trans_script_lines), file=f_o)
                    f_o.close()

                    f_passinfo = open(f'new_passinfo/{target_model_name}-{source_lang}-{target_lang}-passInfo.txt', 'a')
                    print(f"{ID}####"+'\t'.join([str(item) for item in fix_id[2]]), file=f_passinfo)
                    f_passinfo.close()
                else:
                    f_t_passinfo = open(f't_passinfo/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt', 'w')
                    print('-1', file=f_t_passinfo)
                    f_t_passinfo.close()

                    if len(pass_t_ids) > 9000:
                        shutil.copy(f'{trans_traces_dir}/{ID}.txt', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')

                    shutil.copy(f'{target_model_name}-data/{source_lang}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}/{ID}.{source_ext}')
                    shutil.copy(f'Fix_Code/{target_model_name}-{source_lang}-{target_lang}/{ID}/{fix_id[0]}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}/{ID}.{target_ext}')
                    shutil.copy(f'{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                    shutil.copy(f'{source_script_dir}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script/{ID}.{source_ext}')
                    shutil.copy(f'{trans_script_dir}/{ID}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script/{ID}.{target_ext}')

                    new_source_script_lines = rewrite_script(f'{source_script_for_trace_dir}/{ID}.{source_ext}', fix_id[2], source_lang)
                    new_trans_script_lines = rewrite_script(f'{trans_script_for_trace_dir}/{ID}/{fix_id[0]}.{target_ext}', fix_id[2], target_lang)
                    f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}', 'w')
                    print(''.join(new_source_script_lines), file=f_o)
                    f_o.close()
                    f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}', 'w')
                    print(''.join(new_trans_script_lines), file=f_o)
                    f_o.close()

                    f_passinfo = open(f'new_passinfo/{target_model_name}-{source_lang}-{target_lang}-passInfo.txt', 'a')
                    print(f"{ID}####"+'\t'.join([str(item) for item in fix_id[2]]), file=f_passinfo)
                    f_passinfo.close()
            else:
                info.sort(reverse=True)
                if_print = False
                for info_item in info:
                    if if_print:
                        break
                    for info_id in info_item[1]:
                        if if_print == False:
                            target_script = f'{target_model_name}-data-new/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}/{info_id}.cpp'
                            target_script_lines_str = ''.join(open(target_script).readlines())
                            if 'mpz_class' in target_script_lines_str or '#include <gmpxx.h>' in target_script_lines_str:
                                continue

                            if_print = True

                            if len(pass_t_ids) > 9000:
                                shutil.copy(f'{trans_traces_dir}/{ID}.txt', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')

                            shutil.copy(f'{target_model_name}-data/{source_lang}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}/{ID}.{source_ext}')
                            shutil.copy(f'Fix_Code/{target_model_name}-{source_lang}-{target_lang}/{ID}/{info_id}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}/{ID}.{target_ext}')
                            shutil.copy(f'{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace/{ID}.args')
                            shutil.copy(f'{source_script_dir}/{ID}.{source_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script/{ID}.{source_ext}')
                            shutil.copy(f'{trans_script_dir}/{ID}.{target_ext}', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script/{ID}.{target_ext}')
                            shutil.copy(f'{source_traces_dir}/{ID}.txt', f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')

                            new_source_script_lines = rewrite_script(f'{source_script_for_trace_dir}/{ID}.{source_ext}', passinfo_ID2info[ID], source_lang)
                            new_trans_script_lines = rewrite_script(f'{trans_script_for_trace_dir}/{ID}/{info_id}.{target_ext}', passinfo_ID2info[ID], target_lang)
                            f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace/{ID}.{source_ext}', 'w')
                            print(''.join(new_source_script_lines), file=f_o)
                            f_o.close()
                            f_o = open(f'CODE-round2/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-script-for-trace/{ID}.{target_ext}', 'w')
                            print(''.join(new_trans_script_lines), file=f_o)
                            f_o.close()

                            f_passinfo = open(f'new_passinfo/{target_model_name}-{source_lang}-{target_lang}-passInfo.txt', 'a')
                            print(f"{ID}####" + '\t'.join([str(item) for item in passinfo_ID2info[ID]]), file=f_passinfo)
                            f_passinfo.close()

                            f_t_passinfo = open(f't_passinfo/{target_model_name}-{source_lang}-{target_lang}/{ID}.txt', 'w')
                            print(len(pass_t_ids), file=f_t_passinfo)
                            f_t_passinfo.close()

                            break

                f = open(f'FAIL/fail_fix-{target_model_name}-{source_lang}-{target_lang}.txt', 'a')
                print(ID, file=f)
                f.close()

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
        "--path_to_code",
        default='/home/ubuntu/RulER/DATABASE/DATA/CODE',
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
        "--tmp_dir",
        default='tmp',
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
    path_to_code = args.path_to_code
    path_to_DATABASE = args.path_to_DATABASE
    tmp_dir = args.tmp_dir
    count_right, count_wrong, count_right_B, count_wrong_B = run(path_to_map, path_to_code, path_to_DATABASE, target_model_name, source_lang, target_lang, model_name, tmp_dir)

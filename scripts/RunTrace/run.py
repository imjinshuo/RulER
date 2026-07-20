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
from utils import *


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


def raise_exception_cpp(info, file_name):
    if not info.endswith('(gdb) ') and not info.endswith(
            '--Type <RET> for more, q to quit, c to continue without paging--'):
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
    txt = txt[:-len('(gdb)') - 1]
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
                pocess_values_lists.append(token + ' = {}')
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
                pocess_values_lists.append(token + ' = {}')
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
        ori_code = line.split(ID)[1].split('\r\n')[1].split('\t')[1].split(' ')
        code = []
        for token in ori_code:
            code.append(token)
        code = ' '.join(code)
        for punc in punctuation:
            if punc != '_' and punc in code:
                code = code.replace(punc, ' ')
        return [item for item in code.split(' ') if item != '']
    elif line.startswith('next'):
        ori_code = line.split('\r\n')[-2].split('\t')[1].split(' ')
        code = []
        for token in ori_code:
            code.append(token)
        code = ' '.join(code)
        for punc in punctuation:
            if punc != '_' and punc in code:
                code = code.replace(punc, ' ')
        return [item for item in code.split(' ') if item != '']
    else:
        return []


def extract_trace_cpp(file_name, start_time, time_limit, tmp_dir, trans_stmt_list, source_stmt_list_pos, listarg2len,
                      source_lang_trace_vars, f_trace_file, max_steps, lang, t_passinfo_num, source_lang, target_lang,
                      line_M, source_lines, trans_lines, path_to_code, target_model_name, ID):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.cpp'
    f_code = open(file_path)
    code_lines = f_code.readlines()
    f_code.close()
    bias_brace = 0
    func_line_id = -1
    for line_id, code_line in enumerate(code_lines):
        if 'f_filled' in code_line and 'f_gold' not in code_line:
            func_line_id = line_id + 1
            if code_lines[line_id + 1].strip() == '{':
                bias_brace = 1
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
    cmd.sendline(f"break {func_name}")
    time.sleep(1)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    a = re.sub(r'\x1b\[[0-9;]*m', '', a)
    print(a)

    not_stop_lines = []
    stmt_id = -1
    for stmt_list, stmt_pos in zip(trans_stmt_list, source_stmt_list_pos):
        stmt_id += 1
        if stmt_id > 1:
            if stmt_list == 'declaration-0||||primitive_type-0||||identifier-0||||;-0':
                not_stop_lines.append(stmt_pos[0][0] + func_line_id - 1)
    pass_line_ids = []

    raise_exception_cpp(a, file_name)
    cmd.sendline(f"run")
    time.sleep(1)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
    print(current_line_info)
    raise_exception_cpp(current_line_info, file_name)
    cmd.sendline(f"frame")
    time.sleep(0.2)
    cmd.expect('.+')
    line_id_info = cmd.match.string.decode()
    line_id_info = re.sub(r'\x1b\[[0-9;]*m', '', line_id_info)
    print(line_id_info)
    pre_line_info = copy.deepcopy(current_line_info)
    func_line_id = find_line_id_cpp(line_id_info)
    current_line_id = func_line_id
    while current_line_id != func_line_id + 1 and current_line_id != func_line_id + 2:
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
        print(current_line_info)
        raise_exception_cpp(current_line_info, file_name)
        cmd.sendline(f"frame")
        time.sleep(0.2)
        cmd.expect('.+')
        line_id_info = cmd.match.string.decode()
        line_id_info = re.sub(r'\x1b\[[0-9;]*m', '', line_id_info)
        print(line_id_info)
        current_line_id = find_line_id_cpp(line_id_info)
    traces_list = []
    traces = []
    if_first = True
    if_second = False
    defined_locals = []
    max_steps = [i for i in range(max_steps)]
    for i in tqdm(max_steps):

        this_trace = []
        line_id = find_line_id_cpp(pre_line_info)
        print(f"{color.BOLD}{color.YELLOW}{line_id}{color.END}")
        this_trace.append(pre_line_info)

        if line_id not in pass_line_ids:
            pass_line_ids.append(line_id)

        if line_id - 1 not in pass_line_ids and line_id - 1 in not_stop_lines:
            traces.append(['', int(line_id) - func_line_id + bias_brace - 1, []])

        if if_first:
            this_trace.append(0)
        else:
            this_trace.append(int(line_id) - func_line_id + bias_brace)

        if line_id_info.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
            cmd.sendline(f"q")
            time.sleep(0.2)
            cmd.expect('.+')
            a = cmd.match.string.decode()
            a = re.sub(r'\x1b\[[0-9;]*m', '', a)
            print(a)
            raise_exception_cpp(a, file_name)
        if f'{func_name}' not in line_id_info.split('\n')[1]:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        if time.time() - start_time > time_limit or t_passinfo_num == 10000 - 5:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        if i > t_passinfo_num and len(traces) % 150 == 0:
            source_traces = load_trace(
                f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
            trans_traces = load_trace(
                f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-traces/{ID}.txt')
            diff_info = compare_stepbystep_for_trace(source_traces, trans_traces, source_lang, target_lang, line_M,
                                                     len(source_lines), len(trans_lines), source_lines, trans_lines)
            if diff_info:
                this_trace.append([])
                traces.append(this_trace)
                traces_list.append(traces)
                traces = []
                break

        pre_code_tokens = extract_cpp_code_line(pre_line_info, file_name)

        if if_first:
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
                args_values_infos = args_values_infos.replace(
                    '--Type <RET> for more, q to quit, c to continue without paging--', '')
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
            this_trace.append(args_values)
        else:
            this_trace.append([])

        if i > t_passinfo_num:
            for token in pre_code_tokens:
                if token in source_lang_trace_vars and token not in listarg2len:
                    cmd.sendline(f"print {token}")
                    time.sleep(0.2)
                    cmd.expect('.+')
                    locals_values_infos = ''
                    locals_values_info = cmd.match.string.decode()
                    locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                    print(locals_values_info)
                    raise_exception_cpp(locals_values_info, file_name)
                    locals_values_infos += locals_values_info
                    while locals_values_infos.endswith(
                            '--Type <RET> for more, q to quit, c to continue without paging--'):
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
                    if 'No symbol' in locals_values_infos:
                        continue
                    this_locals_values = find_values_cpp(locals_values_infos, listarg2len, token)
                    vari = token
                    if this_locals_values and '=' in this_locals_values[0]:
                        val = this_locals_values[0].split(' = ')[-1]
                        local_value = f'{vari} = {val}'
                        if local_value not in this_trace[-1]:
                            this_trace[-1].append(local_value)
                        if vari not in defined_locals:
                            defined_locals.append(vari)

            listargs_values = []
            for arg, arg_len in listarg2len.items():
                if arg in source_lang_trace_vars and (arg in pre_code_tokens or if_first):
                    cmd.sendline(f"p *{arg}@{arg_len}")
                    time.sleep(0.2)
                    cmd.expect('.+')
                    locals_values_infos = ''
                    locals_values_info = cmd.match.string.decode()
                    locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                    print(locals_values_info)
                    raise_exception_cpp(locals_values_info, file_name)
                    locals_values_infos += locals_values_info
                    while locals_values_infos.endswith(
                            '--Type <RET> for more, q to quit, c to continue without paging--'):
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
                    listargs_values.append(locals_values[0])
                    if arg not in defined_locals:
                        defined_locals.append(arg)
            this_trace[-1].extend(listargs_values)

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
        print(current_line_info)
        raise_exception_cpp(current_line_info, file_name)

        cmd.sendline(f"frame")
        time.sleep(0.2)
        cmd.expect('.+')
        line_id_info = cmd.match.string.decode()
        line_id_info = re.sub(r'\x1b\[[0-9;]*m', '', line_id_info)
        print(line_id_info)
        current_line_id = find_line_id_cpp(line_id_info)

        if if_second:
            this_line_id = int(line_id) - func_line_id + bias_brace
            if bias_brace:
                if this_line_id >= 2:
                    for this_id in range(2, this_line_id):
                        new_trace = ['', this_id, []]
                        this_code_line = code_lines[this_id + func_line_id - bias_brace - 1]
                        this_pre_code_tokens = extract_cpp_code_line(
                            f'next\r\n{this_id + func_line_id}\t{this_code_line}\r\n(gdb)', file_name)
                        for token in this_pre_code_tokens:
                            if token in source_lang_trace_vars and token not in listarg2len:
                                cmd.sendline(f"print {token}")
                                time.sleep(0.2)
                                cmd.expect('.+')
                                locals_values_infos = ''
                                locals_values_info = cmd.match.string.decode()
                                locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                                print(locals_values_info)
                                raise_exception_cpp(locals_values_info, file_name)
                                locals_values_infos += locals_values_info
                                while locals_values_infos.endswith(
                                        '--Type <RET> for more, q to quit, c to continue without paging--'):
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
                                if 'No symbol' in locals_values_infos:
                                    continue
                                this_locals_values = find_values_cpp(locals_values_infos, listarg2len, token)
                                vari = token
                                if this_locals_values and '=' in this_locals_values[0]:
                                    val = this_locals_values[0].split(' = ')[-1]
                                    local_value = f'{vari} = {val}'
                                    if local_value not in new_trace[-1]:
                                        new_trace[-1].append(local_value)
                                    if vari not in defined_locals:
                                        defined_locals.append(vari)
                        traces.append(new_trace)
                        f_trace = open(f_trace_file, 'a')
                        print_step_info(f_trace, new_trace, lang)
                        f_trace.close()
            else:
                if this_line_id >= 1:
                    for this_id in range(1, this_line_id):
                        new_trace = ['', this_id, []]
                        this_code_line = code_lines[this_id + func_line_id - bias_brace - 1]
                        this_pre_code_tokens = extract_cpp_code_line(
                            f'next\r\n{this_id + func_line_id}\t{this_code_line}\r\n(gdb)', file_name)
                        for token in this_pre_code_tokens:
                            if token in source_lang_trace_vars and token not in listarg2len:
                                cmd.sendline(f"print {token}")
                                time.sleep(0.2)
                                cmd.expect('.+')
                                locals_values_infos = ''
                                locals_values_info = cmd.match.string.decode()
                                locals_values_info = re.sub(r'\x1b\[[0-9;]*m', '', locals_values_info)
                                print(locals_values_info)
                                raise_exception_cpp(locals_values_info, file_name)
                                locals_values_infos += locals_values_info
                                while locals_values_infos.endswith(
                                        '--Type <RET> for more, q to quit, c to continue without paging--'):
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
                                if 'No symbol' in locals_values_infos:
                                    continue
                                this_locals_values = find_values_cpp(locals_values_infos, listarg2len, token)
                                vari = token
                                if this_locals_values and '=' in this_locals_values[0]:
                                    val = this_locals_values[0].split(' = ')[-1]
                                    local_value = f'{vari} = {val}'
                                    if local_value not in new_trace[-1]:
                                        new_trace[-1].append(local_value)
                                    if vari not in defined_locals:
                                        defined_locals.append(vari)
                        traces.append(new_trace)
                        f_trace = open(f_trace_file, 'a')
                        print_step_info(f_trace, new_trace, lang)
                        f_trace.close()
            if_second = False

        if 'Breakpoint ' in pre_line_info and func_name in pre_line_info and file_name in pre_line_info:
            this_trace[-1] = []
        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace, lang)
        f_trace.close()

        if if_first:
            if_first = False
            if_second = True

        if 'Breakpoint ' in pre_line_info and func_name in pre_line_info and file_name in pre_line_info:
            if_first = False
            if_second = True
            defined_locals = []
            while current_line_id != func_line_id + 1 and current_line_id != func_line_id + 2:
                cmd.sendline(f"next")
                time.sleep(0.2)
                cmd.expect('.+')
                current_line_info = cmd.match.string.decode()
                current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
                print(current_line_info)
                raise_exception_cpp(current_line_info, file_name)
                cmd.sendline(f"frame")
                time.sleep(0.2)
                cmd.expect('.+')
                line_id_info = cmd.match.string.decode()
                line_id_info = re.sub(r'\x1b\[[0-9;]*m', '', line_id_info)
                print(line_id_info)
                current_line_id = find_line_id_cpp(line_id_info)

            pre_line_info = copy.deepcopy(current_line_info)
            cmd.sendline(f"next")
            time.sleep(0.2)
            cmd.expect('.+')
            current_line_info = cmd.match.string.decode()
            current_line_info = re.sub(r'\x1b\[[0-9;]*m', '', current_line_info)
            print(current_line_info)
            raise_exception_cpp(current_line_info, file_name)
            cmd.sendline(f"frame")
            time.sleep(0.2)
            cmd.expect('.+')
            line_id_info = cmd.match.string.decode()
            line_id_info = re.sub(r'\x1b\[[0-9;]*m', '', line_id_info)
            print(line_id_info)
            current_line_id = find_line_id_cpp(line_id_info)

    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def extract_trace_java(file_name, start_time, time_limit, tmp_dir, f_trace_file, max_steps, lang, ID):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.java'
    f_code = open(file_path)
    code_lines = f_code.readlines()
    f_code.close()
    bias_brace = 0
    func_line_id = -1
    for line_id, code_line in enumerate(code_lines):
        if 'f_filled' in code_line and 'f_gold' not in code_line:
            func_line_id = line_id
            if code_lines[line_id + 1].strip() == '{':
                bias_brace = 1
            break
    if func_line_id == -1:
        raise Exception('Not found func line_id!')
    try:
        p = Popen(['/usr/lib/jvm/java-17-openjdk-amd64/bin/java', '--module-path',
                   '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
                   '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
        stdout, stderr_data = p.communicate(timeout=5)
        p.kill()
    except:
        p.kill()
        return []

    p = Popen(['/usr/lib/jvm/java-17-openjdk-amd64/bin/java', '-Xdebug',
               '-Xrunjdwp:transport=dt_socket,server=y,address=6001', '--module-path',
               '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
               '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)

    compile_cmd = f"jdb -attach 6001"
    cmd = pexpect.spawn(compile_cmd)
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_java(a, file_name)
    cmd.sendline(f"stop in {file_name}.{func_name}")
    time.sleep(5)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_java(a, file_name)
    cmd.sendline(f"run")
    time.sleep(5)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    print(current_line_info)
    raise_exception_java(current_line_info, file_name)

    pre_line_info = copy.deepcopy(current_line_info)

    traces_list = []
    traces = []
    if_first = True
    for i in range(max_steps):
        print('LOGGGGG:', ID)

        this_trace = []
        line_id = find_line_id_java(pre_line_info)
        print(f"{color.BOLD}{color.YELLOW}{line_id}{color.END}")
        this_trace.append(pre_line_info)

        if if_first:
            this_trace.append(0)
        else:
            this_trace.append(int(line_id) - func_line_id - 1)

        if f'{file_name}.{func_name}()' not in current_line_info:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        if time.time() - start_time > time_limit:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        cmd.sendline(f"locals")
        time.sleep(0.2)
        cmd.expect('.+')
        args_values_info = cmd.match.string.decode()
        print(args_values_info)
        raise_exception_java(args_values_info, file_name)
        args_values = []
        for args_values_line in args_values_info.split('\n'):
            if args_values_line == 'main[1] ':
                break
            if args_values_line in ['locals\r', '方法参数:\r', '本地变量:\r']:
                continue
            elif '= instance of' in args_values_line and '[][' in args_values_line and args_values_line.count('[') == 2:
                var_name = args_values_line.split(' = ')[0].strip()
                x = re.search('\[\]\[(\d+)\]', args_values_line)
                if x:
                    if_success = True
                    args_value = var_name + ' = ['
                    for this_indx in range(int(x.group(1))):
                        cmd.sendline(f"dump {var_name}[{this_indx}]")
                        time.sleep(0.2)
                        cmd.expect('.+')
                        this_args_values_info = cmd.match.string.decode()
                        print(this_args_values_info)
                        raise_exception_java(this_args_values_info, file_name)
                        if '= instance of' not in this_args_values_info:
                            this_match = re.search(r"= ((.|\r\n)+)\r\nmain\[1\]", this_args_values_info)
                            if this_match:
                                this_args_value = this_match.group(1).replace("\r\n", "") + ", "
                                args_value = args_value + this_args_value
                            else:
                                if_success = False
                        else:
                            if_success = False
                    if if_success:
                        args_value = args_value.replace('{', '[')
                        args_value = args_value.replace('}', ']')
                        args_value = args_value[:-2] + ']'
                        args_values.append(args_value)
            elif '= instance of' in args_values_line and '[' in args_values_line and args_values_line.count('[') == 1:
                var_name = args_values_line.split(' = ')[0].strip()
                cmd.sendline(f"dump {var_name}")
                time.sleep(0.2)
                cmd.expect('.+')
                this_args_values_info = cmd.match.string.decode()
                print(this_args_values_info)
                raise_exception_java(this_args_values_info, file_name)
                args_value_lines = this_args_values_info.split('\r\n')
                args_value = ''.join(args_value_lines[1:-1])
                args_value = args_value.replace('{', '[')
                args_value = args_value.replace('}', ']')
                args_values.append(args_value.strip())
            elif '= instance of java.util.HashMap' in args_values_line:
                var_name = args_values_line.split(' = ')[0].strip()
                cmd.sendline(f"print {var_name}")
                time.sleep(0.2)
                cmd.expect('.+')
                this_args_values_info = cmd.match.string.decode()
                print(this_args_values_info)
                raise_exception_java(this_args_values_info, file_name)
                args_value_lines = this_args_values_info.split('\r\n')
                args_value = ''.join(args_value_lines[1:-1])
                args_value = args_value.replace('"{', '{')
                args_value = args_value.replace('}"', '}')
                parts = args_value.split('=', 1)
                result = parts[0] + '=' + parts[1].replace('=', ': ')
                args_values.append(result.strip())
            elif '= instance of java.util.ArrayDeque' in args_values_line:
                var_name = args_values_line.split(' = ')[0].strip()
                cmd.sendline(f"print {var_name}")
                time.sleep(0.2)
                cmd.expect('.+')
                this_args_values_info = cmd.match.string.decode()
                print(this_args_values_info)
                raise_exception_java(this_args_values_info, file_name)
                args_value_lines = this_args_values_info.split('\r\n')
                args_value = ''.join(args_value_lines[1:-1])
                args_value = args_value.replace('"[', '[')
                args_value = args_value.replace(']"', ']')
                args_values.append(args_value.strip())
            elif '= instance of' in args_values_line:
                continue
            else:
                args_values.append(args_values_line.strip('\r'))
        pocess_values_lists = []
        for values_list in args_values:
            variable = values_list.split('=')[0].strip()
            value = values_list.split('=')[1].strip()
            if value.startswith('{') and value.endswith('}'):
                this_value = value.replace('{', '[')
                this_value = this_value.replace('}', ']')
                pocess_values_lists.append(f'{variable} = {this_value}')
            else:
                pocess_values_lists.append(values_list)
        for args_value in pocess_values_lists:
            print(f"{color.BOLD}{color.BLUE}{args_value}{color.END}")
        this_trace.append(args_values)

        traces.append(this_trace)

        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace, lang)
        f_trace.close()

        if if_first:
            this_line_id = int(line_id) - func_line_id - 1
            if bias_brace:
                if this_line_id > 2:
                    for this_id in range(2, this_line_id):
                        new_trace = ['', this_id, []]
                        traces.append(new_trace)
                        f_trace = open(f_trace_file, 'a')
                        print_step_info(f_trace, new_trace, lang)
                        f_trace.close()
            else:
                if this_line_id > 1:
                    for this_id in range(1, this_line_id):
                        new_trace = ['', this_id, []]
                        traces.append(new_trace)
                        f_trace = open(f_trace_file, 'a')
                        print_step_info(f_trace, new_trace, lang)
                        f_trace.close()
            if_first = False

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        print(current_line_info)
        raise_exception_java(current_line_info, file_name)

    cmd.close()
    p.kill()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def extract_trace_python(file_name, start_time, time_limit, tmp_dir, f_trace_file, max_steps, lang):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.py'
    f_code = open(file_path)
    code_lines = f_code.readlines()
    f_code.close()
    func_line_id = -1
    for line_id, code_line in enumerate(code_lines):
        if 'f_filled' in code_line and 'f_gold' not in code_line:
            func_line_id = line_id
            break
    if func_line_id == -1:
        raise Exception('Not found func line_id!')
    try:
        p = Popen(['python3', '-m', 'py_compile', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
        stdout, stderr_data = p.communicate(timeout=5)
        p.kill()
    except:
        p.kill()
        return []

    compile_cmd = f"python -m pdb {file_path}"
    cmd = pexpect.spawn(compile_cmd)
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_python(a, file_name)
    cmd.sendline(f"b {func_name}")
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_python(a, file_name)
    cmd.sendline(f"c")
    time.sleep(3)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    print(current_line_info)
    raise_exception_python(current_line_info, file_name)

    pre_line_id = func_line_id + 1
    pre_line_info = copy.deepcopy(current_line_info)

    traces_list = []
    traces = []
    for i in range(max_steps):

        this_trace = []
        print(f"{color.BOLD}{color.YELLOW}{pre_line_id}{color.END}")
        this_trace.append(pre_line_info)
        this_trace.append(int(pre_line_id) - func_line_id - 1)

        if f'){func_name}' not in current_line_info:
            this_trace.append([{}])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        if time.time() - start_time > time_limit:
            this_trace.append([{}])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break

        cmd.sendline(f"locals()")
        time.sleep(0.5)
        cmd.expect('.+')
        args_values_info = cmd.match.string.decode()
        print(args_values_info)
        while not args_values_info.endswith('(Pdb) '):
            time.sleep(0.5)
            cmd.expect('.+')
            this_args_values_info = cmd.match.string.decode()
            print(this_args_values_info)
            args_values_info = args_values_info + this_args_values_info
        if not args_values_info.endswith('(Pdb) '):
            new_args_info_list = args_values_info.split(', \'')
            new_args_values_info = ', \''.join(new_args_info_list[:-1]) + '}\r\n(Pdb) '
            args_values_info = new_args_values_info
            print('Updated_args_values_info:', args_values_info)
        raise_exception_python(args_values_info, file_name)
        args_values = []
        args_value = re.search('\{.*\}', args_values_info)
        if args_value:
            args_value_string = args_value.group()
            if ': -inf' in args_value_string:
                args_value_string = args_value_string.replace(': -inf', ': \"-inf\"')
            if ': inf' in args_value_string:
                args_value_string = args_value_string.replace(': inf', ': \"inf\"')
            print(f"{color.BOLD}{color.GREEN}{args_value_string}{color.END}")
            this_args_value = re.search('\'[^\s]+\': <class \'[^\s]+\'>', args_value_string)
            if this_args_value:
                if ', ' + this_args_value.group() in args_value_string:
                    args_value_string = args_value_string.replace(', ' + this_args_value.group(), '')
                elif this_args_value.group() + ', ' in args_value_string:
                    args_value_string = args_value_string.replace(this_args_value.group() + ', ', '')
            if ", '__exception__': (<class 'IndexError'>, IndexError('string index out of range'))" in args_value_string:
                args_value_string = args_value_string.replace(
                    ", '__exception__': (<class 'IndexError'>, IndexError('string index out of range'))", '')
            if ": deque([" in args_value_string and '])' in args_value_string:
                args_value_string = args_value_string.replace(": deque([", ': [')
                args_value_string = args_value_string.replace("])", ']')
            args_values.append(ast.literal_eval(args_value_string))
        for args_value in args_values:
            print(f"{color.BOLD}{color.BLUE}{args_value}{color.END}")
        this_trace.append(args_values)

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"next")
        time.sleep(0.5)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        print(current_line_info)
        raise_exception_python(current_line_info, file_name)

        pre_line_id = find_line_id_python(pre_line_info)

        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace, lang)
        f_trace.close()
    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def check_item_len(val, lang):
    if lang == 'C++':
        items = val[1:-1].split(', ')
        if_1 = True
        new_val = '"'
        for item in items:
            this_items = item.split(' ')
            if len(this_items) == 2 and this_items[0].isdigit() and len(this_items[1]) == 3 and this_items[1][
                0] == "'" and this_items[1][-1] == "'":
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
        syb_val = val[val.index(this_match_str) + len(this_match_str):]
        repeat_str = repeat_item
        for _ in range(repeat_time - 1):
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


def change(info, lang):
    items = info.split('=')
    var = items[0].strip()
    val = '='.join(items[1:]).strip()
    new_val = ''
    if len(items) == 2:
        if val.endswith(
                '.0') and '[' not in val and ']' not in val and '{' not in val and '}' not in val and ',' not in val:
            new_val = val[:-2]
        elif '.' in val and '[' not in val and ']' not in val and '{' not in val and '}' not in val and ',' not in val:
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
        elif val.count('[') == 1 and val.count(']') == 1 and val[0] == '[' and val[-1] == ']' and \
                check_item_len(val, lang)[0]:
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


def print_step_info(f_trace, step, lang):
    print(f'Line: {step[1]}', file=f_trace)
    if lang == 'Python':
        for vari, val in step[2][0].items():
            if type(val) == str:
                new_info = change(f'{vari} = \"{val}\"', lang)
                if new_info:
                    print(new_info, file=f_trace)
            else:
                new_info = change(f'{vari} = {val}', lang)
                if new_info:
                    print(f'{vari} = {val}', file=f_trace)
        print('', file=f_trace)
    else:
        for var in step[2]:
            new_info = change(f'{var.strip()}', lang)
            if new_info:
                print(new_info, file=f_trace)
        print('', file=f_trace)


def compare_stepbystep_for_trace(source_traces, trans_traces, source_lang, target_lang, line_M, len_s, len_t,
                                 source_lines, trans_lines):
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
        if not s_suc:
            if_step = False
            diff_info.append(['diff_path'])
        elif not t_suc:
            if_step = False
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
    return diff_info


def main(source_lang, target_lang, lang, tmp_dir, path_to_map, path_to_code, target_model_name):
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    ext = extensions[lang]
    source_ext = extensions[source_lang]
    target_ext = extensions[target_lang]

    code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}-script-for-trace'
    args_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace'
    source_trace_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces'
    trace_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}-traces'
    log_file = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}.txt'
    t_passinfo_dir = f't_passinfo/{target_model_name}-{source_lang}-{target_lang}'

    generated_map = loadMap(f'{path_to_map}/{target_model_name}-{source_lang}-{target_lang}-Ours-mapping')

    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(trace_dir, exist_ok=True)

    all_code_files = os.listdir(code_dir)
    IDs = [code_file.split('.')[0] for code_file in all_code_files]
    exist_IDs = [code_file.split('.')[0] for code_file in os.listdir(trace_dir)]
    IDs.sort()
    for ID in tqdm(IDs):
        if ID in exist_IDs:
            continue
        t_passinfo_line = open(f'{t_passinfo_dir}/{ID}.txt', 'r').readlines()[0]
        t_passinfo_num = int(t_passinfo_line.strip())
        t_passinfo_num = max(0, t_passinfo_num - 5)
        script_path = f'{code_dir}/{ID}.{ext}'
        arg_path = f'{args_dir}/{ID}.args'

        listarg2len = {}
        source_lang_trace_vars = []
        if lang == 'C++':

            source_code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}'
            trans_code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}'
            _, source_lines = read_code(f'{source_code_dir}/{ID}.{source_ext}', source_lang)
            _, trans_lines = read_code(f'{trans_code_dir}/{ID}.{target_ext}', target_lang)

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
                                                          trans_varilable_names, only_block=False,
                                                          exclude_last_child=False,
                                                          only_path=True, fun_block=0)
                ori_trans_stmt_info_lists = reduce_pos_of_java_tree(ori_trans_stmt_info_lists)
                trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                    ori_trans_stmt_info_lists)
            elif target_lang == 'Python':
                ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                          trans_varilable_names, only_block=False,
                                                          exclude_last_child=False,
                                                          only_path=True, fun_block=0)
                trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                    ori_trans_stmt_info_lists)
            elif target_lang == 'C++':
                ori_trans_stmt_info_lists = traverse_tree(trans_tree.root_node, target_lang, trans_lines,
                                                          trans_varilable_names, only_block=False,
                                                          exclude_last_child=False,
                                                          only_path=True, fun_block=0)
                trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos, _ = filter_traverse_tree_paths(
                    ori_trans_stmt_info_lists)

            source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree, source_stmt_list_pos = rephrase_stmt_trees(
                source_lang, source_stmt_list, source_stmt_list_depth, this_source_trees, this_source_path2tree,
                source_stmt_list_pos, source_lines)
            trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree, trans_stmt_list_pos = rephrase_stmt_trees(
                target_lang, trans_stmt_list, trans_stmt_list_depth, this_trans_trees, this_trans_path2tree,
                trans_stmt_list_pos, trans_lines)

            line_M = {}
            for s_id in range(len(source_lines)):
                for t_id in range(len(trans_lines)):
                    line_M[f'{s_id}-{t_id}'] = False
            for pair in generated_map[ID]:
                line_M[f'{pair[0]}-{pair[1]}'] = True

            source_lang_traces = load_trace(f'{source_trace_dir}/{ID}.txt')
            for trace in source_lang_traces:
                var_vals = read_var_val(trace[1:])
                for k, v in var_vals.items():
                    if k not in source_lang_trace_vars:
                        source_lang_trace_vars.append(k)
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
                        print(f"{color.BOLD}{color.YELLOW}{arg}{color.END}")
                        if ' ' not in arg:
                            args.append([arg.strip(), False])
                        else:
                            if '*' in arg:
                                args.append([arg.strip().split('*')[-1].strip(), True])
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

        exist_files = os.listdir(tmp_dir)
        for exist_file in exist_files:
            if os.path.isdir(f'{tmp_dir}/{exist_file}'):
                shutil.rmtree(f'{tmp_dir}/{exist_file}')
            else:
                os.remove(f'{tmp_dir}/{exist_file}')
        shutil.copyfile(script_path, f'{tmp_dir}/{ID}.{ext}')

        traces_list = []
        for i in range(1):
            f_log = open(log_file, 'a')
            print(f'{ID}-{i}', file=f_log)
            f_log.close()
            try:
                f_trace = open(f'{trace_dir}/{ID}.txt', 'w')
                f_trace.close()
                time_limit = 600
                start_time = time.time()
                if lang == 'C++':
                    if source_lang_trace_vars:
                        traces_list = extract_trace_cpp(ID, start_time, time_limit, tmp_dir, trans_stmt_list,
                                                        source_stmt_list_pos, listarg2len, source_lang_trace_vars,
                                                        f'{trace_dir}/{ID}.txt', 10000, lang, t_passinfo_num,
                                                        source_lang, target_lang, line_M, source_lines, trans_lines,
                                                        path_to_code, target_model_name, ID)
                elif lang == 'Java':
                    if ID.startswith('CTCI_') or ID.isdigit():
                        shutil.copyfile(script_path, f'{tmp_dir}/MAIN_FUNC.{ext}')
                        traces_list = extract_trace_java('MAIN_FUNC', start_time, time_limit, tmp_dir,
                                                         f'{trace_dir}/{ID}.txt', 10000, lang, ID)
                    else:
                        traces_list = extract_trace_java(ID, start_time, time_limit, tmp_dir, f'{trace_dir}/{ID}.txt',
                                                         10000, lang, ID)
                elif lang == 'Python':
                    traces_list = extract_trace_python(ID, start_time, time_limit, tmp_dir, f'{trace_dir}/{ID}.txt',
                                                       10000, lang)
                if not traces_list:
                    raise Exception('No trace!')
                break
            except:
                continue
        if not traces_list:
            continue
        f_trace = open(f'{trace_dir}/{ID}.txt', 'w')
        for step in traces_list[0]:
            print_step_info(f_trace, step, lang)
        f_trace.close()


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
        "--path_to_code",
        default='CODE-round2',
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
        "--tmp_dir",
        default='tmp',
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
    args = parser.parse_args()
    path_to_code = args.path_to_code
    source_lang = args.source_lang
    target_model_name = args.target_model_name
    tmp_dir = args.tmp_dir
    path_to_map = args.path_to_map
    target_lang = 'C++'

    main(source_lang, target_lang, source_lang, tmp_dir, path_to_map, path_to_code, target_model_name)

    main(source_lang, target_lang, target_lang, tmp_dir, path_to_map, path_to_code, target_model_name)

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


def find_values_cpp(txt, listarg2len):
    lines = txt.split('\n')
    available_lines = lines[1:]
    only_single_line = False
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


def extract_trace_cpp(file_name, tmp_dir, listarg2len, f_trace_file, max_steps):
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
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"break {func_name}")
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_cpp(a, file_name)
    cmd.sendline(f"run")
    time.sleep(3)
    cmd.expect('.+')
    current_line_info = cmd.match.string.decode()
    print(current_line_info)
    raise_exception_cpp(current_line_info, file_name)
    cmd.sendline(f"frame")
    time.sleep(0.2)
    cmd.expect('.+')
    line_id_info = cmd.match.string.decode()
    print(line_id_info)
    pre_line_info = copy.deepcopy(current_line_info)
    func_line_id = find_line_id_cpp(line_id_info)
    current_line_id = func_line_id
    while current_line_id != func_line_id + 1 and current_line_id != func_line_id + 2:
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        print(current_line_info)
        raise_exception_cpp(current_line_info, file_name)
        cmd.sendline(f"frame")
        time.sleep(0.2)
        cmd.expect('.+')
        line_id_info = cmd.match.string.decode()
        print(line_id_info)
        current_line_id = find_line_id_cpp(line_id_info)
    traces_list = []
    traces = []
    if_first = True
    defined_locals = []
    for i in range(max_steps):

        this_trace = []
        line_id = find_line_id_cpp(pre_line_info)
        print(f"{color.BOLD}{color.YELLOW}{line_id}{color.END}")
        this_trace.append(pre_line_info)
        this_trace.append(int(line_id)-func_line_id)

        cmd.sendline(f"frame")
        time.sleep(0.2)
        cmd.expect('.+')
        line_id_info = cmd.match.string.decode()
        print(line_id_info)
        raise_exception_cpp(line_id_info, file_name)
        if line_id_info.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
            cmd.sendline(f"q")
            time.sleep(0.2)
            cmd.expect('.+')
            a = cmd.match.string.decode()
            print(a)
            raise_exception_cpp(a, file_name)
        if f' {func_name}' not in line_id_info.split('\n')[1]:
            this_trace.append([])
            traces.append(this_trace)
            traces_list.append(traces)
            traces = []
            break
            # continue
        pre_code_tokens = extract_cpp_code_line(pre_line_info, file_name)
        cur_code_tokens = extract_cpp_code_line(current_line_info, file_name)

        cmd.sendline(f"info args")
        time.sleep(0.2)
        cmd.expect('.+')
        args_values_infos = ''
        args_values_info = cmd.match.string.decode()
        print(args_values_info)
        raise_exception_cpp(args_values_info, file_name)
        args_values_infos += args_values_info
        while args_values_info.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
            args_values_infos = args_values_infos.replace('--Type <RET> for more, q to quit, c to continue without paging--', '')
            cmd.sendline(f"<RET>")
            time.sleep(0.2)
            cmd.expect('.+')
            args_values_info = cmd.match.string.decode()
            print(args_values_info)
            raise_exception_cpp(args_values_info, file_name)
            args_values_info = args_values_info.replace('<RET>\r\n', '')
            args_values_infos += args_values_info

        args_values = find_values_cpp(args_values_infos, listarg2len)
        for args_value in args_values:
            print(f"{color.BOLD}{color.BLUE}{args_value}{color.END}")

        this_trace.append(args_values)

        cmd.sendline(f"info locals")
        time.sleep(0.2)
        cmd.expect('.+')
        locals_values_infos = ''
        locals_values_info = cmd.match.string.decode()
        print(locals_values_info)
        raise_exception_cpp(locals_values_info, file_name)
        locals_values_infos += locals_values_info
        while locals_values_infos.endswith('--Type <RET> for more, q to quit, c to continue without paging--'):
            locals_values_infos = locals_values_infos.replace('--Type <RET> for more, q to quit, c to continue without paging--', '')
            cmd.sendline(f"<RET>")
            time.sleep(0.2)
            cmd.expect('.+')
            locals_values_info = cmd.match.string.decode()
            print(locals_values_info)
            raise_exception_cpp(locals_values_info, file_name)
            locals_values_info = locals_values_info.replace('<RET>\r\n', '')
            locals_values_infos += locals_values_info

        filter_locals_values = []
        locals_values = find_values_cpp(locals_values_infos, listarg2len)
        for local_value in locals_values:
            vari = local_value.split(' = ')[0]
            if vari in defined_locals:
                filter_locals_values.append(local_value)
                print(f"{color.BOLD}{color.GREEN}{local_value}{color.END}")
            else:
                if vari in pre_code_tokens:
                    defined_locals.append(vari)
                    filter_locals_values.append(local_value)
                    print(f"{color.BOLD}{color.GREEN}{local_value}{color.END}")
        if not if_first:
            this_trace[-1].extend(filter_locals_values)

        listargs_values = []
        for arg, arg_len in listarg2len.items():


            cmd.sendline(f"p *{arg}@{arg_len}")
            time.sleep(0.2)
            cmd.expect('.+')
            locals_values_infos = ''
            locals_values_info = cmd.match.string.decode()
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
                print(locals_values_info)
                raise_exception_cpp(locals_values_info, file_name)
                locals_values_info = locals_values_info.replace('<RET>\r\n', '')
                locals_values_infos += locals_values_info

            locals_values = find_values_cpp_singlevari(locals_values_infos)
            filter_locals_values = []
            for local_value in locals_values:
                vari = local_value.split(' = ')[0]
                if vari in defined_locals:
                    filter_locals_values.append(local_value)
                    print(f"{color.BOLD}{color.GREEN}{local_value}{color.END}")
                else:
                    if vari in pre_code_tokens:
                        defined_locals.append(vari)
                        filter_locals_values.append(local_value)
                        print(f"{color.BOLD}{color.GREEN}{local_value}{color.END}")
            listargs_values.extend(filter_locals_values)
        this_trace[-1].extend(listargs_values)

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        print(current_line_info)
        raise_exception_cpp(current_line_info, file_name)

        cmd.sendline(f"frame")
        time.sleep(0.2)
        cmd.expect('.+')
        line_id_info = cmd.match.string.decode()
        print(line_id_info)
        current_line_id = find_line_id_cpp(line_id_info)

        if_first = False

        if 'Breakpoint ' in current_line_info and func_name in current_line_info and file_name in current_line_info:
            if_first = True
            defined_locals = []
            while current_line_id != func_line_id + 1 and current_line_id != func_line_id + 2:
                cmd.sendline(f"next")
                time.sleep(0.2)
                cmd.expect('.+')
                current_line_info = cmd.match.string.decode()
                print(current_line_info)
                raise_exception_cpp(current_line_info, file_name)
                cmd.sendline(f"frame")
                time.sleep(0.2)
                cmd.expect('.+')
                line_id_info = cmd.match.string.decode()
                print(line_id_info)
                current_line_id = find_line_id_cpp(line_id_info)

        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace)
        f_trace.close()

    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def extract_trace_java(file_name, tmp_dir, f_trace_file, max_steps):
    func_name = 'f_filled'
    file_path = f'{tmp_dir}/{file_name}.java'
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
        p = Popen(['java', '--module-path', '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
                   '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
        stdout, stderr_data = p.communicate(timeout=5)
        p.kill()
    except:
        p.kill()
        return []

    p = Popen(['java', '-Xdebug', '-Xrunjdwp:transport=dt_socket,server=y,address=6001', '--module-path',
               '/home/ubuntu/openjfx-17.0.11_linux-x64_bin-sdk/javafx-sdk-17.0.11/lib',
               '--add-modules', 'javafx.controls', file_path], cwd=os.getcwd(), stdout=PIPE, stderr=PIPE)
    compile_cmd = f"jdb -attach 6001"
    cmd = pexpect.spawn(compile_cmd)
    time.sleep(3)
    cmd.expect('.+')
    a = cmd.match.string.decode()
    print(a)
    raise_exception_java(a, file_name)
    cmd.sendline(f"stop at {file_name}.{func_name}")
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

    pre_line_id = func_line_id + 1
    pre_line_info = copy.deepcopy(current_line_info)

    traces_list = []
    traces = []
    for i in range(max_steps):

        this_trace = []
        print(f"{color.BOLD}{color.YELLOW}{pre_line_id}{color.END}")
        this_trace.append(pre_line_info)
        this_trace.append(int(pre_line_id)-func_line_id-1)

        if f'{file_name}.{func_name}()' not in current_line_info:
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

        pre_line_info = copy.deepcopy(current_line_info)
        cmd.sendline(f"next")
        time.sleep(0.2)
        cmd.expect('.+')
        current_line_info = cmd.match.string.decode()
        print(current_line_info)
        raise_exception_java(current_line_info, file_name)

        pre_line_id = find_line_id_java(pre_line_info)

        traces.append(this_trace)
        f_trace = open(f_trace_file, 'a')
        print_step_info(f_trace, this_trace)
        f_trace.close()

    cmd.close()
    p.kill()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def extract_trace_python(file_name, tmp_dir, f_trace_file, max_steps):
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
            this_trace.append(int(pre_line_id)-func_line_id-1)

            if f'){func_name}' not in current_line_info:
                this_trace.append([{}])
                traces.append(this_trace)
                traces_list.append(traces)
                traces = []
                break
                # continue
            cmd.sendline(f"locals()")
            time.sleep(0.5)
            cmd.expect('.+')
            args_values_info = cmd.match.string.decode()
            print(args_values_info)
            while not args_values_info.endswith('(Pdb) '):
                # cmd.sendline(f"\n")
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
                    args_value_string = args_value_string.replace(", '__exception__': (<class 'IndexError'>, IndexError('string index out of range'))", '')
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
            print_step_info(f_trace, this_trace)
            f_trace.close()
    cmd.close()
    if not traces_list:
        traces_list.append(traces)
    return traces_list


def print_step_info(f_trace, step):
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



def main(log_file, lang, code_dir, args_dir, trace_dir, tmp_dir):
    extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
    ext = extensions[lang]
    all_code_files = os.listdir(code_dir)
    IDs = [code_file.split('.')[0] for code_file in all_code_files]
    IDs.sort()
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(trace_dir, exist_ok=True)
    for ID in tqdm(IDs):
        script_path = f'{code_dir}/{ID}.{ext}'
        arg_path = f'{args_dir}/{ID}.args'
        listarg2len = {}
        if lang == 'C++':
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
                if lang == 'C++':
                    traces_list = extract_trace_cpp(ID, tmp_dir, listarg2len, f'{trace_dir}/{ID}.txt', 10000)
                elif lang == 'Java':
                    traces_list = extract_trace_java(ID, tmp_dir, f'{trace_dir}/{ID}.txt', 10000)
                elif lang == 'Python':
                    traces_list = extract_trace_python(ID, tmp_dir, f'{trace_dir}/{ID}.txt', 10000)
                if not traces_list:
                    raise Exception('No trace!')
                break
            except:
                continue
        if not traces_list:
            continue
        f_trace = open(f'{trace_dir}/{ID}.txt', 'w')
        for step in traces_list[0]:
            print_step_info(f_trace, step)
        f_trace.close()
        print('')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source_lang",
        default='Java',
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
    parser.add_argument(
        "--target_model_name",
        default='TransCoder',
        type=str,
        required=False,
        help=""
    )
    parser.add_argument(
        "--tmp_dir",
        default='tmp',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    path_to_code = args.path_to_code
    path_to_DATABASE = args.path_to_DATABASE
    source_lang = args.source_lang
    target_model_name = args.target_model_name
    tmp_dir = args.tmp_dir

    lang = 'C++'
    target_lang = 'C++'
    code_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}-script-for-trace'
    args_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{target_lang}-args-for-trace'
    trace_dir = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}-traces'
    log_file = f'{path_to_code}/{target_model_name}-data/{source_lang}-{target_lang}-{lang}.txt'
    main(log_file, lang, code_dir, args_dir, trace_dir, tmp_dir)
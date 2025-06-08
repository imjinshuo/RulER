import os
import argparse

numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

def read_trace(file):
    lines = open(file, encoding='utf-8').readlines()
    trace = []
    traces = []
    for line in lines:
        if line.strip():
            trace.append(line.strip())
        else:
            traces.append(trace)
            trace = []
    if trace:
        traces.append(trace)
        trace = []
    return traces


def save_trace(file, traces):
    f = open(file, 'w', encoding='utf-8')
    for trace in traces:
        for item in trace:
            print(item.strip(), file=f)
        print('', file=f)
    f.close()


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

import copy
import re
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


def change(info, lang):
    items = info.split('=')
    var = items[0].strip()
    val = '='.join(items[1:]).strip()
    new_val = ''
    if len(items) == 2:
        if val.endswith('.0') and '[' not in val and ']' not in val and '{' not in val and '}' not in val and ',' not in val:
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
            # if 'std' in new_val:
            #     print('')
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_code",
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()
    path_to_code = args.path_to_code
    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for source_lang in ['Java', 'Python']:
            target_lang = 'C++'
            for lang in [target_lang]:
                trace_dir = f'{path_to_code}/{model_name}-data/{source_lang}-{target_lang}-{lang}-traces'
                save_trace_dir = f'{path_to_code}/{model_name}-data/{source_lang}-{target_lang}-{lang}-traces'
                os.makedirs(save_trace_dir, exist_ok=True)

                trace_files = os.listdir(trace_dir)
                trace_files.sort()

                for file in trace_files:
                    traces = read_trace(f'{trace_dir}/{file}')
                    new_traces = []
                    for trace in traces:
                        new_trace = [trace[0]]
                        for info in trace[1:]:
                            new_info = change(info, lang)
                            if new_info:
                                new_trace.append(new_info)
                        new_traces.append(new_trace)
                    save_trace(f'{save_trace_dir}/{file}', new_traces)



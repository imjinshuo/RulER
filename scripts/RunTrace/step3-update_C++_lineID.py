import os
import argparse


def update_lineID(file):
    f = open(file)
    lines = f.readlines()
    f.close()

    traces = []
    step = []
    for line in lines:
        if line.strip():
            step.append(line.strip())
        else:
            traces.append(step)
            step = []

    new_traces = []
    for step in traces:
        if int(step[0][len('Line: '):]) != 0:
            this_step = ['Line: ' + str(int(step[0][len('Line: '):]) + 1)]
            for item in step[1:]:
                this_step.append(item)
            new_traces.append(this_step)
        else:
            new_traces.append(step)
    return new_traces


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
            extensions = {'Python': 'py', 'C++': 'cpp', 'Java': 'java'}
            source_ext = extensions[source_lang]
            target_ext = extensions[target_lang]

            dir = f'{path_to_code}/{model_name}-data'
            trace_dir = f'{dir}/{source_lang}-{target_lang}-{target_lang}-traces'

            files = os.listdir(trace_dir)
            for file in files:
                ID = file.split('.')[0]
                code_file = f'{dir}/{source_lang}-{target_lang}/{ID}.{target_ext}'
                code_f = open(code_file, 'r')
                code_lines = code_f.readlines()
                code_f.close()
                if code_lines[1].strip() == '{':
                    f = open(f'{dir}/{source_lang}-{target_lang}-{target_lang}-traces/{file}')
                    lines = f.readlines()
                    f.close()

                    traces = []
                    step = []
                    for line in lines:
                        if line.strip():
                            step.append(line.strip())
                        else:
                            traces.append(step)
                            step = []

                    new_traces = []
                    for step in traces:
                        if int(step[0][len('Line: '):]) != 0:
                            this_step = ['Line: ' + str(int(step[0][len('Line: '):]) + 1)]
                            for item in step[1:]:
                                this_step.append(item)
                            new_traces.append(this_step)
                        else:
                            new_traces.append(step)

                    new_new_trace = []
                    start_id = 2
                    for step in new_traces:
                        if int(step[0][len('Line: '):]) == 0:
                            new_new_trace.append(step)
                            continue
                        if len(new_new_trace) == 1:
                            this_line_id = int(step[0][len('Line: '):])
                            if this_line_id > start_id:
                                for this_id in range(start_id, this_line_id):
                                    this_step = ['Line: ' + str(this_id)]
                                    new_new_trace.append(this_step)
                            new_new_trace.append(step)
                        else:
                            new_new_trace.append(step)

                    f = open(f'{dir}/{source_lang}-{target_lang}-{target_lang}-traces/{file}', 'w')
                    for step in new_new_trace:
                        for item in step:
                            print(item, file=f)
                        print('', file=f)
                    f.close()
                    print(file)
                else:
                    f = open(f'{dir}/{source_lang}-{target_lang}-{target_lang}-traces/{file}')
                    lines = f.readlines()
                    f.close()

                    traces = []
                    step = []
                    for line in lines:
                        if line.strip():
                            step.append(line.strip())
                        else:
                            traces.append(step)
                            step = []
                    new_traces = traces[:]

                    new_new_trace = []
                    start_id = 1
                    for step in new_traces:
                        if int(step[0][len('Line: '):]) == 0:
                            new_new_trace.append(step)
                            continue
                        if len(new_new_trace) == 1:
                            this_line_id = int(step[0][len('Line: '):])
                            if this_line_id > start_id:
                                for this_id in range(start_id, this_line_id):
                                    this_step = ['Line: ' + str(this_id)]
                                    new_new_trace.append(this_step)
                            new_new_trace.append(step)
                        else:
                            new_new_trace.append(step)

                    f = open(f'{dir}/{source_lang}-{target_lang}-{target_lang}-traces/{file}', 'w')
                    for step in new_new_trace:
                        for item in step:
                            print(item, file=f)
                        print('', file=f)
                    f.close()
                    print(file)

                if source_lang == 'Java':
                    f = open(f'{dir}/{source_lang}-{target_lang}-{source_lang}-traces/{file}')
                    lines = f.readlines()
                    f.close()

                    traces = []
                    step = []
                    for line in lines:
                        if line.strip():
                            step.append(line.strip())
                        else:
                            traces.append(step)
                            step = []
                    new_traces = traces[:]

                    new_new_trace = []
                    start_id = 1
                    for step in new_traces:
                        if int(step[0][len('Line: '):]) == 0:
                            new_new_trace.append(step)
                            continue
                        if len(new_new_trace) == 1:
                            this_line_id = int(step[0][len('Line: '):])
                            if this_line_id > start_id:
                                for this_id in range(start_id, this_line_id):
                                    this_step = ['Line: ' + str(this_id)]
                                    new_new_trace.append(this_step)
                            new_new_trace.append(step)
                        else:
                            new_new_trace.append(step)

                    f = open(f'{dir}/{source_lang}-{target_lang}-{source_lang}-traces/{file}', 'w')
                    for step in new_new_trace:
                        for item in step:
                            print(item, file=f)
                        print('', file=f)
                    f.close()
                    print(file)

                print('')



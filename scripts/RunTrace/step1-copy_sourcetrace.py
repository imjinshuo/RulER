import os
import shutil
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()
    path_to_code = args.path_to_code
    path_to_DATABASE = args.path_to_DATABASE

    for model_name in ['TransCoder', 'TransCoderST', 'Codex', 'Qwen2.5-Coder-32B-Instruct']:
        for source_lang in ['Java', 'Python']:
            target_lang = 'C++'
            os.makedirs(f'{path_to_code}/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces', exist_ok=True)

            files = os.listdir(f'{path_to_code}/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-script-for-trace')
            for file in files:
                ID = file.split('.')[0]
                shutil.copy(f'{path_to_DATABASE}/DATA/CODE/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt', f'{path_to_code}/{model_name}-data/{source_lang}-{target_lang}-{source_lang}-traces/{ID}.txt')
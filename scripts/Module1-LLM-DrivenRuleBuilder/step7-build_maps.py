import os.path
import argparse
from map_utils import build_statement_mapping, extend_mapping1, extend_mapping2, build_expression_mapping


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
        "--model_name",
        default='qwen2.5-coder-32b-instruct',
        type=str,
        required=False,
        help=""
    )
    args = parser.parse_args()

    source_lang = args.source_lang
    target_lang = args.target_lang
    model_names_for_mining = [args.model_name]
    datasets = ['CodeNet']

    invalid_stmt = f'invalid_stmt/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps.txt'
    invalid_expr = f'invalid_expr/{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps.txt'

    number1 = 5000
    task_name = f'task-{number1}-{"_".join(model_names_for_mining)}-CodeNet-{source_lang}-{target_lang}'
    statement_maps_count = build_statement_mapping(model_names_for_mining, source_lang, target_lang, task_name, datasets, number1, invalid_stmt)

    loop_limit = 1000
    extend_maps_count1, max_loop1 = extend_mapping1(model_names_for_mining, source_lang, target_lang, task_name, datasets, loop_limit, number1, invalid_stmt)
    extend_maps_count2, max_loop2 = extend_mapping2(model_names_for_mining, source_lang, target_lang, task_name, datasets, loop_limit, number1, invalid_stmt)

    expression_maps_count, max_loop3 = build_expression_mapping(model_names_for_mining, source_lang, target_lang, task_name, invalid_expr)
from utils import *
from tqdm import tqdm
from pyvis.network import Network
import uuid


def get_subtree_by_path(root_tree, path):
    subtree = root_tree
    try:
        for idx in path:
            subtree = subtree.children[idx]
        return subtree
    except:
        return None


def visualize_map(
    data,
    output_path="tree_anchor_visualization.html"
):
    net = Network(
        height="1000px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#333333",
        layout=True
    )

    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 15,
          "color": "#555555",
          "face": "monospace"
        },
        "size": 20,
        "borderWidth": 2,
        "borderColor": "#000000"
      },
      "edges": {
        "color": "#666666",
        "width": 4,
        "arrows": {
          "to": { "enabled": true, "scaleFactor": 0.8 }
        },
        "smooth": { "type": "curvedCW", "roundness": 0.05 }
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "nodeSpacing": 250,
          "levelSeparation": 200,
          "treeSpacing": 1600
        }
      },
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0.0,
          "springLength": 100,
          "nodeDistance": 200
        },
        "solver": "hierarchicalRepulsion"
      },
      "interaction": {
        "dragNodes": true,
        "zoomView": true,
        "hover": true
      }
    }
    """)

    def traverse_and_add(tree, prefix, group):
        node_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        tree_text = tree.text.split('\n')[0]
        label = f"AST Node Type: {tree.type}\nCode for Example: {tree_text}"

        color = "#87CEEB" if prefix == "S" else "#FFA07A"

        net.add_node(
            node_id,
            label=label,
            title=label,
            color=color,
            borderWidth=2,
            group=group
        )

        tree2id = {tree: node_id}
        edges = []

        for child in tree.children:
            c_id, c_map, c_edges = traverse_and_add(child, prefix, group)
            tree2id.update(c_map)
            edges.append((node_id, c_id))
            edges.extend(c_edges)

        return node_id, tree2id, edges

    source_tree = data.source_tree
    source_root_id, source_tree2id, source_edges = traverse_and_add(source_tree, "S", group=1)

    trans_tree = data.trans_trees[0]
    trans_root_id, trans_tree2id, trans_edges = traverse_and_add(trans_tree, "T", group=2)

    for u, v in source_edges + trans_edges:
        net.add_edge(u, v, color="#333333", width=2)

    net.add_edge(
        source_root_id, trans_root_id,
        color="#9370DB",
        width=5,
        label="Translation Rule",
        font={"color": "#6A0DAD", "size": 18, "bold": True},
        arrows={"to": {"enabled": True}, "from": {"enabled": True}}
    )

    anchors = data.anchors
    anchor_idx = 1
    for src_path_item, trans_pairs in anchors:
        src_subtree = get_subtree_by_path(source_tree, src_path_item)

        for trans_path_item, _ in trans_pairs:
            tgt_subtree = get_subtree_by_path(trans_tree, trans_path_item)

            if src_subtree in source_tree2id and tgt_subtree in trans_tree2id:
                s_id = source_tree2id[src_subtree]
                t_id = trans_tree2id[tgt_subtree]
                net.add_edge(
                    s_id, t_id,
                    color="red",
                    dashes=True,
                    width=3,
                    title="Link between ASTs",
                    label=f"Link-{anchor_idx}",
                    arrows={"to": {"enabled": True}, "from": {"enabled": True}}
                )
                anchor_idx += 1

    net.write_html(output_path)
    return net


def run(model_names_for_mining, source_lang, target_lang, path_to_DATABASE, number):
    task1_name = f'{path_to_DATABASE}/task-{5000}-{"_".join(model_names_for_mining)}-CodeNet-{source_lang}-{target_lang}'
    existing_maps_files_number = [int(file.split('.')[-2].split('-')[-1])
                                  for file in os.listdir(f'{task1_name}/')
                                  if file.startswith(f'{"_".join(model_names_for_mining)}-{source_lang}-{target_lang}-maps-')
                                  and file.split('.')[-1] == 'txt']
    max_loop = max(existing_maps_files_number)
    path2pair = load_path2pair(task1_name, source_lang, target_lang, max_loop)
    vs = []
    for k, v in path2pair.items():
        for this_v in v:
            vs.append(this_v)
    random.shuffle(vs)
    os.makedirs(f'Rule-Visualize-from-{source_lang}-to-{target_lang}', exist_ok=True)
    id = 0
    for v in tqdm(vs[:number]):
        id += 1
        visualize_map(v, output_path=f"Rule-Visualize-from-{source_lang}-to-{target_lang}/Rule-{id}.html")


run(['qwen2.5-coder-32b-instruct'], 'Java', 'C++', '/DATABASE', 1000)


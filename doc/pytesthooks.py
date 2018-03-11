from anytree import Node, RenderTree
from anytree.exporter import DotExporter

def get_indentation(line):
    content = line.lstrip(' ')
    # Split string using version without indentation; First item of result is the indentation itself.
    indentation_length = len(line.split(content)[0])
    return indentation_length, content

def tree_from_indented_str(lines):
    root = Node("root")
    indentations = {}
    indentations[0] = root
    for line in lines:
        current_indentation, name = get_indentation(line)

        if current_indentation not in indentations:
            # parent is the next lower indentation
            keys = [key for key in indentations.keys() if key < current_indentation]
            parent = indentations[max(keys)]
            indentations[current_indentation] = Node(name, parent=parent)

        else: #current_indentation in indentations
            # current line uses the parent of the last line with same indentation and replaces it as the last line with this given indentation
            parent = indentations[current_indentation].parent
            indentations[current_indentation] = Node(name, parent=parent)

        # delete all higher indentations
        keys = [key for key in indentations.keys() if key > current_indentation]
        for key in keys:
            indentations.pop(key)
    return root

def merge_similar(node):
    unique_children = {}

    for child in node.children:
        if child.name in unique_children:
            # Repeated child. All its children (grandchildren) are attached to the already existing node.
            for grandchild in child.children:
                grandchild.parent = unique_children[child.name]
            # Detach this repeated child from the Tree
            child.parent = None
        else:
            unique_children[child.name] = child

    # Apply recursively for each unique children
    for child in node.children:
        merge_similar(child)

with open("pytestdebug2.log") as f:
    raw_lines = f.readlines()

hooks = []
for line in raw_lines:
    if "[hook]" in line and line.lstrip(' ')[:6] != "finish":
       hooks.append(line.replace("[hook]","").replace("\n","").rstrip())

root = tree_from_indented_str(hooks)

merge_similar(root)

for pre, _, node in RenderTree(root):
    print("%s%s" % (pre, node.name))

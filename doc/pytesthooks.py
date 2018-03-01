from anytree import Node, RenderTree
from anytree.exporter import DotExporter

def merge_similar(node):
    unique_children = {}
    for child in node.children:
        if child.name in unique_children:
            #unique_children[child.name].children.append(child.children)
            for child2 in child.children:
                child2.parent = unique_children[child.name]
            child.parent = None
        else:
            unique_children[child.name] = child
    for child in node.children:
        merge_similar(child)

with open("pytestdebug.log") as f:
    raw_lines = f.readlines()

hooks = [line.replace("[hook]","").replace("\n","").lstrip().rstrip() for line in raw_lines if "[hook]" in line]
root = Node("root")
parent_hook = root
previous_hook = None
for hook in hooks:
    if "finish pytest_runtest_setup" in hook:
        pass

    if hook[:7] == "finish ":
        current_hook = parent_hook.parent
        parent_hook = current_hook
        continue

    if len(parent_hook.children) > 0:
        if hook == parent_hook.children[-1].name:
            current_hook = parent_hook.children[-1]
            parent_hook = current_hook
            continue

    current_hook = Node(hook, parent=parent_hook)
    parent_hook = current_hook

merge_similar(root)

for pre, _, node in RenderTree(root):
    print("%s%s" % (pre, node.name))

DotExporter(root).to_picture("root.png")
DotExporter(root).to_dotfile("rootdot")


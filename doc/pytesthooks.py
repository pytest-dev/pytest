from anytree import Node, RenderTree
from anytree.exporter import DotExporter

with open("pytestdebug.log") as f:
    lines = f.readlines()

lines2 = []
for line in lines:
    if "[hook]" in line:
        lines2.append(line.replace(" [hook]","").replace("\n","").lstrip())

root = Node("root")
parent_hook = root
previous_hook = None
jumpfinish = False
for hook in lines2:
    if "finish " in hook:
    #   if jumpfinish:
    #        jumpfinish = False
    #   else:
    #        parent_hook = parent_hook.parent
        parent_hook = parent_hook.parent
        continue

    #if len(parent_hook.children) > 0:
    #    if hook == parent_hook.children[-1].name:
    #        jumpfinish = True
    #        continue

    current_hook = Node(hook, parent=parent_hook)
    parent_hook = current_hook

#print(RenderTree(root, style=ContRoundStyle))
for pre, _, node in RenderTree(root):
    print("%s%s" % (pre, node.name))

#DotExporter(root).to_picture("root.png")
DotExporter(root).to_dotfile("rootdot")


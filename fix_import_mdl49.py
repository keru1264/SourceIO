import re
import os

file_path = './blender_bindings/models/mdl49/import_mdl.py'

with open(file_path, 'r') as f:
    content = f.read()

old = r"    for flex_name, \(expr, inputs\) in all_exprs.items\(\):"
# Actually, mdl49 unpacks the tuple, so it shouldn't have the tuple problem.
# Wait, the user error comes from `import_mdl.py`, let's check which version of import_mdl.py it is.
# The user's stacktrace showed:
# "File "C:\Users\kuso\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\SourceIO\blender_bindings\models\mdl44\import_mdl.py", line 236, in create_flex_drivers"
# This confirms the user was hitting mdl44 import_mdl.py. My `expr[0]` fix is exactly what's needed to prevent `str(expr)` from evaluating to `(<final_expr object>, [inputs])`.

import os
import re, shutil, tempfile

import rope.base.libutils
import rope.base.project
import rope.contrib.generate
import rope.refactor.move

COMFYUI_ROOT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COMFYUI_SUBMODULES = ['cuda_malloc.py', 'execution.py', 'fix_torch.py', 'folder_paths.py', 'latent_preview.py', 'main.py', 'new_updater.py', 'node_helpers.py', 'nodes.py', 'server.py']
COMFYUI_SUBPACKAGES = ['comfy', 'comfy_execution', 'comfy_extras', 'model_filemanager', 'utils', 'api_server', 'app']


# inspired by https://stackoverflow.com/a/57332922
def sed_inplace(filename, pattern, repl):
    '''
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    `sed -i -e 's/'${pattern}'/'${repl}' "${filename}"`.
    '''

    # For efficiency, precompile the passed regular expression.
    pattern_compiled = re.compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e., binary
    # writing with updating). This is usually a good thing. In this case,
    # however, binary writing imposes non-trivial encoding constraints trivially
    # resolved by switching to text writing. Let's do that.
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        with open(filename, 'r') as src_file:
            for line in src_file:
                tmp_file.write(pattern_compiled.sub(repl, line))

    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(filename, tmp_file.name)
    shutil.move(tmp_file.name, filename)


# fixup certain subpackages
for subpackage in ['comfy', 'comfy_execution', 'comfy_extras', 'tests-unit']:
    for root, dirs, files in os.walk(os.path.join(COMFYUI_ROOT_PATH, subpackage)):
        init_py_path = os.path.join(root, '__init__.py')
        if not os.path.exists(init_py_path):
            with open(init_py_path, 'w'):
                pass
        if 'comfy' == subpackage:
            for filename in files:
                if filename.endswith(".py"):
                    sed_inplace(os.path.join(root, filename), '"comfy\.', '"comfyui.comfy.')
        if 'tests-unit' == subpackage:
            for filename in files:
                if filename.endswith(".py"):
                    sed_inplace(os.path.join(root, filename), "'app\.frontend_management\.", "'comfyui.app.frontend_management.")


proj = rope.base.project.Project(COMFYUI_ROOT_PATH)

comfyui = rope.contrib.generate.create_package(proj, 'comfyui')

for submodule in COMFYUI_SUBMODULES:
    resource = rope.base.libutils.path_to_resource(proj, os.path.join(COMFYUI_ROOT_PATH, submodule))
    changes = rope.refactor.move.MoveModule(proj, resource).get_changes(comfyui)
    proj.do(changes)

for subpackage in COMFYUI_SUBPACKAGES:
    print(f"moving {subpackage}")
    resource = rope.base.libutils.path_to_resource(proj, os.path.join(COMFYUI_ROOT_PATH, subpackage))
    changes = rope.refactor.move.MoveModule(proj, resource).get_changes(comfyui)
    proj.do(changes)

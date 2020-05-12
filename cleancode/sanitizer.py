import tokenize, sys, ast, os, astunparse, json, base64
from io import StringIO


def rename(code):
    tree = ast.parse(code)
    var = set()
    fun = set()
    mod = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            node.name = 'C'
        elif isinstance(node, ast.ImportFrom):
            for n in node.names:
                mod.add(n.name)
        elif isinstance(node, ast.Import):
            for n in node.names:
                mod.add(n.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var.add(target.id)
                    target.id = 'V'
        elif isinstance(node, ast.FunctionDef):
            for ar in (node.args.args):
                fun.add(ar.arg)
                ar.arg = 'V'
        elif isinstance(node, ast.Name):
            if node.id in mod:
                continue
            if node.id in var or node.id in fun:
                node.id = 'V'

    return astunparse.unparse(tree)


def clean_snippet(path):
    doc = {}
    with open(path, 'r') as hdle:
        raw = hdle.read()

        trim_vars = None
        try:
            trim_vars = rename(raw)
        except:
            pass

        doc['text'] = trim_vars if trim_vars else raw
        doc['encoded'] = base64.b64encode(raw.encode('ascii')).decode('ascii')

    return doc

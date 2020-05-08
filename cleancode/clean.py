import tokenize, sys, ast, os, astunparse, json, base64
from io import StringIO


def remove_comments_and_docstrings(source):
    """
    Returns 'source' minus comments and docstrings.
    """

    io_obj = (source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        ltext = tok[4]
        # The following two conditionals preserve indentation.
        # This is necessary because we're not using tokenize.untokenize()
        # (because it spits out code with copious amounts of oddly-placed
        # whitespace).
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += (" " * (start_col - last_col))
        # Remove comments:
        if token_type == tokenize.COMMENT:
            pass
        # This series of conditionals removes docstrings:
        elif token_type == tokenize.STRING:
            if prev_toktype != tokenize.INDENT:
                # This is likely a docstring; double-check we're not inside an operator:
                if prev_toktype != tokenize.NEWLINE:
                    # Note regarding NEWLINE vs NL: The tokenize module
                    # differentiates between newlines that start a new statement
                    # and newlines inside of operators such as parens, brackes,
                    # and curly braces.  Newlines inside of operators are
                    # NEWLINE and newlines that start new code are NL.
                    # Catch whole-module docstrings:
                    if start_col > 0:
                        # Unlabelled indentation means we're inside an operator
                        out += token_string

        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = end_line

    return out


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


# usage : python3 cleancode/clean.py samples/raw
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('specify input folder')

    samples = os.listdir(sys.argv[1])
    for sample in samples:
        sample_path = os.path.join(sys.argv[1], sample)
        if not os.path.isfile(sample_path):
            continue
        source = open(sample_path)
        no_com = remove_comments_and_docstrings(source)
        text = rename(no_com)

        out = {
            'language': 'python',
            'text': text,
            'encoded': base64.b64encode(no_com.encode('ascii')).decode('ascii')
        }

        cur_path = os.path.abspath(os.curdir)
        out_path = cur_path + '/samples/' + sample.split('.')[0] + ".json"
        with open(out_path, 'w+') as write_file:
            json.dump(out, write_file, sort_keys=True, indent=4)

        # to load and decode text from json
        # with open(out_path,'r') as ff:
        #     test = json.load(ff)
        #     print(base64.b64decode(test['encoded']).decode('ascii'))

from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/tokenize', methods=['POST'])
def tokenize():
    try:
        code = request.json.get('source_code', '')
        if not code: return jsonify({"error": "No code", "tokens": [], "summary": {}, "total": 0}), 400

        tokens = []
        pos = 0
        line = 1
        col = 1

        patterns = [
            ("PREPROCESSOR", r'\#include\s*<[^>]+>'),
            ("KEYWORD", r'\b(int|float|char|void|if|else|while|for|return|printf|scanf|main|include)\b'),
            ("FLOAT", r'\b\d+\.\d+\b'),
            ("INTEGER", r'\b\d+\b'),
            ("STRING", r'"[^"]*"'),
            ("OPERATOR", r'(==|!=|<=|>=|\+\+|--|&&|\|\||->|[+\-*/%=<>!&|])'),
            ("DELIMITER", r'[(){}\[\];,:]'),
            ("IDENTIFIER", r'[a-zA-Z_]\w*'),
            ("WHITESPACE", r'\s+'),
        ]
        errors = []

        while pos < len(code):
            matched = False
            for typ, pat in patterns:
                m = re.compile(pat).match(code, pos)
                if m:
                    val = m.group(0)
                    if typ != "WHITESPACE":
                        tokens.append({"type": typ, "value": val, "line": line, "col": col})
                    if '\n' in val:
                        line += val.count('\n')
                        col = 1
                    else:
                        col += len(val)
                    pos = m.end()
                    matched = True
                    break
            if not matched:
                errors.append({"character": code[pos], "line": line, "col": col})
                pos += 1
                col += 1

        summary = {}
        for t in tokens:
            summary[t['type']] = summary.get(t['type'], 0) + 1

        error = None
        if errors:
            error = f"Lexical errors detected: {len(errors)} invalid character(s)"

        return jsonify({"tokens": tokens, "summary": summary, "total": len(tokens), "errors": errors, "error": error}), 200
    except Exception as e:
        return jsonify({"error": str(e), "tokens": [], "summary": {}, "total": 0}), 500


@app.route('/icdg', methods=['POST'])
def icdg():
    try:
        code = request.json.get('source_code', '')
        if not code: return jsonify({"error": "No code", "tac": "", "quadruples": []}), 400

        import re

        # Generator state
        quads = []
        temp_count = 1
        label_count = 1

        def get_temp():
            nonlocal temp_count
            t = f"t{temp_count}"
            temp_count += 1
            return t

        def get_label():
            nonlocal label_count
            l = f"L{label_count}"
            label_count += 1
            return l

        # Helper to parse conditions like (i == 1 || i == n)
        def parse_condition(cond):
            cond = cond.strip()
            # Handle multiple ORs
            if '||' in cond:
                parts = [p.strip() for p in cond.split('||')]
                prev_t = None
                for i, p in enumerate(parts):
                    # Handle sub-condition like i == 1
                    sub_t = parse_condition(p)
                    if prev_t is None:
                        prev_t = sub_t
                    else:
                        new_t = get_temp()
                        quads.append({'op': '||', 'arg1': prev_t, 'arg2': sub_t, 'result': new_t})
                        prev_t = new_t
                return prev_t

            # Handle single comparison
            for op in ['<=', '>=', '==', '!=', '<', '>']:
                if op in cond:
                    c_parts = cond.split(op)
                    t = get_temp()
                    quads.append({'op': op, 'arg1': c_parts[0].strip(), 'arg2': c_parts[1].strip(), 'result': t})
                    return t
            return cond

        # Pre-process code: clean up and normalize
        clean_code = re.sub(r'#include\s+<.*?>', '', code)
        clean_code = re.sub(r'int\s+main\s*\(\s*\)\s*\{', '', clean_code)
        clean_code = re.sub(r'return\s+0\s*;', '', clean_code)

        # Tokenize basic constructs (very simple regex-based tokenizer)
        # We look for for loops, if statements, printf, and assignments

        def process_block(text):
            # Find assignments: int n = 5;
            assigns = re.findall(r'(?:int|float|char)?\s*([a-zA-Z_]\w*)\s*=\s*([^;]+);', text)
            for var, val in assigns:
                quads.append({'op': ':=', 'arg1': val.strip(), 'arg2': '', 'result': var.strip()})
                text = text.replace(f"{var} = {val};", "", 1) # remove to avoid double processing

        # This is a very complex task for a simple endpoint.
        # I'll implement a recursive-descent style parser for the specific constructs we care about.

        def parse_recursive(text):
            text = text.strip()
            if not text: return

            # 1. Handle FOR loop: for(init; cond; inc) { ... }
            for_match = re.search(r'for\s*\(([^;]+);([^;]+);([^)]+)\)\s*\{', text)
            if for_match:
                init, cond, inc = for_match.groups()
                # Init
                if '=' in init:
                    v, val = init.split('=')
                    quads.append({'op': ':=', 'arg1': val.strip(), 'arg2': '', 'result': v.replace('int','').strip()})

                start_label = get_label()
                quads.append({'op': 'label', 'arg1': start_label, 'arg2': '', 'result': ''})

                # Condition
                t_cond = parse_condition(cond)
                end_label = get_label()
                # We use 'if_false' goto end to match the requested style if possible,
                # or 'if' with inverted condition. The user used 'if i > n goto L8' for 'i <= n'.
                # Let's try to invert common ops.
                inv_op = {'<=': '>', '>=': '<', '==': '!=', '!=': '==', '<': '>=', '>': '<='}
                op_found = False
                for op, inv in inv_op.items():
                    if op in cond:
                        c_parts = cond.split(op)
                        t_inv = get_temp()
                        quads.append({'op': inv, 'arg1': c_parts[0].strip(), 'arg2': c_parts[1].strip(), 'result': t_inv})
                        quads.append({'op': 'if', 'arg1': t_inv, 'arg2': end_label, 'result': 'goto'})
                        op_found = True
                        break
                if not op_found:
                    quads.append({'op': 'if_false', 'arg1': t_cond, 'arg2': end_label, 'result': 'goto'})

                # Body (find matching brace)
                body_start = for_match.end()
                bracket_level = 1
                body_end = body_start
                while bracket_level > 0 and body_end < len(text):
                    if text[body_end] == '{': bracket_level += 1
                    elif text[body_end] == '}': bracket_level -= 1
                    body_end += 1

                body_text = text[body_start : body_end-1]
                parse_recursive(body_text)

                # Increment
                if '++' in inc:
                    v = inc.replace('++', '').strip()
                    quads.append({'op': ':=', 'arg1': f"{v} + 1", 'arg2': '', 'result': v})
                elif '--' in inc:
                    v = inc.replace('--', '').strip()
                    quads.append({'op': ':=', 'arg1': f"{v} - 1", 'arg2': '', 'result': v})
                elif '=' in inc:
                    v, val = inc.split('=')
                    quads.append({'op': ':=', 'arg1': val.strip(), 'arg2': '', 'result': v.strip()})

                quads.append({'op': 'goto', 'arg1': start_label, 'arg2': '', 'result': ''})
                quads.append({'op': 'label', 'arg1': end_label, 'arg2': '', 'result': ''})

                parse_recursive(text[body_end:])
                return

            # 2. Handle IF: if(cond) { ... } else { ... }
            if_match = re.search(r'if\s*\(([^)]+)\)\s*\{', text)
            if if_match:
                cond = if_match.group(1)
                t_cond = parse_condition(cond)

                l_true = get_label()
                l_false = get_label()
                l_end = get_label()

                quads.append({'op': 'if', 'arg1': t_cond, 'arg2': l_true, 'result': 'goto'})
                quads.append({'op': 'goto', 'arg1': l_false, 'arg2': '', 'result': ''})

                quads.append({'op': 'label', 'arg1': l_true, 'arg2': '', 'result': ''})

                # Body
                body_start = if_match.end()
                bracket_level = 1
                body_end = body_start
                while bracket_level > 0 and body_end < len(text):
                    if text[body_end] == '{': bracket_level += 1
                    elif text[body_end] == '}': bracket_level -= 1
                    body_end += 1

                parse_recursive(text[body_start : body_end-1])
                quads.append({'op': 'goto', 'arg1': l_end, 'arg2': '', 'result': ''})

                quads.append({'op': 'label', 'arg1': l_false, 'arg2': '', 'result': ''})

                # Else
                rest = text[body_end:].strip()
                if rest.startswith('else'):
                    else_body_start = rest.find('{') + 1
                    bracket_level = 1
                    else_body_end = else_body_start
                    while bracket_level > 0 and else_body_end < len(rest):
                        if rest[else_body_end] == '{': bracket_level += 1
                        elif rest[else_body_end] == '}': bracket_level -= 1
                        else_body_end += 1
                    parse_recursive(rest[else_body_start : else_body_end-1])
                    quads.append({'op': 'label', 'arg1': l_end, 'arg2': '', 'result': ''})
                    parse_recursive(rest[else_body_end:])
                else:
                    quads.append({'op': 'label', 'arg1': l_end, 'arg2': '', 'result': ''})
                    parse_recursive(rest)
                return

            # 3. Handle PRINTF
            print_match = re.search(r'printf\s*\("([^"]*)"(?:,\s*([^)]+))?\)\s*;', text)
            if print_match:
                fmt, args = print_match.groups()
                if args:
                    arg_list = [a.strip() for a in args.split(',')]
                    for a in arg_list:
                        quads.append({'op': 'print', 'arg1': a, 'arg2': '', 'result': ''})
                else:
                    if fmt == '\\n':
                        quads.append({'op': 'print', 'arg1': 'newline', 'arg2': '', 'result': ''})
                    else:
                        quads.append({'op': 'print', 'arg1': f'"{fmt}"', 'arg2': '', 'result': ''})

                parse_recursive(text[print_match.end():])
                return

            # 4. Handle simple assignments
            assign_match = re.search(r'(?:int|float|char)?\s*([a-zA-Z_]\w*)\s*=\s*([^;]+);', text)
            if assign_match:
                var, val = assign_match.groups()
                quads.append({'op': ':=', 'arg1': val.strip(), 'arg2': '', 'result': var.strip()})
                parse_recursive(text[assign_match.end():])
                return

        # Start parsing
        parse_recursive(clean_code)
        quads.append({'op': 'end', 'arg1': '', 'arg2': '', 'result': ''})

        # Format results (same as before)
        tac_lines = []
        for q in quads:
            if q['op'] == 'label': tac_lines.append(f"{q['arg1']}:")
            elif q['op'] == ':=': tac_lines.append(f"  {q['result']} = {q['arg1']}")
            elif q['op'] in ['+', '-', '*', '/', '%', '<=', '>=', '==', '!=', '<', '>', '||', '&&']:
                tac_lines.append(f"  {q['result']} = {q['arg1']} {q['op']} {q['arg2']}")
            elif q['op'] == 'if': tac_lines.append(f"  if {q['arg1']} goto {q['arg2']}")
            elif q['op'] == 'if_false': tac_lines.append(f"  if_false {q['arg1']} goto {q['arg2']}")
            elif q['op'] == 'goto': tac_lines.append(f"  goto {q['arg1']}")
            elif q['op'] == 'print': tac_lines.append(f"  print {q['arg1']}")
            elif q['op'] == 'end': tac_lines.append("  end")

        quad_fmt = []
        for i, q in enumerate(quads):
            quad_fmt.append({"NO.": f"({i+1})", "OP": q['op'], "ARG1": q['arg1'], "ARG2": q['arg2'], "RESULT": q['result']})

        triple_fmt = []
        res_to_idx = {}
        for i, q in enumerate(quads):
            a1, a2 = q['arg1'], q['arg2']
            if a1 in res_to_idx: a1 = res_to_idx[a1]
            if a2 in res_to_idx: a2 = res_to_idx[a2]
            triple_fmt.append({"NO.": f"({i+1})", "OP": q['op'], "ARG1": a1, "ARG2": a2})
            if q['result'] and q['result'].startswith('t'): res_to_idx[q['result']] = f"({i+1})"

        indirect_fmt = [{"POINTER": 40+i, "NO.": t["NO."], "OP": t["OP"], "ARG1": t["ARG1"], "ARG2": t["ARG2"]} for i, t in enumerate(triple_fmt)]

        return jsonify({
            "tac": "\n".join(tac_lines),
            "quadruples": quad_fmt,
            "triples": triple_fmt,
            "indirect_triples": indirect_fmt,
            "instruction_count": len(quads),
            "error": None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "tac": "", "quadruples": [], "triples": [], "indirect_triples": [], "instruction_count": 0}), 500


@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        code = request.json.get('source_code', '')
        if not code: return jsonify({"error": "No code", "optimized": [], "removed": 0}), 400

        tac = []
        for line in code.split('\n'):
            s = line.strip()
            if s and not s.startswith('//'):
                if 'main' in s:
                    tac.append("FUNC_BEGIN main")
                elif s == '}':
                    tac.append("FUNC_END")
                elif '=' in s and 'if' not in s:
                    tac.append(f"  {s.rstrip(';')}")
                elif 'for' in s:
                    tac.append("; FOR")
                elif 'while' in s:
                    tac.append("; WHILE")
                elif 'printf' in s:
                    tac.append("; CALL")
                elif 'return' in s:
                    tac.append("; RETURN")

        opt = []
        prev = None
        for x in tac:
            if x != prev:
                opt.append(x)
                prev = x

        removed = len(tac) - len(opt)
        fmt = [{"#": i + 1, "Instruction": x} for i, x in enumerate(opt)]
        return jsonify({"optimized": fmt, "original_count": len(tac), "optimized_count": len(opt), "removed": removed,
                        "error": None}), 200
    except Exception as e:
        return jsonify({"error": str(e), "optimized": [], "removed": 0}), 500


@app.route('/codegen', methods=['POST'])
def codegen():
    try:
        code = request.json.get('source_code', '')
        if not code: return jsonify({"error": "No code", "assembly": [], "assembly_count": 0}), 400

        asm = ["; x86-64 Assembly", ".section .text", ".globl main", "main:", "  PUSH RBP", "  MOV RBP, RSP"]
        for line in code.split('\n'):
            s = line.strip()
            if not s or s.startswith('//') or s.startswith('#'):
                continue

            if 'printf' in s:
                asm.append("  CALL printf")
            elif 'scanf' in s:
                asm.append("  CALL scanf")
            elif s == 'return 0;':
                continue
            elif '++' in s:
                var = re.sub(r'[^a-zA-Z0-9_]', '', s.replace('++', ''))
                asm.append(f"  INC DWORD PTR [{var}]")
            elif '--' in s:
                var = re.sub(r'[^a-zA-Z0-9_]', '', s.replace('--', ''))
                asm.append(f"  DEC DWORD PTR [{var}]")
            elif '=' in s and 'if' not in s and 'for' not in s and 'while' not in s:
                s = s.rstrip(';')
                if ',' in s and '=' in s:
                    parts = s.split(',')
                    for p in parts:
                        if '=' in p:
                            p = re.sub(r'^(int|float|char)\s+', '', p.strip())
                            l, r = p.split('=', 1)
                            asm.append(f"  MOV DWORD PTR [{l.strip()}], {r.strip()}")
                else:
                    s = re.sub(r'^(int|float|char)\s+', '', s)
                    if '=' in s:
                        l, r = s.split('=', 1)
                        l, r = l.strip(), r.strip()
                        if '+' in r:
                            op1, op2 = r.split('+')
                            asm.append(f"  MOV EAX, {op1.strip()}")
                            asm.append(f"  ADD EAX, {op2.strip()}")
                            asm.append(f"  MOV DWORD PTR [{l}], EAX")
                        elif '-' in r:
                            op1, op2 = r.split('-')
                            asm.append(f"  MOV EAX, {op1.strip()}")
                            asm.append(f"  SUB EAX, {op2.strip()}")
                            asm.append(f"  MOV DWORD PTR [{l}], EAX")
                        elif '*' in r:
                            op1, op2 = r.split('*')
                            asm.append(f"  MOV EAX, {op1.strip()}")
                            asm.append(f"  IMUL EAX, {op2.strip()}")
                            asm.append(f"  MOV DWORD PTR [{l}], EAX")
                        elif '/' in r:
                            op1, op2 = r.split('/')
                            asm.append(f"  MOV EAX, {op1.strip()}")
                            asm.append(f"  MOV EBX, {op2.strip()}")
                            asm.append(f"  CDQ")
                            asm.append(f"  IDIV EBX")
                            asm.append(f"  MOV DWORD PTR [{l}], EAX")
                        elif '%' in r:
                            op1, op2 = r.split('%')
                            asm.append(f"  MOV EAX, {op1.strip()}")
                            asm.append(f"  MOV EBX, {op2.strip()}")
                            asm.append(f"  CDQ")
                            asm.append(f"  IDIV EBX")
                            asm.append(f"  MOV DWORD PTR [{l}], EDX")
                        else:
                            asm.append(f"  MOV EAX, {r}")
                            asm.append(f"  MOV DWORD PTR [{l}], EAX")
            elif 'if' in s:
                asm.append("; IF Condition Check")
                asm.append("  CMP EAX, EBX")
                asm.append("  JLE .L_ELSE")
            elif 'else' in s:
                asm.append(".L_ELSE:")
            elif 'while' in s:
                asm.append(".L_WHILE_START:")
                asm.append("; While Condition")
                asm.append("  CMP EAX, 0")
                asm.append("  JE .L_WHILE_END")
            elif 'for' in s:
                asm.append("; FOR loop setup")
                asm.append(".L_FOR_START:")
        asm.extend(["  XOR EAX, EAX", "  POP RBP", "  RET"])

        fmt = [{"#": i + 1, "Code": x} for i, x in enumerate(asm)]
        return jsonify({"assembly": fmt, "assembly_count": len(asm), "error": None}), 200
    except Exception as e:
        return jsonify({"error": str(e), "assembly": [], "assembly_count": 0}), 500


if __name__ == '__main__':
    print("=" * 40)
    print(" Backend running on :5001")
    print("=" * 40)
    app.run(host='localhost', port=5001, debug=False, threaded=True)

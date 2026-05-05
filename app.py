import streamlit as st
import requests
import pandas as pd
import json

BACKEND_URL = "http://127.0.0.1:5001"

st.set_page_config(page_title="Compiler 4 Phases", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    .phase-header { background:linear-gradient(135deg,#1e3a5f,#2563eb); color:white; padding:14px 20px; border-radius:8px; margin-bottom:16px; font-size:18px; font-weight:bold; }
    .err  { background:#3d1f1f; border:1px solid #f85149; border-radius:6px; padding:12px; color:#f85149; font-family:monospace; margin:6px 0; }
    .ok   { background:#1a3d1f; border:1px solid #3fb950; border-radius:6px; padding:12px; color:#3fb950; font-family:monospace; margin:6px 0; }
    .warn { background:#3d3010; border:1px solid #f2cc60; border-radius:6px; padding:12px; color:#f2cc60; font-family:monospace; margin:6px 0; }
    .token-badge { display:inline-block; padding:3px 10px; border-radius:4px; font-family:monospace; font-size:12px; margin:2px; font-weight:bold; }
    .stButton>button { background:linear-gradient(135deg,#1e3a5f,#2563eb)!important; color:white!important; font-weight:bold!important; border:none!important; }
</style>
""", unsafe_allow_html=True)

TOKEN_COLORS = {
    "KEYWORD": ("#ff7b72", "#3d1f1f"),
    "IDENTIFIER": ("#79c0ff", "#1a2c3d"),
    "INTEGER": ("#f2cc60", "#3d3010"),
    "FLOAT": ("#ffa657", "#3d2510"),
    "STRING": ("#a5d6ff", "#1a2535"),
    "CHAR_LIT": ("#a5d6ff", "#1a2535"),
    "OPERATOR": ("#d2a8ff", "#2d1f3d"),
    "DELIMITER": ("#8b949e", "#1f2328"),
}

SAMPLES = {
    "Hollow Rectangle": """#include <stdio.h>
int main() {
    int i, j, n = 5;
    for(i = 1; i <= n; i++) {
        for(j = 1; j <= n; j++) {
            if(i == 1 || i == n || j == 1 || j == n)
                printf("* ");
            else
                printf("  ");
        }
        printf("\\n");
    }
    return 0;
}""",
    "Sum of digits": """#include <stdio.h>
int main() {
    int num = 1234, sum = 0, digit;
    while(num != 0) {
        digit = num % 10;
        sum = sum + digit;
        num = num / 10;
    }
    printf("Sum = %d\\n", sum);
    return 0;
}""",
    "Grade": """#include <stdio.h>
int main() {
    int marks = 75;
    if(marks >= 90)
        printf("Grade A");
    else if(marks >= 75)
        printf("Grade B");
    else if(marks >= 50)
        printf("Grade C");
    else
        printf("Fail");
    return 0;
}"""
}


def safe_post(endpoint, code):
    """Make a safe POST request — always returns (data_dict, error_string)"""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/{endpoint}",
            json={"source_code": code},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        # Debug: print raw response in console
        print(f"[DEBUG] /{endpoint} status={resp.status_code} len={len(resp.text)}")
        print(f"[DEBUG] raw response = {resp.text[:200]}")

        if resp.status_code == 0 or not resp.text.strip():
            return None, "Backend returned empty response. Is Flask running on port 5001?"

        try:
            return resp.json(), None
        except json.JSONDecodeError as je:
            return None, f"Backend response is not valid JSON: {str(je)}\nRaw: {resp.text[:200]}"

    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Run: python app.py in backend folder"
    except requests.exceptions.Timeout:
        return None, "Backend timed out. Check if Flask is running."
    except Exception as e:
        return None, f"Request failed: {str(e)}"


# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Compiler Phases")
    st.markdown("---")
    phase = st.radio("Select Phase", [
        "1️⃣  Tokenization",
        "2️⃣  ICG (Intermediate Code)",
        "3️⃣  Code Optimization",
        "4️⃣  Code Generation",
    ])
    st.markdown("---")

    # Backend status check
    try:
        hresp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if hresp.status_code == 200:
            st.markdown('<div class="ok">✓ Backend running</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="err">✗ Backend error</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div class="err">✗ Backend offline<br>Run: python app.py</div>', unsafe_allow_html=True)

# ── Main Layout ───────────────────────────────────────
st.title("⚙️ Compiler 4 Phases")
st.caption("C Language Compiler — Tokenization → ICDG → Optimization → Code Generation")
st.markdown("---")

col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.markdown("### 📝 Source Code Input")
    sample_choice = st.selectbox("Load a sample", ["— custom —"] + list(SAMPLES.keys()))
    default_code = SAMPLES.get(sample_choice, "") if sample_choice != "— custom —" else ""
    code = st.text_area("C Code", value=default_code, height=340, label_visibility="collapsed")
    run_btn = st.button("▶  Run Phase", use_container_width=True)

with col_out:
    # ── PHASE 1 ─────────────────────────────────────
    if "1️⃣" in phase:
        st.markdown('<div class="phase-header">🔤 Phase 1 — Tokenization (Lexical Analysis)</div>',
                    unsafe_allow_html=True)

        if run_btn:
            if not code.strip():
                st.markdown('<div class="warn">⚠ Please enter some code first.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Tokenizing..."):
                    result, err = safe_post("tokenize", code)

                if err:
                    st.markdown(f'<div class="err">❌ {err}</div>', unsafe_allow_html=True)
                elif result.get("error"):
                    st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                else:
                    st.session_state["tok"] = result

        if "tok" in st.session_state:
            res = st.session_state["tok"]
            tokens = res.get("tokens", [])
            summary = res.get("summary", {})

            st.markdown(f'<div class="ok">✓ {res.get("total", 0)} tokens generated</div>', unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("KEYWORD", summary.get("KEYWORD", 0))
            c2.metric("IDENTIFIER", summary.get("IDENTIFIER", 0))
            c3.metric("OPERATOR", summary.get("OPERATOR", 0))
            c4.metric("Total", res.get("total", 0))

            st.markdown("**Token Stream:**")
            html = " ".join([
                f'<span class="token-badge" style="background:{TOKEN_COLORS.get(t["type"], ("#8b949e", "#1f2328"))[1]};color:{TOKEN_COLORS.get(t["type"], ("#8b949e", "#1f2328"))[0]};border:1px solid {TOKEN_COLORS.get(t["type"], ("#8b949e", "#1f2328"))[0]}55">{t["value"]}</span>'
                for t in tokens
            ])
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("**Token Table:**")
            df = pd.DataFrame([{"Line": t["line"], "Token Type": t["type"], "Lexeme": t["value"]} for t in tokens])
            df.index += 1
            st.dataframe(df, use_container_width=True, height=300)

    # ── PHASE 2 ─────────────────────────────────────
    elif "2️⃣" in phase:
        st.markdown('<div class="phase-header">📋 Phase 2 — Intermediate Code Generation</div>',
                    unsafe_allow_html=True)

        if run_btn:
            if not code.strip():
                st.markdown('<div class="warn">⚠ Please enter some code first.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Generating ICDG..."):
                    result, err = safe_post("icdg", code)

                if err:
                    st.markdown(f'<div class="err">❌ {err}</div>', unsafe_allow_html=True)
                elif result.get("error"):
                    st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                else:
                    st.session_state["icdg"] = result

        if "icdg" in st.session_state:
            res = st.session_state["icdg"]
            st.markdown(f"### C Code — {res.get('instruction_count', 0)} instructions generated")

            # 1. TAC
            with st.container():
                st.markdown('<div style="background:#f0f4f8; padding:15px; border-radius:10px; border-left:5px solid #2563eb; margin-bottom:20px;">'
                            '<h4 style="color:#1e3a5f; margin-top:0;">● THREE ADDRESS CODE (TAC)</h4>', unsafe_allow_html=True)
                st.code(res.get("tac", ""), language="text")
                st.markdown('</div>', unsafe_allow_html=True)

            # 2. Quadruple
            with st.container():
                st.markdown('<div style="background:#f0f4f8; padding:15px; border-radius:10px; border-left:5px solid #2563eb; margin-bottom:20px;">'
                            '<h4 style="color:#1e3a5f; margin-top:0;">● QUADRUPLE</h4>', unsafe_allow_html=True)
                df_quad = pd.DataFrame(res.get("quadruples", []))
                st.table(df_quad)
                st.markdown('</div>', unsafe_allow_html=True)

            # 3. Triple
            with st.container():
                st.markdown('<div style="background:#f0f4f8; padding:15px; border-radius:10px; border-left:5px solid #2563eb; margin-bottom:20px;">'
                            '<h4 style="color:#1e3a5f; margin-top:0;">● TRIPLE</h4>', unsafe_allow_html=True)
                df_triple = pd.DataFrame(res.get("triples", []))
                st.table(df_triple)
                st.markdown('</div>', unsafe_allow_html=True)

            # 4. Indirect Triple
            with st.container():
                st.markdown('<div style="background:#f0f4f8; padding:15px; border-radius:10px; border-left:5px solid #2563eb; margin-bottom:20px;">'
                            '<h4 style="color:#1e3a5f; margin-top:0;">● INDIRECT TRIPLE</h4>', unsafe_allow_html=True)
                df_indirect = pd.DataFrame(res.get("indirect_triples", []))
                st.table(df_indirect)
                st.markdown('</div>', unsafe_allow_html=True)

    # ── PHASE 3 ─────────────────────────────────────
    elif "3️⃣" in phase:
        st.markdown('<div class="phase-header">⚡ Phase 3 — Code Optimization</div>', unsafe_allow_html=True)

        if run_btn:
            if not code.strip():
                st.markdown('<div class="warn">⚠ Please enter some code first.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Optimizing..."):
                    result, err = safe_post("optimize", code)

                if err:
                    st.markdown(f'<div class="err">❌ {err}</div>', unsafe_allow_html=True)
                elif result.get("error"):
                    st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                else:
                    st.session_state["opt"] = result

        if "opt" in st.session_state:
            res = st.session_state["opt"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Original", res.get("original_count", 0))
            c2.metric("Optimized", res.get("optimized_count", 0))
            c3.metric("Removed", res.get("removed", 0))
            if res.get("removed", 0) > 0:
                pct = res["removed"] / res["original_count"] * 100 if res["original_count"] else 0
                st.markdown(f'<div class="ok">✓ {pct:.1f}% code size reduction</div>', unsafe_allow_html=True)
            opt = res.get("optimized", [])
            opt_text = "\n".join([row["Instruction"] for row in opt])
            st.code(opt_text, language="text")
            st.markdown("**Optimized Instructions:**")
            df = pd.DataFrame(opt)
            st.dataframe(df, use_container_width=True, height=300)

    # ── PHASE 4 ─────────────────────────────────────
    elif "4️⃣" in phase:
        st.markdown('<div class="phase-header">💻 Phase 4 — Code Generation (x86-64 Assembly)</div>',
                    unsafe_allow_html=True)

        if run_btn:
            if not code.strip():
                st.markdown('<div class="warn">⚠ Please enter some code first.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Generating assembly..."):
                    result, err = safe_post("codegen", code)

                if err:
                    st.markdown(f'<div class="err">❌ {err}</div>', unsafe_allow_html=True)
                elif result.get("error"):
                    st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                else:
                    st.session_state["cg"] = result

        if "cg" in st.session_state:
            res = st.session_state["cg"]
            asm = res.get("assembly", [])
            st.markdown(f'<div class="ok">✓ {res.get("assembly_count", 0)} assembly lines generated</div>',
                        unsafe_allow_html=True)
            asm_text = "\n".join([row["Code"] for row in asm])
            st.code(asm_text, language="asm")
            st.markdown("**Assembly Table:**")
            df = pd.DataFrame(asm)
            st.dataframe(df, use_container_width=True, height=300)

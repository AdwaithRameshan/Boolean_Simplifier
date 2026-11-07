import re
import pandas as pd # type: ignore
import streamlit as st  # type: ignore

def letter(i):
    return chr(65 + i)

def parse_list(text, n):
    out = []
    for tok in re.split(r"[,\s]+", text.strip()):
        if not tok:
            continue
        if not tok.isdigit():
            raise ValueError(f"'{tok}' is not a whole number.")
        v = int(tok)
        if v >= 2 ** n:
            raise ValueError(f"Minterm {v} is too large for {n} variables (max {2 ** n - 1}).")
        out.append(v)
    return sorted(set(out))


def parse_expr(text):
    s = text.replace("\u2032", "'").replace(" ", "")
    if not s:
        raise ValueError("Enter an expression.")
    terms = []
    for t in s.split("+"):
        if not re.fullmatch(r"(?:!?[A-Za-z]'?)+", t or "#"):
            raise ValueError(f"Cannot read term '{t}'.")
        lits = [(ord(m[1].upper()) - 65, not (m[0] or m[2]))
                for m in re.findall(r"(!?)([A-Za-z])('?)", t)]
        terms.append(lits)
    n = max(i for t in terms for i, _ in t) + 1
    if n > 10:
        raise ValueError("Use variables A-J only.")
    return terms, max(n, 2)


def expr_to_minterms(terms, n):
    out = []
    for v in range(2 ** n):
        bits = format(v, f"0{n}b")
        if any(all((bits[i] == "1") == pos for i, pos in t) for t in terms):
            out.append(v)
    return out


def combine(a, b):
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    if len(diff) != 1 or "-" in (a[diff[0]], b[diff[0]]):
        return None
    d = diff[0]
    return a[:d] + "-" + a[d + 1:]


def quine_mccluskey(minterms, dcs, n):
    cur = {format(v, f"0{n}b"): {v} for v in set(minterms) | set(dcs)}
    steps, primes = [], []
    while cur:
        groups = {}
        for k in cur:
            groups.setdefault(k.count("1"), []).append(k)
        steps.append([(g, [(k, sorted(cur[k])) for k in groups[g]]) for g in sorted(groups)])
        used, nxt = set(), {}
        for g in sorted(groups):
            for a in groups.get(g, []):
                for b in groups.get(g + 1, []):
                    c = combine(a, b)
                    if c:
                        used |= {a, b}
                        nxt.setdefault(c, set()).update(cur[a], cur[b])
        primes += [(k, sorted(v)) for k, v in cur.items() if k not in used]
        cur = nxt

    need = set(minterms)
    chosen, essential = set(), set()
    for m in minterms:
        cover = [p for p in primes if m in p[1]]
        if len(cover) == 1:
            chosen.add(cover[0][0])
            essential.add(cover[0][0])
    covered = {m for k, c in primes if k in chosen for m in c}
    while need - covered:  # greedy cover for what is left
        best = max((p for p in primes if p[0] not in chosen),
                   key=lambda p: len((need - covered) & set(p[1])))
        chosen.add(best[0])
        covered |= set(best[1])
    return steps, primes, chosen, essential


def term_str(bits):
    s = "".join(letter(i) + ("\u2032" if b == "0" else "") for i, b in enumerate(bits) if b != "-")
    return s or "1"


def literal_count(bits):
    return sum(b != "-" for b in bits)


def verify(minterms, dcs, n, chosen):
    """True if the chosen terms give the same output as the original on every input."""
    for v in range(2 ** n):
        if v in dcs:
            continue
        bits = format(v, f"0{n}b")
        value = any(all(c == "-" or c == b for c, b in zip(k, bits)) for k in chosen)
        if value != (v in minterms):
            return False
    return True


st.set_page_config(page_title="Boolean Logic Minimizer", page_icon="🔌", layout="wide")

EXAMPLE_6VAR = "1,3,5,7,9,11,13,15,17,19,21,23,33,35,37,39,41,43,45,47,60,61"

# default values (only set the first time the page opens)
st.session_state.setdefault("mode", "Minterms")
st.session_state.setdefault("n", 4)
st.session_state.setdefault("mt", "0,1,2,5,6,7,8,9,10,14")
st.session_state.setdefault("dc", "")
st.session_state.setdefault("ex", "A'B' + A'C + BC' + AB'")


def load_example():
    st.session_state.mode = "Minterms"
    st.session_state.n = 6
    st.session_state.mt = EXAMPLE_6VAR
    st.session_state.dc = "0,2"


st.title("🔌 Boolean Logic Minimizer")
st.caption("Quine-McCluskey method · up to 10 variables · results update as you type")

# ---------------- sidebar: input ----------------
st.sidebar.header("Input")
mode = st.sidebar.radio("Mode", ["Minterms", "Expression (SOP)"], key="mode")

if mode == "Minterms":
    n = st.sidebar.slider("Number of variables", 2, 10, key="n")
    st.sidebar.text_input("Minterms (comma separated)", key="mt")
    st.sidebar.text_input("Don't-cares (optional)", key="dc")
else:
    st.sidebar.text_input("Expression", key="ex")
    st.sidebar.caption("Use ' or ! for NOT and + for OR. Example: A'B + AC'")

st.sidebar.button("Load 6-variable example", on_click=load_example)

# ---------------- read the input ----------------
try:
    if mode == "Minterms":
        minterms = parse_list(st.session_state.mt, n)
        dcs = parse_list(st.session_state.dc, n)
        if set(minterms) & set(dcs):
            raise ValueError("A number cannot be both a minterm and a don't-care.")
    else:
        terms, n = parse_expr(st.session_state.ex)
        minterms = expr_to_minterms(terms, n)
        dcs = []
        st.sidebar.info(f"Detected {n} variables ({letter(0)} to {letter(n - 1)})")
except ValueError as error:
    st.error(str(error))
    st.stop()

if not minterms:
    st.success("### F = 0")
    st.stop()

# ---------------- run the algorithm ----------------
with st.spinner("Minimizing..."):
    steps, primes, chosen, essential = quine_mccluskey(minterms, dcs, n)

selected = [p for p in primes if p[0] in chosen]
answer = " + ".join(term_str(bits) for bits, _ in selected)
ok = verify(minterms, dcs, n, chosen)

st.success(f"### F = {answer}")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Minterms", len(minterms))
c2.metric("Prime implicants", len(primes))
c3.metric("Essential", len(essential))
c4.metric("Terms in answer", len(selected))
c5.metric("Literals", sum(literal_count(bits) for bits, _ in selected))
c6.metric("Check", "Pass ✓" if ok else "Fail ✗")

# ---------------- tabs ----------------
tab1, tab2 = st.tabs(["Grouping steps", "Prime implicant chart"])

with tab1:
    rows = []
    for number, column in enumerate(steps, 1):
        for ones, items in column:
            for bits, covered in items:
                rows.append({"Column": number, "1s": ones, "Minterms": ",".join(map(str, covered)), "Bits": bits})
    st.dataframe(pd.DataFrame(rows), hide_index=True)

with tab2:
    chart = []
    for bits, covered in primes:
        if bits in essential:
            status = "essential"
        elif bits in chosen:
            status = "chosen"
        else:
            status = ""
        row = {"Term": term_str(bits), "Bits": bits, "Status": status}
        for m in minterms:
            row[str(m)] = "●" if m in covered else ""
        chart.append(row)
    st.dataframe(pd.DataFrame(chart), hide_index=True)
    st.caption("Essential terms are always in the answer. 'chosen' terms were added to cover the rest.")

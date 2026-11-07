# Boolean Logic Minimizer

Minor project for **Digital Circuit Design (DCD)**, NIT Bhopal.

A web app that minimizes Boolean functions of up to 10 variables using the **Quine-McCluskey** method.

**Live app:** <PASTE-STREAMLIT-LINK-HERE>

## Features

- Input as minterms (with optional don't-cares) or as a sum-of-products expression
- Results update as you type
- Minimal expression with counts of minterms, prime implicants, essential terms and literals
- Grouping steps table and prime implicant chart with essential terms marked
- Automatic equivalence check of the answer against the original function

## Method

1. Write each minterm and don't-care in binary and group by number of 1s.
2. Combine terms from neighbouring groups that differ in one bit (that bit becomes `-`). Repeat until nothing combines.
3. Terms that never combine are the prime implicants.
4. Essential prime implicants (the only ones covering some minterm) are always selected.
5. Remaining minterms are covered greedily, choosing the term that covers the most uncovered minterms each time.

## Example

F(A,B,C,D) = Σm(0,1,2,5,6,7,8,9,10,14) gives `F = A′BD + B′C′ + CD′`

## Files

| File | Purpose |
|------|---------|
| `app.py` | Everything: Quine-McCluskey logic (section 1) and Streamlit interface (section 2) |
| `requirements.txt` | Libraries needed |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limitations

- Step 5 is greedy, so for some functions the answer may not have the fewest possible terms
- Expressions must be in sum-of-products form without brackets
- Very large inputs (10 variables with hundreds of minterms) can be slow


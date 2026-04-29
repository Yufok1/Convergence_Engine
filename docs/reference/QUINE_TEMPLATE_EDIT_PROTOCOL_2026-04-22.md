# Quine Template Edit Protocol

**Document:** `QUINE_TEMPLATE_EDIT_PROTOCOL_2026-04-22.md`
**Purpose:** safe editing of templated code-generation inside quine/capsule systems
**Scope:** any file where Python f-strings emit source code that must compile and, if recursive, emit further f-strings

---

## 1. What This Protocol Governs

A quine template is a Python f-string (or nested chain of f-strings) whose output is itself source code. Editing such a template is not editing text; it is editing the program that writes the program. Every brace, quote, and backslash has a level-dependent meaning. This protocol defines the levels, the escape transformations, the failure modes, and the verification steps required to preserve the quine property across edits.

## 2. The Three Levels

| Level | What you are writing | What `{x}` means |
|---|---|---|
| 0 | Host Python. The compiler source. | Inject value of variable `x` from host scope. |
| 1 | Template body inside `f'''...'''`. Code that will exist after generation. | `{{x}}` - literal `{x}` in the generated file. `{x}` still injects from the host. |
| 2 | Template inside a template. Code that writes code. | `{{{{x}}}}` - literal `{x}` in the output of the output. |

## 3. The Doubling Rule

`braces_required = 2 ^ level`

- Level 0 -> 1 brace: `{x}`
- Level 1 -> 2 braces: `{{x}}`
- Level 2 -> 4 braces: `{{{{x}}}}`
- Level 3 -> 8 braces: `{{{{{{{{x}}}}}}}}`

Every level boundary crossed downward doubles the required braces. Every level boundary crossed upward halves them. Count levels, then count braces.

## 4. The Nine Transformations (Level 1 Reference)

When writing inside a Level 1 template, these substitutions produce the listed output:

| Desired output | Write in template |
|---|---|
| `{` | `{{` |
| `}` | `}}` |
| `{variable}` | `{{variable}}` |
| `{"key": "val"}` | `{{"key": "val"}}` |
| `"""` | `\"\"\"` |
| literal `\n` | `\\n` |
| `\` | `\\` |
| `f"{x}"` | `f"{{x}}"` |
| `f"{x}"` at Level 2 | `f"{{{{x}}}}"` |

## 5. Worked Example - One Variable, All Levels

Host variable: `model_name = "gpt2"`

**Level 0 (host Python):**

```python
model_name = "gpt2"
```

**Level 1 (inside template `f'''...'''`):**

```python
# Written in template:
MODEL = "{model_name}"
# Appears in generated file:
MODEL = "gpt2"
```

**Level 1, but you want the generated file to contain a literal `{model_name}` reference:**

```python
# Written in template:
MODEL = "{{model_name}}"
# Appears in generated file:
MODEL = "{model_name}"
```

**Level 2 (template inside template, rare):**

```python
# Written in outer template:
inner = f'''
    MODEL = "{{{{model_name}}}}"
'''
# The outer template produces an inner template that reads:
inner = f'''
    MODEL = "{{model_name}}"
'''
# Which, when the inner template runs, produces:
MODEL = "gpt2"
```

## 6. Common Failures

### 6.1 Collapsed brace

```python
# Wrong - braces eaten by the Level 1 compiler:
data = {"key": "value"}
# Right - braces pass through to the generated file:
data = {{"key": "value"}}
```

### 6.2 Unescaped triple quote

```python
# Wrong - closes the template prematurely:
docstring = """docstring"""
# Right:
docstring = \"\"\"docstring\"\"\"
```

### 6.3 Level confusion (f-string inside f-string)

```python
# Wrong - host tries to evaluate `name`:
print(f"Hello {name}")
# Right - produces an f-string in the output:
print(f"Hello {{name}}")
```

### 6.4 Injection mistake (doubled when you wanted interpolation)

```python
# Wrong - outputs the literal string {model_name}:
model = "{{model_name}}"
# Right - injects the host value:
model = "{model_name}"
```

## 7. Pre-Edit Checklist

1. Read the 50 lines above and the 50 lines below the edit site.
2. Identify the level of the edit site (0, 1, or 2+).
3. Classify every brace in the edit window:
   - host injection -> `{x}`
   - literal in output -> `{{`, `}}`
   - dict in output -> `{{"k": "v"}}`
   - f-string in output -> `{{x}}`
4. If any existing brace pattern is not understood, do not modify it.
5. Confirm the edit is the minimum change that achieves the intent.
6. Confirm the verification commands are prepared for the human operator to run.
7. Do not trigger compilation, regeneration, or quine verification yourself unless the human operator explicitly revokes this boundary for that exact action.

## 8. Verification Commands

Run after every edit, in order.

Operator boundary:

- These commands are for the human operator.
- The agent may prepare, explain, or restate them.
- The agent must not run compilation, regeneration, emission, or verify-quine commands on its own initiative.

```bash
python -m py_compile <quine_file>.py       # host syntax still compiles
python <quine_file>.py --verify-quine      # self-hash still matches
python <quine_file>.py --emit > regen.py   # emission still produces valid output
python -m py_compile regen.py              # emitted file also compiles
diff <quine_file>.py regen.py              # emission is byte-identical (fixed point)
```

A quine that no longer emits a byte-identical copy of itself has lost the fixed-point property and is no longer a quine.

## 9. The Five Precepts (Operational Form)

1. **Read before write.** No edit without reading surrounding context; escape levels and injection sites are not inferable from local syntax alone.
2. **Count braces.** Every `{` has a matching `}` at its own level. Mismatch corrupts emission silently.
3. **Preserve unexplained escaping.** Quadruple braces and stacked backslashes exist for a reason; leave them unless the reason is known.
4. **Test after every edit.** The five verification commands in section 8 are mandatory, not optional.
5. **Minimal diff.** Every added character is a character that can break emission. Prefer surgical edits over refactors.

## 10. Failure Mode Summary

| Symptom | Likely cause |
|---|---|
| `SyntaxError` on host compile | unescaped brace or quote at Level 1 |
| Compiles, emission crashes with `KeyError` | literal `{x}` reached the output but `x` was meant to interpolate |
| Compiles, emission produces `{x}` literal where a value was wanted | over-doubled braces |
| Compiles, emits, regen does not compile | Level 2 escaping lost during edit |
| Compiles, emits, regen compiles, diff non-empty | fixed-point broken; emission is no longer self-identical |
| Compiles, emits, regen identical, hash verify fails | merkle/provenance field not regenerated; check hash-recompute hook |

## 11. When To Stop And Audit

Stop editing and audit the template if any of the following occur:

- three consecutive failed compile attempts in the same region
- a brace pattern appears that does not match any of the nine transformations
- the emitted file differs from the source by more than the edited region
- `--verify-quine` fails despite a clean diff

In all four cases, the edit has crossed a level boundary that was not recognized. Revert and re-read.

---

**End of protocol.**

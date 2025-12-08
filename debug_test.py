import pytest
pytest.skip("Debug script - requires sim_run.log which is not committed", allow_module_level=True)

with open('sim_run.log', 'r') as f:
    lines = f.readlines()
    print(f'Total lines: {len(lines)}')

    # Look for tutor lines
    tutor_lines = [i for i, line in enumerate(lines) if '[MULTI-DOMAIN TUTOR]' in line]
    print(f'Tutor line indices: {tutor_lines[:5]}')

    if tutor_lines:
        print(f'First tutor line: {repr(lines[tutor_lines[0]][:100])}')

        # Check the pattern matching
        import re
        line = lines[tutor_lines[0]]
        print(f'Contains [MULTI-DOMAIN TUTOR]: {"[MULTI-DOMAIN TUTOR]" in line}')
        print(f'Contains Calling: {"Calling" in line}')
        gen_match = re.search(r'Generation (\d+)', line)
        print(f'Generation regex match: {gen_match}')

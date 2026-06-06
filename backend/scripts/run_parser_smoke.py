import sys
sys.path.insert(0, 'backend')
from ai_engine.command_parser import parse_command

def assert_parsed(cmd, action, target, location=None):
    res = parse_command(cmd)
    assert res['action'] == action, f"action mismatch for '{cmd}': {res}"
    assert res['target'] == target, f"target mismatch for '{cmd}': {res}"
    if location is not None:
        assert res.get('location') == location, f"location mismatch for '{cmd}': {res}"

variants = [
    'open downloads',
    'open download',
    'open my downloads',
    'open my downloads folder',
    'please open downloads',
    'can you open downloads',
    'could you open my downloads',
]

for v in variants:
    assert_parsed(v, 'open', 'downloads')

assert_parsed('create folder test', 'create_folder', 'test')
assert_parsed('please create folder projects', 'create_folder', 'projects')
assert_parsed('create a folder called notes in documents', 'create_folder', 'notes', 'documents')
assert_parsed('create a folder on desktop called college', 'create_folder', 'college', 'desktop')
assert_parsed('delete document', 'delete', 'documents')
assert_parsed('remove pictures', 'delete', 'pictures')
res = parse_command('fly to the moon')
assert res['action'] == 'unknown'
print('parser smoke tests passed')

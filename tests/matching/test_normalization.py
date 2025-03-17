import pytest
from tunesynctool.utilities.normalization import clean_str

def test_clean_str_empty():
    assert clean_str('') == ''

def test_clean_str_none():
    assert clean_str(None) == ''

def test_clean_str_basic():
    assert clean_str('Hello World!') == 'hello world'

def test_clean_str_special_characters():
    assert clean_str('feat. Artist ft. Another Artist') == 'artist another artist'
    assert clean_str('feat Artist ft Another Artist') == 'artist another artist'
    assert clean_str('featuring Artist with Another Artist') == 'artist another artist'
    assert clean_str('prod. by Producer') == 'by producer'
    assert clean_str('prod by Producer') == 'by producer'

def test_clean_str_conjunctions():
    assert clean_str('Rock & Roll') == 'rock and roll'
    assert clean_str('Rock + Roll') == 'rock and roll'

def test_clean_str_brackets_parentheses():
    assert clean_str('[Hello] (World)') == 'hello world'

def test_clean_str_quotation_marks_punctuation():
    assert clean_str("It's a 'test'!") == 'its a test'
    assert clean_str('Hello, World!') == 'hello world'

def test_clean_str_separators():
    assert clean_str('Hello/World') == 'hello world'
    assert clean_str('Hello\\World') == 'hello world'
    assert clean_str('Hello_World') == 'hello world'
    assert clean_str('Hello-World') == 'hello world'
    assert clean_str('Hello.World') == 'hello world'
    assert clean_str('Hello, World') == 'hello world'
    assert clean_str('Hello; World') == 'hello world'
    assert clean_str('Hello: World') == 'hello world'

def test_clean_str_whitespace():
    assert clean_str('   Hello   World   ') == 'hello world'
    assert clean_str('Hello   World') == 'hello world'

def test_clean_str_case():
    assert clean_str('Hello World') == 'hello world'
    assert clean_str('HELLO WORLD') == 'hello world'
    assert clean_str('hello world') == 'hello world'

def test_clean_stuff_from_between_parentheses():
    assert clean_str('Hello (World)') == 'hello'
    assert clean_str('Hello (World) (Again)') == 'hello'
    assert clean_str('{curly} [square] (parentheses)') == ''
    assert clean_str('Hello (World) [Again]') == 'hello'
    assert clean_str('2. - Sense Field - Save Yourself - (Album Version)') == '2 sense field save yourself'
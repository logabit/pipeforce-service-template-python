import os
import subprocess


def test_codestyle():
    """
    Apply linter test on all source code.
    :return:
    """

    test_path = os.path.dirname(os.path.realpath(__file__))
    src_path = os.path.dirname(test_path)
    root_path = os.path.dirname(src_path)
    config = os.path.join(root_path, '.pylintrc')
    process = subprocess.run(['pylint', '--rcfile', config, '..', '--output-format=parseable', src_path],
                             stdout=subprocess.PIPE,
                             universal_newlines=True,
                             check=False)
    result = process.stdout
    if '*************' in result:
        msg = 'There are code style errors. Please fix and re-run tests.'
        print('\n' + msg + '\n' + result)
        assert False, msg
    else:
        print('\nGood job! No code style errors found.\n' + result)

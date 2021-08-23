from search_run.dmenu_run import DmenuRun



def test_renders_dmenu():
    DmenuRun().run('echo "abc\ncde\nefg"')

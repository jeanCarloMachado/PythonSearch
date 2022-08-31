import os

class End2End:
    def run(self):
        self._run_shell('pip install python-search')
        self._run_shell('python_search new_project /tmp/test1')

    def _run_shell(self, cmd):
        os.system(cmd)


if __name__ == '__main__':
    import fire
    fire.Fire(End2End)



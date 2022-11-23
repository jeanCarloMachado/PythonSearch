import os
import subprocess;

def sync_host():
  os.system("git config pull.rebase true")


  sync_repo('/entries')
  sync_repo('/src')

def get_current_branch():
  return subprocess.check_output('git branch 2> /dev/null | grep "*" | cut -d" " -f2', shell=True, text=True)

def sync_repo(folder):
  print('Syncing entries project')
  current_branch = get_current_branch()
  os.system(f"cd {folder} ; git add . ; git commit -m 'Automatic changes' && git pull origin {current_branch} && git push origin {current_branch}")


if __name__ == '__main__':
    import fire
    fire.Fire(sync_host)

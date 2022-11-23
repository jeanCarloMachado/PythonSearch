#!/usr/bin/env python3

import os
import subprocess

def sync_from_container():
  os.system("ps_container run /src/sync_hosts.py sync")

def sync_both_from_mac():
  sync()
  sync_archlinux()

def sync_archlinux():
  os.system("ssh -t jean@192.168.178.20 'ps_container run /src/sync_hosts.py sync'")

def sync():
  os.system("git config pull.rebase true")
  sync_repo('/entries')
  sync_repo('/src')


def pull_cb():
  current_branch = get_current_branch()
  os.system("git pull origin " + current_branch)

def get_current_branch():
  return subprocess.check_output('git branch 2> /dev/null | grep "*" | cut -d" " -f2 | tr -d "\n"', shell=True, text=True)

def sync_repo(folder):
  print('Syncing entries project')
  current_branch = get_current_branch()
  print('Current branch: ' + current_branch)

  cmd = f'bash -c "cd {folder} ; git add . ; git commit -m AutomaticChanges && git pull origin {current_branch} ; git push origin {current_branch}"'
  print(cmd)
  os.system(cmd)



if __name__ == '__main__':
    import fire
    fire.Fire()

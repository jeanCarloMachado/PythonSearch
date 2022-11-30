#!/usr/bin/env python3

import os
import subprocess
import time

def sync_both_from_mac():
  sync_archlinux()
  time.sleep(1)
  sync()
  sync_archlinux()

def sync_from_container():
  os.system("ps_container run /src/sync_hosts.py sync")

def sync_archlinux():
  os.system("ssh -t jean@192.168.178.20 \"ps_container run '/src/sync_hosts.py sync'\"")

def sync():
  print("Starting sync current host")
  os.system("git config pull.rebase true")
  sync_repo('/entries')
  sync_repo('/src')


def pull_cb(folder="/entries"):
  current_branch = get_current_branch()
  os.system(f"cd {folder} ; git pull origin " + current_branch)


def get_current_branch():
  return subprocess.check_output('git branch 2> /dev/null | grep "*" | cut -d" " -f2 | tr -d "\n"', shell=True, text=True)

def sync_repo(folder):
  print('Syncing entries project')
  current_branch = get_current_branch()
  print('Current branch: ' + current_branch)

  cmd = f'cd {folder} ; git add . ; git commit -m AutomaticChanges '
  os.system(cmd)

  time.sleep(0.3)
  os.system(f"cd {folder}  ; git pull origin {current_branch} ")
  time.sleep(0.3)
  os.system(f"cd {folder}  ;  git push origin {current_branch} ")



if __name__ == '__main__':
    import fire
    fire.Fire()

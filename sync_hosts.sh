#!/bin/bash

git config pull.rebase true

function current_branch() {
  git branch 2> /dev/null | grep "*" | cut -d" " -f2
}

cd /entries

git add .
git commit -m 'Automatic changes'
git pull origin `current_branch`
git push origin `current_branch`

cd /src
git add .
git commit -m 'Automatic changes'
git pull origin `current_branch`
git push origin `current_branch`

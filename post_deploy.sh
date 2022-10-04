#!/bin/bash

cd /apps/bot

git remote update
if !(git status -uno | grep -q "Your branch is up to date with 'origin/main'.")
then
    git pull
fi

sudo /bin/systemctl restart telebot

cd -

#!/usr/bin/env bash

git push
git push --tags origin master

TAG=$(git describe --abbrev=0 --tags)
git archive ${TAG} --prefix=DuetRRFPlugin/ --format=zip -o ~/Downloads/DuetRRFPlugin_${TAG}.zip

open https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/new
open https://contribute.ultimaker.com/app/developer/plugins

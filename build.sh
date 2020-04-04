#!/usr/bin/env bash

git push --tags origin master

TAG=$(git describe --abbrev=0 --tags)
git archive ${TAG} --prefix=DuetRRFPlugin/ --format=zip -o ~/Downloads/DuetRRFPlugin_${TAG}.zip

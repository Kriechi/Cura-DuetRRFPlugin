#!/usr/bin/env bash

git push --tags

TAG=$(git describe --abbrev=0 --tags)
git archive ${TAG} --prefix=DuetRRFPlugin/ --format=zip -o ~/Downloads/DuetRRFPlugin_${TAG}.zip

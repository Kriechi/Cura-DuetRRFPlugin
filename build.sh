#!/usr/bin/env bash

set -o errexit

TAG=$(git describe --abbrev=0 --tags --exact-match)
git archive ${TAG} --prefix=DuetRRFPlugin/ --format=zip -o ~/Downloads/DuetRRFPlugin_${TAG}.zip

open https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/new
open https://contribute.ultimaker.com/app/developer/plugins

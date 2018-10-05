default: curaplugin

curaplugin:
	git archive HEAD --prefix=DuetRRFPlugin/ --format=zip -o ~/Downloads/DuetRRFPlugin.curaplugin

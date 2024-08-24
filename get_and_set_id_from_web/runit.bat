rem see https://manual.calibre-ebook.com/creating_plugins.html#id14 goto Debugging plugins...
rem click runit from from the directory where the plugin is developed... 
rem this will kill any running calibre, push a new plugin.zip where appropriate and start calibre again

calibre-debug -s
calibre-customize -b .
rem START /b calibre executes calibre sans ouvrir une nouvelle fenêtre d’invite de commandes. 
start /b calibre

SVT-Play.bundle
===============

To use this repository instead of the Plex delivered client do the following:

OSX (with git installed)
===============
* Open a Terminal
* Execute the following commands:

```bash
  # mkdir github
  # cd github
  # git clone git://github.com/Coi-l/SVT-Play.bundle.git
  # cd
  # rm ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/SVT-Play.bundle
  # ln -s ~/github/SVT-Play.bundle/ ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/SVT-Play.bundle
```

* Close the Terminal program

To update the plugin:
* Open a Terminal
* Execute the following commands:

```bash
  # cd github/SVT-Play.bundle
  # git pull
```

* Close the Terminal program

OSX (without git installed)
* Download zip file from here: https://github.com/Coi-l/SVT-Play.bundle/archive/master.zip
* Unzip the file
* Move the unzipped folder to your home directory into a folder called github and rename the unzipped folder to SVT-Play.bundle (removing the -master suffix)
* Open a Terminal
* Execute the following commands

```bash
  # rm ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/SVT-Play.bundle
  # ln -s ~/github/SVT-Play.bundle/ ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/SVT-Play.bundle
```

To update the plugin.
Redownload the zip file and replace the .bundle file found here: github/SVT-Play.bundle

Other OSs
===============
I don't have any possibilities to test out solutions for Windows or Linux. If you know how to do it for any of these 
operating system I'll gladly accept a description and add it here. 

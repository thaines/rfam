# RFAM (Render Farm Asset Manager)

An asset manager for Blender that is designed with 14-18 year old students who have never made an animated film before in mind. In other words its very easy to use, idiot proof (ish), and does some random stuff that happens to be useful in that very specific scenario. Should be usable by others however, as the core feature set is fairly standard and the weird stuff can be ignored, plus its heavily customisable.

The docs directory contains extensive help on how to configure it. Comes with a default configuration that I use for testing.


## Features
* Simple web interface, with an asset list, a home page that shows a priority-sorted list of what a user should be working on, and a team page that shows what everyone is working on.
* New assets are created in the web interface, to encourage sensible defaults, including directory structure.
* Asset types and their states are per-project customisable.
* Profile pictures, so the students can use the interface to learn each others names!
* Built in render farm, which reports render statistics back to the users so they know which files to optimise.
* Automatic credit generation, including licensing information for 3rd party assets.
* No database - stores meta data in .json files next to the .blend files. Users can move files around etc. and there is no risk of the asset manager getting out of sync with the actual data on disk. Makes reverting to backups trivial, and allows syncing between multiple locations via any file sharing technology, each with their own RFAM server. Comes with the disadvantage that it's quite slow as a result.
* Servers only dependency is Python 3 - its easy to run via built in wsgi server, but can be run on a proper server as well.
* Render nodes are dependent on Python 3 and Blender only, and communicate via http from node to server alone. Requires that storage is mounted on both server and nodes (e.g. nfs, samba etc.).
* Cluster support via a monitoring node, that enqueues on the cluster 'single use' render nodes for each job added.
* (untested) Multilingual support.


## Components
It consists of the server, a wsgi app in main.py (run.py uses Pythons built in wsgi server to run it), and a node, which is a python script run.py in the sub-directory node. It is entirely configured using .json files, of which there are many - see docs/configuration.txt for a list of all files and details of the parameters contained in each. A default configuration is provided, which puts all the data in the directory data within the provided rfam file structure.

The directory 'performance' contains performance profiling scripts. My general advice for 3Dami is to use sim_asset_creation.py to fill every team with a fake film (configuration script indicates which team to fill), then test the speed using 'time_assets_page.py'. You want at least 30 page loads per second - if you are not getting this then get faster hardware. The file system is critical, and you ideally want SSD, a SAN or RAID for speed. Don't forget to clean up all the gibberish that sim_asset_creation.py generated afterwards! (just empty the teams directory - the advantage of no database!)

If a cluster is available then you can use it as the render farm. First test that Blender runs on it - Clusters tend to be ultra-conservative and run really old software, that is often incompatible. You then run a single 'prenode' (in directory of same name) - it is configured to watch the server, and then when jobs arrive call a single command with the number of frames required by all new jobs. That command is configurable, and should enqueue on the cluster to run single use nodes, one for every job. Note that the prenode has a name - this is the tag applied to jobs to indicate that the prenode has seen them. Hence you can have multiple names with multiple prenodes, and commands that do stuff other than render, e.g. notify someone etc.

There are a number of helpful scripts provided in misc that tend to prove useful when setting up a real server for a 3Dami event.


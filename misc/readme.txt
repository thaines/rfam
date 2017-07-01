A number of miscellaneous things that are also useful when setting up this system. Be warned they all contain paths that will need to be modified to match your particular setup - these are for people who know basic Linux admin:

* backup.py - Simple Python script that performs a proper incremental backup using rsync with symlinks; to be called from a crontab file.

* go.sh - A script that moves to the right directory, sets the umask (as required when you have users that are all in the same group) and uses authbind to run the server, assuming that authbind will let it use the desired port (invariably port 80) - how I run it in production.

* proj_to_ext.py - Extracts the external assets from an rfam project, but as a standalone script that can be run without a server. Exists for use after an event when the students have messed up the credits.

* rfam-init.d - A file for running rfam properly with the init.d system.

* node.sh - A script file to be handed to qsub when running single use nodes on a Sun grid engine cluster.


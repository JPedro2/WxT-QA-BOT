## MySQL backup folder
The MySQL-Backup container will save the DB backups in this folder. The DB is backed up everyday at 4.30am.
The backup files are compressed as `.tgz`. To  extract backup file you  will needd to be in this directoory and use the following command:

```
tar -xvzf <name-of-file>.tgz
```

If you are running this application in a Linux machine you might want to make sure that your backups do not pile up. For that you can schedule a `cron` job to delete all backups that are older than 2 days by doing the following.

Display the contents of the `crontab` file of the currently logged in user (you may need to use sudo) and edit the current user’s cron jobs, respectively:
```
crontab -l
crontab -e
```
Once the `cron` editor is open (you may select either `[1]nano` or `[2]vim`), copy the following line of code with the respective `path`.
```
0 5 * * * /usr/bin/find /path/to/db/backups/*.tgz -mtime +2 -exec rm {} \;
```
This code executes at exactly 5am everyday and deletes all DB backups that are older than 2 days. You can change either the [frequency of the cron job](https://crontab.guru/) by editing `0 5 * * *` or [how long you want to save backups for](http://manpages.ubuntu.com/manpages/xenial/man1/find.1.html) by editing `-mtime +2`.
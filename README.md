### Workflow:
1. Make changes
2. Update image version in dockerfile
3. Push up add, commit, and push changes to remote branch
4. Rebuild image in Portainer
5. Delete and recreate `/opt/appdata/hebrews-pos/sqlite3/db.sqlite3` database
6. Redeploy stack
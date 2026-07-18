# Administrator Bootstrap

Create the first local super administrator after MongoDB is configured:

```powershell
uv run devmind-auth bootstrap-admin --email <admin-email> --username <admin-username> --password "<strong-password>"
```

The command:

- Uses the configured MongoDB URI and database.
- Refuses weak passwords.
- Refuses to create a second super administrator.
- Does not print secrets.

After bootstrap, sign in through `/api/v1/auth/login` or the frontend Auth tab.

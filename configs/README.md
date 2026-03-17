# Opsight Configuration

## Environments
Opsight supports environment-based configuration through environment variables.

## Files
- `.env.example` — documented template of required variables
- `configs/production.env` — production-style non-secret settings example

## Notes
- Never commit real secrets
- Use environment variables for credentials and connection strings
- Production should not rely on development-only defaults
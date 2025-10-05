#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create Roles with passwords from environment variables
    CREATE ROLE app_owner NOLOGIN;
    CREATE ROLE migrator WITH LOGIN PASSWORD '$MIGRATOR_USER_PASSWORD';
    CREATE ROLE app_user WITH LOGIN PASSWORD '$APP_USER_PASSWORD';

    -- Grant Hierarchy
    GRANT app_owner TO migrator;
    
    -- Configure Database
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO app_owner, migrator, app_user;
    ALTER DATABASE "$POSTGRES_DB" OWNER TO app_owner;

    -- Create Extensions
    \c "$POSTGRES_DB" "$POSTGRES_USER"
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    ALTER SCHEMA public OWNER TO app_owner;

    GRANT USAGE ON SCHEMA public TO app_user, migrator;

    GRANT CREATE, USAGE ON SCHEMA public TO app_owner, migrator;

    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

    -- Set Default Privileges
    ALTER DEFAULT PRIVILEGES FOR ROLE migrator IN SCHEMA public
       GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE migrator IN SCHEMA public
       GRANT USAGE, SELECT ON SEQUENCES TO app_user;

    ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO app_user;
EOSQL
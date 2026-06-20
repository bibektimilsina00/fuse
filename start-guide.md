docker stop nexushq-postgres
make db-up
make migrate

## Kill Port
fuser -k 3001/tcp

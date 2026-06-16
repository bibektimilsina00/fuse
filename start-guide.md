docker stop nexushq-postgres
docker-compose down && docker-compose up -d db redis
make migrate

## Kill Port
fuser -k 3001/tcp

## Create Pull Request
gh pr create --base main --title "type(scope): short description" --body "PR description"

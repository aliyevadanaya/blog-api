
![ERD](.docs/djangoerd.png)

# Blog API

## Database Setup

Apply database migrations:

```bash
python manage.py migrate
```

## Database Seeding

The project includes a custom Django management command for generating sample data.

Run the command with default values:

```bash
python manage.py seed
```

Default generated data:
- 20 users
- 100 posts
- 500 comments
- 8 categories
- 20 tags

### Available Arguments

| Argument | Description | Default |
|---|---|---|
| `--users` | Number of users to create | 20 |
| `--posts` | Number of posts to create | 100 |
| `--comments` | Number of comments to create | 500 |
| `--clear` | Clear existing seeded data before generation | False |

### Examples

```bash
python manage.py seed --users 10 --posts 50 --comments 200
```

```bash
python manage.py seed --clear
```

## Admin Panel

Create an administrator:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver 8080
```

Open the admin panel:

http://127.0.0.1:8080/admin/

## Admin Screenshots

Screenshots are available in `docs/screenshots/`.

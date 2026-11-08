![ERD](.docs/djangoerd.png)

Blog API 

Database setup
Apply database migrations: python manage.py migrate

Database Seeding
The project includes a custom Django management command for generating sample data. 
Run the command with default values: python manage.py seed
Default generated data:
- 20 users
- 100 posts
- 500 comments
- 8 categories
- 20 tags

Available arguments:
1. --users (Number of users to create, default: 20)
2. --posts (Number of posts to create, default: 100)
3. --comments (Number of comments to create, default: 500)
4. --clear (Clear existing seeded data before generation, default: False)

Examples: 
- python manage.py seed --users 10 --posts 50 --comments 200
- python manage.py --clear

Admin Panel
1. Create an administrator:
python manage.py createsuperuser
2. Run the development server:
python manage.py runserver
3. Open the admin panel at:
http://127.0.0.1:8080/admin/

Admin Screenshots
Screenshots are available in docs/screenshots/.
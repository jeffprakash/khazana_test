from app import create_app, db
from flask_migrate import Migrate
from flask.cli import AppGroup

app = create_app()

# Set up migrations
migrate = Migrate(app, db)

# Create a custom CLI group for database commands
db_cli = AppGroup('db')

@app.cli.command('db init')
def init_db():
    """Initialize the database."""
    from flask_migrate import init
    init()

@app.cli.command('db migrate')
def migrate_db():
    """Create a new migration."""
    from flask_migrate import migrate
    migrate()

@app.cli.command('db upgrade')
def upgrade_db():
    """Apply the database migrations."""
    from flask_migrate import upgrade
    upgrade()

@app.cli.command('db downgrade')
def downgrade_db():
    """Downgrade the database migrations."""
    from flask_migrate import downgrade
    downgrade()

if __name__ == '__main__':
    app.run(debug=True,port=5000)

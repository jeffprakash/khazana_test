from app import create_app, db
from flask_migrate import Migrate, MigrateCommand

app = create_app()

# Set up migrations
migrate = Migrate(app, db)

# Add migration command to the CLI
app.cli.add_command(MigrateCommand)

if __name__ == '__main__':
    app.run(debug=True)

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="useractivitylog",
            name="activity_type",
            field=models.CharField(
                choices=[
                    ("register", "Register"),
                    ("login", "Login"),
                    ("logout", "Logout"),
                    ("profile_update", "Profile Update"),
                    ("password_change", "Password Change"),
                    ("email_change", "Email Change"),
                ],
                max_length=20,
            ),
        ),
    ]

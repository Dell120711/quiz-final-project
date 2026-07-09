from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0002_quizattempt_quizanswer"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="useranswerhistory",
            options={
                "verbose_name": "複習狀態",
                "verbose_name_plural": "複習狀態",
            },
        ),
        migrations.AlterField(
            model_name="useranswerhistory",
            name="answered_at",
            field=models.DateTimeField(auto_now=True, verbose_name="最後作答時間"),
        ),
    ]

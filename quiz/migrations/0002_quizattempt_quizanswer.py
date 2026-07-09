import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_count", models.PositiveIntegerField(default=0, verbose_name="題數")),
                ("score", models.PositiveIntegerField(default=0, verbose_name="分數")),
                ("started_at", models.DateTimeField(auto_now_add=True, verbose_name="開始時間")),
                ("completed_at", models.DateTimeField(blank=True, null=True, verbose_name="完成時間")),
                (
                    "chapter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quiz_attempts",
                        to="quiz.chapter",
                        verbose_name="章節",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz_attempts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="使用者",
                    ),
                ),
            ],
            options={
                "verbose_name": "測驗紀錄",
                "verbose_name_plural": "測驗紀錄",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="QuizAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_correct", models.BooleanField(default=False, verbose_name="是否答對")),
                ("answered_at", models.DateTimeField(auto_now_add=True, verbose_name="作答時間")),
                (
                    "attempt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="quiz.quizattempt",
                        verbose_name="測驗紀錄",
                    ),
                ),
                (
                    "correct_option",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="correct_answers",
                        to="quiz.option",
                        verbose_name="正確答案",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="quiz.question",
                        verbose_name="題目",
                    ),
                ),
                (
                    "selected_option",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="selected_answers",
                        to="quiz.option",
                        verbose_name="學生答案",
                    ),
                ),
            ],
            options={
                "verbose_name": "作答明細",
                "verbose_name_plural": "作答明細",
                "ordering": ["id"],
            },
        ),
    ]

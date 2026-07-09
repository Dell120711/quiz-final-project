from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


DEFAULT_CHAPTER_NAME = "雜湊表"


def get_default_chapter():
    # 沒有章節時自動建立雜湊表。
    chapter = Chapter.objects.filter(name=DEFAULT_CHAPTER_NAME).first()
    if chapter:
        return chapter

    only_chapter = Chapter.objects.first() if Chapter.objects.count() == 1 else None
    if only_chapter:
        only_chapter.name = DEFAULT_CHAPTER_NAME
        only_chapter.save(update_fields=["name"])
        return only_chapter

    return Chapter.objects.create(name=DEFAULT_CHAPTER_NAME, order=1)


class Chapter(models.Model):
    name = models.CharField(max_length=100, verbose_name="章節名稱")
    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "章節"
        verbose_name_plural = "章節"

    def __str__(self):
        return self.name


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "簡單"),
        ("medium", "中等"),
        ("hard", "困難"),
    ]

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="章節",
    )
    content = models.TextField(verbose_name="題目內容")
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        verbose_name="難度",
    )
    is_original = models.BooleanField(default=False, verbose_name="原創題")
    explanation = models.TextField(blank=True, verbose_name="解析")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "題目"
        verbose_name_plural = "題目"

    def __str__(self):
        return f"[{self.chapter}] {self.content[:40]}"

    def correct_option(self):
        return self.options.filter(is_correct=True).first()


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="題目",
    )
    content = models.CharField(max_length=500, verbose_name="選項內容")
    is_correct = models.BooleanField(default=False, verbose_name="是否正確")

    class Meta:
        verbose_name = "選項"
        verbose_name_plural = "選項"

    def __str__(self):
        prefix = "正確" if self.is_correct else "選項"
        return f"{prefix}: {self.content[:30]}"

    @property
    def display_content(self):
        # 前台顯示用。
        return self.content


class QuizAttempt(models.Model):
    # 一次測驗一筆。
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        verbose_name="使用者",
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.PROTECT,
        related_name="quiz_attempts",
        verbose_name="章節",
    )
    question_count = models.PositiveIntegerField(default=0, verbose_name="題數")
    score = models.PositiveIntegerField(default=0, verbose_name="分數")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="開始時間")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成時間")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "測驗紀錄"
        verbose_name_plural = "測驗紀錄"

    def __str__(self):
        return f"{self.user.username} - {self.chapter.name} - {self.score}/{self.question_count}"

    @property
    def accuracy(self):
        if not self.question_count:
            return 0
        return int(self.score / self.question_count * 100)

    def finish(self):
        self.completed_at = timezone.now()
        self.save(update_fields=["completed_at"])


class QuizAnswer(models.Model):
    # 一題作答一筆。
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="測驗紀錄",
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT, verbose_name="題目")
    selected_option = models.ForeignKey(
        Option,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_answers",
        verbose_name="學生答案",
    )
    correct_option = models.ForeignKey(
        Option,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correct_answers",
        verbose_name="正確答案",
    )
    is_correct = models.BooleanField(default=False, verbose_name="是否答對")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="作答時間")

    class Meta:
        ordering = ["id"]
        verbose_name = "作答明細"
        verbose_name_plural = "作答明細"

    def __str__(self):
        status = "答對" if self.is_correct else "答錯"
        return f"{self.attempt_id} - {self.question_id} - {status}"


class UserAnswerHistory(models.Model):
    # 只給錯題重複出現用，不放到後台顯示。
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answer_history",
        verbose_name="使用者",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="題目")
    is_correct = models.BooleanField(verbose_name="是否答對")
    wrong_count = models.PositiveIntegerField(default=0, verbose_name="答錯次數")
    answered_at = models.DateTimeField(auto_now=True, verbose_name="最後作答時間")
    next_review = models.DateTimeField(null=True, blank=True, verbose_name="下次複習時間")

    class Meta:
        unique_together = ("user", "question")
        verbose_name = "複習狀態"
        verbose_name_plural = "複習狀態"

    def __str__(self):
        status = "答對" if self.is_correct else "答錯"
        return f"{self.user.username} - {self.question_id} - {status}"

    def update_spaced_repetition(self, answered_correct: bool):
        if answered_correct:
            self.is_correct = True
            days = min(2 ** max(self.wrong_count - 1, 0), 14)
        else:
            self.is_correct = False
            self.wrong_count += 1
            days = 1

        self.next_review = timezone.now() + timezone.timedelta(days=days)
        self.save()

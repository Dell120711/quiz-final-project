from django.contrib import admin

from .models import Option, Question, QuizAnswer, QuizAttempt, get_default_chapter


OPTION_HELP_TEXT = "只輸入選項文字即可，不需要加 A/B/C/D；測驗時系統會依照隨機排列自動標示。"


class OptionInline(admin.TabularInline):
    # 題目頁直接新增選項。
    model = Option
    extra = 4
    min_num = 2
    fields = ["content", "is_correct"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "content":
            formfield.help_text = OPTION_HELP_TEXT
        return formfield


class QuizAnswerInline(admin.TabularInline):
    # 測驗紀錄只拿來看，不在這裡手動新增。
    model = QuizAnswer
    extra = 0
    readonly_fields = ["question", "selected_option", "correct_option", "is_correct", "answered_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # 章節固定為雜湊表，後台不用選。
    exclude = ["chapter"]
    list_display = ["id", "short_content", "difficulty", "is_original", "option_count", "created_at"]
    list_filter = ["difficulty", "is_original"]
    search_fields = ["content", "options__content"]
    inlines = [OptionInline]
    list_editable = ["difficulty", "is_original"]

    def save_model(self, request, obj, form, change):
        # 新增題目時自動指定章節。
        if not obj.chapter_id:
            obj.chapter = get_default_chapter()
        super().save_model(request, obj, form, change)

    @admin.display(description="題目內容")
    def short_content(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")

    @admin.display(description="選項數")
    def option_count(self, obj):
        return obj.options.count()


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    # 保留前台顯示欄位，方便檢查實際文字。
    list_display = ["id", "question", "content", "display_content", "is_correct"]
    list_filter = ["is_correct"]
    search_fields = ["content", "question__content"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "content":
            formfield.help_text = OPTION_HELP_TEXT
        return formfield

    @admin.display(description="前台顯示")
    def display_content(self, obj):
        return obj.display_content


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "chapter", "score", "question_count", "accuracy", "started_at", "completed_at"]
    list_filter = ["started_at", "completed_at"]
    search_fields = ["user__username"]
    readonly_fields = ["user", "chapter", "question_count", "score", "started_at", "completed_at"]
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ["attempt", "question", "selected_option", "correct_option", "is_correct", "answered_at"]
    list_filter = ["is_correct", "answered_at"]
    search_fields = ["attempt__user__username", "question__content"]

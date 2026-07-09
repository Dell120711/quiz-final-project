import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    DEFAULT_CHAPTER_NAME,
    Option,
    Question,
    QuizAnswer,
    QuizAttempt,
    UserAnswerHistory,
    get_default_chapter,
)


QUIZ_COUNTS = (5, 10)
# 題目最多五個選項，寫死到 E。
OPTION_LABELS = ["A", "B", "C", "D", "E"]


def option_label(index):
    if index < len(OPTION_LABELS):
        return OPTION_LABELS[index]
    return ""


def labelled_options(options):
    return [
        {
            "label": option_label(index),
            "option": option,
        }
        for index, option in enumerate(options)
    ]


def get_setup_context(extra=None):
    # 測驗章節固定為雜湊表。
    chapter = get_default_chapter()
    context = {
        "chapter": chapter,
        "chapter_name": DEFAULT_CHAPTER_NAME,
        "counts": QUIZ_COUNTS,
        "question_count": Question.objects.filter(chapter=chapter).count(),
    }
    if extra:
        context.update(extra)
    return context


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "註冊成功，請使用新帳號登入。")
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def home(request):
    return render(request, "quiz/setup.html", get_setup_context())


@login_required
def quiz_setup(request):
    return render(request, "quiz/setup.html", get_setup_context())


@login_required
def quiz_start(request):
    if request.method != "POST":
        return redirect("quiz_setup")

    difficulty = request.POST.get("difficulty", "")

    try:
        count = int(request.POST.get("count", 10))
    except (TypeError, ValueError):
        count = 10
    if count not in QUIZ_COUNTS:
        count = 10

    chapter = get_default_chapter()
    questions = Question.objects.filter(chapter=chapter, options__is_correct=True).distinct()
    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    pool = list(questions)
    if not pool:
        return render(
            request,
            "quiz/setup.html",
            get_setup_context(
                {
                    "error": "目前雜湊表題庫沒有可測驗的題目，請管理員先到 Django Admin 新增題目與正確選項。",
                }
            ),
        )

    # 錯題優先排進下一次測驗。
    due_ids = set(
        UserAnswerHistory.objects.filter(user=request.user, is_correct=False)
        .filter(Q(next_review__isnull=True) | Q(next_review__lte=timezone.now()))
        .values_list("question_id", flat=True)
    )
    review_questions = [question for question in pool if question.id in due_ids]
    new_questions = [question for question in pool if question.id not in due_ids]
    random.shuffle(review_questions)
    random.shuffle(new_questions)
    selected = (review_questions + new_questions)[:count]

    # 選項順序存在 session，避免重新整理後改變。
    option_order = {}
    for question in selected:
        options = list(question.options.all())
        random.shuffle(options)
        option_order[str(question.id)] = [option.id for option in options]

    # 建立本次測驗紀錄。
    attempt = QuizAttempt.objects.create(
        user=request.user,
        chapter=chapter,
        question_count=len(selected),
        score=0,
    )

    request.session["quiz_ids"] = [question.id for question in selected]
    request.session["quiz_option_order"] = option_order
    request.session["quiz_attempt_id"] = attempt.id
    request.session["quiz_index"] = 0
    request.session["quiz_score"] = 0
    request.session["quiz_results"] = []
    request.session.modified = True

    return redirect("quiz_question")


@login_required
def quiz_question(request):
    ids = request.session.get("quiz_ids", [])
    index = request.session.get("quiz_index", 0)

    if not ids:
        return redirect("quiz_setup")
    if index >= len(ids):
        return redirect("quiz_summary")

    question = get_object_or_404(Question, id=ids[index])
    option_ids = request.session.get("quiz_option_order", {}).get(str(question.id), [])
    options_by_id = {option.id: option for option in question.options.all()}
    options = [options_by_id[option_id] for option_id in option_ids if option_id in options_by_id]

    if not options:
        options = list(question.options.all())
        random.shuffle(options)

    return render(
        request,
        "quiz/question.html",
        {
            "question": question,
            "options": options,
            "labelled_options": labelled_options(options),
            "index": index + 1,
            "total": len(ids),
            "progress_pct": int((index / len(ids)) * 100),
        },
    )


@login_required
def quiz_answer(request):
    if request.method != "POST":
        return redirect("quiz_question")

    ids = request.session.get("quiz_ids", [])
    index = request.session.get("quiz_index", 0)

    if not ids or index >= len(ids):
        return redirect("quiz_summary")

    question = get_object_or_404(Question, id=ids[index])
    selected_id = request.POST.get("option_id")
    selected = None
    is_correct = False

    if selected_id:
        selected = Option.objects.filter(id=selected_id, question=question).first()
        is_correct = bool(selected and selected.is_correct)

    correct_opt = question.correct_option()
    if is_correct:
        request.session["quiz_score"] = request.session.get("quiz_score", 0) + 1

    # 記錄本題作答結果。
    attempt = QuizAttempt.objects.filter(id=request.session.get("quiz_attempt_id"), user=request.user).first()
    if attempt:
        QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected,
            correct_option=correct_opt,
            is_correct=is_correct,
        )
        attempt.score = request.session.get("quiz_score", 0)
        if (index + 1) >= len(ids):
            attempt.completed_at = timezone.now()
            attempt.question_count = len(ids)
            attempt.save(update_fields=["score", "question_count", "completed_at"])
        else:
            attempt.save(update_fields=["score"])

    results = request.session.get("quiz_results", [])
    results.append(
        {
            "qid": question.id,
            "selected_id": selected.id if selected else None,
            "correct": is_correct,
        }
    )
    request.session["quiz_results"] = results
    request.session["quiz_index"] = index + 1
    request.session.modified = True

    # 更新錯題狀態。
    history, _ = UserAnswerHistory.objects.get_or_create(
        user=request.user,
        question=question,
        defaults={"is_correct": is_correct, "wrong_count": 0},
    )
    history.update_spaced_repetition(is_correct)

    return render(
        request,
        "quiz/result.html",
        {
            "question": question,
            "selected": selected,
            "correct_opt": correct_opt,
            "is_correct": is_correct,
            "index": index + 1,
            "total": len(ids),
            "is_last": (index + 1) >= len(ids),
        },
    )


@login_required
def quiz_summary(request):
    results = request.session.get("quiz_results", [])
    score = request.session.get("quiz_score", 0)
    total = len(results)
    pct = int(score / total * 100) if total else 0

    detailed = []
    for result in results:
        question = Question.objects.filter(id=result["qid"]).first()
        selected = Option.objects.filter(id=result.get("selected_id")).first()
        correct = question.correct_option() if question else None
        if question:
            detailed.append(
                {
                    "question": question,
                    "selected": selected,
                    "correct_option": correct,
                    "correct": result["correct"],
                }
            )

    return render(
        request,
        "quiz/summary.html",
        {"score": score, "total": total, "pct": pct, "detailed": detailed},
    )


@login_required
def history(request):
    attempts = (
        QuizAttempt.objects.filter(user=request.user)
        .select_related("chapter")
        .prefetch_related("answers")
        .order_by("-started_at")
    )

    return render(
        request,
        "quiz/history.html",
        {"attempts": attempts},
    )


@login_required
def history_detail(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("chapter").prefetch_related(
            "answers__question",
            "answers__selected_option",
            "answers__correct_option",
        ),
        id=attempt_id,
        user=request.user,
    )
    return render(request, "quiz/history_detail.html", {"attempt": attempt})


@login_required
def leaderboard(request):
    attempts = (
        QuizAttempt.objects.filter(completed_at__isnull=False)
        .select_related("user")
        .order_by("-score", "-question_count", "-completed_at")
    )
    # 每位使用者只取最高分。
    best_by_user = {}
    for attempt in attempts:
        if attempt.user_id not in best_by_user:
            best_by_user[attempt.user_id] = attempt

    board = sorted(
        best_by_user.values(),
        key=lambda attempt: (-attempt.score, -attempt.accuracy, attempt.user.username),
    )
    return render(request, "quiz/leaderboard.html", {"board": board[:20]})


@login_required
def wrong_review(request):
    wrong_count = UserAnswerHistory.objects.filter(user=request.user, is_correct=False).count()
    return render(request, "quiz/wrong_review.html", {"wrong_count": wrong_count})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Count, Q
from .models import Task
import anthropic
import os

def generate_kogoto(task_title='', action='create', task_count=0):
    """義雄翁スタイルの小言をAIで生成"""
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError('ANTHROPIC_API_KEY is not configured')

        client = anthropic.Anthropic(api_key=api_key)

        if action == 'done':
            prompt = f"""あなたは田中義雄翁（80歳、昭和の頑固おじいさん）です。
部下がタスクを1つ完了しました。昭和気質で短い反応を1〜2文で言ってください。
完了を褒めつつも「当然じゃ」「遅いわ」などツンデレ気味に。
毎回違う切り口で、同じセリフの繰り返しにならないようにしてください。

完了したタスク名：「{task_title}」
残りの未完了タスク数：{task_count}件"""
        elif action == 'delete':
            prompt = f"""あなたは田中義雄翁（80歳、昭和の頑固おじいさん）です。
部下がタスクを削除しました。昭和気質で短い反応を1〜2文で言ってください。
「逃げるのか」「根性なし」など厳しめだが愛のある小言で。
毎回違う切り口で、同じセリフの繰り返しにならないようにしてください。

削除されたタスク名：「{task_title}」
残りの未完了タスク数：{task_count}件"""
        elif action == 'greeting':
            prompt = f"""あなたは田中義雄翁（80歳、昭和の頑固おじいさん）です。
部下がタスク管理画面を開きました。現在のタスク状況に応じた一言を1〜2文で言ってください。
「じゃ」「わしの時代は」「情けない」「喝」などの口癖を使ってください。
毎回違う切り口で、同じセリフの繰り返しにならないようにしてください。

現在の未完了タスク数：{task_count}件"""
        else:
            prompt = f"""あなたは田中義雄翁（80歳、昭和の頑固おじいさん）です。
以下のタスクに対して、昭和気質で短い小言を1〜2文で言ってください。
「じゃ」「わしの時代は」「情けない」「喝」などの口癖を使ってください。
毎回違う切り口で、同じセリフの繰り返しにならないようにしてください。

タスク名：「{task_title}」
現在の未完了タスク数：{task_count}件"""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=150,
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )
        return message.content[0].text
    except Exception as e:
        print(f'AI小言エラー: {e}')
        return None

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_list')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/signup.html', {'form': form})

@login_required
def task_list(request):
    tasks = request.user.tasks.all().order_by('-created_at')
    ai_kogoto = request.session.pop('ai_kogoto', None)
    ai_kogoto_task = request.session.pop('ai_kogoto_task', None)

    if not ai_kogoto:
        pending_count = tasks.filter(is_done=False).count()
        ai_kogoto = generate_kogoto('', action='greeting', task_count=pending_count)

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'ai_kogoto': ai_kogoto,
        'ai_kogoto_task': ai_kogoto_task,
    })


@login_required
def task_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            task = Task.objects.create(user=request.user, title=title)
            pending_count = Task.objects.filter(user=request.user, is_done=False).count()
            print(f"AI小言生成開始: {title}")
            kogoto = generate_kogoto(title, action='create', task_count=pending_count)
            print(f"AI小言生成結果: {kogoto}")
            if kogoto:
                request.session['ai_kogoto'] = kogoto
                request.session['ai_kogoto_task'] = title
            return redirect('task_list')
    return redirect('task_list')

@login_required
def task_done(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task_title = task.title
    task.is_done = True
    task.save()
    pending_count = Task.objects.filter(user=request.user, is_done=False).count()
    kogoto = generate_kogoto(task_title, action='done', task_count=pending_count)
    if kogoto:
        request.session['ai_kogoto'] = kogoto
        request.session['ai_kogoto_task'] = task_title
    return redirect('task_list')

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task_title = task.title
    task.delete()
    pending_count = Task.objects.filter(user=request.user, is_done=False).count()
    kogoto = generate_kogoto(task_title, action='delete', task_count=pending_count)
    if kogoto:
        request.session['ai_kogoto'] = kogoto
        request.session['ai_kogoto_task'] = task_title
    return redirect('task_list')

@login_required
def user_task_summary(request):
    users = User.objects.annotate(
        total_tasks=Count('tasks'),
        pending_tasks=Count('tasks', filter=Q(tasks__is_done=False)),
        done_tasks=Count('tasks', filter=Q(tasks__is_done=True)),
    ).order_by('-total_tasks')
    return render(request, 'tasks/user_summary.html', {
        'users': users,
    })
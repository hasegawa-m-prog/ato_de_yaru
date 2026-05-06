from django.shortcuts import render, redirect, get_object_or_404
from .models import Task
import anthropic
import os

def generate_kogoto(task_title):
    """義雄翁スタイルの小言をAIで生成"""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": f"""あなたは田中義雄翁（80歳、昭和の頑固おじいさん）です。
以下のタスクに対して、昭和気質で短い小言を1〜2文で言ってください。
「じゃ」「わしの時代は」「情けない」「喝」などの口癖を使ってください。

タスク名：「{task_title}」"""
            }]
        )
        return message.content[0].text
    except Exception as e:
        print(f"AI小言エラー: {e}")
        return None

def task_list(request):
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'tasks/task_list.html', {'tasks': tasks})

def task_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            task = Task.objects.create(title=title)
            # AI小言を生成してsessionに保存
            print(f"AI小言生成開始: {title}")
            kogoto = generate_kogoto(title)
            print(f"AI小言生成結果: {kogoto}")
            if kogoto:
                request.session['ai_kogoto'] = kogoto
                request.session['ai_kogoto_task'] = title
            return redirect('task_list')
    return redirect('task_list')

def task_done(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.is_done = True
    task.save()
    return redirect('task_list')

def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.delete()
    return redirect('task_list')
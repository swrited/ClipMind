# ClipMind 历史记录功能实现文档

## 功能概述

本次更新为 ClipMind 应用添加了以下功能：

1. 修复了用户界面中用户名右边的双箭头问题
2. 实现了使用历史记录的数据库存储功能
3. 实现了与 AI 老师对话记录的保存功能
4. 添加了历史记录详情页面，允许用户查看和继续之前的对话
5. 实现了清空历史记录功能

## 数据库设计

### 表结构

新增了两个数据库表：

#### 1. usage_history 表

```sql
CREATE TABLE IF NOT EXISTS usage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_text TEXT,
    summary TEXT,
    keywords_and_framework TEXT,
    test_questions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 2. chat_history 表

```sql
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usage_history_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' 或 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usage_history_id) REFERENCES usage_history(id)
);
```

### 关系说明

- `usage_history` 表通过 `user_id` 外键关联到 `users` 表
- `chat_history` 表通过 `usage_history_id` 外键关联到 `usage_history` 表
- 每个用户可以有多个使用历史记录
- 每个使用历史记录可以有多个聊天消息

## 后端实现

### 数据库初始化

修改了 `init_db()` 函数，添加了新表的创建：

```python
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建使用历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_text TEXT,
        summary TEXT,
        keywords_and_framework TEXT,
        test_questions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # 创建对话记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usage_history_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usage_history_id) REFERENCES usage_history(id)
    )
    ''')
    
    conn.commit()
    conn.close()
```

### 历史记录相关函数

添加了以下函数用于操作历史记录：

```python
def save_usage_history(user_id, filename, original_text, summary, keywords_and_framework, test_questions):
    """保存使用历史到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO usage_history 
        (user_id, filename, original_text, summary, keywords_and_framework, test_questions) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, filename, original_text, summary, keywords_and_framework, test_questions))
        conn.commit()
        history_id = cursor.lastrowid
        success = True
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        history_id = None
        success = False
    conn.close()
    return success, history_id

def save_chat_message(usage_history_id, role, content):
    """保存聊天消息到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO chat_history 
        (usage_history_id, role, content) 
        VALUES (?, ?, ?)
        """, (usage_history_id, role, content))
        conn.commit()
        success = True
    except Exception as e:
        print(f"保存聊天消息失败: {e}")
        success = False
    conn.close()
    return success

def get_user_history(user_id):
    """获取用户的使用历史"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, filename, summary, created_at 
    FROM usage_history 
    WHERE user_id = ? 
    ORDER BY created_at DESC
    """, (user_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_history_detail(history_id):
    """获取历史记录的详细信息"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取历史记录详情
    cursor.execute("""
    SELECT * FROM usage_history WHERE id = ?
    """, (history_id,))
    history = dict(cursor.fetchone()) if cursor.fetchone() else None
    
    if history:
        # 获取聊天记录
        cursor.execute("""
        SELECT role, content, created_at 
        FROM chat_history 
        WHERE usage_history_id = ? 
        ORDER BY created_at ASC
        """, (history_id,))
        chat_history = [dict(row) for row in cursor.fetchall()]
        history['chat_history'] = chat_history
    
    conn.close()
    return history
```

### 修改处理文件的路由

在处理完成后保存结果到数据库：

```python
# 保存到数据库
processing_tasks[task_id]['progress'] = 98
processing_tasks[task_id]['message'] = '正在保存处理结果...'

user_id = session.get('user_id')
success, history_id = save_usage_history(
    user_id, 
    file_info, 
    text, 
    summary, 
    keywords_and_framework, 
    test_questions
)

# 处理完成
processing_tasks[task_id]['status'] = 'completed'
processing_tasks[task_id]['progress'] = 100
processing_tasks[task_id]['message'] = '处理完成'

return jsonify({
    "original_text": text,
    "summary": summary,
    "keywords_and_framework": keywords_and_framework,
    "test_questions": test_questions,
    "history_id": history_id
})
```

### 修改聊天路由

保存用户和 AI 的对话到数据库：

```python
# 如果有历史记录ID，保存聊天记录到数据库
if history_id:
    # 保存用户消息
    save_chat_message(history_id, 'user', user_message)
    # 保存AI回复
    save_chat_message(history_id, 'assistant', ai_response)
```

### 添加历史记录详情页面路由

```python
@app.route('/history/<int:history_id>')
def history_detail(history_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    username = session.get('username')
    
    # 获取历史记录详情
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 确认该历史记录属于当前用户
    cursor.execute("SELECT user_id FROM usage_history WHERE id = ?", (history_id,))
    record = cursor.fetchone()
    
    if not record or record['user_id'] != user_id:
        conn.close()
        return redirect(url_for('profile'))
    
    # 获取历史记录详情
    cursor.execute("""
    SELECT * FROM usage_history WHERE id = ?
    """, (history_id,))
    history = dict(cursor.fetchone())
    
    # 获取聊天记录
    cursor.execute("""
    SELECT role, content, created_at 
    FROM chat_history 
    WHERE usage_history_id = ? 
    ORDER BY created_at ASC
    """, (history_id,))
    chat_history = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('history_detail.html',
                          username=username,
                          history=history,
                          chat_history=chat_history)
```

### 修改清空历史记录路由

```python
@app.route('/clear_history')
def clear_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    
    # 从数据库中删除用户的历史记录
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 首先获取所有历史记录ID
    cursor.execute("SELECT id FROM usage_history WHERE user_id = ?", (user_id,))
    history_ids = [row[0] for row in cursor.fetchall()]
    
    # 删除相关的聊天记录
    for history_id in history_ids:
        cursor.execute("DELETE FROM chat_history WHERE usage_history_id = ?", (history_id,))
    
    # 删除历史记录
    cursor.execute("DELETE FROM usage_history WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('profile'))
```

### 修改个人中心路由

从数据库获取真实的历史记录：

```python
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 获取用户信息
    user_id = session.get('user_id')
    username = session.get('username')

    # 从数据库获取用户信息
    import datetime
    
    # 获取用户注册时间
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    register_time = user_data['created_at'] if user_data else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 获取使用历史
    cursor.execute("SELECT COUNT(*) as count FROM usage_history WHERE user_id = ?", (user_id,))
    usage_data = cursor.fetchone()
    usage_count = usage_data['count'] if usage_data else 0
    
    # 计算加入天数
    try:
        register_date = datetime.datetime.strptime(register_time, '%Y-%m-%d %H:%M:%S')
    except:
        register_date = datetime.datetime.strptime(register_time, '%Y-%m-%d %H:%M:%S.%f')
    join_days = (datetime.datetime.now() - register_date).days
    
    # 获取上次使用时间
    cursor.execute("SELECT created_at FROM usage_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    last_usage_data = cursor.fetchone()
    last_usage = last_usage_data['created_at'].split(' ')[0] if last_usage_data else '暂无记录'
    
    # 获取使用历史
    history = get_user_history(user_id)
    
    conn.close()

    return render_template('profile.html',
                          username=username,
                          user_id=user_id,
                          register_time=register_time,
                          usage_count=usage_count,
                          join_days=join_days,
                          last_usage=last_usage,
                          history=history)
```

## 前端实现

### 修改个人中心页面

更新了历史记录显示部分，添加了可点击的链接：

```html
<div class="profile-info">
  <h3 class="profile-info-title">使用历史</h3>
  {% if history %}
    {% for item in history %}
    <div class="history-item">
      <div class="history-item-title">
        <a href="{{ url_for('history_detail', history_id=item.id) }}">{{ item.filename }}</a>
      </div>
      <div class="history-item-date">{{ item.created_at }}</div>
      <div class="history-item-summary">{{ item.summary[:150] }}{% if item.summary|length > 150 %}...{% endif %}</div>
      <div class="mt-2">
        <a href="{{ url_for('history_detail', history_id=item.id) }}" class="btn btn-sm btn-outline-primary">查看详情</a>
      </div>
    </div>
    {% endfor %}
  {% else %}
  <p>暂无使用记录</p>
  {% endif %}
</div>
```

### 创建历史记录详情页面

新增了 `history_detail.html` 模板，包含以下主要功能：

1. 显示历史记录的详细信息
2. 使用选项卡显示不同类型的内容（摘要、关键词、测试问题、原始文本）
3. 显示与 AI 老师的对话记录
4. 允许用户继续与 AI 老师对话

关键代码片段：

```html
<div class="tab-content" id="myTabContent">
  <div class="tab-pane fade show active" id="summary" role="tabpanel">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">内容总结</h5>
        <div class="card-text">{{ history.summary|safe }}</div>
      </div>
    </div>
  </div>
  <!-- 其他选项卡内容 -->
  
  <div class="tab-pane fade" id="test" role="tabpanel">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">课堂测试</h5>
        <div class="card-text">{{ history.test_questions|safe }}</div>
        
        <div class="mt-4">
          <h5>与AI老师对话</h5>
          <div class="chat-container" id="chatContainer">
            {% if chat_history %}
              {% for message in chat_history %}
                <div class="chat-message {% if message.role == 'user' %}user-message{% else %}assistant-message{% endif %}">
                  <div class="message-content">{{ message.content }}</div>
                  <div class="message-time">{{ message.created_at }}</div>
                </div>
              {% endfor %}
            {% else %}
              <div class="text-center text-muted">
                <p>暂无对话记录，开始提问吧！</p>
              </div>
            {% endif %}
          </div>
          
          <div class="chat-input-container">
            <input type="text" class="chat-input" id="chatInput" placeholder="输入您的问题...">
            <button class="send-btn" id="sendBtn">发送</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 修改前端 JavaScript 代码

在处理完成后保存历史记录 ID：

```javascript
// 存储原始数据
rawData.original_text = data.original_text;
rawData.summary = data.summary;
rawData.keywords_and_framework = data.keywords_and_framework || '';
rawData.test_questions = data.test_questions || '';
rawData.history_id = data.history_id || null;
```

在聊天请求中包含历史记录 ID：

```javascript
fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: message,
    chat_history: chatHistory,
    context: {
      original_text: rawData.original_text,
      summary: rawData.summary,
      test_questions: rawData.test_questions,
      history_id: rawData.history_id
    }
  })
})
```

## 使用流程

1. 用户登录后，在使用页面上传并处理文件
2. 处理结果自动保存到数据库
3. 用户与 AI 老师的对话也会保存到数据库
4. 用户可以在个人中心页面查看所有的使用历史
5. 用户可以点击历史记录查看详情
6. 用户可以在历史记录详情页面查看之前的对话记录
7. 用户可以继续与 AI 老师对话，新的对话记录会自动保存
8. 用户可以清空所有历史记录

## 总结

本次更新为 ClipMind 应用添加了使用历史记录和对话记录功能，大大提高了应用的用户体验。用户现在可以随时回顾之前的学习内容和对话记录，继续之前的学习过程，使学习更加连贯和高效。

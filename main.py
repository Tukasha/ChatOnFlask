from flask import Flask, request, session, redirect, url_for, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import threading
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(hours=24)

socketio = SocketIO(app)

users = {}
messages = []

lock = threading.Lock()

base_template = '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ title }}</title>
<style>
  :root {
    --bg-color: #1e1e2f;
    --container-bg: #2a2a3d;
    --chat-bg: #121222;
    --text-color: #eee;
    --accent-color: #80d8ff;
    --accent-hover: #4fc3f7;
    --form-bg: #22223b;
    --error-color: #ff6b6b;
    --timestamp-color: #666;
  }
  .day-theme {
    --bg-color: #f0f4f8;
    --container-bg: #ffffff;
    --chat-bg: #e6ebf1;
    --text-color: #222222;
    --accent-color: #0066cc;
    --accent-hover: #004a99;
    --form-bg: #d9e2ef;
    --error-color: #cc0000;
    --timestamp-color: #555555;
  }
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: var(--bg-color);
    color: var(--text-color);
    margin: 0;
    padding: 0;
    display: flex;
    height: 100vh;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .container {
    background: var(--container-bg);
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
    width: 90vw;
    max-width: 600px;
    height: 80vh;
    display: flex;
    flex-direction: column;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px 5px 20px;
  }
  h1 {
    margin: 0;
    color: var(--accent-color);
    font-weight: 700;
    font-size: 1.5rem;
  }
  #theme-label {
    font-weight: 600;
    font-size: 0.9rem;
    user-select: none;
    color: var(--accent-color);
    cursor: pointer;
    padding: 8px 12px;
    border-radius: 6px;
    background-color: var(--form-bg);
    transition: background-color 0.3s ease;
  }
  #theme-label:hover {
    background-color: var(--accent-hover);
    color: #fff;
  }
  #chat {
    flex: 1;
    overflow-y: auto;
    background: var(--chat-bg);
    padding: 15px;
    border-radius: 0 0 8px 8px;
    color: var(--text-color);
    font-size: 14px;
    line-height: 1.3em;
  }
  #chat .message {
    margin-bottom: 10px;
    word-wrap: break-word; /* Перенос слов */
    overflow-wrap: break-word; /* Перенос слов */
    white-space: pre-wrap; /* Перенос строк по пробелам и перенос длинных слов */
    max-width: 75ch; /* Ограничение длины строки до 75 символов */
  }
  #chat .username {
    font-weight: 700;
  }
  #chat .timestamp {
    color: var(--timestamp-color);
    font-size: 10px;
    margin-right: 5px;
  }
  #chat .message img {
    display: block;
    margin-top: 5px;
    max-width: 100%;
    max-height: 300px;
    border-radius: 6px;
    object-fit: contain;
  }
  form {
    display: flex;
    align-items: center;
    padding: 10px;
    background: var(--form-bg);
    border-radius: 0 0 8px 8px;
  }
  /* Msg input with beautiful style */
  #msg-input {
    flex: 1;
    border: none;
    border-radius: 25px;
    padding: 12px 20px;
    font-size: 15px;
    background-color: var(--container-bg);
    color: var(--text-color);
    box-shadow:
      inset 0 0 5px rgba(0,0,0,0.7),
      0 4px 6px rgba(0,0,0,0.3);
    transition: background-color 0.3s ease, box-shadow 0.3s ease;
    margin-right: 8px;
  }
  #msg-input::placeholder {
    color: var(--timestamp-color);
    font-style: italic;
  }
  #msg-input:focus {
    outline: none;
    background-color: var(--chat-bg);
    box-shadow:
      inset 0 0 8px var(--accent-color),
      0 4px 10px var(--accent-color);
  }
  /* Make username input visually same style as msg-input */
  #username {
    border: none;
    border-radius: 25px;
    padding: 12px 20px;
    font-size: 15px;
    background-color: var(--container-bg);
    color: var(--text-color);
    box-shadow:
      inset 0 0 5px rgba(0,0,0,0.7),
      0 4px 6px rgba(0,0,0,0.3);
    transition: background-color 0.3s ease, box-shadow 0.3s ease;
    margin: 0;
    flex: 1;
  }
  #username::placeholder {
    color: var(--timestamp-color);
    font-style: italic;
  }
  #username:focus {
    outline: none;
    background-color: var(--chat-bg);
    box-shadow:
      0 0 8px var(--accent-color),
      inset 0 0 8px var(--accent-color);
  }
  /* Wrap username and button on one line */
  #register-container form {
    display: flex;
    width: 100%;
    gap: 12px;
    align-items: center;
  }
  /* Hidden file input */
  input[type=file] {
    display: none;
  }
  /* Custom file upload button */
  label#upload-label {
    background: var(--accent-color);
    color: #111;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s ease;
    margin-right: 8px;
    user-select: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  label#upload-label:hover {
    background-color: var(--accent-hover);
    box-shadow: 0 4px 8px var(--accent-hover);
  }
  button {
    border: none;
    background: var(--accent-color);
    color: #111;
    padding: 14px 18px;
    font-size: 18px; /* Enlarged text */
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  button:hover {
    background-color: var(--accent-hover);
    box-shadow: 0 4px 8px var(--accent-hover);
  }
  .error {
    color: var(--error-color);
    text-align: center;
    margin-top: 10px;
  }
  /* Registration form styles */
  #register-container {
    background: var(--container-bg);
    border-radius: 12px;
    width: 320px;
    padding: 30px 40px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    text-align: center;
    margin: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  #register-container h2 {
    margin-bottom: 25px;
    color: var(--accent-color);
    font-weight: 700;
    font-size: 1.8rem;
    user-select: none;
  }
</style>
</head>
<body>

<div class="container" id="container">
  <div class="header">
    <h1>Общий чат</h1>
    <div id="theme-label" title="Переключить тему" tabindex="0" role="button" aria-pressed="false" aria-label="Переключить тему">...</div>
  </div>
  {{ content|safe }}
</div>

<script>
  const container = document.getElementById('container');
  const themeLabel = document.getElementById('theme-label');

  function updateThemeLabel(day) {
    themeLabel.textContent = day ? 'Светлая тема' : 'Тёмная тема';
    themeLabel.setAttribute('aria-pressed', day ? 'true' : 'false');
  }

  function setTheme(day) {
    if(day){
      document.body.classList.add('day-theme');
    } else {
      document.body.classList.remove('day-theme');
    }
    localStorage.setItem('dayTheme', day ? 'true' : 'false');
    updateThemeLabel(day);
  }

  const savedTheme = localStorage.getItem('dayTheme');
  let isDay = false;
  if(savedTheme === 'true'){
    isDay = true;
  }
  setTheme(isDay);

  themeLabel.addEventListener('click', () => {
    isDay = !isDay;
    setTheme(isDay);
  });
  themeLabel.addEventListener('keydown', (e) => {
    if(e.key === 'Enter' || e.key === ' '){
      e.preventDefault();
      isDay = !isDay;
      setTheme(isDay);
    }
  });
</script>

</body>
</html>
'''

register_form_content = '''
<div id="register-container">
  <h2>Регистрация в чате</h2>
  <form method="POST" action="{{ url_for('register') }}">
    <input id="username" maxlength="20" minlength="2" required autofocus placeholder="Введите имя пользователя" name="username" autocomplete="off" />
    <button type="submit">Войти</button>
  </form>
  {% if error %}
  <div class="error">{{ error }}</div>
  {% endif %}
</div>
'''

chat_page_content = '''
<div id="chat"></div>

<form id="send-form" enctype="multipart/form-data">
  <input id="msg-input" autocomplete="off" placeholder="Введите сообщение..." maxlength="500" />
  
  <label for="img-input" id="upload-label" title="Загрузить изображение">Загрузить изображение</label>
  <input type="file" id="img-input" accept="image/*" />

  <button type="submit">Отправить</button>
</form>

<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
<script>
  const socket = io();
  const chatDiv = document.getElementById('chat');
  const form = document.getElementById('send-form');
  const msgInput = document.getElementById('msg-input');
  const imgInput = document.getElementById('img-input');

  // Mapping from username to color, loaded from server
  let usernameColors = {};

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatTime(timestamp) {
    const d = new Date(timestamp);
    return d.toLocaleTimeString();
  }

  // Store messages for continuous display
  let allMessages = [];

  function addMessages(msgs, scrollToBottom=false) {
    msgs.forEach(m => {
      allMessages.push(m);
    });
    
    // Limit stored messages to last 100
    if(allMessages.length > 100){
      allMessages = allMessages.slice(allMessages.length - 100);
    }

    chatDiv.innerHTML = '';
    allMessages.forEach(m => {
      const msgEl = document.createElement('div');
      msgEl.className = 'message';
      let color = m.color || '#ffffff';
      let html = '<span class="timestamp">[' + formatTime(m.timestamp) + ']</span>' +
                 '<span class="username" style="color: ' + color + ';">' + escapeHtml(m.username) + '</span>: ';
      if(m.text){
        html += escapeHtml(m.text);
      }
      if(m.image){
        html += '<br><img src="' + m.image + '" alt="image" />';
      }
      msgEl.innerHTML = html;
      chatDiv.appendChild(msgEl);
    });
    if(scrollToBottom){
      chatDiv.scrollTop = chatDiv.scrollHeight;
    }
  }

  socket.on('load_messages', (msgs) => {
    allMessages = msgs;
    addMessages([], true);
  });

  socket.on('user_colors', (colors) => {
    usernameColors = colors;
  });

  socket.on('new_message', (msg) => {
    addMessages([msg], true);
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const text = msgInput.value.trim();
    const file = imgInput.files[0];

    if(text.length === 0 && !file){
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const base64Data = reader.result;
      socket.emit('send_message', {text: text, image: base64Data});
      msgInput.value = '';
      imgInput.value = '';
    };

    if(file){
      const maxSize = 2 * 1024 * 1024;
      if(file.size > maxSize){
        alert('Размер изображения не должен превышать 2MB');
        return;
      }
      reader.readAsDataURL(file);
    } else {
      socket.emit('send_message', {text: text});
      msgInput.value = '';
    }
  });
</script>
'''

def random_color():
    r = random.randint(100, 255)
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    return f'#{r:02X}{g:02X}{b:02X}'

def render_page(content, title=''):
    return render_template_string(base_template, content=content, title=title)

@app.route('/', methods=['GET'])
def index():
    if 'username' not in session:
        return redirect(url_for('register'))
    return render_page(chat_page_content, title='Общий чат')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            error = 'Введите имя пользователя'
        elif len(username) < 2 or len(username) > 20:
            error = 'Имя пользователя должно быть от 2 до 20 символов'
        else:
            with lock:
                if username in users:
                    error = 'Данное имя уже занято'
                else:
                    color = random_color()
                    users[username] = color
            if not error:
                session['username'] = username
                session.permanent = True
                return redirect(url_for('index'))
    return render_page(render_template_string(register_form_content, error=error), title='Регистрация')

@app.before_request
def make_session_permanent():
    session.permanent = True

@socketio.on('connect')
def handle_connect():
    with lock:
        last_msgs = messages[-100:]
        emit('load_messages', last_msgs)
        emit('user_colors', users)

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        emit('error', {'error': 'Not authenticated'})
        return
    
    username = session['username']
    text = data.get('text', '')
    image_data = data.get('image', None)

    if not isinstance(text, str):
        emit('error', {'error': 'Invalid text data'})
        return
    text = text.strip()
    if len(text) > 500:
        emit('error', {'error': 'Message length invalid'})
        return

    image = None
    if image_data:
        if not (isinstance(image_data, str) and image_data.startswith('data:image/')):
            emit('error', {'error': 'Invalid image data'})
            return
        if len(image_data) > 5 * 1024 * 1024:
            emit('error', {'error': 'Image too large'})
            return
        image = image_data

    if not text and not image:
        emit('error', {'error': 'Message must contain text or image'})
        return
    
    with lock:
        if username not in users:
            users[username] = random_color()
        color = users[username]

        msg = {
            'username': username,
            'text': text,
            'timestamp': datetime.utcnow().isoformat(),
            'color': color
        }
        if image:
            msg['image'] = image
        messages.append(msg)

    emit('new_message', msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)

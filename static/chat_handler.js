var socket = io();
var chat = document.getElementById('chat');
var input = document.getElementById('user_input');
var inputHeading = document.getElementById('input-heading');
var llm_model_select = document.getElementById('llm_model');
var knowledge_base_select = document.getElementById('kb');
var spinner = document.getElementById('spinner');
var send_button = document.getElementById('send_button');

let username = getCookie("username");
  if (username == "") {
    username = "Anonymous";
    setCookie("username", username, 365);
  }

function renderUserMessage(txt) {
  return txt.replace("\n","\n<br>");
}

function message_as_html(msg){
    var entry = document.createElement('div');
    if (msg.role === 'user') {
        entry.className = "user-message";
        entry.innerHTML = "<img src='/static/svg-icons/square-bubble-user-svgrepo-com.svg' class=\"user-icon\" style='height:23px;width:23px;margin-right:10px;vertical-align:middle;'>"
            + "<span><span class='user'>" + msg.username + ":</span><div class='message'>" + renderUserMessage(msg.content) + "</div></span>";
    } else {
        entry.className = "assistant-message";
        entry.innerHTML = "<img src='/static/svg-icons/robot-svgrepo-com.svg' class=\"user-icon\" style='height:23px;width:23px;margin-right:10px;vertical-align:middle;'>"
            + "<span><span class='assistant'>ausma.ai:</span><div class='message'>" + msg.content + "</div></span>"
            + "<a href=\"/download_message/"+msg.id+"\" target=\"_blank\" rel=\"noopener\" download>"
            + "<img src='/static/svg-icons/align-bottom-svgrepo-com.svg' class=\"assistant-utils-download\" style='height:30px;width:30px;margin-right:5px;vertical-align:middle;'>"
            + "</a>"
            + "<a href=\"/download_rag_sources/"+msg.id+"\" target=\"_blank\" rel=\"noopener\" download>"
            + "<img src='/static/svg-icons/copy-svgrepo-com.svg' class=\"assistant-utils-download\" style='height:30px;width:30px;margin-right:5px;vertical-align:middle;'>"
            + "</a>"
            + "<span class='assistant-model'>("+msg.username+")</span>";
    }
    return entry;
}

//inputHeading.innerText = document.title = `ausma.ai: ${room.name}`;
socket.emit('join_room', {"room_id": room.id, "username": username});
fetch(`/room_history/${room.id}`).then(r => r.json()).then(r => {
    console.log('Response', r) // You will get JSON response here.
    r.forEach(
        function(message) {
            chat.appendChild(message_as_html(message));
            }
        )
    }
)


socket.on('message', function(data) {
  var entry = document.createElement('div');
  if (data.role !== 'user') {
    spinner.style.display = 'none';
    enableInputs();
  }
  chat.appendChild(message_as_html(data));
  chat.scrollTop = chat.scrollHeight;
});

socket.on('progress', function(data) {
  tokens_per_s = data.new_tokens / data.duration_s;
  tokens_per_s_formatted = Number(tokens_per_s).toFixed(3);
  tokens = data.total_response_tokens;
  spinner.style.display = 'flex';
  var msg = 'Processing... ' + tokens_per_s_formatted + ' tokens/s, total so far: ' + tokens + ' tokens';
  setProcessingText(msg);
});

function setProcessingText(txt){
  var collection = document.getElementsByClassName('processing')
  // there should only be one item, but it is only identified by the class so get a list
  for (let i = 0; i < collection.length; i++) {
    collection[i].innerHTML = txt;
  }
}

function getSelectedCase() {
  let radios = document.getElementsByName('rag_type');
  for (let i = 0; i < radios.length; i++) {
    if (radios[i].checked) {
      return radios[i].value;
    }
  }
  return 'none';
}

function sendMessage() {
  var user_input = input.value;
  var llm_model = llm_model_select.value;
  var kb = knowledge_base_select.value;
  var rag_type_select = getSelectedCase();
  if (user_input.trim() !== '') {
    socket.send({user_input: user_input, llm_model: llm_model, kb_name: kb, room_id: room.id, username: username});
    input.value = '';
    spinner.style.display = 'flex';
    setProcessingText('Processing...');
    disableInputs();
  }
}

function disableInputs() {
  var input = document.getElementById('user_input');
  var rag_type = document.getElementsByName('rag_type');
  var llm_model_select = document.getElementById('llm_model');
  var send_button = document.getElementById('send_button');

  inputDisabled = true;
  input.disabled = true;
  rag_type.forEach((e) => {
    e.disabled = true;
  });
  llm_model_select.disabled = true;
  send_button.disabled = true;
}

function enableInputs() {
  var input = document.getElementById('user_input');
  var rag_type = document.getElementsByName('rag_type');
  var llm_model_select = document.getElementById('llm_model');
  var send_button = document.getElementById('send_button');

  inputDisabled = false;
  input.disabled = false;
  rag_type.forEach((e) => {
    e.disabled = false;
  });
  llm_model_select.disabled = false;
  send_button.disabled = false;
  input.focus();
}

input.addEventListener('keypress', function(e) {
  if ((e.key === 'Enter')&& !e.shiftKey) sendMessage();
});

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
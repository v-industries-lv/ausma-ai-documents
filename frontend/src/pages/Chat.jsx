import { useContext, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import styles from "./Chat.module.css";
import "./Index.css";
import { socket } from "../socket";
import KnowledgeBaseSelector from "../components/KnowledgeBaseSelector";
import ModelSelector from "../components/ModelSelector";
import Spinner from "../components/Spinner";
import { MarkdownHooks } from "react-markdown";
import rehypeStarryNight from "rehype-starry-night";
import "@wooorm/starry-night/style/both";
import { UsernameContext } from "../components/UserName";
import onigurumaURL from "vscode-oniguruma/release/onig.wasm?url";
import ChatCToolbar from "../components/ChatToolbar";
import { RagReferenceModal } from "../components/RagReferenceContent";
import { renderNewLines } from "../utils/jsxUtils";

export default function ChatWrapper() {
  const params = useParams();
  const roomId = params.room;
  return <Chat key={roomId} roomId={roomId} />;
}

function Chat({ roomId }) {
  const [_roomDefaults, setRoomDefaults] = useState(null);
  const { username } = useContext(UsernameContext);
  useEffect(() => {
    async function load() {
      const req = await fetch(`/api/config/room_defaults`);
      const json = await req.json();
      setRoomDefaults(json ?? {});
    }
    load();
  }, []);
  const roomDefaults = _roomDefaults ?? {};

  const [room, setRoom] = useState({});
  useEffect(() => {
    async function fetchRoomDetails() {
      const req = await fetch(`/api/room/${roomId}`);
      const json = await req.json();
      setRoom(json ?? {});
    }
    fetchRoomDetails();
  }, [roomId]);

  // knowledge base set by the UI
  const [_kb, setKb] = useState(null);
  // model set by the UI
  const [_model, setModel] = useState(null);

  const [progress, setProgress] = useState({ status: "initial" });

  useEffect(() => {
    async function updateInitialProgress() {
      const req = await fetch(`/api/room/${roomId}/progress`);
      const json = await req.json();
      if (json) {
        setProgress((progress) =>
          progress.status === "initial" ? json : progress
        );
      }
    }
    updateInitialProgress();
  }, [roomId]);
  useEffect(() => {
    function onMessage(data, targetRoomId) {
      if (targetRoomId === roomId) {
        // remove previous temp messages (where id===null)
        // the add the new (temporary or normal message)
        setHistory((history) => [...history.filter((msg) => msg.id), data]);
      }
    }
    function onProgress(data, targetRoomId) {
      if (targetRoomId === roomId) {
        setProgress(data);
      }
    }
    function onRoomList(data) {
      const room_data = data.find((r) => r.id === roomId) ?? {};
      setRoom(room_data);
    }
    socket.on("message", onMessage);
    socket.on("progress", onProgress);
    socket.on("rooms_list", onRoomList);
    socket.emit("join_room", { room_id: roomId });

    return () => {
      socket.off("message", onMessage);
      socket.off("progress", onProgress);
      socket.off("rooms_list", onRoomList);
      socket.emit("leave_room", { room_id: roomId });
    };
  }, [roomId]);

  const [history, setHistory] = useState([]);
  useEffect(() => {
    async function fetchRoomDetails() {
      const req = await fetch(`/api/room_history/${roomId}`);
      const json = await req.json();
      setHistory(json ?? {});
    }
    fetchRoomDetails();
  }, [roomId]);

  let lastAssitentMessage = null;
  history.forEach((element) => {
    if (element.role === "assistant") {
      lastAssitentMessage = element;
    }
  });

  const [reference, setReference] = useState(null);

  // model set by constraints from history
  const lockedModel = lastAssitentMessage?.username;
  // effective model - to be used
  const model = lockedModel ?? _model ?? roomDefaults?.model;

  function getLastKnowledgeBase() {
    let kb = null;
    const rag_sources =
      JSON.parse(lastAssitentMessage?.rag_sources ?? "[]") ?? [];
    rag_sources.forEach((rag_source) => {
      const current_kb = rag_source.knowledge_base;
      if (current_kb) {
        kb = current_kb;
      }
    });
    return kb;
  }
  // knowledge base last used
  const lastKnowledgeBase = getLastKnowledgeBase();
  // effective knowledge base
  const kb = _kb ?? lastKnowledgeBase ?? roomDefaults?.knowledge_base ?? "None";

  const generating = ["started", "generating"].includes(progress.status);
  const inputDisabled = model === null || generating;

  function sendMessage(input) {
    if (input.trim() !== "") {
      socket.send({
        user_input: input,
        llm_model: model,
        kb_name: kb,
        room_id: roomId,
        username: username,
      });
    }
  }

  function stopGenerating() {
    fetch(`/api/room/${roomId}/stop`);
  }

  const chatMessagesEndRef = useRef();
  const observer = useRef(new MutationObserver(scrollToBottom));

  function observe(e) {
    if (e) {
      observer.current.observe(e, {
        childList: true,
        subtree: true,
      });
    }
  }

  function scrollToBottom() {
    const div = chatMessagesEndRef.current;
    if (div) {
      // const scrollHeight = div.scrollHeight;
      // div.scrollTo(0, scrollHeight);
      div.scrollIntoView(false);
    }
  }

  function isEmptyRoomInfo(room = null) {
    return !room || Object.keys(room).length === 0;
  }
  return (
    <>
      {!isEmptyRoomInfo(room) ? (
        <div className={styles["chat_main"]} key={roomId}>
          <div id={styles["Rag-llm"]} className={styles["Rag-llm-class"]}>
            <KnowledgeBaseSelector
              kb={kb}
              setKb={setKb}
              disabled={inputDisabled}
              className={styles["select-ctn"]}
              maxWidth={30}
            />

            <ModelSelector
              model={model}
              setModel={setModel}
              lockedModel={lockedModel}
              disabled={inputDisabled}
              className={styles["select-ctn"]}
              maxWidth={30}
            />
          </div>
          <div className={styles["background_ctn"]}>
            <div id={styles["background"]}>
              <h1
                id={styles["input-heading"]}
                title={`Room : ${room.name}`}
                className={styles["room_heading"]}
              >
                <span
                  title={`Room : ${room.name}`}
                  className={styles["l-outfit"]}
                >
                  ausma.ai
                </span>{" "}
                : {room.name}
              </h1>

              <div id={styles["communication"]}>
                <div id={styles["chat"]} ref={observe}>
                  {history.map((msg) => (
                    <ChatMessage
                      msg={msg}
                      setReference={setReference}
                      key={msg.id ?? "FRESH"}
                    />
                  ))}
                  <div ref={chatMessagesEndRef}></div>
                </div>

                <ProgressInfo progress={progress} />

                <ChatInput
                  onEnter={sendMessage}
                  onStop={stopGenerating}
                  disabled={inputDisabled}
                  generating={generating}
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className={styles["background_ctn"]}>
          <div id={styles["background"]}>
            <h1 id={styles["input-heading"]} className={styles["room_heading"]}>
              <span className={styles["l-outfit"]}>Room is not available!</span>
            </h1>
          </div>
        </div>
      )}
      <RagReferenceModal
        reference={reference}
        close={() => setReference(null)}
      />
    </>
  );
}
function ProgressInfo({ progress }) {
  function calcMsg() {
    if (progress.status === "generating") {
      const tokens_per_s = progress.new_tokens / progress.duration_s;
      const tokens_per_s_formatted = Number(tokens_per_s).toFixed(3);
      const tokens = progress.total_response_tokens;
      let msg = "";
      if (isNaN(tokens_per_s_formatted)) {
        msg = "Processing... Tokens so far: " + tokens;
      } else {
        msg =
          "Processing... " +
          tokens_per_s_formatted +
          " tokens/s, total so far: " +
          tokens +
          " tokens";
      }
      return msg;
    } else if (progress.status === "started") {
      return "Processing history ...";
    } else if (progress.status === "error") {
      return "An error occurred. Error: " + progress.message;
    }
    return null;
  }
  return (
    <div
      className={styles["spinner"]}
      style={{
        display: ["started", "generating", "error"].includes(progress.status)
          ? "flex"
          : "none",
      }}
    >
      {progress.status !== "error" && <Spinner />}
      <span className={styles["processing"]}>{calcMsg()}</span>
    </div>
  );
}

function ChatMessage({ msg, setReference }) {
  const iconStyle = {
    height: "25px",
    width: "25px",
    marginRight: "0.7rem",
    verticalAlign: "middle",
  };

  if (msg.role === "user") {
    return (
      <div className={styles["user-message"]} key={msg.id}>
        <div className={styles["message_ctn"]}>
          <img
            src="/static/svg-icons/square-bubble-user-svgrepo-com.svg"
            className={styles["user-icon"]}
            style={iconStyle}
          />

          <span className={styles["user"]}>{msg.username}:</span>
        </div>
        <div className={styles["message"]}>{renderNewLines(msg.content)}</div>
      </div>
    );
  } else if (msg.role === "assistant") {
    return (
      <div className={styles["assistant-message"]} key={msg.id}>
        <div className={styles["message_ctn"]}>
          <img
            src="/static/svg-icons/ausma.ai_simple_logo_final_006.svg"
            className={styles["user-icon"]}
            style={iconStyle}
          />

          <span className={styles["assistant"]}>ausma.ai:</span>
        </div>
        <div className={styles["message"]}>
          <MarkdownHooks
            rehypePlugins={[
              [rehypeStarryNight, { getOnigurumaUrlFetch: () => onigurumaURL }],
            ]}
          >
            {msg.content}
          </MarkdownHooks>
        </div>
        <ChatCToolbar msg={msg} setReference={setReference} />
      </div>
    );
  } else return null;
}

function ChatInput({ onEnter, onStop, disabled, generating }) {
  const [input, setInput] = useState("");
  useEffect(adjustHeight, [input]);
  const inputArea = useRef(null);
  const inputEmpty = input === "";
  function onSubmit() {
    if (!inputEmpty && !disabled) {
      setInput("");
      onEnter?.(input);
    }
    adjustHeight();
  }

  function handleKeyPress(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      onSubmit();
      e.preventDefault();
    }
  }
  function adjustHeight() {
    // adjust the height when adding new lines via Shift+Enter
    inputArea.current.style.height = "auto";
    inputArea.current.style.height = inputArea.current.scrollHeight + 4 + "px";
  }

  return (
    <div id={styles["input"]} onKeyDown={handleKeyPress}>
      <textarea
        id={styles["user_input"]}
        name="user_input"
        rows="1"
        placeholder="Ask me anything!"
        onChange={(e) => setInput(e.target.value)}
        value={input}
        disabled={disabled}
        ref={inputArea}
      />
      {generating ? (
        <button
          className={styles["button"]}
          onClick={onStop}
          style={{ display: generating ? "block" : "none" }}
        >
          <img src="/static/svg-icons/close-square-svgrepo-com.svg" />
        </button>
      ) : (
        <button
          id={styles["send_button"]}
          className={styles["button"]}
          onClick={onSubmit}
          disabled={disabled || inputEmpty}
        >
          <img src="/static/svg-icons/send.svg" />
        </button>
      )}
    </div>
  );
}

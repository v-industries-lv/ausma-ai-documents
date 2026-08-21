import { useContext, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import styles from "./Chat.module.css";
import "./Index.css";
import { socket } from "../socket";
import KnowledgeBaseSelector from "../components/KnowledgeBaseSelector";
import AssistantSelector from "../components/AssistantSelector";
import Spinner from "../components/Spinner";
import { MarkdownHooks } from "react-markdown";
import rehypeStarryNight from "rehype-starry-night";
import { UsernameContext } from "../components/UserName";
import onigurumaURL from "vscode-oniguruma/release/onig.wasm?url";
import ChatCToolbar from "../components/ChatToolbar";
import { RagReferenceModal } from "../components/RagReferenceContent";
import { renderNewLines } from "../utils/jsxUtils";
import {
  UploadImageIcon,
  SendIcon,
  StopIcon,
  ChatUserIcon,
  ChatAusmaIcon,
  CreateRoomIcon, // Temp placeholder for adding images as input
} from "../components/Icons/ComponentIcons";

export default function ChatWrapper() {
  const params = useParams();
  const roomId = params.room;
  return <Chat key={roomId} roomId={roomId} />;
}

export function Chat({ roomId }) {
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
  // assistant set by the UI
  const [_assistant, setAssistant] = useState(null);

  const [progress, setProgress] = useState({ status: "initial" });

  useEffect(() => {
    async function updateInitialProgress() {
      const req = await fetch(`/api/room/${roomId}/progress`);
      const json = await req.json();
      if (json) {
        setProgress((progress) =>
          progress.status === "initial" ? json : progress,
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

  let lastAssistantMessage = null;
  history.forEach((element) => {
    if (element.role === "assistant") {
      lastAssistantMessage = element;
    }
  });

  const [reference, setReference] = useState(null);

  // Taking username for legacy reasons and extracting assistant name ony if available
  let lockedAssistant = lastAssistantMessage?.username;
  if (history.length > 1) {
    const lastAssistantMessageContent = JSON.parse(
      lastAssistantMessage.content,
    );
    if (lastAssistantMessageContent?.assistant) {
      lockedAssistant = lastAssistantMessageContent.assistant.name;
    }
  }

  // effective assistant - to be used
  const assistant = _assistant ?? roomDefaults?.assistant;
  function getLastKnowledgeBase() {
    let kb = null;
    const rag_sources =
      JSON.parse(lastAssistantMessage?.rag_sources ?? "[]") ?? [];
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
  const inputDisabled = assistant === null || generating;

  function sendMessage(input, images = []) {
    if (input.trim() !== "") {
      var input_data = { content: input };
      if (images.length > 0) {
        input_data["images"] = images;
      }
      socket.send({
        user_input: input_data,
        assistant: assistant,
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
              maxWidth="20ch"
              dynamicWidth
            />

            <AssistantSelector
              assistant={assistant}
              lockedAssistant={lockedAssistant}
              setAssistant={setAssistant}
              disabled={inputDisabled}
              className={styles["select-ctn"]}
              maxWidth="20ch"
              dynamicWidth
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
  let msgContent;
  try {
    msgContent = JSON.parse(msg.content);
  } catch (e) {
    msgContent = { content: msg.content };
  }

  if (msg.role === "user") {
    return (
      <>
        <div className={styles["user-message"]} key={msg.id}>
          <div className={styles["message_ctn"]}>
            <ChatUserIcon
              onDragStart={(e) => e.preventDefault()}
              className={styles["user-icon"]}
              style={iconStyle}
            />
            <span className={styles["user"]}>{msg.username}:</span>
          </div>
          <div className={styles["message"]}>
            {renderNewLines(msgContent.content)}
          </div>
          {msgContent.images?.map((image, index) => (
            <div
              key={msg.id + `-` + index}
              style={{
                position: "relative",
                margin: "5px",
                display: "inline-block",
              }}
            >
              <img
                key={msg.id + `-` + index + `-` + image}
                src={`/instance/blobs/multimodal_input/` + image}
                style={{
                  maxWidth: "150px",
                  maxHeight: "150px",
                  borderRadius: "4px",
                }}
              />
            </div>
          ))}
        </div>
      </>
    );
  } else if (msg.role === "assistant") {
    const assistantName = msgContent?.assistant?.name ?? "ausma.ai";
    return (
      <div className={styles["assistant-message"]} key={msg.id}>
        <div className={styles["message_ctn"]}>
          <ChatAusmaIcon
            onDragStart={(e) => e.preventDefault()}
            className={styles["user-icon"]}
            style={iconStyle}
          />
          <span className={styles["assistant"]}>{assistantName}:</span>
        </div>
        <div className={styles["message"]}>
          <MarkdownHooks
            rehypePlugins={[
              [rehypeStarryNight, { getOnigurumaUrlFetch: () => onigurumaURL }],
            ]}
          >
            {msgContent.content}
          </MarkdownHooks>
        </div>
        <ChatCToolbar msg={msg} setReference={setReference} />
      </div>
    );
  } else return null;
}

function ChatInput({ onEnter, onStop, disabled, generating }) {
  const [input, setInput] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  useEffect(adjustHeight, [input]);
  const inputArea = useRef(null);
  const inputEmpty = input === "";
  function onSubmit() {
    if (!inputEmpty && !disabled) {
      let images = uploadedFiles.map((file) => file.new_filename);
      setInput("");
      onEnter?.(input, images);
      setUploadedFiles([]);
    }
    adjustHeight();
  }

  function handlePaste(e) {
    const items = e.clipboardData.items;
    const imageFiles = Array.from(items)
      .filter((item) => item.type.startsWith("image/"))
      .map((item, index) => {
        const blob = item.getAsFile();

        return new File([blob], `pasted-${Date.now()}-${index}.png`, {
          type: blob.type,
        });
      });

    if (!imageFiles.length) return;
    const dataTransfer = new DataTransfer();
    imageFiles.forEach((file) => dataTransfer.items.add(file));

    const fakeEvent = {
      target: {
        files: dataTransfer.files,
        value: "",
      },
    };
    handleChange(fakeEvent);
  }

  function handleDrop(e) {
    e.preventDefault();

    const files = Array.from(e.dataTransfer.files);
    if (!files.length) return;

    const fakeEvent = {
      target: {
        files,
        value: "",
      },
    };

    handleChange(fakeEvent);
  }

  function handleDragOver(e) {
    e.preventDefault();
  }

  async function handleChange(e) {
    setUploading(true);
    const files = Array.from(e.target.files);
    if (!files.length) {
      setUploading(false);
      return;
    }
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const res = await fetch(`/api/upload_chat_files`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      const doneFiles = data.files;

      setUploadedFiles((prev) => [...prev, ...doneFiles]);
    } catch (err) {
      console.error("Upload error:", err);
    }
    e.target.value = "";
    setUploading(false);
  }

  function handleKeyPress(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      onSubmit();
      e.preventDefault();
    }
  }

  function handleRemove(rm_file) {
    setUploadedFiles((prev) => prev.filter((f) => f.path !== rm_file.path));
  }

  function adjustHeight() {
    // adjust the height when adding new lines via Shift+Enter
    inputArea.current.style.height = "auto";
    inputArea.current.style.height = inputArea.current.scrollHeight + 4 + "px";
  }

  return (
    <div className={styles["input_group"]}>
      <div id={styles["input"]} onKeyDown={handleKeyPress}>
        <textarea
          id={styles["user_input"]}
          name="user_input"
          rows="1"
          placeholder="Ask me anything!"
          onChange={(e) => setInput(e.target.value)}
          onPaste={handlePaste}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
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
            <StopIcon onDragStart={(e) => e.preventDefault()} alt="Stop" />
          </button>
        ) : (
          <button
            id={styles["send_button"]}
            className={styles["button"]}
            onClick={onSubmit}
            disabled={disabled || inputEmpty || uploading}
          >
            <SendIcon
              onDragStart={(e) => e.preventDefault()}
              alt="Send Icon"
              title="Send"
            />
          </button>
        )}
      </div>
      <>
        <div>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            onChange={handleChange}
            disabled={uploading}
            accept=".jpg, .jpeg, .png"
            style={{ display: "none" }}
          />

          <button
            onClick={() => fileInputRef.current.click()}
            className={`${styles["button"]} ${styles["add_btn"]}`}
            disabled={generating}
          >
            <UploadImageIcon />
          </button>

          <div className={styles["upload-wrapper"]}>
            {uploadedFiles.map((file, index) => (
              <div
                key={index + `-` + file.original_clean_filename}
                className={styles["preview"]}
              >
                {/* Remove button */}
                <button
                  onClick={() => handleRemove(file)}
                  className={styles["image_remove_button"]}
                >
                  ×
                </button>

                {/* Image preview */}
                <img
                  src={`/instance/blobs/multimodal_input/` + file.new_filename}
                  alt={file.original_clean_filename}
                  className={styles["image_preview"]}
                />
              </div>
            ))}
          </div>
        </div>
      </>
    </div>
  );
}

import { useState } from "react";
import styles from "./ChatToolbar.module.css";
import RagReferenceContent from "./RagReferenceContent";

export default function ChatToolbar({
  setReference,
  msg,
  className,
  initiallyClosed = true,
}) {
  const [isClosed, setIsClosed] = useState(initiallyClosed);
  function onToggle() {
    setIsClosed((isClosed) => !isClosed);
  }
  return (
    <section>
      <div className={styles["toolbar"]}>
        <div className={styles["toolbar-btns"]}>
          <a
            className={styles["tool"]}
            href={`/api/message/${msg.id}`}
            target="_blank"
            rel="noreferrer"
            download
          >
            <img
              src="/static/svg-icons/align-bottom-svgrepo-com.svg"
              title={"Download Reply"}
            />
          </a>
          <a
            className={styles["tool"]}
            href={`/api/message/${msg.id}/rag`}
            target="_blank"
            rel="noreferrer"
            download
          >
            <img
              src="/static/svg-icons/code-file-svgrepo-com.svg"
              title={"RAG Sources"}
            />
          </a>

          <div className={styles["tool"]} onClick={onToggle} title="Reference">
            <img src="/static/svg-icons/book-bookmark-svgrepo-com.svg" />
            <div className={styles.arrow}>
              <svg
                className={isClosed ? "" : styles.rotated}
                style={{ cursor: "pointer" }}
                xmlns="http://www.w3.org/2000/svg"
                x="0px"
                y="0px"
                width="14"
                height="14"
                viewBox="0 0 30 30"
              >
                <path d="M 24.990234 8.9863281 A 1.0001 1.0001 0 0 0 24.292969 9.2929688 L 15 18.585938 L 5.7070312 9.2929688 A 1.0001 1.0001 0 0 0 4.9902344 8.9902344 A 1.0001 1.0001 0 0 0 4.2929688 10.707031 L 14.292969 20.707031 A 1.0001 1.0001 0 0 0 15.707031 20.707031 L 25.707031 10.707031 A 1.0001 1.0001 0 0 0 24.990234 8.9863281 z"></path>
              </svg>
            </div>
          </div>
        </div>
        <span className={styles["assistant-model"]}>({msg.username})</span>
      </div>
      <div
        className={`${styles["setting-list"]} ${className ?? ""} ${
          isClosed ? "" : styles.open
        }`}
      >
        <RagReferenceContent msg={msg} setReference={setReference} />
      </div>
    </section>
  );
}

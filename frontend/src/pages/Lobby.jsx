import styles from "./Lobby.module.css";
import "./Index.css";
import { Link } from "react-router-dom";

export default function Lobby({ setClosed }) {
  function startAChat() {
    const sideBar = document.querySelector(".side_bar");
    const name = document.getElementById("room-name");

    const validateInput = () => {
      if (!name.value.trim()) {
        name.classList.add("highlight");
        name.reportValidity();
        name.addEventListener(
          "animationend",
          function () {
            name.classList.remove("highlight");
          },
          { once: true }
        );
        name.focus();
      } else {
        alert("Click the '+' button next to the input field to continue.");
      }
    };

    if (sideBar.classList.contains("close")) {
      setClosed(false);

      sideBar.addEventListener("transitionend", function handler() {
        validateInput();
        sideBar.removeEventListener("transitionend", handler);
      });
    } else {
      validateInput();
    }
  }

  return (
    <>
      <div className={styles["lobby_main"]}>
        <div className={styles["welcome_message"]}>
          <div className={styles["ausma_logo"]}>
            <img
              src="/static/svg-icons/ausma.ai_simple_logo_final_003.svg"
              alt="ausma.ai logo"
            />
          </div>
          <h1>
            Welcome to <span className={styles["brand-colors"]}>ausma.ai </span>
            !
          </h1>
          <h2
            className={`${styles["lobby_messages"]} ${styles["start-a-chat"]}`}
            onClick={startAChat}
          >
            Start a chat!
          </h2>
          <h2 className={styles["lobby_messages"]}>
            <Link to="/settings">Go to Settings</Link>
          </h2>
          <h2 className={styles["lobby_messages"]}>
            <Link to="/knowledge-base">Go to Knowledge Base Settings</Link>
          </h2>
          <h2 className={styles["lobby_messages"]}>
            <a href="/about">About ausma. ai Documents</a>
          </h2>
        </div>
      </div>
    </>
  );
}

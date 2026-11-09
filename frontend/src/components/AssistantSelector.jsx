import { useEffect, useState, useRef } from "react";
import _styles3 from "./Selector.module.css";
import _styles2 from "./Layout.module.css";
import _styles from "./RagReferenceContent.module.css";
import { RefreshIcon, LockIcon } from "./Icons/ComponentIcons";

const styles = { ..._styles, ..._styles2, ..._styles3 };

export default function AssistantSelector({
  assistant,
  lockedAssistant,
  setAssistant,
  disabled,
  className,
  dynamicWidth = true,
}) {
  const [assistants, setAssistants] = useState([]);
  const [refreshing, setRefreshing] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  async function fetchAssistants() {
    const req = await fetch("/api/config/assistants");
    const json = await req.json();

    const newAssistants = (json ?? []).map((a) => a.name);

    setAssistants(newAssistants);

    if (!assistant && newAssistants.length > 0) {
      setAssistant(newAssistants[0]);
    }

    setRefreshing(false);
  }

  useEffect(() => {
    fetchAssistants();
  }, []);

  async function refreshAssistants() {
    setRefreshing(true);
    fetchAssistants();
  }

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <>
      <div
        className={`
    ${styles["model-select-wrapper"]}
    ${!dynamicWidth ? styles["static-wrapper"] : ""}
  `}
      >
        <div
          className={`${className}  ${styles["select-ctn"]}`}
          title={
            lockedAssistant
              ? `Selected Assistant: ${lockedAssistant}`
              : `Selected Assistant: ${assistant}`
          }
          ref={dropdownRef}
        >
          {lockedAssistant ? (
            <>
              <span className={styles["select-label"]}>Assistant:</span>
              <span
                className={styles.select}
                title={`Selected Assistant: ${lockedAssistant}`}
              >
                <LockIcon className={`${styles["lock-icon"]}`} />
                {lockedAssistant}
              </span>
            </>
          ) : !refreshing ? (
            dynamicWidth ? (
              <>
                <button
                  type="button"
                  className={`${styles.select} ${
                    styles["dynamic-select"]
                  } ${isOpen ? styles["dynamic-select-open"] : ""}`}
                  onClick={() => setIsOpen(!isOpen)}
                  title={`Selected Assistant: ${assistant}`}
                  disabled={disabled}
                >
                  <span className={styles["select-label"]}>Assistant:</span>
                  <span className={styles["select-value"]}>
                    {assistant || "None"}
                  </span>

                  <span className={styles["select-arrow"]}>
                    <svg
                      width="9"
                      height="8"
                      viewBox="0 0 12 8"
                      xmlns="http://www.w3.org/2000/svg"
                      aria-hidden="true"
                    >
                      <path
                        d="M1 1.5L6 6.5L11 1.5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                </button>
                {isOpen && (
                  <div
                    className={`${styles["dropdown-menu-base"]} ${
                      styles["dropdown-menu-dynamic"]
                    }`}
                  >
                    <div className={styles["dropdown-menu-content"]}>
                      {assistants.map((item) => (
                        <button
                          type="button"
                          key={item}
                          className={`${styles["dropdown-option"]} ${
                            styles["dropdown-button"]
                          }`}
                          onClick={() => {
                            setAssistant(item);
                            setIsOpen(false);
                          }}
                          disabled={disabled}
                        >
                          <span
                            className={styles["dropdown-option-name"]}
                            title={item}
                          >
                            {item}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <>
                <label htmlFor="assistant">Assistant:</label>
                <select
                  id="assistant"
                  name="assistant"
                  className={`${styles.select} ${styles["static-select"]}`}
                  onChange={(e) => setAssistant(e.target.value)}
                  value={assistant ?? undefined}
                  disabled={disabled}
                  title={`Selected Assistant: ${assistant}`}
                >
                  {assistants.map((item) => (
                    <option value={item} key={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </>
            )
          ) : (
            <select
              name="kb_name"
              className={`${styles.select} ${dynamicWidth ? styles["dynamic-select"] : styles["static-select"]}`}
              disabled
            >
              <option>Refreshing...</option>
            </select>
          )}
        </div>
        <button
          type="button"
          className={`${styles["nav_option_btn"]} ${!dynamicWidth ? styles["nav_option_btn_static"] : ""}`}
          onClick={refreshAssistants}
          title="Refresh Assistants"
          disabled={disabled || refreshing || lockedAssistant?.length}
        >
          <RefreshIcon
            className={`${styles["home_icon"]} ${!dynamicWidth ? styles["home_icon_static"] : ""}`}
          />
        </button>
      </div>
    </>
  );
}

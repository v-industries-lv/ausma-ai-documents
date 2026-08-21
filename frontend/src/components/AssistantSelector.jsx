import { useEffect, useState, useRef } from "react";
import _styles3 from "./Selector.module.css";
import _styles2 from "./Layout.module.css";
import _styles from "./RagReferenceContent.module.css";
import { uniqueValues } from "../utils/listTools";
import { RefreshIcon, LockIcon } from "./Icons/ComponentIcons";

const styles = { ..._styles, ..._styles2, ..._styles3 };

export default function AssistantSelector({
  assistant,
  lockedAssistant,
  setAssistant,
  disabled,
  className,
  maxWidth = 100,
  dynamicWidth = true,
}) {
  const [assistants, setAssistants] = useState([]);
  const [refreshing, setRefreshing] = useState(true);
  const selectRef = useRef(null);
  const measureRef = useRef(null);

  useEffect(() => {
    if (!selectRef.current) return;

    if (!dynamicWidth) {
      selectRef.current.style.removeProperty("width");
      return;
    }

    selectRef.current.style.removeProperty("width");

    if (!measureRef.current) return;

    const text =
      selectRef.current.options[selectRef.current.selectedIndex]?.text ?? "";

    measureRef.current.textContent = text;
    selectRef.current.style.width = `${measureRef.current.offsetWidth + 40}px`;
  }, [assistant, dynamicWidth, refreshing]);

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
          title={lockedAssistant ? lockedAssistant : assistant}
        >
          <label htmlFor="assistant">Assistant:</label>

          {lockedAssistant ? (
            <span
              className={styles.select}
              style={{ maxWidth }}
              title={lockedAssistant}
            >
              <LockIcon className={`${styles["lock-icon"]}`} />
              {lockedAssistant}
            </span>
          ) : !refreshing ? (
            <>
              <select
                ref={selectRef}
                id="assistant"
                name="assistant"
                className={`${styles.select} ${dynamicWidth ? styles["dynamic-select"] : styles["static-select"]}`}
                onChange={(e) => setAssistant(e.target.value)}
                style={{ maxWidth }}
                value={assistant ?? undefined}
                disabled={disabled}
                title={assistant}
              >
                {assistants.map((assistant) => (
                  <option value={assistant} key={assistant}>
                    {assistant}
                  </option>
                ))}
              </select>
              <span ref={measureRef} className={styles["measure-span"]} />
            </>
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

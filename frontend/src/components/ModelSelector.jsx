import { useEffect, useState, useRef } from "react";
import _styles from "./Selector.module.css";
import _styles2 from "./Layout.module.css";
import { uniqueValues } from "../utils/listTools";
import { RefreshIcon } from "./Icons/ComponentIcons";

const styles = { ..._styles, ..._styles2 };

export default function ModelSelector({
  model,
  lockedModel,
  setModel,
  disabled,
  className,
  maxWidth = 100,
  dynamicWidth = true,
}) {
  const [models, setModels] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const selectRef = useRef(null);
  const measureRef = useRef(null);

  useEffect(() => {
    if (!selectRef.current) return;

    if (!dynamicWidth) {
      selectRef.current.style.removeProperty("width");
      return;
    }

    selectRef.current.style.removeProperty("width");

    if (refreshing || !measureRef.current || !model) return;

    measureRef.current.textContent = model;

    const width = measureRef.current.offsetWidth + 40;

    selectRef.current.style.width = `${width}px`;
  }, [model, dynamicWidth, refreshing]);

  async function fetchModels() {
    const req = await fetch("/api/llm_runners/models");
    const json = await req.json();

    const newModels = uniqueValues(json?.chat_models ?? []);

    const same =
      models.length === newModels.length &&
      models.every((m) => newModels.includes(m));

    if (!same) {
      setModels(newModels);

      setModel((prev) => (newModels.includes(prev) ? prev : newModels[0]));
    }
  }

  useEffect(() => {
    fetchModels();
  }, []);

  async function refreshModels() {
    setRefreshing(true);
    const req = await fetch("/api/llm_runners/models/refresh");
    const json = await req.json();
    console.log(json);
    fetchModels();
    setRefreshing(false);
  }

  function shortenModel(model, offset = 0) {
    if (model.length <= maxWidth - offset) {
      return model;
    }
    return model.substring(0, maxWidth - offset) + "...";
  }

  return (
    <>
      <div
        className={`
    ${styles["model-select-wrapper"]}
    ${!dynamicWidth ? styles["static-wrapper"] : ""}
  `}
      >
        <div className={`${className}  ${styles["select-ctn"]}`} title={model}>
          <label for="llm_model">LLM model:</label>
          {lockedModel ? (
            <span className={styles.select} style={{ maxWidth }} title={model}>
              🔒 {lockedModel}
            </span>
          ) : models?.length && !refreshing ? (
            <>
              <select
                ref={selectRef}
                name="llm"
                className={`${styles.select} ${dynamicWidth ? styles["dynamic-select"] : styles["static-select"]}`}
                onChange={(e) => setModel(e.target.value)}
                style={{ maxWidth }}
                value={model}
                disabled={disabled}
                title={model}
              >
                {models.map((model) => (
                  <option value={model} key={model}>
                    {model}
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
          onClick={refreshModels}
          title="Refresh Modules"
          disabled={disabled || refreshing || lockedModel?.length}
        >
          <RefreshIcon
            className={`${styles["home_icon"]} ${!dynamicWidth ? styles["home_icon_static"] : ""}`}
          />
        </button>
      </div>
    </>
  );
}

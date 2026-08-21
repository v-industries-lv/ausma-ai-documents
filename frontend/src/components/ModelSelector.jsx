import { useEffect, useState, useRef } from "react";
import _styles from "./Selector.module.css";
import _styles2 from "./Layout.module.css";
import { uniqueValues } from "../utils/listTools";
import { RefreshIcon } from "./Icons/ComponentIcons";

const styles = { ..._styles, ..._styles2 };

export default function ModelSelector({
  model,
  setModel,
  disabled,
  className,
  runnerType = null,
  maxWidth = 100,
  dynamicWidth = true,
}) {
  const [models, setModels] = useState([]);
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

    if (refreshing || !measureRef.current || !model) return;

    measureRef.current.textContent = model;

    const width = measureRef.current.offsetWidth + 40;

    selectRef.current.style.width = `${width}px`;
  }, [model, dynamicWidth, refreshing]);

  async function fetchModels() {
    const req = await fetch("/api/llm_runners/models_with_capabilities");
    const json = await req.json();
    const newModels = json.filter(
      (m) =>
        (m.capabilities ?? []).includes("completion") &&
        (runnerType === null || m.runner_type === runnerType),
    );
    setModels(uniqueValues(newModels.map((m) => m.model)));
    if (model === null && newModels.length > 0) {
      setModel(newModels[0].model);
    }
    setRefreshing(false);
  }

  useEffect(() => {
    fetchModels();
  }, [runnerType]);

  async function refreshModels() {
    setRefreshing(true);
    const req = await fetch("/api/llm_runners/models/refresh");
    await req.json();
    fetchModels();
  }

  function includeCurrentValue(models) {
    if (!model || models.includes(model)) {
      return { title: model, fullModelList: models, missingModel: false };
    } else {
      return {
        title: model + "\nModel not found. Check runner.",
        fullModelList: [model, ...models],
        missingModel: true,
      };
    }
  }
  const { fullModelList, title, missingModel } = includeCurrentValue(models);
  return (
    <>
      <div
        className={`
    ${styles["model-select-wrapper"]}
    ${!dynamicWidth ? styles["static-wrapper"] : ""}
  `}
      >
        <div className={`${className}  ${styles["select-ctn"]}`} title={model}>
          <label htmlFor="llm">LLM model:</label>
          {!refreshing ? (
            <>
              <select
                id="llm"
                ref={selectRef}
                name="llm"
                className={`${styles.select} ${dynamicWidth ? styles["dynamic-select"] : styles["static-select"]}`}
                onChange={(e) => setModel(e.target.value)}
                style={{ maxWidth }}
                value={model}
                disabled={disabled}
                title={title}
              >
                {fullModelList.map((model) => (
                  <option value={model} key={model} title={model}>
                    {(models.includes(model) ? "" : "[!] ") + model}
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
          disabled={disabled || refreshing}
        >
          <RefreshIcon
            className={`${styles["home_icon"]} ${!dynamicWidth ? styles["home_icon_static"] : ""}`}
          />
        </button>
      </div>
    </>
  );
}

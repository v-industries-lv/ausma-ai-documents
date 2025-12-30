import { useEffect, useState } from "react";
import styles from "./Selector.module.css";
import { uniqueValues } from "../utils/listTools";

export default function ModelSelector({
  model,
  lockedModel,
  setModel,
  disabled,
  className,
  maxWidth = 100,
}) {
  const [models, setModels] = useState([]);

  useEffect(() => {
    async function fetchModels() {
      const req = await fetch("/api/llm_runners/models");
      const json = await req.json();
      const oldModels = models.length;
      const newModels = uniqueValues(json?.chat_models ?? []);
      setModels(newModels);
      if (oldModels !== newModels) {
        setModel(model ?? newModels[0]);
      }
    }
    fetchModels();
  }, []);

  function shortenModel(model, offset = 0) {
    if (model.length <= maxWidth - offset) {
      return model;
    }
    return model.substring(0, maxWidth - offset) + "...";
  }

  return (
    <div className={`${className}  ${styles["select-ctn"]}`} title={model}>
      <label for="llm_model">LLM model:</label>
      {lockedModel ? (
        <span className={styles.select} title={model}>
          {shortenModel(`🔒 ${lockedModel}`, 11)}
        </span>
      ) : models?.length ? (
        <select
          name="llm"
          className={styles["select-width"]}
          onChange={(e) => setModel(e.target.value)}
          value={model}
          disabled={disabled}
          title={model}
        >
          {models.map((model) => (
            <option value={model} key={model}>
              {shortenModel(model)}
            </option>
          ))}
        </select>
      ) : (
        <select name="kb_name" className={styles["select-setting"]} disabled>
          <option>No models found!</option>
        </select>
      )}
    </div>
  );
}

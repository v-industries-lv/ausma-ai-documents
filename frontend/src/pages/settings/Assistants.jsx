import { useState } from "react";
import AboutIcon from "../../components/Icons/AboutIcon";
import ModelSelector from "../../components/ModelSelector";
import SpinnerButtons from "../../components/SpinnerButtons";
import { useObjectState } from "../../components/useResetableState";
import _styles from "../Settings.module.css";
import _styles2 from "../SettingsCommon.module.css";
import ListSetting from "./ListSetting";

const styles = { ..._styles, ..._styles2 };

const commonDefaults = {
  history_mode: "full",
  thinking_flag: "high",
  model: null,
  system_prompt:
    "You are a helpful assistant. Provide a conversational answer. Do not respond with anything that might cause XSS. If you don't know the answer, just say \"I do not know.\" Don't make up an answer. ",
  rag_settings: {
    rag_document_count: 20,
    rag_char_chunk_size: 1000,
    rag_char_overlap: 200,
    rag_similarity_score_threshold: 0.8,
    rag_score_margin: 0.2,
    rag_cosine_distance_irrelevance_threshold: 1.0,
  },
};

const assistants = {
  debug: {
    component: DebugAssistant,
    defaultValue: {
      runner_type: "debug",
      ...commonDefaults,
    },
  },
  ollama: {
    component: OllamaAssistant,
    defaultValue: {
      runner_type: "ollama",
      model: "qwen3-vl:latest",
      ...commonDefaults,
      options: {
        seed: 42,
        num_predict: 8000,
        num_ctx: 16000,
      },
    },
  },
  openai: {
    component: OpenAIAssistant,
    defaultValue: {
      runner_type: "openai",
      model: "gpt-4.1",
      ...commonDefaults,
    },
  },
  mistralai: {
    component: MistralAIAssistant,
    defaultValue: {
      runner_type: "mistralai",
      model: "mistral-medium-latest",
      ...commonDefaults,
    },
  },
  remote: {
    component: RemoteAssistant,
    defaultValue: {
      runner_type: "remote",
      ...commonDefaults,
    },
  },
};

const externalServiceWarning = (
  <div className={styles["warning"]}>
    This is an external service! Be aware of their privacy policies.
  </div>
);

function useCommon({ value, onChange }) {
  const model = value?.model;
  const runner_type = value?.runner_type;

  const options = value?.options;
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    let parsedValue;
    switch (type) {
      case "checkbox":
        parsedValue = checked;
        break;

      case "number":
        parsedValue = parseInt(v);
        if (Number.isNaN(parsedValue)) {
          return;
        }
        break;
      default:
        parsedValue = v;
    }
    const newValue = { ...value, [n]: parsedValue };
    onChange?.(newValue);
  }

  function updateOption(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    let parsedValue;
    switch (type) {
      case "checkbox":
        parsedValue = checked;
        break;

      case "number":
        parsedValue = parseInt(v);
        if (Number.isNaN(parsedValue)) {
          return;
        }
        break;
      default:
        parsedValue = v;
    }
    const newValue = { ...value, options: { ...options, [n]: parsedValue } };
    onChange?.(newValue);
  }

  function setModel(_model) {
    const v = typeof _model === "function" ? _model(model) : _model;
    const newName = nameUpdated ? value.name : v + " assistant";
    const newValue = { ...value, model: v, name: newName };

    onChange?.(newValue);
  }

  function setRag(rag_settings) {
    const newValue = { ...value, rag_settings };
    onChange?.(newValue);
  }

  const [nameUpdated, setNameUpdated] = useState(value.name !== undefined);

  const commonComponents = (
    <>
      <div className={styles.setting}>
        <label htmlFor="name">Name:</label>
        <input
          id="name"
          name="name"
          value={value.name}
          onChange={(e) => {
            setNameUpdated(true);
            updateValue(e);
          }}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="runner_type" name="runner_type">
          Runner type:
        </label>
        <input
          name="runner_type"
          id="runner_type"
          defaultValue={value.runner_type}
          readOnly
        />
      </div>

      <ModelSelector
        runnerType={runner_type}
        model={model}
        setModel={(_model) => {
          if (model !== _model) {
            setModel(_model);
          }
        }}
        className={styles["select-ctn"]}
        maxWidth="100%"
        dynamicWidth={false}
      />

      <div className={styles.setting}>
        <label htmlFor="system_prompt" name="default_system_prompt">
          System prompt:
        </label>
        <textarea
          className={styles["system-prompt-input"]}
          id="system_prompt"
          name="system_prompt"
          onChange={updateValue}
          value={value.system_prompt}
        />
      </div>
      <div className={styles.setting}>
        <label htmlFor="thinking_flag" name="thinking_flag">
          Thinking flag:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Turn on/off/set level to thinking/reasoning mode. Typical values - true, false, low, medium, high"
          />
        </label>
        <input
          id="thinking_flag"
          name="thinking_flag"
          onChange={updateValue}
          value={value.thinking_flag}
          defaultValue={`high`}
        />
      </div>
      <div className={styles.setting}>
        <label htmlFor="history_mode" name="history_mode">
          History Mode:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="How the assistant treats coversation history. Whether or not it even considers past messages."
          />
        </label>
        <select
          id="history_mode"
          name="history_mode"
          className={`$styles["select-ctn"]`}
          value={value.history_mode}
          onChange={updateValue}
        >
          <option value="full">Full</option>
          <option value="none">None - Q&A mode</option>
        </select>
      </div>
      <RagSettings value={value.rag_settings} setValue={setRag} />
    </>
  );
  return {
    options,
    updateOption,
    updateValue,
    commonComponents,
  };
}

function RagSettings({ value, setValue }) {
  function upsert(o) {
    setValue({ ...value, ...o });
  }
  const handleInputChange = (event) => {
    const { name, value: newValue, validity, min, max } = event.target;

    if (validity.rangeUnderflow) {
      upsert({ [name]: Number(min) });
    } else if (validity.rangeOverflow) {
      upsert({ [name]: Number(max) });
    } else if (validity.valid) {
      upsert({ [name]: Number(newValue) });
    }
  };

  return (
    <>
      <div className={styles.setting}>
        <label htmlFor="document_count_id">
          Document count:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="How many document chunks to retrieve from vector store. Small values - faster, but might miss relevant documents, large values - slower processing."
          />
        </label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={1}
            max={1000}
            step={1}
            className={styles["input_field"]}
            id="document_count_id"
            name="rag_document_count"
            value={value.rag_document_count}
            onChange={handleInputChange}
          />
          <SpinnerButtons
            value={value.rag_document_count}
            onChange={(v) => upsert({ rag_document_count: v })}
            min={1}
            max={1000}
            step={1}
          />
        </div>

        <label htmlFor="rag_similarity_score_threshold_id">
          Similarity score threshold:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="If 2 or more retrieved document chunks have cosine similarity between them larger than this threshold, reranker keeps only the document chunk with highest retrieval score in this group, discarding the rest."
          />
        </label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            className={styles["input_field"]}
            id="rag_similarity_score_threshold_id"
            name="rag_similarity_score_threshold"
            value={value.rag_similarity_score_threshold}
            onChange={handleInputChange}
          />
          <SpinnerButtons
            value={value.rag_similarity_score_threshold}
            onChange={(v) => upsert({ rag_similarity_score_threshold: v })}
            min={0}
            max={1}
            step={0.1}
          />
        </div>

        <label htmlFor="rag_score_margin_id">
          Score margin:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Reranker takes minimum similarity_score (cosine distance) in retrieved document chunks and adds margin to this score. Documents above this margin get discarded as irrelevant."
          />
        </label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            className={styles["input_field"]}
            id="rag_score_margin_id"
            name="rag_score_margin"
            value={value.rag_score_margin}
            onChange={handleInputChange}
          />
          <SpinnerButtons
            value={value.rag_score_margin}
            onChange={(v) => upsert({ rag_score_margin: v })}
            min={0}
            max={1}
            step={0.1}
          />
        </div>

        <label htmlFor="rag_cosine_distance_irrelevance_threshold_id">
          Irrelevance threshold:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Reranker discards retrieved document chunks above this threshold as irrelevant."
          />
        </label>
        <div className={styles["wrapper"]}>
          <input
            min={0}
            max={2}
            step={0.1}
            type="number"
            className={styles["input_field"]}
            id="rag_cosine_distance_irrelevance_threshold_id"
            name="rag_cosine_distance_irrelevance_threshold"
            value={value.rag_cosine_distance_irrelevance_threshold}
            onChange={handleInputChange}
          />
          <SpinnerButtons
            value={value.rag_cosine_distance_irrelevance_threshold}
            onChange={(v) =>
              upsert({ rag_cosine_distance_irrelevance_threshold: v })
            }
            min={0}
            max={2}
            step={0.1}
          />
        </div>
      </div>
    </>
  );
}

function OllamaAssistant({ value, onChange }) {
  const { commonComponents, updateOption, updateValue, options } = useCommon({
    value,
    onChange,
  });

  return (
    <>
      {commonComponents}

      <div className={styles.setting}>
        <label htmlFor="seed">seed (0 for random):</label>
        <input
          id="seed"
          name="seed"
          value={options.seed}
          type="number"
          min={0}
          step={1}
          onChange={updateOption}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="num_predict">num_predict:</label>
        <input
          id="num_predict"
          name="num_predict"
          value={options.num_predict}
          type="number"
          min={0}
          step={1}
          onChange={updateOption}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="num_ctx">num_ctx:</label>
        <input
          id="num_ctx"
          name="num_ctx"
          value={options.num_ctx}
          type="number"
          min={0}
          step={1}
          onChange={updateOption}
        />
      </div>
    </>
  );
}

function DebugAssistant({ value, onChange }) {
  const { commonComponents, updateOption, updateValue, options } = useCommon({
    value,
    onChange,
  });
  return <>{commonComponents}</>;
}

function OpenAIAssistant({ value, onChange }) {
  const { commonComponents, updateOption, updateValue, options } = useCommon({
    value,
    onChange,
  });
  return (
    <>
      {externalServiceWarning}
      {commonComponents}
    </>
  );
}

function MistralAIAssistant({ value, onChange }) {
  const { commonComponents, updateOption, updateValue, options } = useCommon({
    value,
    onChange,
  });
  return (
    <>
      {externalServiceWarning}
      {commonComponents}
    </>
  );
}

function RemoteAssistant({ value, onChange }) {
  const { commonComponents, updateOption, updateValue, options } = useCommon({
    value,
    onChange,
  });
  return <>{commonComponents}</>;
}

export default function Assistants({ initial, onSave }) {
  return (
    <>
      <ListSetting
        typeParameter="runner_type"
        initial={initial}
        onSave={onSave}
        types={assistants}
        title="Assistants"
        description={<p></p>}
        typeLabel="LLM Runner:"
      />
    </>
  );
}

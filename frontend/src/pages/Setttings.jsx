import { useContext, useEffect } from "react";
import "./Index.css";
import _styles from "./Settings.module.css";
import _styles2 from "./SettingsCommon.module.css";
import { useState } from "react";
import CollapsibleBox from "../components/CollapsibleBox";
import DocumentSources from "./settings/DocumentSources";
import LLMRunners from "./settings/LLMRunners";
import KBStores from "./settings/KBStores";
import {
  useObjectState,
  useStringState,
} from "../components/useResetableState";
import EditButtons from "../components/EditButtons";
import KnowledgeBaseSelector from "../components/KnowledgeBaseSelector";
import ModelSelector from "../components/ModelSelector";
import Spinner from "../components/Spinner";
import { UsernameContext } from "../components/UserName";
import SpinnerButtons from "../components/SpinnerButtons";

const styles = { ..._styles, ..._styles2 };

export default function Settings() {
  const [isLoading, setLoading] = useState(true);
  const [config, setConfig] = useState({
    room_defaults: {},
    default_system_prompt: "",
    rag_settings: {},
    generation_guard: {},
  });

  async function fetchConfig() {
    const response = await fetch("/api/config");
    setConfig(await response.json());
    setLoading(false);
  }

  useEffect(() => {
    fetchConfig();
  }, []);

  async function saveSetting(name, value) {
    // assumes the change will be sucessful before getting the new value from fetchConfig()
    setConfig((config) => ({ ...config, [name]: value }));
    const response = await fetch(`/api/config/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(value),
    });
    const json = await response.json();
    console.log(JSON.stringify(json));

    fetchConfig();
  }

  async function restoreToDefault() {
    const response = await fetch("/api/config/restore_default_settings", {
      method: "GET",
    });
    const json = await response.json();
    console.log(JSON.stringify(json));
    fetchConfig();
  }

  return (
    <>
      <div className={styles["settings_main"]}>
        <h1 className={styles["main-heading"]}>Settings</h1>
        {isLoading ? (
          <>
            <div>
              <Spinner /> Loading Settings ...
            </div>
          </>
        ) : (
          <>
            <GeneralSettings />
            <DefaultRoomSettings
              initial={config.room_defaults}
              onSave={(value) => saveSetting("room_defaults", value)}
            />
            <KBStores
              initial={config.kbstores}
              onSave={(value) => saveSetting("kbstores", value)}
            />
            <DocumentSources
              initial={config.doc_sources}
              onSave={(value) => saveSetting("doc_sources", value)}
            />
            <LLMRunners
              initial={config.llm_runners}
              onSave={(value) => saveSetting("llm_runners", value)}
            />

            <DefaultSystemPrompt
              onSave={(value) => saveSetting("default_system_prompt", value)}
              initial={config.default_system_prompt}
            />
            <RagSettings
              onSave={(value) => saveSetting("rag_settings", value)}
              initial={config.rag_settings}
            />
            <GenerationGuard
              onSave={(value) => saveSetting("generation_guard", value)}
              initial={config.generation_guard}
            />
            <CollapsibleBox
              className={styles["setting-list"]}
              title="Restore To Default Settings"
            >
              <p>Reset all settings to their defaults.</p>
              <div className={styles["reset-button"]}>
                <button
                  onClick={restoreToDefault}
                  className={`${styles["button-style"]} ${styles["button-dimensions"]}`}
                >
                  Reset To Defaults
                </button>
              </div>
            </CollapsibleBox>
          </>
        )}
      </div>
    </>
  );
}

function GeneralSettings() {
  const { username, setUsername } = useContext(UsernameContext);
  return (
    <CollapsibleBox className={styles["setting-list"]} title="General Settings">
      <UsernameEditor initial={username} onSave={setUsername} />
    </CollapsibleBox>
  );
}

function UsernameEditor({ initial, onSave }) {
  const [value, edited, { edit, reset }] = useStringState(initial);
  function save() {
    onSave?.(value);
    reset();
  }

  return (
    <>
      <p>
        Your username is associated with the messages you write in the
        chatrooms. It is set per browser. I.e. if you open ausma.ai from Firefox
        and Chrome you may set different usernames.
      </p>
      <div className={styles.setting}>
        {
          // TODO use more generic classes for CSS
        }
        <div className={styles.setting}>
          <label htmlFor="username"> Username:</label>
          <input id="username" name="username" value={value} onChange={edit} />
        </div>
        <div className={styles["button-row-right"]}>
          <EditButtons
            edited={edited}
            onSave={save}
            onReset={reset}
            styles={styles}
          />
        </div>
      </div>
    </>
  );
}

function DefaultRoomSettings({ initial, onSave }) {
  const [value, edited, { upsert, reset }] = useObjectState(initial);
  function save() {
    onSave?.(value);
    reset();
  }
  const model = initial?.model;
  return (
    <CollapsibleBox
      className={styles["setting-list"]}
      title="Chat Room Defaults"
    >
      <p>The defaults set when looking at an empty chat room.</p>

      <KnowledgeBaseSelector
        kb={value?.knowledge_base ?? {}}
        setKb={(knowledge_base) => upsert({ knowledge_base })}
        className={styles["select-ctn"]}
      />
      <ModelSelector
        model={value?.model ?? {}}
        setModel={(_model) => {
          if (model !== _model) {
            upsert({ model: _model });
          }
        }}
        className={styles["select-ctn"]}
      />

      <div className={styles["button-row-right"]}>
        <EditButtons
          edited={edited}
          onSave={save}
          onReset={reset}
          styles={styles}
        />
      </div>
    </CollapsibleBox>
  );
}

function DefaultSystemPrompt({ initial, onSave }) {
  const [value, edited, { edit, reset }] = useStringState(initial);

  function save() {
    onSave?.(value);
    reset();
  }
  return (
    <CollapsibleBox
      className={styles["setting-list"]}
      title="Default System Prompt"
    >
      <p>
        Set the base instructions that guide how the AI responds. You can
        customize this prompt to change the assistant personality, tone, and
        behavior.
      </p>

      <div className={styles.setting}>
        <label htmlFor="input-textarea" name="default_system_prompt">
          Prompt:
        </label>
        <textarea
          className={styles["system-prompt-input"]}
          id="input-textarea"
          name="default_system_prompt"
          onChange={edit}
          value={value}
        />
      </div>
      <div className={styles["button-row-right"]}>
        <EditButtons
          edited={edited}
          onSave={save}
          onReset={reset}
          styles={styles}
        />
      </div>
    </CollapsibleBox>
  );
}

function RagSettings({ initial, onSave }) {
  const [value, edited, { upsert, reset }] = useObjectState(initial);

  const handleInputChange = (event) => {
    const { name, value: newValue, validity, min, max } = event.target;

    if (validity.rangeUnderflow) {
      upsert({ ...value, [name]: Number(min) });
    } else if (validity.rangeOverflow) {
      upsert({ ...value, [name]: Number(max) });
    } else if (validity.valid) {
      upsert({ ...value, [name]: Number(newValue) });
    }
  };

  const handleInputChangeWithUpperLimitParameter = (event) => {
    const { name, value: newValue, validity, min, max } = event.target;
    const upperLimit = value[event.target.dataset.upperlimitparameter];

    if (Number(newValue) >= upperLimit) {
      upsert({
        ...value,
        [name]: Math.floor(Number(upperLimit) / 2),
      });
    } else if (validity.rangeUnderflow) {
      upsert({ ...value, [name]: Number(min) });
    } else if (validity.rangeOverflow) {
      upsert({ ...value, [name]: Number(max) });
    } else if (validity.valid) {
      upsert({ ...value, [name]: Number(newValue) });
    }
  };

  function save() {
    onSave?.(value);
    reset();
  }

  return (
    <CollapsibleBox className={styles["setting-list"]} title="RAG settings">
      <p>
        Modify RAG (Retrieval Augmented Generation) parameters. RAG allows for
        document enhanced contexts.
        <br />
        "Document count" - How many document chunks to retrieve from vector
        store. Small values - faster, but might miss relevant documents, large
        values - slower processing.
        <br />
        "Chunk size" - How large, in characters, should be the document chunks.
        Smaller chunks mean more granular information at the cost of context
        size, larger chunks - more context, but slower processing.
        <br />
        "Chunk overlap" - How much do chunks overlap, in characters. Overlapping
        takes in some information from previous chunks so the context might
        improve.
        <br />
        "Similarity score threshold" - If 2 or more retrieved document chunks
        have cosine similarity between them larger than this threshold, reranker
        keeps only the document chunk with highest retrieval score in this
        group, discarding the rest.
        <br />
        "Score margin" - Reranker takes minimum similarity_score (cosine
        distance) in retrieved document chunks and adds margin to this score.
        Documents above this margin get discarded as irrelevant.
        <br />
        "Irrelevance threshold" - Reranker discards retrieved document chunks
        above this threshold as irrelevant.
        <br />
      </p>

      <div className={styles.setting}>
        <label htmlFor="document_count_id">Document count:</label>
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

        <label htmlFor="rag_char_chunk_size_id">Chunk size:</label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={100}
            max={20000}
            step={100}
            className={styles["input_field"]}
            id="rag_char_chunk_size_id"
            name="rag_char_chunk_size"
            value={value.rag_char_chunk_size}
            onChange={handleInputChange}
          />
          <SpinnerButtons
            value={value.rag_char_chunk_size}
            onChange={(v) => upsert({ rag_char_chunk_size: v })}
            min={100}
            max={20000}
            step={100}
          />
        </div>

        <label htmlFor="rag_char_overlap_id">Chunk overlap:</label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={0}
            max={20000}
            data-upperlimitparameter="rag_char_chunk_size"
            className={styles["input_field"]}
            id="rag_char_overlap_id"
            name="rag_char_overlap"
            value={value.rag_char_overlap}
            onChange={handleInputChangeWithUpperLimitParameter}
          />
          <SpinnerButtons
            value={value.rag_char_overlap}
            onChange={(v) => upsert({ rag_char_overlap: v })}
            min={0}
            max={20000}
            step={100}
          />
        </div>

        <label htmlFor="rag_similarity_score_threshold_id">
          Similarity score threshold:
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

        <label htmlFor="rag_score_margin_id">Score margin:</label>
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
        <div className={styles["button-row-right"]}>
          <EditButtons
            edited={edited}
            onSave={save}
            onReset={reset}
            styles={styles}
          />
        </div>
      </div>
    </CollapsibleBox>
  );
}

function GenerationGuard({ initial, onSave }) {
  const [value, edited, { upsert, reset }] = useObjectState(initial);

  const handleInputChange = (event) => {
    const { name, value: newValue, validity, min, max} = event.target;

    if (validity.rangeUnderflow) {
      upsert({ ...value, [name]: Number(min) });
    } else if (validity.rangeOverflow) {
      upsert({ ...value, [name]: Number(max) });
    } else if (validity.valid) {
      upsert({ ...value, [name]: Number(newValue) });
    }
  };

  function save() {
    onSave?.(value);
    reset();
  }

  return (
    <CollapsibleBox className={styles["setting-list"]} title="Generation Guard">
      <p>
        Generation Guard detects LLM infinite generation.
        <br />
        "Safe token threshold" - Starts detecting infinite loop patterns after certain threshold.
        <br />
        "Token check interval" - How often, in tokens, to check for infinite loop patterns.
        <br />
        "Max repeats" - How many repeating token patterns should be detected to stop generation.
        <br />
        "Window size" - The size of token pattern window.
        <br />
      </p>

      <div className={styles.setting}>
        <label htmlFor="safe_token_threshold_id">Safe token threshold:</label>
        <input
          type="number"
          min={0}
          className={styles["input_field"]}
          id="safe_token_threshold_id"
          name="safe_token_threshold"
          value={value.safe_token_threshold}
          onChange={handleInputChange}
        />

        <label htmlFor="token_check_interval_id">Token check interval:</label>
        <input
          type="number"
          min={1}
          className={styles["input_field"]}
          id="token_check_interval_id"
          name="token_check_interval"
          value={value.token_check_interval}
          onChange={handleInputChange}
        />

        <label htmlFor="max_repeats_id">Max repeats:</label>
        <input
          type="number"
          min={1}
          className={styles["input_field"]}
          id="max_repeats_id"
          name="max_repeats"
          value={value.max_repeats}
          onChange={handleInputChange}
        />

        <label htmlFor="window_size_id">
          Window size:
        </label>
        <input
          type="number"
          min={1}
          className={styles["input_field"]}
          id="window_size_id"
          name="window_size"
          value={value.window_size}
          onChange={handleInputChange}
        />

        <div className={styles["button-row-right"]}>
          <EditButtons
            edited={edited}
            onSave={save}
            onReset={reset}
            styles={styles}
          />
        </div>
      </div>
    </CollapsibleBox>
  );
}
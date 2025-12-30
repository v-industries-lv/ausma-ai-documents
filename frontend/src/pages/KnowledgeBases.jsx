import React, { useState } from "react";
import _styles from "./KnowledgeBases.module.css";
import _styles2 from "./SettingsCommon.module.css";
import "./Index.css";
import { useEffect } from "react";
import CollapsibleBox from "../components/CollapsibleBox";
import { useObjectState } from "../components/useResetableState";
import { addInitialKeys, addKey } from "../utils/listTools";
import EditButtons from "../components/EditButtons";
import SpinnerButtons from "../components/SpinnerButtons";
import RandomNumberButton from "../components/RandomNumberButton";
import SourceSelection from "./knowledgebases/SourceSelection";

const styles = { ..._styles, ..._styles2 };

export default function KnowledgeBases() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  async function fetchAll() {
    const req = await fetch("/api/kb/");
    const kbs = (await req.json()) ?? [];
    const names = new Set(kbs.map((kb) => kb.name));
    setKnowledgeBases((knowledgeBases) => {
      // keep the newly created (fresh) knowledge bases unless there is a newer version from the server
      const freshKnowledgeBases = knowledgeBases.filter((kb) => kb.fresh);
      const relevantFreshKnowledgeBases = freshKnowledgeBases.filter(
        (kb) => !names.has(kb.name)
      );
      return [...kbs, ...relevantFreshKnowledgeBases];
    });
  }

  useEffect(() => {
    fetchAll();
  }, []);

  async function saveKnowledgeBase(kb) {
    // remove fresh atribute from kb
    const { fresh, ...cleanKb0 } = kb;
    const cleanKb = {
      ...cleanKb0,
      // remove key atribute from convertors
      convertors: kb.convertors.map((convertor) => {
        const { key, ...cleanConvertor } = convertor;
        return cleanConvertor;
      }),
    };
    const req = await fetch("/api/kb/put", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cleanKb),
    });
    const result = await req.json();
    // if (result.status === "success") {
    fetchAll();
    // }
    return result.status === "success";
  }

  async function clearKnowledgeBase(name) {
    const nameForURI = encodeURIComponent(name);
    const msg = `Are you sure you want to clear the knowledge base "${name}"?`;
    if (window.confirm(msg)) {
      const req = await fetch(`/api/kb/${nameForURI}/clear`, {
        method: "POST",
      });
      const result = await req.json();
    }
  }

  async function removeKnowledgeBase(name) {
    const nameForURI = encodeURIComponent(name);
    const msg = `Are you sure you want to remove the knowledge base "${name}"?`;
    if (window.confirm(msg)) {
      const req = await fetch(`/api/kb/${nameForURI}/delete`, {
        method: "POST",
      });
      const result = await req.json();
      fetchAll();
    }
  }

  function newKnowledgeBase(name) {
    const kb = {
      fresh: true,
      name: name,
      selection: ["**/*"],
      convertors: [
        {
          conversion: "ocr_llm",
          model: "qwen2.5:latest",
          seed: 42,
          temperature: 0.7,
        },
        {
          conversion: "raw",
        },
      ],
      embedding: {
        model: "bge-m3:latest",
      },
    };
    setKnowledgeBases((knowledgeBases) => [...knowledgeBases, kb]);
  }

  return (
    <>
      <div className={styles["settings_main"]}>
        <h1 className={styles["main-heading"]}>Knowledge Base Settings</h1>
        <KBService />
        {knowledgeBases.map((kb) => (
          <KBEditor
            kb={kb}
            key={kb.name}
            onSave={saveKnowledgeBase}
            onRemove={() => removeKnowledgeBase(kb.full_name)}
            onClear={() => clearKnowledgeBase(kb.full_name)}
          />
        ))}

        <AddKnowledgeBase onAdd={newKnowledgeBase} />
      </div>
    </>
  );
}

function KBService() {
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(false);
  async function updateStatus() {
    const req = await fetch("/api/kb_service/status");
    setStatus(await req.json());
  }
  useEffect(() => {
    updateStatus();
    const interval = setInterval(updateStatus, 500);
    return () => {
      clearInterval(interval);
    };
  }, []);

  async function control(command) {
    setLoading(true);
    try {
      await fetch(`/api/kb_service/control/${command}`);
    } finally {
      setLoading(false);
      updateStatus();
    }
  }

  function statusStr(result) {
    let status = result.status;
    if (
      result.kb_num !== undefined &&
      result.kb_name !== undefined &&
      result.kb_total !== undefined
    ) {
      status += ` - Knowledge Base [${result.kb_num}/${result.kb_total}] - \"${result.kb_name}\"`;
    }
    if (
      result.doc_num !== undefined &&
      result.doc_path !== undefined &&
      result.doc_total !== undefined
    ) {
      status += ` - Document [${result.doc_num}/${result.doc_total}] - \"${result.doc_path}\"`;
    }
    if (result.convertor !== undefined) {
      status += ` - Convertor \"${result.convertor}\"`;
    }
    return status;
  }

  return (
    <section
      className={styles["kb_service-container"]}
      id={styles["kb_service_id"]}
    >
      <h1 className={styles["kb-heading"]}>Knowledge Base Service</h1>
      <div className={styles["button_group"]}>
        <button
          disabled={loading}
          onClick={() => control("start")}
          className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
        >
          Start
        </button>
        <button
          disabled={loading}
          onClick={() => control("stop")}
          className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
        >
          Stop
        </button>
      </div>
      <div className={styles["status__container"]}>
        {status.status && statusStr(status)}
      </div>
    </section>
  );
}

const convertors = {
  ocr_llm: {
    convertor: OCRLLMConvertor,
    defaultValue: {
      conversion: "ocr_llm",
      model: "qwen2.5:latest",
      seed: 42,
      temperature: 0.7,
    },
  },
  raw: {
    convertor: RawConvertor,
    defaultValue: {
      conversion: "raw",
    },
  },
  llm: {
    convertor: LLMConvertor,
    defaultValue: {
      conversion: "llm",
      model: "qwen2.5vl:latest",
      seed: 42,
      temperature: 0.7,
    },
  },
  ocr: {
    convertor: OCRConvertor,
    defaultValue: {
      conversion: "ocr",
    },
  },
};

function OCRLLMConvertor({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.type === "number" ? Number(target.value) : target.value;

    const newValue = { ...value, [n]: v };
    onChange?.(newValue);
  }
  return (
    <>
      <div>
        <label
          className={styles["selection_conversion"]}
          htmlFor="chosen_conversion_id"
        >
          Conversion:
        </label>
        <input
          className={styles["input_field"]}
          id={styles["chosen_conversion_id"]}
          name="conversion"
          defaultValue={value.conversion}
          disabled
        />
      </div>
      <div>
        <label htmlFor="model_id">Model:</label>
        <input
          className={styles["input_field"]}
          id={styles["model_id"]}
          name="model"
          value={value.model}
          onChange={updateValue}
        />

        <label htmlFor="seed_id">Seed:</label>
        <div className={styles["wrapper"]}>
          <input
            min={0}
            max={32767}
            step={1}
            type="number"
            className={styles["input_field"]}
            id={styles["seed_id"]}
            name="seed"
            value={value.seed}
            onChange={updateValue}
          />
          <RandomNumberButton
            setNumber={(random) => onChange?.({ ...value, seed: random })}
          />
        </div>
        <label htmlFor="temperature_id">Temperature:</label>
        <div className={styles["wrapper"]}>
          <input
            type="number"
            min={0.1}
            max={1.5}
            step={0.1}
            className={styles["input_field"]}
            id={styles["temperature_id"]}
            name="temperature"
            value={value.temperature}
            onChange={updateValue}
          />
          <SpinnerButtons
            value={value.temperature}
            min={0.1}
            max={1.5}
            step={0.1}
            onChange={(v) => onChange?.({ ...value, temperature: v })}
          />
        </div>
      </div>
    </>
  );
}

function RawConvertor({}) {
  const value = { conversion: "raw" };
  return (
    <>
      <div>
        <label
          className={styles["selection_conversion"]}
          htmlFor="chosen_conversion_id"
        >
          Conversion:
        </label>
        <input
          className={styles["input_field"]}
          id={styles["chosen_conversion_id"]}
          name="conversion"
          defaultValue={value.conversion}
          disabled
        />
      </div>
    </>
  );
}

function LLMConvertor({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.type === "number" ? Number(target.value) : target.value;

    const newValue = { ...value, [n]: v };
    onChange?.(newValue);
  }

  return (
    <>
      <div>
        <label
          className={styles["selection_conversion"]}
          htmlFor="chosen_conversion_id"
        >
          Conversion:
        </label>
        <input
          className={styles["input_field"]}
          id={styles["chosen_conversion_id"]}
          name="conversion"
          defaultValue={value.conversion}
          disabled
        />
      </div>
      <div>
        <label htmlFor="model_id">Model:</label>
        <input
          className={styles["input_field"]}
          id={styles["model_id"]}
          name="model"
          value={value.model}
          onChange={updateValue}
        />
        <label htmlFor="seed_id">Seed:</label>
        <div className={styles["wrapper"]}>
          <input
            min={0}
            max={32767}
            step={1}
            type="number"
            className={styles["input_field"]}
            id={styles["seed_id"]}
            name="seed"
            value={value.seed}
            onChange={updateValue}
          />
          <RandomNumberButton
            setNumber={(random) => onChange?.({ ...value, seed: random })}
          />
        </div>
        <label htmlFor="temperature_id">Temperature:</label>
        <div className={styles["wrapper"]}>
          <input
            min={0.1}
            max={1.5}
            step={0.1}
            type="number"
            className={styles["input_field"]}
            id={styles["temperature_id"]}
            name="temperature"
            value={value.temperature}
            onChange={updateValue}
          />
          <SpinnerButtons
            value={value.temperature}
            min={0.1}
            max={1.5}
            step={0.1}
            onChange={(v) => onChange?.({ ...value, temperature: v })}
          />
        </div>
      </div>
    </>
  );
}

function OCRConvertor({}) {
  const value = { conversion: "raw" };
  return (
    <>
      <div>
        <label
          className={styles["selection_conversion"]}
          htmlFor="chosen_conversion_id"
        >
          Conversion:
        </label>
        <input
          className={styles["input_field"]}
          id={styles["chosen_conversion_id"]}
          name="conversion"
          defaultValue={value.conversion}
          disabled
        />
      </div>
    </>
  );
}

function ConvertorList({ value, onChange, children }) {
  function update(v) {
    onChange?.(value.map((item) => (item.key === v.key ? v : item)));
  }

  function add(v) {
    onChange?.([...value, v]);
  }

  function remove(key) {
    onChange?.(value.filter((v) => v.key !== key));
  }

  function swap(i1, i2) {
    if (i1 >= 0 && i1 < value.length && i2 >= 0 && i2 < value.length) {
      const newValue = [...value];
      const tmp = newValue[i1];
      newValue[i1] = newValue[i2];
      newValue[i2] = tmp;
      onChange?.(newValue);
    }
  }

  function addConvertor(type) {
    const defaultValue = convertors[type]?.defaultValue;
    if (defaultValue) {
      add(addKey(defaultValue));
    }
  }

  return (
    <div className={styles["convertors"]}>
      <h1>Convertors</h1>

      <div>
        {value.map((convertor, i) => {
          return (
            <div className={styles["convertor_item"]} key={convertor.key}>
              {React.createElement(convertors[convertor.conversion].convertor, {
                value: convertor,
                onChange: update,
                key: convertor.key,
              })}
              <div
                className={`${styles["button_group"]} ${styles["list_item_btn_group"]}`}
              >
                <button
                  className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
                  onClick={() => remove(convertor.key)}
                >
                  Remove &#x2212;
                </button>
                <button
                  className={`${styles["move-up"]} ${styles["button-style"]} ${styles["button-dimensions"]}`}
                  disabled={i <= 0}
                  onClick={() => swap(i - 1, i)}
                >
                  Move Up
                  <span className={`${styles["small-arrows"]} ${styles["up"]}`}>
                    <svg
                      style={{ cursor: "pointer" }}
                      xmlns="http://www.w3.org/2000/svg"
                      x="0px"
                      y="0px"
                      width="10"
                      height="10"
                      viewBox="0 0 30 30"
                    >
                      <path d="M 24.990234 8.9863281 A 1.0001 1.0001 0 0 0 24.292969 9.2929688 L 15 18.585938 L 5.7070312 9.2929688 A 1.0001 1.0001 0 0 0 4.9902344 8.9902344 A 1.0001 1.0001 0 0 0 4.2929688 10.707031 L 14.292969 20.707031 A 1.0001 1.0001 0 0 0 15.707031 20.707031 L 25.707031 10.707031 A 1.0001 1.0001 0 0 0 24.990234 8.9863281 z"></path>
                    </svg>
                  </span>
                </button>
                <button
                  className={`${styles["move-down"]} ${styles["button-style"]} ${styles["button-dimensions"]}`}
                  disabled={i >= value.length - 1}
                  onClick={() => swap(i, i + 1)}
                >
                  Move Down
                  <span className={styles["small-arrows"]}>
                    <svg
                      style={{ cursor: "pointer" }}
                      xmlns="http://www.w3.org/2000/svg"
                      x="0px"
                      y="0px"
                      width="10"
                      height="10"
                      viewBox="0 0 30 30"
                    >
                      <path d="M 24.990234 8.9863281 A 1.0001 1.0001 0 0 0 24.292969 9.2929688 L 15 18.585938 L 5.7070312 9.2929688 A 1.0001 1.0001 0 0 0 4.9902344 8.9902344 A 1.0001 1.0001 0 0 0 4.2929688 10.707031 L 14.292969 20.707031 A 1.0001 1.0001 0 0 0 15.707031 20.707031 L 25.707031 10.707031 A 1.0001 1.0001 0 0 0 24.990234 8.9863281 z"></path>
                    </svg>
                  </span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
      <div className={styles["button-row-two-sides"]}>
        <AddConvertor onAdd={addConvertor}></AddConvertor>
        {children}
      </div>
    </div>
  );
}

function AddConvertor({ onAdd, children, startsDirty }) {
  const conversions = ["", ...Object.keys(convertors)];
  const [selected, setSelected] = useState(conversions[0], startsDirty);
  return (
    <>
      <div className={styles["button_group"]}>
        <label htmlFor="conversion_select_id" name="type-select">
          Conversion:
        </label>
        <select
          className={styles["select-setting"]}
          name="type-select"
          id={styles["conversion_select_id"]}
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          {conversions.map((runner) => (
            <option key={runner} value={runner}>
              {runner}
            </option>
          ))}
        </select>

        <button
          className={`${styles["convertor_add_button"]} ${styles["button-style"]} ${styles["button-dimensions"]}`}
          name="convertor_add_button"
          disabled={selected === ""}
          onClick={() => onAdd?.(selected)}
        >
          Add +
        </button>
      </div>
      {children}
    </>
  );
}

function KBEditor({ kb, onSave, onRemove, onClear }) {
  function addKeys(kb) {
    return { ...kb, convertors: addInitialKeys(kb.convertors) };
  }
  const [value, edited, { upsert, reset }] = useObjectState(
    addKeys(kb),
    kb.fresh
  );

  async function save() {
    if (await onSave?.(value)) {
      reset();
    } else {
      console.log("Failed to save", value);
    }
  }

  return (
    <CollapsibleBox
      title={
        <>
          <i>Knowledge Base: </i>
          <span
            className={`${styles["main-heading"]} ${styles["heading_name"]}`}
          >
            {value.name}
          </span>
        </>
      }
      initiallyClosed={!value.fresh}
    >
      <div className={styles["item"]}>
        <SourceSelection
          value={value.selection}
          onChange={(v) => upsert({ selection: v })}
        />
        <div>
          <label
            className={styles["selection_model"]}
            id={styles["selection_model"]}
            htmlFor="model"
          >
            Embedding Model:
          </label>
          <input
            className={styles["input_field"]}
            id={styles["model"]}
            name="model"
            // we can do this because there isn't anything else in embedding
            onChange={(e) => upsert({ embedding: { model: e.target.value } })}
            value={value.embedding.model}
          />
        </div>
      </div>
      <ConvertorList
        value={value.convertors}
        onChange={(v) => upsert({ convertors: v })}
      >
        <div className={styles["button_group"]}>
          <EditButtons
            edited={edited}
            fresh={value.fresh}
            onSave={save}
            onReset={reset}
            onRemove={onRemove}
            onClear={onClear}
            styles={styles}
          />
        </div>
      </ConvertorList>
    </CollapsibleBox>
  );
}

function AddKnowledgeBase({ onAdd }) {
  const [name, setName] = useState("");
  const cleanName = name.trim();
  function add() {
    if (cleanName.length > 0) {
      onAdd?.(cleanName);
      setName("");
    }
  }
  return (
    <section
      className={`${styles["new_kb_section"]} ${styles["kb_service-container"]}`}
    >
      <div className={styles["item"]}>
        <h1>Add Knowledge Base</h1>
        <label className={styles["new_kb_name_label"]} htmlFor="new_kb_name_id">
          Name:
        </label>
        <input
          className={styles["input_field"]}
          id="new_kb_name_id"
          name="new_kb_name"
          placeholder="Knowledge Base Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div className={styles["add_button_cnt"]}>
          <button
            className={`${styles["button-style"]} ${styles["button-dimensions"]}`}
            onClick={add}
            disabled={cleanName.length <= 0}
          >
            Add +
          </button>
        </div>
      </div>
    </section>
  );
}

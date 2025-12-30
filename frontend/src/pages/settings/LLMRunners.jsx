import _styles from "../Settings.module.css";
import _styles2 from "../SettingsCommon.module.css";
import ListSetting from "./ListSetting";

const styles = { ..._styles, ..._styles2 };

const llmRunners = {
  debug: {
    component: DebugRunner,
    defaultValue: {
      active: true,
      type: "debug",
      name: "new_debug_runner",
    },
  },
  ollama: {
    component: OllamaRunner,
    defaultValue: {
      active: true,
      type: "ollama",
      name: "new_ollama_runner",
      host: "http://localhost:11434",
    },
  },
  huggingface: {
    component: HuggingFaceRunner,
    defaultValue: {
      active: true,
      type: "huggingface",
      name: "new_huggingface_runner",
      api_token: "hf_[rest of your token here]",
    },
  },
  openai: {
    component: OpenAIRunner,
    defaultValue: {
      active: true,
      type: "openai",
      name: "new_openai_runner",
      api_key: "sk-proj-[rest of your key here]",
    },
  },
};

const externalServiceWarning = (
  <div className={styles["warning"]}>
    This is an external service! Be aware of their privacy policies.
  </div>
);
function DebugRunner({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    const newValue = { ...value, [n]: type === "checkbox" ? checked : v };
    onChange?.(newValue);
  }
  return (
    <>
      <div className={styles.setting}>
        <label htmlFor="type" name="type">
          Type:
        </label>
        <input name="type" id="type" defaultValue={value.type} readOnly />
      </div>

      <div className={styles.setting}>
        <label htmlFor="name">Name:</label>
        <input
          id="name"
          name="name"
          value={value.name}
          onChange={updateValue}
        />
      </div>

      <div className={styles["checkbox-wrapper"]}>
        <label htmlFor="active">Active:</label>
        <input
          id="active"
          className={styles["checkbox"]}
          name="active"
          type="checkbox"
          checked={Boolean(value.active)}
          onChange={updateValue}
          title="Active / Inactive"
        />
      </div>
    </>
  );
}

function OllamaRunner({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    const newValue = { ...value, [n]: type === "checkbox" ? checked : v };
    onChange?.(newValue);
  }
  return (
    <>
      <div className={styles.setting}>
        <label htmlFor="type" name="type">
          Type:
        </label>
        <input name="type" id="type" defaultValue={value.type} readOnly />
      </div>
      <div className={styles.setting}>
        <label htmlFor="name">Name:</label>
        <input
          id="name"
          name="name"
          value={value.name}
          onChange={updateValue}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="host">Host:</label>
        <input
          id="host"
          name="host"
          value={value.host}
          onChange={updateValue}
        />
      </div>

      <div className={styles["checkbox-wrapper"]}>
        <label htmlFor="active">Active:</label>
        <input
          className={styles["checkbox"]}
          id="active"
          name="active"
          type="checkbox"
          checked={Boolean(value.active)}
          onChange={updateValue}
          title="Active / Inactive"
        />
      </div>
    </>
  );
}

function HuggingFaceRunner({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    const newValue = { ...value, [n]: type === "checkbox" ? checked : v };
    onChange?.(newValue);
  }
  return (
    <>
      <div className={styles.setting}>
        <label htmlFor="type" name="type">
          Type:
        </label>
        <input name="type" id="type" defaultValue={value.type} readOnly />
      </div>
      <div className={styles.setting}>
        <label htmlFor="api_name"> Name:</label>
        <input
          id="api_name"
          name="name"
          value={value.name}
          onChange={updateValue}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="api">API token:</label>
        <input
          id="api"
          name="api_token"
          value={value.api_token}
          onChange={updateValue}
        />
      </div>

      <div className={styles["checkbox-wrapper"]}>
        <label htmlFor="active">Active:</label>
        <input
          className={styles["checkbox"]}
          id="active"
          name="active"
          type="checkbox"
          checked={Boolean(value.active)}
          onChange={updateValue}
          title="Active / Inactive"
        />
      </div>
    </>
  );
}

function OpenAIRunner({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const checked = target.checked;
    const type = target.type;
    const newValue = { ...value, [n]: type === "checkbox" ? checked : v };
    onChange?.(newValue);
  }
  return (
    <>
      {externalServiceWarning}
      <div className={styles.setting}>
        <label htmlFor="type" name="type">
          Type:
        </label>
        <input name="type" id="type" defaultValue={value.type} readOnly />
      </div>
      <div className={styles.setting}>
        <label htmlFor="api_name"> Name:</label>
        <input
          id="api_name"
          name="name"
          value={value.name}
          onChange={updateValue}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="api">API key:</label>
        <input
          id="api"
          name="api_key"
          value={value.api_key}
          onChange={updateValue}
        />
      </div>

      <div className={styles["checkbox-wrapper"]}>
        <label htmlFor="active">Active:</label>
        <input
          id="active"
          className={styles["checkbox"]}
          name="active"
          type="checkbox"
          checked={Boolean(value.active)}
          onChange={updateValue}
          title="Active / Inactive"
        />
      </div>
    </>
  );
}

export default function LLMRunners({ initial, onSave }) {
  return (
    <>
      <ListSetting
        initial={initial}
        onSave={onSave}
        types={llmRunners}
        title="LLM Runners"
        description={
          <p>
            Control which LLM runners are available and adjust their order to
            define priority — the top runner has the highest priority.
          </p>
        }
      />
    </>
  );
}

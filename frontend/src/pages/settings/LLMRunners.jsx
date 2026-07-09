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
      seed: 42,
      num_predict: 8000,
      num_ctx: 16000,
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
  remote: {
    component: RemoteRunner,
    defaultValue: {
      active: true,
      type: "remote",
      name: "new_remote_runner",
      url: "http://localhost:5101/api",
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
      default:
        parsedValue = v;
    }
    const newValue = { ...value, [n]: parsedValue };
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

      <div className={styles.setting}>
        <label htmlFor="seed">seed (0 for random):</label>
        <input
          id="seed"
          name="seed"
          value={value.seed}
          type="number"
          min={0}
          step={1}
          onChange={updateValue}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="num_predict">num_predict:</label>
        <input
          id="num_predict"
          name="num_predict"
          value={value.num_predict}
          type="number"
          min={0}
          step={1}
          onChange={updateValue}
        />
      </div>

      <div className={styles.setting}>
        <label htmlFor="num_ctx">num_ctx:</label>
        <input
          id="num_ctx"
          name="num_ctx"
          value={value.num_ctx}
          type="number"
          min={0}
          step={1}
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
          type="password"
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

function RemoteRunner({ value, onChange }) {
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
      {"Custom remote runner. See docs on how to implement. (BETA)"}
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
        <label htmlFor="url">API url:</label>
        <input
          id="url"
          name="url"
          value={value.url}
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

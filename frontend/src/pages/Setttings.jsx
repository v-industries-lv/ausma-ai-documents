import { useContext, useEffect, useState } from "react";
import "./Index.css";
import _styles from "./Settings.module.css";
import _styles2 from "./SettingsCommon.module.css";
import _styles3 from "../components/ThemeSelector.module.css";
import CollapsibleBox from "../components/CollapsibleBox";
import DocumentSources from "./settings/DocumentSources";
import LLMRunners from "./settings/LLMRunners";
import Assistants from "./settings/Assistants.jsx";
import KBStores from "./settings/KBStores";
import {
  useObjectState,
  useStringState,
} from "../components/useResetableState";
import EditButtons from "../components/EditButtons";
import KnowledgeBaseSelector from "../components/KnowledgeBaseSelector";
import Spinner from "../components/Spinner";
import { UsernameContext } from "../components/UserName";
import { THEMES } from "../../src/styles/themeList.js";
import AssistantSelector from "../components/AssistantSelector.jsx";
import AboutIcon from "../components/Icons/AboutIcon";

const styles = { ..._styles, ..._styles2, ..._styles3 };

export default function Settings() {
  const [isLoading, setLoading] = useState(true);
  const [config, setConfig] = useState({
    room_defaults: {},
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
        <h1
          className={`${styles["main-heading"]} ${styles["main-heading-color"]}`}
        >
          Settings
        </h1>
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
            <Assistants
              initial={config.assistants}
              onSave={(value) => saveSetting("assistants", value)}
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
      <GeneralSettingOptions initial={username} onSave={setUsername} />
    </CollapsibleBox>
  );
}

function GeneralSettingOptions({ initial, onSave }) {
  const [value, edited, { edit, reset }] = useStringState(initial);

  const savedTheme = localStorage.getItem("theme");
  const browserPrefersDark = window.matchMedia(
    "(prefers-color-scheme: dark)",
  ).matches;
  const defaultTheme = savedTheme || (browserPrefersDark ? "dark" : "light");

  const [theme, setTheme] = useState(defaultTheme);
  const [themeEdited, setThemeEdited] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);

    return () => {
      const stored =
        localStorage.getItem("theme") ||
        (browserPrefersDark ? "dark" : "light");
      document.documentElement.setAttribute("data-theme", stored);
    };
  }, [theme, browserPrefersDark]);

  function onThemeChange(newTheme) {
    setTheme(newTheme);
    setThemeEdited(true);
  }

  function save() {
    onSave?.(value);
    reset();

    localStorage.setItem("theme", theme);
    setThemeEdited(false);
  }

  function resetAll() {
    reset();
    const stored = savedTheme || (browserPrefersDark ? "dark" : "light");
    setTheme(stored);
    setThemeEdited(false);
  }

  return (
    <>
      <div className={styles["general_settings_section"]}>
        <h3>Username Settings</h3>
        <p>
          Your username is associated with the messages you write in the
          chatrooms. It is set per browser. I.e. if you open ausma.ai from
          Firefox and Chrome you may set different usernames.
        </p>
        {
          // TODO use more generic classes for CSS
        }
        <div className={styles.setting}>
          <label htmlFor="username">Username:</label>
          <input id="username" name="username" value={value} onChange={edit} />
        </div>
      </div>

      <div className={styles["select-ctn"]}>
        <h3 className={styles["option-subheading"]}>Theme Settings</h3>
        <p>Choose a theme from the dropdown.</p>
        <label htmlFor="theme-select">Theme:</label>
        <select
          id="theme-select"
          value={theme}
          onChange={(e) => onThemeChange(e.target.value)}
        >
          {[...THEMES]
            .sort((a, b) =>
              a.label.localeCompare(b.label, undefined, {
                sensitivity: "base",
              }),
            )
            .map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
        </select>
      </div>

      <div className={styles["button-row-right"]}>
        <EditButtons
          edited={edited || themeEdited}
          onSave={save}
          onReset={resetAll}
          styles={styles}
        />
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
  const assistant = value?.assistant;

  function setAssistant(_assistant) {
    const newValue =
      typeof _assistant === "function" ? _assistant(assistant) : _assistant;
    upsert({
      assistant: newValue,
    });
  }

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
        maxWidth="100%"
        dynamicWidth={false}
      />
      <AssistantSelector
        assistant={assistant}
        setAssistant={setAssistant}
        className={styles["select-ctn"]}
        maxWidth="100%"
        dynamicWidth={false}
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

function GenerationGuard({ initial, onSave }) {
  const [value, edited, { upsert, reset }] = useObjectState(initial);

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

  function save() {
    onSave?.(value);
    reset();
  }

  return (
    <CollapsibleBox className={styles["setting-list"]} title="Generation Guard">
      <p>Generation Guard detects LLM infinite generation.</p>

      <div className={styles.setting}>
        <label htmlFor="safe_token_threshold_id">
          Safe token threshold:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Safe token threshold - Starts detecting infinite loop patterns after certain threshold."
          />
        </label>
        <input
          type="number"
          min={0}
          className={styles["input_field"]}
          id="safe_token_threshold_id"
          name="safe_token_threshold"
          value={value.safe_token_threshold}
          onChange={handleInputChange}
        />

        <label htmlFor="token_check_interval_id">
          Token check interval:
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Token check interval - How often, in tokens, to check for infinite loop patterns."
          />
        </label>
        <input
          type="number"
          min={1}
          className={styles["input_field"]}
          id="token_check_interval_id"
          name="token_check_interval"
          value={value.token_check_interval}
          onChange={handleInputChange}
        />

        <label htmlFor="max_repeats_id">
          Max repeats:{" "}
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Max repeats - How many repeating token patterns should be detected to stop generation."
          />
        </label>
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
          <AboutIcon
            className={`${styles["help_icon"]}`}
            title="Window size - The size of token pattern window."
          />
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

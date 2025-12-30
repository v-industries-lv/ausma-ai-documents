import _styles from "../Settings.module.css";
import _styles2 from "../SettingsCommon.module.css";
import ListSetting from "./ListSetting";

const styles = { ..._styles, ..._styles2 };

const docSources = {
  local_fs: {
    component: LocalFileSystem,
    defaultValue: {
      doc_source_type: "local_fs",
      name: "default_local",
      root_path: "documents",
    },
  },
};

function LocalFileSystem({ value, onChange }) {
  function updateValue(e) {
    const target = e.target;
    const n = target.name;
    const v = target.value;
    const newValue = { ...value, [n]: v };
    onChange?.(newValue);
  }
  return (
    <>
      <div className={styles.setting}>
        <label htmlFor="doc_source_type">Type:</label>
        <input
          id="doc_source_type"
          name="doc_source_type"
          defaultValue={value.doc_source_type}
          readOnly
        />
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
        <label htmlFor="root_path">Root Path:</label>
        <input
          id="root_path"
          name="root_path"
          value={value.root_path}
          onChange={updateValue}
        />
      </div>
    </>
  );
}

export default function DocumentSources({ initial, onSave }) {
  return (
    <ListSetting
      initial={initial}
      onSave={onSave}
      types={docSources}
      typeParameter="doc_source_type"
      title="Document Sources"
      description={
        <p>Add folders to specify where your documents are stored.</p>
      }
    />
  );
}

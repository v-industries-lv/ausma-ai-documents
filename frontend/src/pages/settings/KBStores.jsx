import _styles from "../Settings.module.css";
import _styles2 from "../SettingsCommon.module.css";
import ListSetting from "./ListSetting";

const styles = { ..._styles, ..._styles2 };

const kbstores = {
  chroma: {
    component: Chroma,
    defaultValue: {
      store_type: "chroma",
      name: "chroma_store",
      kb_store_folder: "knowledge_bases/chroma",
    },
  },
};

function Chroma({ value, onChange }) {
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
        <label htmlFor="store_type">Type:</label>
        <input
          id="store_type"
          name="store_type"
          defaultValue={value.store_type}
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
        <label htmlFor="kb_store_folder">Folder:</label>
        <input
          id="kb_store_folder"
          name="kb_store_folder"
          value={value.kb_store_folder}
          onChange={updateValue}
        />
      </div>
    </>
  );
}

export default function KBStores({ initial, onSave }) {
  return (
    <ListSetting
      initial={initial}
      onSave={onSave}
      types={kbstores}
      typeParameter="store_type"
      title="Knowledge Base Stores"
      description={
        <p>
          Select the location(s) where knowledge bases are stored. Newly created
          knowledge bases appear at the top of the list by default. Locations
          listed higher have greater priority.
        </p>
      }
    />
  );
}

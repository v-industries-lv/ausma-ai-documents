import React from "react";
import { useState } from "react";
import CollapsibleBox from "../../components/CollapsibleBox";
import { useListState } from "../../components/useResetableState";
import _styles from "../Settings.module.css";
import _styles2 from "../SettingsCommon.module.css";
import { addInitialKeys, addKey } from "../../utils/listTools";
import EditButtons from "../../components/EditButtons";
import ListEditButtons from "../../components/ListEditButtons";

const styles = { ..._styles, ..._styles2 };

export default function ListSetting({
  initial,
  onSave,
  types,
  title,
  description,
  typeParameter = "type",
}) {
  const [value, edited, { add, update, remove, swap, reset }] = useListState(
    addInitialKeys(initial ?? [])
  );
  function addItem(type) {
    const defaultValue = types[type]?.defaultValue;
    if (defaultValue) {
      add(addKey(defaultValue));
    }
  }

  function save() {
    onSave?.(value);
    reset();
  }

  return (
    <CollapsibleBox className={styles["setting-list"]} title={title}>
      {description}
      <div className={styles["llm-runners-list"]}>
        {value.map((item, i) => {
          return (
            <div className={styles["llm-runners-item"]} key={item.key}>
              {React.createElement(types[item[typeParameter]].component, {
                value: item,
                onChange: update,
                key: item.key,
              })}
              <ListEditButtons
                styles={styles}
                onRemove={() => remove(item.key)}
                onMoveUp={i > 0 ? () => swap(i - 1, i) : undefined}
                onMoveDown={
                  i < value.length - 1 ? () => swap(i, i + 1) : undefined
                }
              />
            </div>
          );
        })}
      </div>

      <div className={styles["button-row-two-sides"]}>
        <AddRunner onAdd={addItem} types={types} />
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

function AddRunner({ onAdd, types: allTypes }) {
  const types = ["", ...Object.keys(allTypes)];
  const [selected, setSelected] = useState(types[0]);
  return (
    <div className={styles["button_group"]}>
      <label htmlFor="new-llm-runner-type" name="type-select">
        Type:
      </label>
      <select
        className={styles["select-setting"]}
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
      >
        {types.map((runner) => (
          <option key={runner} value={runner}>
            {runner}
          </option>
        ))}
      </select>

      <button
        className={`${styles["button-style"]} ${styles["button-dimensions"]}`}
        disabled={selected === ""}
        onClick={() => onAdd?.(selected)}
      >
        Add +
      </button>
    </div>
  );
}

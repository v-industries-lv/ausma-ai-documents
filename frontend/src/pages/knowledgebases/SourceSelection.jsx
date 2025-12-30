import { useEffect, useState } from "react";
import FullScreenModal from "../../components/FullScreenModal";

import _styles from "../KnowledgeBases.module.css";
import _styles2 from "../SettingsCommon.module.css";
import _styles3 from "../../components/SmallButtons.module.css";
import _styles4 from "./SourceSelection.module.css";
import Spinner from "../../components/Spinner";
import { uniqueValues } from "../../utils/listTools";
import { useStringListState } from "../../components/useResetableState";

const styles = { ..._styles, ..._styles2, ..._styles3, ..._styles4 };

export default function SourceSelection({ value: _values, onChange }) {
  const [modalClosed, setModalClosed] = useState(true);
  const cleanedValues = uniqueValues(_values.toSorted());
  const [value, edited, { add, remove, reset }] =
    useStringListState(cleanedValues);
  function handleClose() {
    setModalClosed(true);
    reset();
  }

  function onSave() {
    onChange(value);
    setModalClosed(true);
    reset();
  }

  const [selected, setSelected] = useState(null);
  function onFileAdd() {
    const file = selected;
    if (file.is_file) {
      add(file.path);
    } else if (file.is_dir) {
      add(file.path + "/**");
    }
  }

  return (
    <>
      <div className={styles["item_input_selection"]}>
        <label className={styles["selection_label"]} htmlFor="selection">
          Selection:
        </label>
        <div className={styles["wrapper"]}>
          <SingleFieldEditor onChange={onChange} value={value} />
          <div className={styles["button-container"]}>
            <button
              title="Document Source"
              className={`${styles["button-style"]} ${styles["small-btn"]}`}
              onClick={() => setModalClosed(false)}
            >
              <b>&#8230;</b>
            </button>
          </div>
        </div>
      </div>
      <FullScreenModal
        isClosed={modalClosed}
        onClickOff={handleClose}
        className={styles["modal"]}
      >
        <h1>Document Selection </h1>
        <div className={styles["content_layout"]}>
          <div className={styles["wrapper2"]}>
            <h1>All Documents</h1>
            <div className={styles["scroll"]}>
              <DocSelector selected={selected} setSelected={setSelected} />
            </div>
            <div className={styles["button-row-center"]}>
              <button
                title="Add Document"
                className={`${styles["button-style"]} ${styles["button-dimensions"]}`}
                onClick={onFileAdd}
                disabled={selected === null}
              >
                Add +
              </button>
            </div>
          </div>
          <div className={styles["wrapper2"]}>
            <h1>Selection</h1>
            <ul className={`${styles["current_list"]} ${styles["scroll"]}`}>
              {value.map((path, i) => (
                <li key={path}>
                  {path}
                  <img
                    src="/static/svg-icons/trash-bin-trash-svgrepo-com.svg"
                    className={`${styles["remove_room_image"]} ${styles["hover_btn"]}`}
                    data-value="${room.id}"
                    data-name="${fullName}"
                    style={{
                      height: "20px",
                      cursor: "pointer",
                      width: "20px",
                      verticalAlign: "middle",
                    }}
                    title="Remove Document"
                    onClick={() => remove(i)}
                  />
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className={styles["footer-cnt"]}>
          <div>
            <ManualEntry add={add} />
          </div>
          <div className={styles["button-row-right"]}>
            <div className={styles["button_group"]}>
              <button
                className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
                onClick={onSave}
              >
                OK
              </button>
              <button
                className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
                onClick={handleClose}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </FullScreenModal>
    </>
  );
}

function SingleFieldEditor({ onChange, value }) {
  function handleChange(e) {
    const newValue = e.target.value;
    const selectionArray = newValue
      .split(";")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    onChange?.(selectionArray);
  }
  return (
    <input
      className={styles["input_field"]}
      title="Document Source"
      id="selection"
      name="selection"
      value={value.join("; ")}
      onChange={handleChange}
    />
  );
}

function ManualEntry({ add }) {
  const [fieldValue, setFieldValue] = useState("");

  function onEnter() {
    add(fieldValue);
    setFieldValue("");
  }

  function handleKeyPress(e) {
    if (e.key === "Enter") {
      onEnter();
      e.preventDefault();
    }
  }
  return (
    <>
      <div
        className={styles["manual-entry-cnt"]}
        style={{ display: "grid", gridTemplateColumns: "auto 100px" }}
      >
        <input
          placeholder="Enter manual path here"
          title="Enter path"
          onChange={(e) => setFieldValue(e.target.value)}
          value={fieldValue}
          onKeyDown={handleKeyPress}
        />
        <button
          title="Add Path"
          className={`${styles["button-style"]} ${styles["button-dimensions"]}`}
          onClick={onEnter}
          disabled={fieldValue.length <= 0}
        >
          Add +
        </button>
      </div>
    </>
  );
}

function Directory({ docSource, selected, setSelected, prefix = "" }) {
  const [_isOpen, _setIsOpen] = useState({});
  function isOpen(path) {
    return _isOpen[path] ?? false;
  }
  function open(path) {
    _setIsOpen((_isOpen) => ({ ..._isOpen, [path]: true }));
  }

  function close(path) {
    _setIsOpen((_isOpen) => {
      const { [path]: _, ...newValue } = _isOpen;
      return newValue;
    });
  }

  const [files, setFiles] = useState(null);
  useEffect(() => {
    async function load() {
      const files = await docSource(prefix);
      setFiles(files);
    }
    load();
  }, [docSource, prefix]);

  function renderFile(file) {
    const path = file.path;
    const __isOpen = isOpen(path);
    const name = path.substring(prefix.length);

    let controls = <span>&nbsp;&nbsp;</span>;
    if (file.is_dir) {
      if (__isOpen) {
        controls = <span onClick={() => close(path)}>-&nbsp;</span>;
      } else {
        controls = <span onClick={() => open(path)}>+&nbsp;</span>;
      }
    }

    return (
      <li
        key={file.path}
        style={{
          display: "block",
          color: selected?.path === file.path ? "#fa994a" : null,
        }}
      >
        {controls}
        <span onClick={() => setSelected(file)}>{name}</span>
        {__isOpen && (
          <Directory
            docSource={docSource}
            selected={selected}
            setSelected={setSelected}
            prefix={file.path + "/"}
          />
        )}
      </li>
    );
  }

  if (files === null) {
    return (
      <span>
        <Spinner />
        Loading ...
      </span>
    );
  }

  return <ul>{files.map(renderFile)}</ul>;
}

function DocSelector({ selected, setSelected }) {
  async function getFiles(prefix) {
    const req = await fetch(`/api/doc/${prefix}*`);
    return await req.json();
  }

  return (
    <Directory
      docSource={getFiles}
      selected={selected}
      setSelected={setSelected}
    />
  );
}

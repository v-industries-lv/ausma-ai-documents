import styles2 from "./EditButtons.module.css";

export default function EditButtons({
  styles,
  edited,
  fresh = false,
  onSave,
  onReset,
  onRemove,
  onClear,
}) {
  return (
    <>
      <div className={styles2.buttons}>
        <button
          className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
          style={edited ? { backgroundColor: "#fa994a" } : {}}
          onClick={onSave}
        >
          Save
        </button>
        <button
          className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
          onClick={onReset}
          disabled={fresh}
        >
          Cancel
        </button>
        {onClear && (
          <button
            onClick={onClear}
            className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
          >
            Clear
          </button>
        )}
        {onRemove && (
          <button
            onClick={onRemove}
            className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
          >
            Remove &#x2212;
          </button>
        )}
      </div>
    </>
  );
}

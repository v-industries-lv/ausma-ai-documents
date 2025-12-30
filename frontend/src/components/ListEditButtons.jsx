import componentStyles from "./ListEditButtons.module.css";

export default function ListEditButtons({
  styles,
  onRemove,
  onMoveUp,
  onMoveDown,
}) {
  return (
    <div
      className={`${styles["button_group"]} ${styles["list_item_btn_group"]}`}
    >
      <button
        className={`${styles["button-dimensions"]} ${styles["button-style"]}`}
        onClick={onRemove}
      >
        Remove &#x2212;
      </button>
      <button
        className={`${styles["move-up"]} ${styles["button-dimensions"]} ${styles["button-style"]}`}
        disabled={!onMoveUp}
        onClick={onMoveUp}
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
        className={`${styles["move-down"]} ${styles["button-dimensions"]} ${styles["button-style"]}`}
        disabled={!onMoveDown}
        onClick={onMoveDown}
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
  );
}

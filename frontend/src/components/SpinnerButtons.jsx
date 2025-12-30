import { useRef } from "react";
import _styles from "./SmallButtons.module.css";
import _styles2 from "../pages/SettingsCommon.module.css";

const styles = { ..._styles, ..._styles2 };

export default function SpinnerButtons({
  value,
  onChange,
  step = 1,
  min = -Infinity,
  max = Infinity,
}) {
  const timeoutRef = useRef(null);
  const currentValue = useRef(value);
  const delayRef = useRef(300);

  currentValue.current = value;

  const clampAndRound = (val) => {
    let clamped = Math.min(max, Math.max(min, val));
    clamped = Math.round(clamped / step) * step;
    const stepDecimals = (step.toString().split(".")[1] || "").length;
    clamped = Number(clamped.toFixed(stepDecimals));
    return clamped;
  };

  const startAutoChange = (type) => {
    const action = () => {
      let newValue;
      if (type === "up") {
        newValue = clampAndRound(currentValue.current + step);
      } else {
        newValue = clampAndRound(currentValue.current - step);
      }
      currentValue.current = newValue;
      onChange(newValue);

      delayRef.current = Math.max(50, delayRef.current - 20);

      timeoutRef.current = setTimeout(action, delayRef.current);
    };

    action();
  };

  const stopAutoChange = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    delayRef.current = 300;
  };

  return (
    <>
      <div className={styles["button-container"]}>
        <button
          onMouseDown={() => startAutoChange("up")}
          onMouseUp={stopAutoChange}
          onMouseLeave={stopAutoChange}
          disabled={value >= max}
          className={`${styles["button-style"]} ${styles["small-btn"]}`}
          title="Increase Value"
        >
          ▲
        </button>
        <button
          onMouseDown={() => startAutoChange("down")}
          onMouseUp={stopAutoChange}
          onMouseLeave={stopAutoChange}
          disabled={value <= min}
          className={`${styles["button-style"]} ${styles["small-btn"]}`}
          title="Decrease Value"
        >
          ▼
        </button>
      </div>
    </>
  );
}

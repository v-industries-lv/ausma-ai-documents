import { useEffect, useState, useRef } from "react";
import styles from "./Selector.module.css";

export default function KnowledgeBaseSelector({
  kb,
  setKb,
  className,
  maxWidth = 100,
  dynamicWidth = true,
}) {
  const [kbs, setKbs] = useState([]);
  const selectRef = useRef(null);
  const measureRef = useRef(null);

  useEffect(() => {
    if (!selectRef.current) return;

    if (!dynamicWidth) {
      selectRef.current.style.removeProperty("width");
      return;
    }

    if (!measureRef.current || !kb) return;

    measureRef.current.textContent = kb;

    const width = measureRef.current.offsetWidth + 40;

    selectRef.current.style.width = `${width}px`;
  }, [kb, dynamicWidth]);

  useEffect(() => {
    async function fetchKBs() {
      const req = await fetch("/api/kb/");
      const json = [{ name: "None" }, ...(await req.json())];
      setKbs(json ?? []);
    }
    fetchKBs();
  }, []);

  function shortenName(name) {
    if (name.length <= maxWidth) {
      return name;
    }
    return name.substring(0, maxWidth) + "...";
  }

  return (
    <div className={`${styles["select-ctn"]} ${className}`} title={kb}>
      <label for="kb">Knowledge base:</label>
      <select
        ref={selectRef}
        className={`${styles.select} ${dynamicWidth ? styles["dynamic-select"] : styles["static-select"]}`}
        style={{ maxWidth }}
        name="kb_name"
        value={kb}
        onChange={(e) => setKb(e.target.value)}
        title={kb.name}
      >
        {kbs.map((kb) => (
          <option value={kb.name} key={kb.name}>
            {kb.name}
          </option>
        ))}
      </select>
      <span ref={measureRef} className={styles["measure-span"]} />
    </div>
  );
}

import { useEffect, useState, useRef } from "react";
import styles from "./Selector.module.css";

export default function KnowledgeBaseSelector({
  selectedKbs,
  setSelectedKbs,
  className,
  dynamicWidth = true,
}) {
  const [kbs, setKbs] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    async function fetchKBs() {
      const req = await fetch("/api/kb/");
      const json = await req.json();
      setKbs(json ?? []);
    }
    fetchKBs();
  }, []);

  function toggleKb(name) {
    setSelectedKbs((current) => {
      if (current.includes(name)) {
        return current.filter((item) => item !== name);
      }

      return [...current, name];
    });
  }

  function toggleAllKbs() {
    setSelectedKbs((current) => {
      if (current.length === kbs.length) {
        return [];
      }

      return kbs.map((kb) => kb.name);
    });
  }

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div
      className={`${styles["select-ctn"]} ${className}`}
      ref={dropdownRef}
      title={`Selected Knowledge Bases:\n${selectedKbs.join("\n")}`}
    >
      <button
        type="button"
        className={`${styles.select} ${
          dynamicWidth ? styles["dynamic-select"] : styles["static-select"]
        } ${isOpen && dynamicWidth ? styles["dynamic-select-open"] : ""}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={styles["select-label"]}>Knowledge base:</span>
        <span className={styles["select-value"]}>
          {selectedKbs?.length === 0
            ? "None"
            : selectedKbs.length === 1
              ? selectedKbs[0]
              : `${selectedKbs.length} selected`}
        </span>
        <span className={styles["select-arrow"]}>
          <svg
            width="9"
            height="8"
            viewBox="0 0 12 8"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M1 1.5L6 6.5L11 1.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </button>
      {isOpen && (
        <div
          className={`${styles["dropdown-menu-base"]} ${
            dynamicWidth
              ? styles["dropdown-menu-dynamic"]
              : styles["dropdown-menu-static"]
          }`}
        >
          <label className={styles["dropdown-option"]}>
            <input
              type="checkbox"
              checked={kbs.length > 0 && selectedKbs.length === kbs.length}
              onChange={toggleAllKbs}
            />

            <span className={styles["dropdown-option-name"]}>Select all</span>
          </label>

          <div className={styles["dropdown-divider"]} />
          <div className={styles["dropdown-menu-content"]}>
            {kbs.map((kb) => (
              <label key={kb.name} className={styles["dropdown-option"]}>
                <input
                  type="checkbox"
                  checked={selectedKbs.includes(kb.name)}
                  onChange={() => toggleKb(kb.name)}
                />
                <span
                  className={styles["dropdown-option-name"]}
                  title={kb.name}
                >
                  {kb.name}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

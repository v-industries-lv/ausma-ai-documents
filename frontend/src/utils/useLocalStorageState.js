import { useState } from "react";

export function useLocalStorageState(property, initial) {
  const [value, _setValue] = useState(
    () => window.localStorage.getItem(property) ?? initial
  );
  function setValue(v) {
    window.localStorage.setItem(property, v);
    _setValue(v);
  }
  return [value, setValue];
}

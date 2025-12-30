import { useState } from "react";

export function useStringState(initial, startsDirty) {
  const [_value, setValue] = useState(initial ?? "");
  const [edited, setEdited] = useState(startsDirty ?? false);
  const value = edited ? _value : initial;
  function reset() {
    setValue(initial);
    setEdited(false);
  }
  function update(v) {
    setValue(v);
    setEdited(true);
  }
  function edit(e) {
    update(e.target.value);
  }
  return [value, edited, { edit, update, reset }];
}

export function useObjectState(initial, startsDirty) {
  const [_value, setValue] = useState(initial ?? {});
  const [edited, setEdited] = useState(startsDirty ?? false);
  const value = edited ? _value : initial;
  function reset() {
    setValue(initial);
    setEdited(false);
  }
  function upsert(o) {
    ensureLatestInitial();
    setValue((value) => ({ ...value, ...o }));
    setEdited(true);
  }

  function ensureLatestInitial() {
    if (!edited) {
      setValue(initial);
    }
  }
  return [value, edited, { upsert, reset }];
}

export function useListState(initial, startsDirty) {
  const [_value, setValue] = useState(initial);
  const [edited, setEdited] = useState(startsDirty ?? false);
  const value = edited ? _value : initial;

  function update(v) {
    ensureLatestInitial();
    setValue(value.map((item) => (item.key === v.key ? v : item)));
    setEdited(true);
  }

  function ensureLatestInitial() {
    if (!edited) {
      setValue(initial);
    }
  }

  function reset() {
    setEdited(false);
  }

  function add(v) {
    ensureLatestInitial();
    setValue((value) => {
      const newValue = [...value, v];
      return newValue;
    });
    setEdited(true);
  }

  function remove(key) {
    ensureLatestInitial();
    setValue((value) => value.filter((v) => v.key !== key));
    setEdited(true);
  }

  function swap(i1, i2) {
    if (i1 >= 0 && i1 < value.length && i2 >= 0 && i2 < value.length) {
      ensureLatestInitial();
      setValue((value) => {
        const newValue = [...value];
        const tmp = newValue[i1];
        newValue[i1] = newValue[i2];
        newValue[i2] = tmp;
        return newValue;
      });
      setEdited(true);
    }
  }

  return [value, edited, { add, update, remove, swap, reset }];
}

export function useStringListState(initial, startsDirty) {
  const [_value, setValue] = useState(initial);
  const [edited, setEdited] = useState(startsDirty ?? false);
  const value = edited ? _value : initial;

  function ensureLatestInitial() {
    if (!edited) {
      setValue(initial);
    }
  }

  function reset() {
    setEdited(false);
  }

  function add(s) {
    ensureLatestInitial();
    setValue((value) => {
      const newValue = [...value, s];
      return newValue;
    });
    setEdited(true);
  }

  function removeAll(s) {
    ensureLatestInitial();
    setValue((value) => value.filter((v) => v !== s));
    setEdited(true);
  }

  function remove(index) {
    ensureLatestInitial();
    setValue((value) => value.filter((v, i) => i !== index));
    setEdited(true);
  }

  function swap(i1, i2) {
    if (i1 >= 0 && i1 < value.length && i2 >= 0 && i2 < value.length) {
      ensureLatestInitial();
      setValue((value) => {
        const newValue = [...value];
        const tmp = newValue[i1];
        newValue[i1] = newValue[i2];
        newValue[i2] = tmp;
        return newValue;
      });
      setEdited(true);
    }
  }

  return [value, edited, { add, remove, removeAll, swap, reset }];
}

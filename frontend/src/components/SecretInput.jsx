import { useState } from "react";

export default function SecretInput ( {id, name, value, onChange} ) {
    function handleOnChange(e) {
        setIsDirty(true);
        onChange(e);
    }

    const [isDirty, setIsDirty] = useState(false);
    return <input
      id={id}
      name={name}
      value={isDirty ? value  : ``}
      placeholder={!value ? `` : `[hidden]`}
      onChange={handleOnChange}
      type="password"
    />
}
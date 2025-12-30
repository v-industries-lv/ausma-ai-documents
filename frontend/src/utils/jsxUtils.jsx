export function renderNewLines(txt) {
  const arr = txt.split("\n");
  const len = arr.length;
  return arr.map((line, i) => (
    <>
      {line}
      {i < len - 1 && <br />}
    </>
  ));
}

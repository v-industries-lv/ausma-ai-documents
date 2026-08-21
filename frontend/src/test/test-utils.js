
export function getOptions(llmModel) {
  const options = [...llmModel.querySelectorAll("option")];
  const values = options.map((o) => ({ value: o.value, text: o.innerHTML }));
  return values;
}

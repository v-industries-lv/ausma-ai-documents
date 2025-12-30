export function addInitialKeys(list) {
  return list.map((s, i) => ({ ...s, key: `old_${i}` }));
}

export function addKey(value) {
  const key = `new_${new Date().getUTCMilliseconds()}`;
  return { ...value, key };
}

export function uniqueValues(arr) {
  let arr2 = [];
  for (let i = 0; i < arr.length; i++) {
    const element = arr[i];
    if (!arr2.includes(element)) {
      arr2.push(element);
    }
  }
  return arr2;
}

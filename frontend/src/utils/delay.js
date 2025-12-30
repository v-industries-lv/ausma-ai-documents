// return the value after a delay
export default function delay(value, delay) {
  if (value.then) {
    // value is a Promise
    return new Promise((resolve) =>
      value.then((v) => setTimeout(resolve, delay, value))
    );
  } else {
    return new Promise((resolve) => setTimeout(resolve, delay, value));
  }
}

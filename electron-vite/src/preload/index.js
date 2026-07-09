const usernameArgPrefix = "--defaultUsername=";
const usernameSetting = "username";

process.argv.forEach((arg) => {
  if (arg.startsWith(usernameArgPrefix)) {
    const current = window.localStorage.getItem(usernameSetting);
    if (current === null) {
      const newValue = arg.substring(usernameArgPrefix.length);
      window.localStorage.setItem(usernameSetting, newValue);
    }
  }
});

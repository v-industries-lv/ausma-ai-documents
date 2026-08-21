const {ipcRenderer} = require('electron/renderer')
const { contextBridge } = require('electron');

const usernameArgPrefix = "--defaultUsername=";
const usernameSetting = "username";

contextBridge.exposeInMainWorld('electron', {
  showItemInFolder: (filePath) =>
    ipcRenderer.invoke('show-item-in-folder', filePath),
})

process.argv.forEach((arg) => {
  if (arg.startsWith(usernameArgPrefix)) {
    const current = window.localStorage.getItem(usernameSetting);
    if (current === null) {
      const newValue = arg.substring(usernameArgPrefix.length);
      window.localStorage.setItem(usernameSetting, newValue);
    }
  }
});
